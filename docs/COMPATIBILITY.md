# v1.3.0 development experiment: skip inactive world blur

`composite3` is disabled only for `WORLD_BLUR=0`, independently in the Overworld,
Nether and End. Modes 1 (distance blur) and 2 (depth of field) retain the original
program. Shader bodies and profile defaults are unchanged.

At mode 0 the original fragment program only reads `colortex0.rgb` and writes
the same RGB with alpha 1. The preceding `composite1` already writes alpha 1.
No explicit flip is added: skipping both the copy and its automatic flip leaves
the current image available to the next pass. `composite4` reads that logical
`colortex0` and requests its own mipmaps; `composite5` also reads its RGB before
writing `colortex3`, which feeds the TAA path. Bloom fog is already applied by
`composite1` at mode 0, and is disabled in the End.

This reasoning follows [OptiFine's buffer-flip contract](https://github.com/sp614x/optifine/blob/master/OptiFineDoc/doc/shaders.properties)
and [Iris's composite renderer](https://github.com/IrisShaders/Iris/blob/26.3/common/src/main/java/net/irisshaders/iris/pipeline/CompositeRenderer.java),
which builds later sampler bindings from the active buffer-flip state.
It is source-level evidence, not an in-game framebuffer capture.

`tests/test_world_blur.py` preprocesses the actual properties and expanded
fragment programs for all 18 combinations of three blur modes, three dimensions
and TAA on/off, with both Low (TAA excluded) and High (TAA available), under
OptiFine and modern-Iris macros at Minecraft 26.3: 72 combinations. It checks
the pass gate, copy behavior, alpha, downstream reads, mipmaps, fog routing and
TAA selection. These checks do not execute a loader or GPU.

## Acceptance checks still pending

1. First test the existing End and GGX fixes in Minecraft: cap the End at 5 FPS,
   restore the cap, and inspect reflective surfaces at grazing angles for black
   pixels, flicker or unstable transitions.
2. Compare commit `fddcf1b` against this experiment using identical loader, GPU,
   driver, resolution, resource pack and settings. Test all 18 combinations
   above on High, and repeat Low to cover the path without compiled TAA. Reload
   after settings changes; resize the window and change dimensions. Include
   bloom and motion blur, verify outlines/hand rendering and inspect logs.
3. Capture matching screenshots after TAA settles and, where GPU capture is
   available, verify that mode 0 omits the draw and that `composite4` samples the
   latest `colortex0` image. Modes 1 and 2 must retain the draw and their effect.
4. Measure the same fixed scene with VSync and the FPS cap disabled after
   warmup. Alternate baseline/experiment for at least three 60-second runs;
   record median and p95 frame times and the exact environment. Use a frame
   capture or GPU timings to distinguish eliminated GPU work from CPU limits.
5. Keep the experiment for release only after visual/loader checks pass and
   measurements confirm reduced work without regressions. Record results here;
   until then, FPS gains and runtime compatibility are unverified.

---

# Lumina Lite v1.2.9 emergency hotfix

The user reproduced a Minecraft 26.3 load failure with v1.2.8:
`lines: ERROR: 0:399: Invalid call of undeclared identifier 'ftransform'`.
Version 1.2.9 replaces that call only in the shared line vertex path with
`gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex`.

Validation of v1.2.8 below remains historical evidence, not a runtime guarantee
for v1.2.9. The new regression check preprocesses actual expanded line shaders
and checks that no `ftransform()` call remains active for any dimension/profile,
including TAA on/off. This does not emulate Iris transformation or GPU execution.

The author confirmed successful loading of v1.2.9 in Minecraft 26.3 on
October 3, 2026. Exact loader/GPU/driver details and logs were not supplied.
Visual checks of block selection outlines and fishing lines in the Overworld,
Nether and End, including TAA on/off comparisons, remain pending.

Local checks: 21 regression tests passed; static metadata/include/profile checks
and byte-for-byte ZIP/source parity passed (399 members). The GLSL compilation
matrix was not run locally: glslang is unavailable and Homebrew installation was
blocked by the pending Xcode license. No license was accepted automatically.

---

# Lumina Lite v1.2.8 compatibility work

The stable release is **v1.2.8**, targeting every stable Minecraft Java release
from **1.16.5 through 26.3**. It promotes rc.2 with only release metadata and
documentation changes; shader behavior is unchanged. Runtime validation remains
pending. This release adds compatibility fixes, not new visual effects.

## What has been verified

The initial RC1 work established the broad version-boundary coverage below.
RC2 adds the focused [shadow audit and stress tests](SHADOW_AUDIT.md).
The report for each candidate records the runs performed on that candidate;
RC1 results are retained as historical evidence, not relabeled as RC2 results.


- Property regression tests cover all 35 stable releases in that interval:
  1.16.5; 1.17–1.17.1; 1.18–1.18.2; 1.19–1.19.4; 1.20–1.20.6;
  1.21–1.21.11; 26.1–26.1.2; 26.2; 26.3.
- Offline GLSL compilation and vertex/fragment linking cover the seven profiles
  and all three dimensions at every game-version branch boundary used by the
  shader, plus 26.1, 26.2 and 26.3.
- Additional compilation runs exercise older Iris capabilities, Distant
  Horizons, custom PBR/POM, AMD workaround code, and macOS/vanilla-cloud code.
- Static checks cover includes, preprocessor balance, menus, defaults, quality
  profiles, independent smoothing IDs, version metadata and ZIP/source parity.

The compiler uses synthetic **OptiFine**, **Iris legacy** and **Iris modern**
macro environments. For example, a modern Iris macro environment compiled with
`MC_VERSION=11605` is a source-branch test, **not** a claim that modern Iris can
be installed on 1.16.5. Likewise, macOS/AMD macros do not constitute tests on
those operating systems or GPUs. The original GLSL version is retained.

Iris-injected `mc_chunkFade` and `dhMaterialId` declarations are supplied by the
test harness only. Other loader transformations, actual uniform values, texture
bindings, framebuffer layouts and GPU driver behavior are not emulated.
Colorwheel/Create programs and the disabled colored-light compute program are
outside this compilation matrix. Optional integrations need their own in-game
validation.

Machine-readable offline results are in
[validation-v1.2.8-rc.2.json](validation-v1.2.8-rc.2.json).

## Runtime validation status

**No Minecraft runtime test has been performed for v1.2.8 or its candidates.**
The stable release designation does not certify full stability through offline
checks. The following checks remain pending for **each of the 35 releases** with
an actually available, compatible loader. Do not mark unavailable loader/game
combinations as supported.

| Coverage | Status |
| --- | --- |
| Minecraft 1.16.5 | In-game testing pending |
| Minecraft 1.17, 1.17.1 | In-game testing pending |
| Minecraft 1.18, 1.18.1, 1.18.2 | In-game testing pending |
| Minecraft 1.19 through 1.19.4, every patch | In-game testing pending |
| Minecraft 1.20 through 1.20.6, every patch | In-game testing pending |
| Minecraft 1.21 through 1.21.11, every patch | In-game testing pending |
| Minecraft 26.1, 26.1.1, 26.1.2 | In-game testing pending |
| Minecraft 26.2 | In-game testing pending |
| Minecraft 26.3 | In-game testing pending |

For each run, record the game, loader and Sodium/DH versions (when applicable),
GPU, driver, OS, resource pack, resolution, render distance and shader profile.
Use a disposable test world and capture screenshots plus `latest.log`.

1. Activate every profile, reload the shader, resize the window, and change
   dimensions. Check for compilation/linking errors and missing custom uniforms.
2. Inspect terrain, foliage, water, glass, particles, weather, entities, enchanted
   armor, held items, signs, block outlines and fishing lines in each dimension.
3. Test day/night, rain, underwater views, blindness, and darkness where the
   effect exists. Visit Nether biomes and Pale Garden where available; transitions
   must not affect unrelated biome or eye-brightness smoothing.
4. Test empty and filled cauldrons on 1.16.5 and 1.17+, End flashes on 1.21.9+,
   and looking straight up/down in the End. Watch for flicker or black pixels.
5. On 26.3 inspect Poplar foliage/signs/boats, shrubs, shelf mushrooms, and wool
   and concrete stairs/slabs. Compare their treatment with existing materials.
6. Repeat relevant scenes with vanilla clouds, a known labPBR pack, and Distant
   Horizons where supported. Check transparency sorting and distant water seams.
7. Compare frame times against v1.2.7 in the same scene/settings. Check at least
   one integrated GPU and representative Intel, AMD, NVIDIA and Apple systems
   before making cross-hardware stability claims.

## Reproduce offline checks

Install Python 3.10+ and Khronos glslang (`glslang-tools` on Ubuntu, `glslang`
on Homebrew). The runner also accepts `--compiler /path/to/glslang`.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_shader.py --version 1.2.8 --zip releases/Lumina_Shader_Lite_v1.2.8.zip
python3 scripts/compile_shader.py --report /tmp/lumina-matrix.json
python3 scripts/compile_shader.py --versions 1.16.5 1.20.1 --loaders iris-legacy
python3 scripts/compile_shader.py --versions 1.21.11 26.3 --loaders iris-modern --dh
python3 scripts/compile_shader.py --versions 1.16.5 26.3 --option RP_MODE=2 --vendor AMD
python3 scripts/compile_shader.py --versions 1.16.5 1.21.5 1.21.6 26.3 --profiles LOW ULTRA --option CLOUD_STYLE_DEFINE=50 --os MAC --vendor OTHER
```

GitHub Actions runs these checks on `luminalitedev`, `main` and pull requests,
and retains compilation reports as workflow artifacts.

## Technical references

- [Mojang release manifest](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json)
  identifies the stable game releases (reviewed September 19, 2026).
- [Minecraft 26.3 release notes](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-3)
  document the new content and rendering changes. Loader handling still matters;
  a GLSL shaderpack does not itself provide a Vulkan backend.
- [Iris version macro implementation](https://github.com/IrisShaders/Iris/blob/26.3/common/src/main/java/net/irisshaders/iris/gl/shader/StandardMacros.java)
  encodes 26.3 as `260300`, keeping existing numeric version comparisons valid.
- [Iris compatibility transformation](https://github.com/IrisShaders/Iris/blob/26.3/common/src/main/java/net/irisshaders/iris/pipeline/transform/transformer/VanillaTransformer.java)
  supplies modern line handling and projection conversion for compatibility inputs.
- [OptiFine property reference](https://github.com/sp614x/optifine/blob/master/OptiFineDoc/doc/shaders.properties)
  documents unique explicit `smooth()` IDs.
- Iris documents its injected [chunk fade variable](https://shaders.properties/current/reference/attributes/mc_chunkfade/)
  and [Distant Horizons material ID](https://shaders.properties/current/reference/mod-support/distant_horizons/).
