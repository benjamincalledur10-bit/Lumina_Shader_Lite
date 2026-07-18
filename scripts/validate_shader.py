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


def fail(message: str) -> None:
    raise RuntimeError(message)


def shader_files() -> list[Path]:
    return sorted(path for path in SHADERS.rglob("*") if path.is_file())


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


def validate_version(version: str) -> None:
    required = {
        SHADERS / "pack.json": version,
        SHADERS / "lang/en_US.lang": version,
    }
    for path, expected in required.items():
        if expected not in path.read_text(encoding="utf-8-sig"):
            fail(f"{path.relative_to(ROOT)} does not contain version {version}")


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
    if args.version:
        validate_version(args.version)
    zip_count = validate_zip(args.zip) if args.zip else 0

    print(
        "Validation passed: "
        f"{json_count} JSON files, {include_count} includes, "
        f"{preprocessor_count} preprocessor files, {profile_count} profile values"
        + (f", {zip_count} ZIP members" if args.zip else "")
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
