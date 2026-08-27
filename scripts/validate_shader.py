#!/usr/bin/env python3
"""Static release checks for Lumina Shader Lite."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHADERS = ROOT / "shaders"
SOURCE_SUFFIXES = {".glsl", ".vsh", ".fsh", ".csh"}
PREPROCESSOR_SUFFIXES = SOURCE_SUFFIXES | {".properties"}
INCLUDE_PATTERN = re.compile(r'^\s*#include\s+["<]([^">]+)[">]')
OPEN_PATTERN = re.compile(r"^\s*#(?:if|ifdef|ifndef)\b")
ELSE_PATTERN = re.compile(r"^\s*#(?:else|elif)\b")
END_PATTERN = re.compile(r"^\s*#endif\b")
VERSION_PATTERN = r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?"
PROFILE_PATTERN = re.compile(r"^\s*profile\.([A-Za-z0-9_]+)\s*=\s*(.+)$", re.MULTILINE)
SCREEN_PATTERN = re.compile(r"^\s*screen(?:\.([A-Za-z0-9_]+))?\s*=\s*(.+)$", re.MULTILINE)
SLIDERS_PATTERN = re.compile(r"^\s*sliders\s*=\s*(.+)$", re.MULTILINE)
DEFINE_PATTERN = re.compile(r"^\s*(?://\s*)?#define\s+([A-Za-z_]\w*)\b")
CONST_PATTERN = re.compile(r"^\s*const\s+\w+\s+([A-Za-z_]\w*)\s*=")


def fail(message: str) -> None:
    raise RuntimeError(message)


def shader_files() -> list[Path]:
    return sorted(
        path
        for path in SHADERS.rglob("*")
        if path.is_file() and path.name != ".DS_Store"
    )


def validate_json() -> int:
    files = [SHADERS / "pack.json", *SHADERS.rglob("*.mcmeta")]
    for path in files:
        with path.open(encoding="utf-8-sig") as handle:
            json.load(handle)
    return len(files)


def validate_includes() -> int:
    checked = 0
    for path in shader_files():
        if path.suffix not in SOURCE_SUFFIXES:
            continue
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8-sig").splitlines(), 1
        ):
            match = INCLUDE_PATTERN.match(line)
            if not match:
                continue
            checked += 1
            include = match.group(1)
            target = SHADERS / include.lstrip("/") if include.startswith("/") else path.parent / include
            if not target.is_file():
                fail(f"Missing include {include} at {path.relative_to(ROOT)}:{line_number}")
    return checked


def validate_preprocessors() -> int:
    checked = 0
    for path in shader_files():
        if path.suffix not in PREPROCESSOR_SUFFIXES:
            continue
        stack: list[int] = []
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8-sig").splitlines(), 1
        ):
            if OPEN_PATTERN.match(line):
                stack.append(line_number)
            elif ELSE_PATTERN.match(line):
                if not stack:
                    fail(f"Orphan #else/#elif at {path.relative_to(ROOT)}:{line_number}")
            elif END_PATTERN.match(line):
                if not stack:
                    fail(f"Orphan #endif at {path.relative_to(ROOT)}:{line_number}")
                stack.pop()
        if stack:
            fail(f"Unclosed preprocessor block at {path.relative_to(ROOT)}:{stack[-1]}")
        checked += 1
    return checked


def parse_assignments(value: str) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for item in value.split():
        if "=" in item:
            key, setting = item.split("=", 1)
            assignments[key] = setting
    return assignments


def parse_shader_options(source: str) -> tuple[set[str], set[str]]:
    options: set[str] = set()
    slider_options: set[str] = set()
    for line in source.splitlines():
        match = DEFINE_PATTERN.match(line) or CONST_PATTERN.match(line)
        if not match:
            continue
        option = match.group(1)
        options.add(option)
        if re.search(r"//\s*\[[^]]+\]\s*$", line):
            slider_options.add(option)
    return options, slider_options


def parse_screen_value(value: str) -> tuple[set[str], set[str]]:
    screens: set[str] = set()
    options: set[str] = set()
    for token in value.split():
        if token.startswith("[") and token.endswith("]"):
            screens.add(token[1:-1])
        elif not (token.startswith("<") and token.endswith(">")):
            options.add(token)
    return screens, options


def validate_menu_configuration(properties: str, shader_source: str) -> tuple[int, int, int]:
    shader_options, slider_options = parse_shader_options(shader_source)

    screens: dict[str | None, tuple[set[str], set[str]]] = {}
    for match in SCREEN_PATTERN.finditer(properties):
        name = match.group(1)
        if name in screens:
            fail(f"Duplicate screen definition: {name or 'root'}")
        screens[name] = parse_screen_value(match.group(2))
    if None not in screens:
        fail("Missing root screen definition")

    referenced_screens = set().union(*(references for references, _ in screens.values()))
    missing_screens = sorted(referenced_screens - {name for name in screens if name is not None})
    if missing_screens:
        fail(f"Referenced screens do not exist: {missing_screens}")

    reachable: set[str] = set()
    pending = list(screens[None][0])
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        reachable.add(name)
        pending.extend(screens[name][0] - reachable)
    orphaned = sorted(name for name in screens if name is not None and name not in reachable)
    if orphaned:
        fail(f"Orphaned screens: {orphaned}")

    menu_options = set().union(*(options for _, options in screens.values()))
    missing_options = sorted(menu_options - shader_options)
    if missing_options:
        fail(f"Menu options do not exist: {missing_options}")

    obsolete_profiles: dict[str, list[str]] = {}
    for match in PROFILE_PATTERN.finditer(properties):
        profile = match.group(1)
        assignments = parse_assignments(match.group(2))
        obsolete = sorted(assignments.keys() - menu_options)
        if obsolete:
            obsolete_profiles[profile] = obsolete
    if obsolete_profiles:
        fail(f"Profile options are not exposed in menus: {obsolete_profiles}")

    sliders_match = SLIDERS_PATTERN.search(properties)
    if not sliders_match:
        fail("Missing sliders definition")
    sliders = sliders_match.group(1).split()
    duplicates = sorted({option for option in sliders if sliders.count(option) > 1})
    if duplicates:
        fail(f"Duplicate sliders: {duplicates}")
    invalid_sliders = sorted(set(sliders) - slider_options)
    if invalid_sliders:
        fail(f"Sliders do not have configurable value lists: {invalid_sliders}")
    hidden_sliders = sorted(set(sliders) - menu_options)
    if hidden_sliders:
        fail(f"Sliders are not exposed in menus: {hidden_sliders}")

    return len(menu_options), len(reachable), len(sliders)


def validate_shader_properties() -> tuple[int, int, int]:
    properties = (SHADERS / "shaders.properties").read_text(encoding="utf-8-sig")
    common = (SHADERS / "lib/common.glsl").read_text(encoding="utf-8-sig")
    return validate_menu_configuration(properties, common)


def validate_performance_profiles(properties: str) -> int:
    profile_order = ("POTATO", "VERYLOW", "LOW", "MEDIUM", "HIGH", "VERYHIGH", "ULTRA")
    quality_options = (
        "SHADOW_QUALITY",
        "shadowDistance",
        "WATER_REFLECT_QUALITY",
        "BLOCK_REFLECT_QUALITY",
        "LIGHTSHAFT_QUALI_DEFINE",
        "SSAO_QUALI_DEFINE",
        "FXAA_DEFINE",
        "DETAIL_QUALITY",
        "CLOUD_QUALITY",
        "ANISOTROPIC_FILTER",
        "ENTITY_SHADOW",
    )
    profiles = {
        match.group(1): parse_assignments(match.group(2))
        for match in PROFILE_PATTERN.finditer(properties)
    }
    missing_profiles = [name for name in profile_order if name not in profiles]
    if missing_profiles:
        fail(f"Missing performance profiles: {missing_profiles}")

    for option in quality_options:
        try:
            values = [float(profiles[name][option]) for name in profile_order]
        except KeyError as error:
            fail(f"Performance profile is missing option {error.args[0]}")
        if values != sorted(values):
            fail(f"Performance profile option is not monotonic: {option}={values}")

    potato = profiles["POTATO"]
    required_potato = {
        "SHADOW_QUALITY": "-1",
        "WATER_REFLECT_QUALITY": "-1",
        "SSAO_QUALI_DEFINE": "0",
        "CLOUD_QUALITY": "0",
    }
    mismatches = {
        option: (potato.get(option), expected)
        for option, expected in required_potato.items()
        if potato.get(option) != expected
    }
    if mismatches:
        fail(f"Potato profile enables expensive effects: {mismatches}")

    required_fast_paths = (
        "program.world0/composite.enabled=false",
        "program.world0/composite6.enabled=false",
    )
    missing_fast_paths = [rule for rule in required_fast_paths if rule not in properties]
    if missing_fast_paths:
        fail(f"Missing Lite program fast paths: {missing_fast_paths}")

    return len(profile_order)


def validate_default_profile() -> int:
    properties = (SHADERS / "shaders.properties").read_text(encoding="utf-8-sig")
    match = re.search(r"^\s*profile\.COMPLEMENTARY\s*=\s*(.+)$", properties, re.MULTILINE)
    if not match:
        fail("Missing profile.COMPLEMENTARY")
    profile = parse_assignments(match.group(1))

    common = (SHADERS / "lib/common.glsl").read_text(encoding="utf-8-sig")
    defaults: dict[str, str] = {}
    for key in profile:
        if key == "shadowDistance":
            setting_match = re.search(r"const float shadowDistance\s*=\s*([^;]+);", common)
        else:
            setting_match = re.search(rf"^\s*#define\s+{re.escape(key)}\s+([^\s/]+)", common, re.MULTILINE)
        if not setting_match:
            fail(f"Cannot find default value for {key}")
        defaults[key] = setting_match.group(1)

    mismatches = {
        key: (profile[key], defaults[key])
        for key in profile
        if profile[key] != defaults[key]
    }
    if mismatches:
        fail(f"Default profile does not match shader defaults: {mismatches}")
    return len(profile)


def metadata_versions() -> dict[Path, str]:
    pack_path = SHADERS / "pack.json"
    lang_path = SHADERS / "lang/en_US.lang"

    with pack_path.open(encoding="utf-8-sig") as handle:
        description = json.load(handle)["pack"]["description"]
    pack_match = re.search(rf"\bLite v({VERSION_PATTERN}):", description)
    if not pack_match:
        fail(f"Could not extract an exact version from {pack_path.relative_to(ROOT)}")

    lang_text = lang_path.read_text(encoding="utf-8-sig")
    lang_match = re.search(
        rf"^profile\.COMPLEMENTARY=.*Lite v({VERSION_PATTERN})\s*$",
        lang_text,
        re.MULTILINE,
    )
    if not lang_match:
        fail(f"Could not extract an exact version from {lang_path.relative_to(ROOT)}")

    return {
        pack_path: pack_match.group(1),
        lang_path: lang_match.group(1),
    }


def validate_version(version: str | None = None) -> str:
    found = metadata_versions()
    unique_versions = set(found.values())
    if len(unique_versions) != 1:
        details = ", ".join(
            f"{path.relative_to(ROOT)}={actual}" for path, actual in found.items()
        )
        fail(f"Shader metadata versions do not match: {details}")

    actual = unique_versions.pop()
    if version is not None and actual != version:
        fail(f"Expected exact version {version}, found {actual}")
    return actual


def release_members() -> dict[str, bytes]:
    members: dict[str, bytes] = {}
    for filename in ("HOW TO INSTALL.txt", "License.txt", "CHANGELOG.md"):
        path = ROOT / filename
        members[filename] = path.read_bytes()
    for path in shader_files():
        members[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    return members


def validate_zip(path: Path) -> int:
    expected = release_members()
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            fail(f"Corrupt ZIP member: {bad}")
        actual = {
            info.filename: archive.read(info)
            for info in archive.infolist()
            if not info.is_dir()
        }
    missing = sorted(expected.keys() - actual.keys())
    extra = sorted(actual.keys() - expected.keys())
    changed = sorted(name for name in expected.keys() & actual.keys() if expected[name] != actual[name])
    if missing or extra or changed:
        fail(f"ZIP mismatch: missing={missing}, extra={extra}, changed={changed}")
    return len(actual)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version")
    parser.add_argument("--zip", type=Path)
    args = parser.parse_args()

    json_count = validate_json()
    include_count = validate_includes()
    preprocessor_count = validate_preprocessors()
    profile_count = validate_default_profile()
    menu_option_count, screen_count, slider_count = validate_shader_properties()
    performance_profile_count = validate_performance_profiles(
        (SHADERS / "shaders.properties").read_text(encoding="utf-8-sig")
    )
    metadata_version = validate_version(args.version)
    zip_count = validate_zip(args.zip) if args.zip else 0

    print(
        "Validation passed: "
        f"version {metadata_version}, "
        f"{json_count} JSON files, {include_count} includes, "
        f"{preprocessor_count} preprocessor files, {profile_count} profile values, "
        f"{menu_option_count} menu options, {screen_count} screens, {slider_count} sliders, "
        f"{performance_profile_count} ordered performance profiles"
        + (f", {zip_count} ZIP members" if args.zip else "")
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
