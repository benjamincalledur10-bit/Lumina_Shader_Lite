#!/usr/bin/env python3
"""Link Colorwheel pack programs with its real material callback and test inputs.

Uses the pinned callback bodies from a Colorwheel checkout, synthetic Flywheel
material hooks and compatibility attributes. Does not execute the Java AST
transformer, generated Create instance shaders, OIT renderer or a GPU.
"""
import argparse
from functools import lru_cache
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import compile_shader as shader

PROGRAMS = ('clrwl_gbuffers', 'clrwl_gbuffers_translucent', 'clrwl_shadow',
            'clrwl_gbuffers_additive', 'clrwl_gbuffers_lightning',
            'clrwl_gbuffers_glint', 'clrwl_gbuffers_damagedblock')
DIMENSIONS = ('world0', 'world-1', 'world1')


def extract_function(source, name):
    match = re.search(r'\bvoid\s+' + re.escape(name) + r'\s*\([^)]*\)\s*\{', source)
    if not match:
        raise ValueError('Missing Colorwheel callback: ' + name)
    depth = 1
    end = match.end()
    while depth and end < len(source):
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    if depth:
        raise ValueError('Unbalanced callback: ' + name)
    return source[match.start():end]


@lru_cache(maxsize=None)
def material_library(repository, material):
    path = repository / 'common/src/main/resources/assets/colorwheel/flywheel/internal/iris_compat.frag'
    source = path.read_text()
    # Values normally supplied by Flywheel's generated instance/material shaders.
    prelude = '''
#define _FLW_USE_DISCARD
struct LuminaTestMaterial { bool useOverlay; bool ambientOcclusion; };
LuminaTestMaterial flw_material = LuminaTestMaterial(true, true);
uniform sampler2D flw_overlayTex;
vec4 flw_sampleColor, flw_fragColor;
vec4 flw_vertexColor = vec4(0.8, 0.6, 0.4, 0.5);
vec2 flw_vertexLight = vec2(0.5), flw_fragLight;
ivec2 flw_vertexOverlay = ivec2(0), flw_fragOverlay;
vec4 clrwl_overlayColor = vec4(0.0);
bool flw_discardPredicate(vec4 color) { return color.a < 0.1; }
void flw_materialFragment() { }
void flw_shaderLight() {
'''
    if material == 'emissive':
        prelude += 'flw_fragLight = vec2(1.0);\n'
    else:
        prelude += 'flw_fragColor.rgb *= 0.75;\n'
    prelude += '}\n'
    if material != 'overlay':
        prelude = prelude.replace('LuminaTestMaterial(true, true)', 'LuminaTestMaterial(false, true)')
    functions = ('clrwl_computeDiscard', '_clrwl_materialFragment_hook',
                 '_clrwl_shaderLight_hook', 'clrwl_getDebugColor', 'clrwl_computeFragment')
    return prelude + '\n'.join(extract_function(source, name) for name in functions) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default=shutil.which('glslang') or shutil.which('glslangValidator'))
    parser.add_argument('--colorwheel-source', required=True, type=Path)
    parser.add_argument('--versions', nargs='+', default=['1.20.1', '1.21.1'])
    parser.add_argument('--loaders', nargs='+', choices=['iris-legacy', 'iris-modern'],
                        default=['iris-legacy', 'iris-modern'])
    parser.add_argument('--profiles', nargs='+', choices=shader.PROFILES, default=list(shader.PROFILES))
    parser.add_argument('--materials', nargs='+', choices=['cutout', 'emissive', 'overlay'], default=['cutout'])
    parser.add_argument('--option', action='append', default=[])
    parser.add_argument('--dh', action='store_true')
    parser.add_argument('--voxy', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if not args.compiler:
        parser.error('Install glslang or pass --compiler')
    if args.dh and args.voxy:
        parser.error('Use one distant renderer at a time')
    overrides = dict(item.split('=', 1) for item in args.option)
    paths = [shader.SHADERS / dim / (program + '.vsh') for dim in DIMENSIONS for program in PROGRAMS]
    failures = []
    count = 0
    # Cache option expansion: game/loader/material variants share the same pack code.
    for profile in args.profiles:
        for taa in ('0', '1'):
            options = shader.profile_options()[profile] | {'TAA_MODE': taa} | overrides
            pack = {(path, suffix): shader.apply_options(shader.expand(path.with_suffix(suffix)), options)
                    for path in paths for suffix in ('.vsh', '.fsh')}
            for version in args.versions:
                for loader in args.loaders:
                    macros = shader.environment(version, loader, dh=args.dh)
                    macros += '#define HAS_COLORWHEEL\n#define COLORWHEEL_VERSION 10302\n'
                    if args.voxy:
                        macros += '#define VOXY 3\n'
                    for material in args.materials:
                        library = material_library(args.colorwheel_source, material)
                        for path in paths:
                            count += 1
                            with tempfile.TemporaryDirectory(prefix='lumina-colorwheel-') as folder:
                                targets = []
                                for suffix, stage in (('.vsh', '.vert'), ('.fsh', '.frag')):
                                    source = shader.prepare(pack[path, suffix], macros + (library if suffix == '.fsh' else ''))
                                    # Deliberately DO NOT inject mc_chunkFade: Flywheel isn't a chunk mesh.
                                    target = Path(folder) / ('shader' + stage)
                                    target.write_text(source)
                                    targets.append(str(target))
                                result = subprocess.run([args.compiler, '-l', *targets], text=True,
                                                        capture_output=True, timeout=60)
                            if result.returncode:
                                label = f'{version}/{loader}/{profile}/TAA={taa}/{material}/{path.parent.name}/{path.stem}'
                                failures.append({'case': label, 'output': result.stdout + result.stderr})
                                print(label + '\n' + result.stdout + result.stderr, flush=True)
    report = {'kind': __doc__, 'pairs': count, 'failures': failures,
              'compiler': subprocess.check_output([args.compiler, '--version'], text=True).splitlines()[0],
              'versions': args.versions, 'loaders': args.loaders, 'profiles': args.profiles,
              'materials': args.materials, 'options': overrides, 'distant_horizons': args.dh, 'voxy': args.voxy}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Colorwheel: {count} program pairs, {len(failures)} failures. Runtime rendering not executed.')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
