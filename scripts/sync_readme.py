#!/usr/bin/env python3
"""Keep README release metadata aligned with the public project pages."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path


REPOSITORY = os.environ.get(
    "GITHUB_REPOSITORY", "benjamincalledur10-bit/Lumina_Shader_Lite"
)
MODRINTH_PROJECT = "lumina-shader-lite"
CURSEFORGE_PROJECT = 1490563
README = Path(__file__).resolve().parents[1] / "README.md"
VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+")
FILENAME_PATTERN = re.compile(r"Lumina_Shader_Lite_v(\d+\.\d+\.\d+)\.zip")


def fetch_json(url: str) -> object:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Lumina-Shaders-README-Sync/1.0",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def compatibility_text(game_versions: list[str]) -> str:
    stable = sorted(
        {
            version
            for version in game_versions
            if re.fullmatch(r"\d+(?:\.\d+)+", version)
        },
        key=version_tuple,
    )
    legacy = [version for version in stable if version.startswith("1.")]
    calendar = [version for version in stable if not version.startswith("1.")]
    if not legacy or not calendar:
        raise RuntimeError("Expected both legacy and calendar Minecraft versions")

    return (
        "Minecraft: Java Edition "
        f"{legacy[0]} through {legacy[-1]} and "
        f"{calendar[0]} through {calendar[-1]}"
    )


def main() -> int:
    github = fetch_json(f"https://api.github.com/repos/{REPOSITORY}/releases/latest")
    modrinth_versions = fetch_json(
        f"https://api.modrinth.com/v2/project/{MODRINTH_PROJECT}/version"
    )
    curseforge = fetch_json(f"https://api.cfwidget.com/{CURSEFORGE_PROJECT}")

    if not isinstance(github, dict) or not isinstance(modrinth_versions, list):
        raise RuntimeError("Unexpected release API response")
    if not isinstance(curseforge, dict):
        raise RuntimeError("Unexpected CurseForge metadata response")

    github_version_match = VERSION_PATTERN.search(str(github.get("tag_name", "")))
    github_assets = github.get("assets", [])
    github_filename = github_assets[0].get("name", "") if github_assets else ""

    releases = [
        release
        for release in modrinth_versions
        if release.get("version_type") == "release"
        and release.get("status") == "listed"
    ]
    if not releases:
        raise RuntimeError("Modrinth has no listed release")
    modrinth = max(releases, key=lambda release: release.get("date_published", ""))
    modrinth_version = str(modrinth.get("version_number", ""))
    modrinth_files = modrinth.get("files", [])
    modrinth_filename = modrinth_files[0].get("filename", "") if modrinth_files else ""

    curseforge_file = curseforge.get("download", {})
    curseforge_filename = str(curseforge_file.get("name", ""))
    curseforge_version_match = FILENAME_PATTERN.fullmatch(curseforge_filename)

    if not github_version_match or not curseforge_version_match:
        raise RuntimeError("Could not determine the release version on every platform")

    versions = {
        github_version_match.group(0),
        modrinth_version,
        curseforge_version_match.group(1),
    }
    filenames = {github_filename, modrinth_filename, curseforge_filename}
    if len(versions) != 1 or len(filenames) != 1:
        raise RuntimeError(
            "Public releases are not synchronized; README was left unchanged\n"
            f"versions={sorted(versions)}\nfilenames={sorted(filenames)}"
        )

    version = versions.pop()
    filename = filenames.pop()
    expected_filename = f"Lumina_Shader_Lite_v{version}.zip"
    if filename != expected_filename:
        raise RuntimeError(f"Unexpected release filename: {filename}")

    modrinth_loaders = {loader.lower() for loader in modrinth.get("loaders", [])}
    curseforge_loaders = {
        loader.lower()
        for loader in curseforge_file.get("versions", [])
        if loader.lower() in {"iris", "optifine"}
    }
    if modrinth_loaders != {"iris", "optifine"} or curseforge_loaders != {
        "iris",
        "optifine",
    }:
        raise RuntimeError("Iris/OptiFine metadata differs between platforms")

    readme = README.read_text(encoding="utf-8")
    updated = re.sub(
        r"The current stable release is \*\*v\d+\.\d+\.\d+\*\*\.",
        f"The current stable release is **v{version}**.",
        readme,
        count=1,
    )
    updated = FILENAME_PATTERN.sub(filename, updated)
    compatibility = compatibility_text(modrinth.get("game_versions", []))
    updated = re.sub(
        r"(?m)^\| Game \| Minecraft: Java Edition .* \|$",
        f"| Game | {compatibility} |",
        updated,
        count=1,
    )

    if updated == readme:
        print(f"README is current for Lumina Shader Lite v{version}")
        return 0

    README.write_text(updated, encoding="utf-8")
    print(f"README updated for Lumina Shader Lite v{version}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"README sync failed: {error}", file=sys.stderr)
        raise SystemExit(1)
