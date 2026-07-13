# Lumina Shader: Lite Edition

<p align="center">
  A high-performance Minecraft: Java Edition shader pack designed for low-end
  PCs, laptops, and integrated graphics without losing the Lumina atmosphere.
</p>

<p align="center">
  <a href="https://github.com/benjamincalledur10-bit/Lumina_Shader_Lite/releases/latest"><img alt="Latest GitHub release" src="https://img.shields.io/github/v/release/benjamincalledur10-bit/Lumina_Shader_Lite?style=for-the-badge"></a>
  <a href="https://modrinth.com/shader/lumina-shader-lite"><img alt="Modrinth downloads" src="https://img.shields.io/modrinth/dt/70O0661F?style=for-the-badge&logo=modrinth&label=Modrinth"></a>
  <a href="https://www.curseforge.com/minecraft/shaders/lumina-shader-lite"><img alt="CurseForge downloads" src="https://img.shields.io/curseforge/dt/1490563?style=for-the-badge&logo=curseforge&label=CurseForge"></a>
</p>

## Download

Use one of the official distribution pages:

- [GitHub Releases](https://github.com/benjamincalledur10-bit/Lumina_Shader_Lite/releases/latest)
- [Modrinth](https://modrinth.com/shader/lumina-shader-lite)
- [CurseForge](https://www.curseforge.com/minecraft/shaders/lumina-shader-lite)

The current stable release is **v1.2.3**. Download
`Lumina_Shader_Lite_v1.2.3.zip` and keep it compressed when installing it.

## Highlights

- **High-performance rendering:** lightweight defaults and carefully balanced
  effects for smoother gameplay on modest hardware.
- **Vanilla+ presentation:** vibrant color, clean fog, stylized clouds, and a
  polished atmosphere that preserves Minecraft's visual identity.
- **Scalable profiles:** seven presets from Potato to Ultra for quick
  performance and quality adjustments.
- **Customizable lighting:** controls for shadows, ambient occlusion, light
  shafts, bloom, reflections, and dimension-specific lighting.
- **Water and material effects:** configurable water, generated normals,
  coated textures, and optional PBR resource-pack support.
- **Cinematic controls:** temporal anti-aliasing, motion blur, depth of field,
  color grading, sharpening, and lens effects.
- **Extended rendering support:** dedicated shader programs for Distant
  Horizons terrain and water.

## Compatibility

| Component | Support |
| --- | --- |
| Game | Minecraft: Java Edition 1.16.5 through 1.21.11 and 26.1 through 26.2 |
| Shader loaders | Iris and OptiFine |
| Rendering profiles | Potato, Very Low, Low, Medium, High, Very High, Ultra |
| Edition | Java Edition only; Bedrock Edition is not supported |

[Iris](https://www.irisshaders.dev/) is recommended for modern Minecraft
versions and access to Iris-specific features. Performance and compatibility
depend on resolution, render distance, selected profile, resource packs, mods,
graphics driver, and GPU.

## Installation

1. Install [Iris](https://www.irisshaders.dev/) or a compatible OptiFine
   version.
2. Download `Lumina_Shader_Lite_v1.2.3.zip` from an official source above.
3. Open Minecraft and go to **Options > Video Settings > Shader Packs**.
4. Open the shader-pack folder and place the downloaded ZIP inside it. Do not
   extract the archive.
5. Return to Minecraft, select **Lumina Shader Lite**, and apply the settings.
6. Start with the Low or Medium profile, then adjust quality for your hardware.

The default shader-pack directory is usually:

```text
~/.minecraft/shaderpacks
```

## Configuration tips

- Start with Potato, Very Low, or Low when using integrated graphics.
- Reduce shadow distance, cloud quality, reflections, and light-shaft quality
  first when targeting higher frame rates.
- Raise one setting at a time so performance changes are easy to measure.
- Select the matching material mode when using a resource pack with PBR
  textures.
- Reset the shader profile after upgrading if settings from an older release
  cause unexpected visuals.

## Development

- `main` contains the current stable, published state.
- `luminalitedev` is used for development and validation before a release.
- Every release is documented in [CHANGELOG.md](CHANGELOG.md).
- Bugs and reproducible visual issues can be reported through
  [GitHub Issues](https://github.com/benjamincalledur10-bit/Lumina_Shader_Lite/issues).

When reporting a problem, include the Minecraft version, shader loader and
version, GPU, graphics-driver version, active shader profile, and screenshots or
logs when available.

## Credits

- **Main developer:** Benjiaa
- Lumina Shader Lite is part of the Lumina series and is based on Lumina Event
  Horizon.
- This is a modified pack based on
  [Complementary Reimagined](https://modrinth.com/shader/complementary-reimagined)
  by EminGT. Special thanks to EminGT and the Complementary shader community.

## Community and support

- [Discord community](https://discord.gg/JK6rTQ9T)
- [Support development on Ko-fi](https://ko-fi.com/lumina_dev/goal?g=0)

Lumina Shader Lite is distributed under the included
[Complementary License Agreement 1.6](License.txt). Modpacks must add the pack
through the existing Modrinth or CurseForge systems; direct redistribution of
the ZIP is not permitted. Read the complete license before modifying or
redistributing the project.
