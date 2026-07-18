# Changelog

## 1.2.4-rc.1 - 2026-07-17

Pre-release candidate for in-game validation. This is not yet the stable v1.2.4 release.

### Fixed

- Prevented zero-luminance color normalization from generating invalid `NaN` values.
- Corrected temporal reprojection for Distant Horizons LOD geometry to reduce ghosting during camera movement.

### Optimized

- Reused squared lightmap values during shadow sampling to avoid redundant per-fragment calculations.

### Validation

- Added automated checks for JSON metadata, shader includes, preprocessor balance, default profile mapping, and ZIP/source parity.

## 1.2.3 - 2026-07-13

Lumina Shader Lite 1.2.3 is a maintenance release focused exclusively on bug fixes. It does not introduce intentional visual changes or new features.

### Fixed

- Corrected vertical image-sharpening offsets on non-square resolutions.
- Replaced undefined reversed `smoothstep` calls in dark-color tonemapping.
- Corrected the Distant Horizons water fade to behave consistently across GPU drivers.
- Removed invalid GLSL text from the reserved `composite2` program.
- Centered the final dithering noise to prevent a small positive brightness bias.
- Added the missing default profile mapping so the active defaults are identified correctly.
- Removed the incorrect "Default" label from the High profile.
