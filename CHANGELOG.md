# Changelog

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
