# Changelog

## 1.2.5-pre.1 - 2026-07-19

Pre-release candidate for in-game validation before the stable v1.2.5 release.

### Changed

- Shifted the clear daytime horizon and distant atmospheric fog from pale white toward a cleaner sky blue.

### Fixed

- Removed the spherical coordinate seam from the Milky Way cloud pattern.
- Attached the galactic plane to the moving celestial basis so it follows the night sky.

### Optimized

- Reduced Milky Way value-noise hashing from eight trigonometric hashes per sky pixel to four.

## 1.2.4 - 2026-07-17

Stable release based on the fourth in-game test candidate. It combines internal stability and performance work with a new lightweight Milky Way effect.

### Added

- Added a wide diagonal Milky Way arc with rounded galactic clouds, a warm core, cool outer haze, and a warped central dust lane.

### Fixed

- Prevented zero-luminance color normalization from generating invalid `NaN` values.
- Corrected temporal reprojection for Distant Horizons LOD geometry to reduce ghosting during camera movement.
- Removed directional streaks from the Milky Way while preserving the dark midnight background and existing stars.

### Optimized

- Reused squared lightmap values during shadow sampling to avoid redundant per-fragment calculations.
- Built the Milky Way without texture samples, new assets, or volumetric ray marching.

### Validation

- Added automated checks for JSON metadata, shader includes, preprocessor balance, default profile mapping, and ZIP/source parity.

## 1.2.4-rc.3 - 2026-07-17

Third in-game test candidate. This is not yet the stable v1.2.4 release.

### Changed

- Reworked the Milky Way into a wider and substantially more visible galactic arc.
- Added irregular luminous clouds, a warm galactic core, fine structure, and a warped central dust lane inspired by real night-sky photography.

### Performance

- Reuses the shader pack's existing noise texture with three samples and no iterative noise loops or volumetric ray marching.

## 1.2.4-rc.2 - 2026-07-17

Second in-game test candidate. This is not yet the stable v1.2.4 release.

### Added

- Added a subtle, tilted Milky Way band at night while preserving the existing dark midnight sky and stars.
- Added a lightweight central dust lane and gentle brightness variation to give the band natural structure.

### Performance

- The Milky Way uses an analytic shader calculation with no additional texture samples, loops, or volumetric noise.
- Added the same subtle band to eligible high-quality sky reflections for visual consistency.

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
