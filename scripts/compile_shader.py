#!/usr/bin/env python3
"""Offline GLSL compilation matrix; this does not emulate Iris/OptiFine or a GPU.

Requires Khronos glslang (glslangValidator also works). Includes and profile
options are expanded before compiling each vertex/fragment pair at its declared
GLSL version. Loader macros are synthetic capability environments, not evidence
that a particular loader binary runs on every Minecraft release.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SHADERS = ROOT / "shaders"
# Every boundary used by MC_VERSION conditions in the supported range, plus
# the calendar-version releases. Property-only boundaries are tested separately.
VERSIONS = ("1.16.5", "1.17", "1.18", "1.19", "1.20", "1.21", "1.21.2",
            "1.21.4", "1.21.5", "1.21.6", "1.21.9", "1.21.11", "26.1", "26.2", "26.3")
PROFILES = ("POTATO", "VERYLOW", "LOW", "MEDIUM", "HIGH", "VERYHIGH", "ULTRA")
INCLUDE = re.compile(r'^\s*#include\s+"([^"]+)"', re.MULTILINE)


def version_number(version: str) -> int:
    parts = [int(part) for part in version.split(".")]
    if len(parts) == 2:
        parts.append(0)
    if len(parts) != 3 or not all(0 <= part < 100 for part in parts):
        raise ValueError(f"Invalid Minecraft version: {version}")
    return parts[0] * 10000 + parts[1] * 100 + parts[2]


@lru_cache(maxsize=None)
def expand(path: Path) -> str:
    return INCLUDE.sub(
        lambda match: expand(SHADERS / match[1].lstrip("/") if match[1].startswith("/")
                             else path.parent / match[1]),
        path.read_text(encoding="utf-8-sig"),
    )


def profile_options() -> dict[str, dict[str, str]]:
    source = (SHADERS / "shaders.properties").read_text()
    return {match[1]: dict(token.split("=", 1) for token in match[2].split())
            for match in re.finditer(r'^\s*profile\.(\w+)\s*=\s*(.+)$', source, re.MULTILINE)}


def apply_options(source: str, options: dict[str, str]) -> str:
    for name, value in options.items():
        source = re.sub(r'(?m)^(\s*#define\s+' + re.escape(name) + r')\s+\S+',
                        lambda match: match[1] + " " + value, source)
        source = re.sub(r'(?m)^(\s*const\s+\w+\s+' + re.escape(name) + r'\s*=\s*)[^;]+',
                        lambda match: match[1] + value, source)
    return source


def environment(version: str, loader: str, dh: bool = False,
                vendor: str = "NVIDIA", os_name: str = "WINDOWS") -> str:
    defines = {"MC_VERSION": str(version_number(version)), "MC_OS_" + os_name: "",
               "MC_GL_VENDOR_" + vendor: "", "MC_NORMAL_MAP": "", "MC_SPECULAR_MAP": "",
               "MC_RENDER_QUALITY": "1.0", "MC_SHADOW_QUALITY": "1.0", "MC_HAND_DEPTH": "0.125"}
    if loader != "optifine":
        defines.update(IS_IRIS="", IRIS_VERSION="10611" if loader == "iris-legacy" else "11106",
                       MC_RENDER_STAGE_SUN="2", MC_RENDER_STAGE_MOON="3")
        if loader == "iris-modern":
            defines.update(IRIS_HAS_TRANSLUCENCY_SORTING="", IRIS_FEATURE_BLOCK_EMISSION_ATTRIBUTE="",
                           IRIS_FEATURE_FADE_VARIABLE="", IRIS_FEATURE_CUSTOM_IMAGES="", IRIS_FEATURE_SSBO="")
    if dh:
        defines["DISTANT_HORIZONS"] = ""
        names = ("UNKNOWN", "LEAVES", "STONE", "WOOD", "METAL", "DIRT", "LAVA", "DEEPSLATE",
                 "SNOW", "SAND", "TERRACOTTA", "NETHER_STONE", "WATER", "GRASS", "AIR", "ILLUMINATED")
        defines.update({"DH_BLOCK_" + name: str(i) for i, name in enumerate(names)})
    return "\n".join(f"#define {key} {value}".rstrip() for key, value in defines.items()) + "\n"


def prepare(source: str, macros: str) -> str:
    # Loader preprocessing handles continued macros before the GPU compiler.
    source = source.replace("\\\n", "")
    return re.sub(r'(?m)^(#version[^\n]*\n)', lambda m: m[1] + macros, source, count=1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", default=shutil.which("glslang") or shutil.which("glslangValidator"))
    parser.add_argument("--versions", nargs="+", default=list(VERSIONS))
    parser.add_argument("--loaders", nargs="+", choices=("optifine", "iris-legacy", "iris-modern"),
                        default=["optifine", "iris-modern"])
    parser.add_argument("--profiles", nargs="+", choices=PROFILES, default=list(PROFILES))
    parser.add_argument("--dh", action="store_true", help="Enable Distant Horizons macros and programs (Iris only)")
    parser.add_argument("--option", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--vendor", choices=("NVIDIA", "AMD", "INTEL", "OTHER"), default="NVIDIA")
    parser.add_argument("--os", choices=("WINDOWS", "LINUX", "MAC"), default="WINDOWS")
    parser.add_argument("--jobs", type=int, default=6)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not args.compiler:
        parser.error("Install glslang or provide --compiler; compilation cannot be skipped")
    if args.dh and "optifine" in args.loaders:
        parser.error("--dh requires Iris macro environments")
    options = profile_options()
    overrides = dict(item.split("=", 1) for item in args.option)
    files = sorted(p for p in SHADERS.glob("world*/*.vsh")
                   if not p.name.startswith("clrwl_") and (args.dh or not p.name.startswith("dh_")))
    # These are the runtime graphics programs. clrwl_* belongs to the external
    # Colorwheel/Create integration; shadowcomp.csh is disabled by Lite's COLORED_LIGHTING=0.
    prepared = {(p, profile, stage): apply_options(expand(p.with_suffix(stage)), options[profile] | overrides)
                for p in files for profile in args.profiles for stage in (".vsh", ".fsh")}
    cases = [(version, loader, profile, path) for version in args.versions for loader in args.loaders
             for profile in args.profiles for path in files]

    def compile_pair(case):
        version, loader, profile, path = case
        label = f"{version}/{loader}/{profile}/{path.parent.name}/{path.stem}"
        macros = environment(version, loader, args.dh, args.vendor, args.os)
        with tempfile.TemporaryDirectory(prefix="lumina-glsl-") as folder:
            paths = []
            for suffix, stage in ((".vsh", ".vert"), (".fsh", ".frag")):
                target = Path(folder) / (path.stem + stage)
                source = prepare(prepared[path, profile, suffix], macros)
                # Iris injects this variable; shaderpacks must not declare it.
                # https://shaders.properties/current/reference/attributes/mc_chunkfade/
                if loader == "iris-modern" and suffix == ".vsh":
                    fade = ("in float mc_chunkFade;" if path.stem == "gbuffers_terrain"
                            else "const float mc_chunkFade = -1.0;")
                    source = source.replace("#define VERTEX_SHADER", "#define VERTEX_SHADER\n" + fade, 1)
                if args.dh and suffix == ".vsh" and path.stem.startswith("dh_"):
                    # Like mc_chunkFade, dhMaterialId is supplied by Iris, not the pack.
                    source = source.replace("#define VERTEX_SHADER",
                                            "#define VERTEX_SHADER\nin int dhMaterialId;", 1)
                target.write_text(source)
                paths.append(str(target))
            result = subprocess.run([args.compiler, "-l", *paths], capture_output=True, text=True, timeout=60)
            return label, result.returncode, result.stdout + result.stderr

    failures = []
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        for index, (label, code, output) in enumerate(executor.map(compile_pair, cases), 1):
            if code:
                failures.append({"case": label, "output": output})
                print(f"FAIL {label}\n{output}", flush=True)
            if index % 500 == 0:
                print(f"Checked {index}/{len(cases)} program pairs; failures={len(failures)}", flush=True)
    report = {"kind": "offline GLSL compilation and linking; no runtime/GPU certification",
              "compiler": subprocess.check_output([args.compiler, "--version"], text=True).splitlines()[0],
              "versions": args.versions, "loaders": args.loaders, "profiles": args.profiles,
              "distant_horizons": args.dh, "options": overrides,
              "vendor_macro": args.vendor, "os_macro": args.os,
              "program_pairs": len(cases), "failures": failures}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Compilation: {len(cases)} program pairs, {len(failures)} failures. In-game testing remains required.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
