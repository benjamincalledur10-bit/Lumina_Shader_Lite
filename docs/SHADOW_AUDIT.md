# Shadow audit — v1.2.8-rc.2

Reviewed September 19, 2026. This audit found and fixed five concrete defects.
The coordinate and arithmetic failures below are reproducible from source;
visual severity and GPU behavior still require in-game testing.

## Findings fixed

| Priority | Defect and trigger | Evidence | Fix |
| --- | --- | --- | --- |
| High | Cloud occlusion and volumetric rays read a different depth space from the shadow writer | The writer and surface lookup scaled Z by 0.3; `mainClouds.glsl` and `volumetricLight.glsl` used 0.2 | One shared `DistortShadowClip` function now serves all four paths |
| Medium | Foliage caster offsets rotate with the light view when perpendicular tweaks are enabled | `position` was already transformed by `shadowModelViewInverse`, but the added normal was still in shadow-view space | Transform the normal by the inverse shadow-view rotation before adding the offset |
| Medium | Optional Reimagined cloud shadows do not align with tilted sunlight/moonlight | Independent `cot(acos(x))` and `cot(acos(z))` ratios do not equal the 3D ray/plane intersection when both horizontal components are nonzero | Project both cloud layers using `light.xz / light.y`; skip a light at/below the horizon |
| Medium | Scene-aware light-shaft update uses an invalid modulo divisor during slow frames | At 5 FPS, `int(0.06666 / 0.2 + 0.5)` is zero; startup at zero frame time also divides by zero | Clamp frame time before computing an update interval of at least one frame |
| Medium | Scene-aware shadow-height average is undefined when every sample is rejected | Empty sample set gives `0.0 / 0` | Use a denominator of at least one, yielding the neutral zero-height result |

For the depth mismatch, an occluder at clip Z=0.6 writes depth 0.59. A receiver
behind it at Z=0.7 should compare at 0.605 (shadowed), but the old reader used
0.57 (lit). This explains why valid compilation could coexist with light leaks
or displaced occlusion. The inverse situation can also incorrectly shadow a
point in front of an occluder.

For cloud projection, a unit light direction `(0.6, 0.6, sqrt(0.28))` and a
128-block cloud-height difference require horizontal offsets of approximately
`(128, 112.9)` blocks. The old independent-angle method gives approximately
`(96, 79.8)` instead.

The foliage issue affects the `PERPENDICULAR_TWEAKS` branch (for example,
`SUN_ANGLE=0` with Medium or higher detail); it is not a claim that every profile
or the default inclined sun path exhibited it.

## Scope reviewed

The review covered the shadow vertex/fragment writer, direct-light receivers,
cloud occlusion, optional cloud shadows, volumetric light, quality/filter paths,
foliage waving and bias, PBR shadow integration, dimension paths, shadow-program
activation and entity-shadow configuration. Disabled World-Space Reflections
and colored-light voxelization were not enabled as new Lite features.

No evidence justified changing the existing shadow resolutions, sample counts,
normal bias magnitude, distance falloff or quality profiles. Some visible limits
are deliberate configuration choices:

- Potato and Very Low disable the shadow pass.
- Low and Medium use the inexpensive basic shadow filter; colored transmission
  is handled by the higher-quality path.
- Entity shadows are disabled in lower profiles, and enabled entity shadows use
  the configured `entityShadowDistanceMul=0.125` cutoff.

These limits should be distinguished from rendering defects when comparing
screenshots. This audit does not certify that all shadow bugs are gone.

## Validation

`tests/test_shadows.py` evaluates scalar/matrix expressions taken directly from
the GLSL source against independent numerical expectations. It checks depth
ordering, ray/plane collinearity, rotation-invariant foliage displacement,
startup/slow frame intervals and empty sample sets. It also guards against
reintroducing separate shadow-depth scales and tests boolean option overrides.

Offline compilation/linking exercises all seven profiles on 1.16.5 and 26.3 in
OptiFine and modern-Iris macro environments, plus the following stress cases:

- Two Reimagined cloud layers and cloud shadows with a vertical sun path.
- A -40-degree sun path, maximum shadow quality, 1024-block shadow distance,
  custom PBR/POM, entity shadows and TAA disabled.
- Unbound clouds, maximum light-shaft quality, labPBR and macOS macros.
- Distant Horizons enabled on 1.21.11 and 26.3 with all seven profiles.

[Machine-readable results](validation-v1.2.8-rc.2.json) describe these RC2 runs.
The broader initial version-boundary validation remains available separately in
[the RC1 report](validation-v1.2.8-rc.1.json). CI retains that broad matrix and adds
the optional shadow stress cases.

## Visual validation still required

1. Compare RC1 and RC2 using the same world, time, weather and profile. Inspect
   sunbeams through a roof/window and terrain occluding low clouds.
2. Enable cloud shadows, then compare `SUN_ANGLE=0`, `-40` and `40`, at noon and
   around sunrise/sunset. Test both cloud layers, underwater, and above clouds.
3. With Medium or Ultra and `SUN_ANGLE=0`, inspect short grass/flowers as the sun
   moves. Compare the shadow position with the visible waving geometry.
4. Enable scene-aware light shafts and temporarily cap FPS to 5, then restore it.
   Check both an unobstructed sky and an enclosed room for unstable exposure.
5. Check opaque/transparent casters, leaves, glass, water, entities and held items
   in all dimensions. Include PBR and supported Distant Horizons setups.
6. Capture `latest.log`, screenshots and frame times with exact loader, GPU,
   driver, OS and shader settings. No runtime results are recorded yet.

The coordinate-space interpretation follows the
[Iris matrix reference](https://shaders.properties/current/reference/uniforms/matrices/)
and [shadow-program reference](https://shaders.properties/current/reference/programs/shadow/).
