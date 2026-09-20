# Changelog

## Lumina Shader Lite v1.2.8-rc.2 — 2026-09-19

Shadow-focused bug fixes following the compatibility candidate. This remains a
release candidate pending visual testing in Minecraft.

### Fixed

- Unified shadow-map projection for the writer, surface lighting, cloud occlusion
  and volumetric light. Clouds/light shafts previously compared a 0.2-scaled
  depth against a map written with a 0.3 scale, producing incorrect occlusion.
- Transformed the foliage caster offset back into player space before adding it
  to vertex positions when the perpendicular-lighting tweaks are active.
- Corrected optional Reimagined cloud-shadow projection for tilted sun/moon paths,
  including both cloud layers, and avoided projection at/below the horizon.
- Prevented scene-aware light shafts from using a zero update divisor during
  slow frames or invalid arithmetic during startup.
- Kept scene-aware light-shaft calculations finite when no valid shadow-height
  samples are available.

### Validation

- Added numerical regression tests for depth comparisons, cloud projection,
  foliage coordinate transforms, low-FPS update intervals and empty sample sets.
- Extended the compilation runner to enable/disable boolean options so optional
  cloud shadows and double cloud layers are actually compiled in stress tests.
- Preserved the existing shadow resolutions, filtering sample counts and profile
  defaults; this candidate does not add a new shadow effect.
- See `docs/SHADOW_AUDIT.md` for findings and the pending in-game checks.

---


## Lumina Shader Lite v1.2.8-rc.1 — 2026-09-19

Compatibility and stability candidate targeting Minecraft Java 1.16.5 through
26.3. No new visual effects. In-game validation is still required before a stable
v1.2.8 release; this candidate does not claim universal hardware/mod compatibility.

### Fixed

- Restored version-correct mapping of empty and water-filled cauldrons on 1.16.5.
- Avoided referencing Pale Garden and the darkness effect in custom uniform
  expressions on game versions where those features do not exist.
- Gave Pale Garden, Soul Sand Valley and the two eye-brightness expressions
  independent smoothing state to prevent interference between them.
- Replaced undeclared core-profile inputs in the line vertex shader with the
  compatibility transform handled by shader loaders.
- Selected the anisotropic-filter matrix inverse by GLSL capability instead of
  Minecraft version, retaining a GLSL 1.30-compatible fallback.
- Protected End-flash direction calculations and vertical End views from
  zero-length normalization and negative square-root inputs.
- Completed Pale Oak wall-sign and bamboo raft material mappings and removed
  an invalid stained-glass mapping token.

### Compatibility

- Mapped 26.3 Poplar leaves, saplings, signs and boats, Red Shrubs and Shelf
  Mushrooms to the existing appropriate material families.
- Mapped wool/concrete stairs and slabs to existing materials while preserving
  partial-block classification and the special lime material handling.

### Validation

- Added property regressions across all 35 stable releases in the target range.
- Added offline GLSL compilation and linking across game-version boundaries,
  all seven profiles and all three dimensions, plus legacy Iris, Distant Horizons,
  custom PBR/POM, AMD workaround and macOS/vanilla-cloud paths.
- Added CI compilation reports and duplicate smoothing-ID validation.
- Runtime testing status and reproduction steps are documented in
  `docs/COMPATIBILITY.md` in the repository.

---


# 🚀 Lumina Shader Lite v1.2.7 — Performance Unleashed

**Lumina Shader Lite is now faster, cleaner, and more efficient than ever.** ⚡

This major performance-focused update completely reworks every quality profile, significantly reduces unnecessary GPU work, and improves the experience on integrated and low-end graphics—while preserving the visual identity of Lumina Lite.

Internal testing showed an impressive **28–30% increase in FPS**, depending on the hardware, profile, and scene. 📈

## ⚡ Massive Performance Improvements

* Completely optimized all **seven performance profiles**, from Potato to Ultra.
* Reduced the cost of shadows, reflections, SSAO, bloom, water, clouds, and entity shadows.
* Prevented unused reflection and post-processing passes from running on lower profiles.
* Disabled inactive Temporal Anti-Aliasing programs when they are not required.
* Reduced low-detail bloom filtering from **49 to 25 samples** per active tile.
* Reduced low-detail procedural water normals from **four texture reads to two**.
* Improved shader activation times on **Low, Very Low, and Potato**.
* Significantly improved performance on integrated graphics and low-end GPUs.

## 🎚️ Completely Rebalanced Profiles

Every profile now follows a clear and consistent quality ladder:

🥔 **Potato** → Maximum performance  
⚡ **Very Low** → Lightweight visuals  
🚀 **Low** → Best performance-quality balance  
🎮 **Medium** → Improved effects and detail  
✨ **High** → Higher shadows and visual quality  
💎 **Very High** → Advanced effects  
🌟 **Ultra** → Maximum visual quality

**Low is now the default profile**, providing smoother performance, lower GPU usage, and a better experience immediately after installing the shader.

The inherited **Complementary profile has been removed**, making the profile selector cleaner and preventing confusing or incorrect default settings.

## 🌕 New Configurable Moon Halo

The Minecraft night sky receives a beautiful new atmospheric detail:

* Added a soft procedural halo around the Moon.
* Fully configurable intensity.
* Automatically reacts to rain, clouds, and lunar phases.
* Appears naturally in eligible sky and water reflections.
* Uses no additional textures or expensive volumetric effects.
* When disabled, its code is completely excluded from compilation.

The result is a more cinematic and immersive night sky without sacrificing Lumina Lite’s lightweight design. 🌌

## 🌊 Water and Visual Fixes

* Fixed water compilation errors affecting Potato, Very Low, and Low.
* Improved the stability of low-detail procedural water.
* Added safer custom normal-map reconstruction for labPBR resource packs.
* Stabilized PBR and POM displacement calculations.
* Improved GGX reflections at extreme viewing angles.
* Protected cloud-shadow calculations from invalid angles.
* Added safer anisotropic-filtering fallbacks.
* Fixed mathematical instability in pixelated rainbows near the horizon.

## 🧹 Cleaner Interface

* Removed obsolete Advanced Color Tracing controls.
* Removed unavailable World-Space Reflections options.
* Eliminated inherited and orphaned settings screens.
* Simplified the optimization menu.
* Improved profile consistency and default-value handling.

## 🧪 Stronger Automatic Validation

Lumina Shader Lite now automatically validates:

* Performance-profile order and safeguards.
* Menus, options, screens, and sliders.
* Lightweight shader program paths.
* Metadata and version consistency.
* Shader includes and conditional blocks.
* Release ZIP integrity and source parity.
* Invalid, duplicated, hidden, or obsolete controls.

These checks help prevent configuration mistakes and performance regressions in future updates. 🛡️

## 📈 The Result

* Up to **28–30% higher FPS** in testing.
* Faster shader activation on lower profiles.
* Lower GPU usage in expensive scenes.
* Better performance on integrated graphics.
* More consistent quality progression.
* Improved water and PBR stability.
* Cleaner menus and safer configuration.
* A beautiful new Moon halo with minimal performance cost.

---

💙 Thank you for using **Lumina Shader Lite**!

Enjoy smoother gameplay, faster performance, cleaner settings, and beautiful lightweight visuals with **v1.2.7 — Performance Unleashed**. 🚀✨

## 🧪 Lumina Shader Lite v1.2.7-rc.4 — 2026-08-27

Final optimization release candidate, making Low the factory-default profile and removing the inherited Complementary profile entry.

### ⚡ Optimized

- 🚀 Changed the shader's factory defaults to match the Low profile, including its lightweight material, shadow, antialiasing, and post-processing paths.

### 🎨 Interface

- 🧹 Removed the inherited Complementary profile from the profile selector so new installations identify Low as the active default.

### ✅ Validation

- 🧪 Updated release metadata and default-profile validation to use the new Low baseline.

## 🧪 Lumina Shader Lite v1.2.7-rc.3 — 2026-08-27

Hotfix release candidate restoring Potato, Very Low, and Low profile compatibility after the RC2 water optimization.

### 🛠️ Fixed

- 🌊 Restored low-detail water shader compilation by keeping the optional small-wave normal available to later lighting calculations without restoring its texture lookup.

## 🧪 Lumina Shader Lite v1.2.7-rc.2 — 2026-08-27

Second release candidate for v1.2.7, introducing the first real-optimization pass for low-end hardware and integrated graphics.

### ⚡ Optimized

- 🎚️ Rebalanced every performance profile into a consistent quality ladder, with expensive shadows, reflections, SSAO, and shader clouds removed from Potato.
- 🪞 Skipped the full-screen reflection pass when advanced block and world-space reflections are inactive.
- 🎬 Skipped the temporal antialiasing pass on minimum detail quality, where TAA is not compiled.
- ✨ Reduced low-detail bloom filtering from 49 to 25 samples per active tile.
- 🌊 Reduced low-detail procedural water normals from four texture reads to two.

### ✅ Validation

- 🧪 Added automatic checks for ordered performance profiles, Potato safeguards, and required Lite program fast paths.

## 🧪 Lumina Shader Lite v1.2.7-rc.1 — 2026-08-27

First release candidate for v1.2.7, focused on shader stability, cleaner Lite controls, stronger configuration validation, and a configurable procedural moon halo.

### ✨ Added

- 🌕 Added an optional procedural moon halo with a configurable intensity control and support in eligible sky reflections.

### 🛠️ Fixed

- 🎛️ Removed obsolete Advanced Color Tracing and World-Space Reflections controls from Lite profiles and the optimization menu.
- 🧹 Removed the orphaned Advanced Color Tracing settings-screen definition.
- 🧭 Protected custom labPBR normal-map reconstruction from negative square-root inputs caused by floating-point precision.
- 🧱 Initialized POM depth before every parallax path to prevent undefined custom-PBR displacement and slope normals.
- 🌈 Protected pixelated rainbows from horizon-aligned division by zero.
- ✨ Stabilized GGX highlights at degenerate half vectors and extreme reflection angles.
- ☁️ Clamped cloud-shadow angles before inverse trigonometric projection.
- 🔎 Added safe fallbacks for degenerate UV derivatives and transparent samples in anisotropic filtering.

### ✅ Validation

- 🧪 Added automatic checks for obsolete profile controls, missing menu options, orphaned screens, and duplicate or invalid sliders.

## 🌌 Lumina Shader Lite v1.2.6 — 2026-08-01

This maintenance update makes Lumina Shader Lite more stable in difficult rendering conditions while preserving its lightweight design and visual identity. ✨

### 🛠️ Fixed — Rendering Stability

- 🛡️ Prevented black rectangles around enchanted armor and players by safely discarding near-transparent fragments.
- 🌤️ Prevented invalid `NaN` values in natural and ice light shafts when shadow colors have no length.
- ☁️ Stabilized cloud-shadow projection when the sun aligns with a horizontal world axis.
- ❄️ Protected biome-tint removal from division by zero on snowy terrain, leaves, and IPBR materials.
- 💧 Prevented high water-wave settings from producing invalid normal-map calculations.
- 🌫️ Protected Lightshaft Smoke from division by zero in empty volumetric samples.

### 🎨 Improved — Compatibility & Interface

- 👻 Preserved intentionally translucent modded entities while still discarding fully transparent fragments.
- 🎛️ Removed unavailable Advanced Color Tracing controls from the Lite interface and profiles.

### ✅ Validation

- 🔍 Version checks now require exact metadata matches and reject incorrect pre-release suffixes.
- 🤖 Added automatic shader validation for development pushes, `main`, and pull requests.
- 📦 Verified shader includes, preprocessor blocks, default profiles, metadata, and ZIP/source parity.
- 🧹 Confirmed that the final ZIP contains 397 files with no unnecessary macOS metadata.

💙 Thank you for using Lumina Shader Lite! Enjoy a cleaner, safer, and more stable visual experience.

## 1.2.5 - 2026-07-25

Stable release focused on sky customization, clearer distant atmosphere, safer emissive lighting, and inherited weather-color corrections.

### Added

- Added a Milky Way Brightness control under Environment & Sky with OFF, 25%, 50%, 75%, 100%, 125%, and 150% levels.
- Disabling the Milky Way now removes its procedural calculation from the compiled sky and reflection shaders.

### Changed

- Added an independent Lava Brightness slider under IntegratedPBR+ glowing-material settings.

### Fixed

- Limited lava emission and bloom input so large lava surfaces no longer overexpose the image to white.
- Corrected the middle-sky color used by the Heavy & Colder rainy-weather style.

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
