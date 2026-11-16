# v1.3.0 Create/Flywheel integration through Colorwheel

Reviewed November 16, 2026 against Colorwheel source commit
[`0a3e94b`](https://github.com/djefrey/Colorwheel/tree/0a3e94b7b300ebf188ef030a8ff14734408ec85d).
That checkout identifies Colorwheel 1.3.2 on Minecraft 1.20.1, Flywheel 1.0.6,
Create Forge 6.0.4 and Create Fabric 6.0.7. These are the reviewed source
dependencies, not an installed/tested mod combination. Older Flywheel backends
and the separate Iris/Flywheel compatibility mod are outside this integration.

## Source review and fixes

The inherited pack already supplied opaque, translucent and shadow Colorwheel
programs, but the ordinary compiler explicitly excluded them. This update
retains those programs and adds dedicated handling for the other material blend
modes. It does not enable Lite's disabled voxel/colored-light features.

| Finding | Change |
| --- | --- |
| Colorwheel material overlays mixed all four channels, changing glass opacity | Mix only RGB and preserve the material's alpha |
| The shadow callback applied vertex tint before ordinary shadow code multiplied it again | Skip the second tint in the Colorwheel natural/water shadow paths |
| Flywheel vertex alpha was reused as vanilla terrain AO | Keep opacity in the native material callback; pass neutral AO alpha to Lumina lighting |
| Raw texture alpha could discard terrain before the Flywheel material ran | Delegate Colorwheel cutout decisions to its callback |
| The frontmost OIT material attachment used RGB8 without alpha | Use RGBA8 for that OIT attachment; keep ordinary buffer formats intact |
| Modern-Iris fade code referenced `mc_chunkFade` for instanced geometry | Use fade 1 for Colorwheel instances; ordinary chunk fading remains active |
| Additive/glint/lightning/crumbling materials fell back to terrain outputs with their own blend modes | Add color-only programs so these modes cannot blend into material/transmission metadata |
| Colorwheel shadow activation only checked entity-shadow settings | Also disable it when shadow quality is off |

All Colorwheel entry points now explicitly declare `#version 330 compatibility`.
The opaque and translucent paths share Lumina's terrain/water lighting; special
blend passes preserve the material output and use Colorwheel's native blend
mode, writing only scene color before deferred processing. Shadow outputs retain
the existing DRAWBUFFERS directives and OIT frontmost policy.

## Offline checks

`scripts/compile_colorwheel.py` reads the actual `clrwl_computeFragment`,
discard, light and overlay callback bodies from the pinned Colorwheel checkout.
Synthetic Flywheel inputs/material hooks exercise cutout, emissive and overlay
cases; glslang then compiles and links each pack vertex/fragment pair. It
deliberately does not inject `mc_chunkFade`, preventing that dependency from
being hidden by the test harness.

This is a callback/interface compilation test. It does not execute Colorwheel's
Java AST transformer, generated Create instance/material shaders, actual draw
submission or OIT accumulation/compositing. The 1.21.1 and 26.3 runs below are
shader source/macro checks, not evidence that the pinned 1.20.1 mod binary can
run on those game versions.

- 1,176 pairs: seven program types, three dimensions, seven profiles, TAA on/off,
  1.20.1/1.21.1, legacy/modern-Iris macro environments.
- 252 PBR stress pairs: Low/Ultra with custom PBR, POM/cutout, anisotropic
  filtering, puddles, active jitter and shadows; cutout/emissive/overlay inputs.
- 84 pairs with DH macros and 84 with Voxy macros, checking shader-level
  coexistence with the pack's distant-depth integration.
- Unit regressions cover opacity, shadow tint, cutout ownership, AO/fade input,
  OIT formats, shadow activation and color-only outputs for special blend modes.
- CI fetches the pinned Colorwheel source and repeats these checks separately
  from the ordinary shader compilation matrix.

Reproduce with Python 3.10+, cpp/clang, glslang and a Colorwheel checkout:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_shader.py
python3 scripts/compile_colorwheel.py --colorwheel-source /path/to/Colorwheel --report /tmp/colorwheel.json
```

## Runtime scope and known upstream limits

Use compatible game, loader, Iris/Oculus, Flywheel, Create and Colorwheel
versions; record all versions and GPU/driver details. Confirm the active backend
using `/flywheel backend` and check that it reports `colorwheel:instancing`
(or the appropriate enabled Colorwheel backend for that installation).

Inspect rotating cogwheels, shafts, water wheels, lit train tracks, tinted glass
contraptions, overlay effects and destruction cracks in all dimensions and
profiles, with shadows and TAA on/off. Compare tinted shadows and translucent
opacity from several angles, and reload/resize/change dimensions. Test optional
PBR and one LOD renderer at a time. Capture logs and matching screenshots and
frame times before claiming runtime compatibility or a performance improvement.

Colorwheel's documented render order/OIT limitations remain: translucent
contraptions and ordinary translucent terrain/water are not fully composited
together in every viewing order. These are not fixed by passing compilation.
No in-game test is recorded for this update.

Primary references: [program/material integration](https://djefrey.github.io/colorwheel/guides/adapt-your-shaderpack/1_programs/),
[OIT contracts and limits](https://djefrey.github.io/colorwheel/guides/adapt-your-shaderpack/2_oit/),
[native callback source](https://github.com/djefrey/Colorwheel/blob/0a3e94b7b300ebf188ef030a8ff14734408ec85d/common/src/main/resources/assets/colorwheel/flywheel/internal/iris_compat.frag)
and [program selection/blend groups](https://github.com/djefrey/Colorwheel/blob/0a3e94b7b300ebf188ef030a8ff14734408ec85d/common/src/main/java/dev/djefrey/colorwheel/shaderpack/ClrwlProgramId.java).

---

# v1.3.0 experimental Voxy integration

Implemented against Voxy's API-3 macro and version-1 shaderpack descriptor,
reviewed November 16, 2026, at upstream commit
[`5bf3335`](https://github.com/MCRcortex/voxy/tree/5bf33350a1cc7bb7e2b5d947b236c56d878b8a7d).
That source targets Minecraft 26.3 and Iris 1.11.7. These identify the reviewed
contract, not a completed in-game compatibility test. Stable v1.2.9 does not
contain this integration.

## Implemented scope

- Per-dimension `voxy.json`, opaque and translucent callbacks for all three
  dimensions. Opaque LODs write color and neutral material metadata; basic
  translucency writes color with separate alpha blending. Shader bodies reuse
  Lumina's existing lighting and translucent fog rather than vanilla lighting.
- Voxy's `customId` uses the pack's existing block mapping for basic foliage,
  lava and selected emissive handling. Distant geometry has simplified materials:
  near-field PBR normal maps, parallax, waving geometry and procedural water
  waves/reflections are not reproduced by these callbacks. These remain visual
  limits to evaluate at the near/LOD transition.
- LODs are excluded from vanilla depth. A small internal bridge maps existing
  distant-terrain consumers to `vxDepthTexTrans`, `vxDepthTexOpaque`, `vxProj`,
  `vxProjInv`, `vxProjPrev` and the block-converted `vxRenderDistance`. It enables
  the pack's internal distant-depth branches; it does not require installing DH.
- Deferred world-position reconstruction and TAA use Voxy model-view matrices;
  native callbacks use the same jitter offsets and scale as near geometry.
  Ordinary shaders continue to use standard Iris uniform declarations; callbacks
  receive their fields through Voxy's own UBO.
- No descriptor is active without Voxy API 3 or newer. If real DH macros are
  also present, the bridge is inactive and the Voxy descriptor is suppressed.
  Use one LOD renderer at a time. OptiFine is not a Voxy integration target.

## Offline evidence

Local GLSL checks use the official Khronos glslang 16.6.0 compiler, not a GPU.
The native harness supplies the documented Voxy fragment-parameter struct,
requested UBO fields and samplers, then compiles the expanded pack callbacks
and TAA function. With `--voxy-source`, it also assembles and links the actual
MDIC vertex/fragment GLSL from the pinned Voxy checkout, including its imports,
native fragment struct, opaque/translucent branches and reverse/zero-to-one
depth defines. The callback's `gl_FragCoord` conversion is reproduced; the full
Java AST transformation and runtime framebuffer bindings are not executed.
Source compatibility does not establish pixel
correctness or mod binary compatibility.

- 126 native callback/TAA cases at default jitter and 126 with jitter enabled:
  seven profiles, three dimensions, TAA on/off, opaque/translucent/TAA stages.
- 36 optional-effect cases: Low/Ultra, bloom/motion blur off, depth of field on,
  cloud shadows and light/atmosphere color controls on.
- Additional source audit: link the actual Voxy MDIC renderer with the pack's
  opaque/translucent callbacks for all seven profiles, three dimensions and
  TAA on/off (84 pairs), plus 42 TAA function cases. The same real-renderer
  check covers the 36 optional-effect cases above.
- 588 ordinary shader program pairs with Voxy API-3 macros on 26.3 across all
  seven profiles and three dimensions.
- Regression compilation: 672 ordinary pairs at 1.16.5/26.3, Low/Ultra,
  OptiFine/modern-Iris macros, and 360 DH pairs at 1.21.11/26.3, Low/Ultra.
- Unit checks cover descriptor activation and precedence, buffer/blend contract,
  typed bindings, jitter parity and renderer-specific depth/reprojection inputs.

CI checks out the pinned Voxy source and runs the real-renderer links plus
Voxy-enabled ordinary shaders. Reproduce (the standalone harness needs no checkout):

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_shader.py
python3 scripts/compile_voxy.py --option TAA_JITTER=3 --report /tmp/voxy-native.json
python3 scripts/compile_shader.py --versions 26.3 --loaders iris-modern --voxy --report /tmp/voxy-consumers.json
python3 scripts/compile_voxy.py --voxy-source /path/to/voxy --option TAA_JITTER=3 --report /tmp/voxy-renderer.json
```

## Runtime acceptance still pending

Use an actually compatible Minecraft/Iris/Sodium/Voxy installation. Record exact
versions, GPU/driver, resolution and profile. First test Voxy alone as the LOD
renderer, without DH. Check all dimensions and all seven profiles:

1. Inspect chunk transitions, mountains against sky, leaves, emissive blocks,
   water/glass, underwater views, sunrise/sunset, rain and dimension fog.
2. Check LOD occlusion behind near terrain, entities, water and clouds. Verify
   no LODs bleed through opaque objects or overwrite vanilla depth in captures.
3. Compare TAA on/off and jitter levels while standing still and moving/turning;
   inspect distant edges for ghosting, flicker or reprojection drift.
4. Test Bloom OFF + WORLD_BLUR OFF, both other blur modes, motion blur, shadows,
   window resizing and shader reloads. Treat depth-based post effects as unverified
   until their actual near/LOD boundary behavior has been observed.
5. Capture logs/screenshots and matching frame-time runs against the same pack
   without Voxy. Check a separate DH installation for regressions. Do not label
   the integration runtime-verified or claim a performance gain before this.

Primary contracts: [Voxy patch parser](https://github.com/MCRcortex/voxy/blob/5bf33350a1cc7bb7e2b5d947b236c56d878b8a7d/src/main/java/me/cortex/voxy/client/iris/IrisShaderPatch.java),
[fragment callback](https://github.com/MCRcortex/voxy/blob/5bf33350a1cc7bb7e2b5d947b236c56d878b8a7d/src/main/resources/assets/voxy/shaders/lod/gl46/quads.frag),
[native depth samplers](https://github.com/MCRcortex/voxy/blob/5bf33350a1cc7bb7e2b5d947b236c56d878b8a7d/src/main/java/me/cortex/voxy/client/iris/VoxySamplers.java)
and [Voxy uniforms](https://github.com/MCRcortex/voxy/blob/5bf33350a1cc7bb7e2b5d947b236c56d878b8a7d/src/main/java/me/cortex/voxy/client/iris/VoxyUniforms.java).

---

# v1.3.0 development experiment: skip inactive world blur

`composite3` is disabled only for `WORLD_BLUR=0`, independently in the Overworld,
Nether and End. Modes 1 (distance blur) and 2 (depth of field) retain the original
program. Shader bodies and profile defaults are unchanged.

At mode 0 the original fragment program only reads `colortex0.rgb` and writes
the same RGB with alpha 1. The preceding `composite1` already writes alpha 1.
No explicit flip is added: skipping both the copy and its automatic flip leaves
the current image available to the next pass. `composite4` reads that logical
`colortex0` and requests its own mipmaps when bloom is enabled; `composite5` also reads its RGB before
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

# v1.3.0 development experiment: conditional bloom mipmaps

The only shader change in this experiment wraps `composite4`'s
`colortex0MipmapEnabled` declaration in `#if BLOOM_ENABLED == 1`. The actual OFF
value is `-1`. Motion blur samples color using `texelFetch` or explicit LOD 0;
its computations, outputs and buffer flips are unchanged. `composite3` retains
its independent mipmap request for `WORLD_BLUR=1` and `2`.

The additional regression in `tests/test_world_blur.py` checks all 36
combinations of bloom on/off, motion blur on/off, three world-blur modes and
three dimensions. Low/High profiles and OptiFine/modern-Iris macro environments
at Minecraft 26.3 expand this to 144 combinations. Each compares the actual
expanded `composite4` against the unconditional-mipmap baseline: preprocessed
fragment calculations must match after removing the mipmap declaration. It
also checks bloom execution, motion-blur base-level reads and outputs, and
the retained blur/mipmap request in `composite3`.

The downstream `composite5` color read uses implicit LOD (`texture2D`) at
fullscreen coordinates. Its source is unchanged. Removing a mipmap request
can affect sampler filtering state, so matching preprocessed calculations
does not establish pixel equivalence. Specifically inspect this read in a
GPU capture and compare fine texture edges at native and non-square resolutions.
Do not force LOD 0 as part of this experiment without separate evidence.

Visual validation of the preceding `composite3` optimization is still pending.
Use commit `04d15ac` as this experiment's immediate baseline, after validating
that preceding change independently. Repeat the same-scene screenshot and
median/p95 frame-time procedure above for the 36 combinations, on compatible
Iris and OptiFine installations. With bloom OFF, verify no mipmap generation
is requested by `composite4`; with world blur ON, verify `composite3` still
generates the levels it needs. Check motion blur, bloom, TAA, dimension changes,
window resizing and shader reloads. GPU timings should isolate mipmap cost.
No in-game comparison, FPS result or runtime compatibility result is recorded
for this experiment. Offline preprocessing does not replace GLSL compilation.

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
