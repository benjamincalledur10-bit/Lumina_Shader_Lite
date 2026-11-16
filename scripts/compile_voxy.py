#!/usr/bin/env python3
"""Preprocess Voxy API-3 descriptors and compile callback/UBO ABI harnesses.

This validates shaderpack code, not Voxy's renderer, Iris transforms or GPU output.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import compile_shader as shader

DIMENSIONS = ('world0', 'world-1', 'world1')
PARAMETERS = '''struct VoxyFragmentParameters {
    vec4 sampledColour; vec2 tile; vec2 uv; uint face; uint modelId;
    vec2 lightMap; vec4 tinting; uint customId;
};
'''


def preprocess(source, macros):
    clang = Path('/Library/Developer/CommandLineTools/usr/bin/clang')
    command = [str(clang), '-E', '-x', 'c'] if clang.is_file() else [shutil.which('cpp')]
    if command[0] is None:
        raise RuntimeError('Install cpp or clang for Voxy preprocessing')
    result = subprocess.run(command + ['-P', '-'], input=macros + source,
                            text=True, capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr)
    # Multiline GLSL strings are legal in Voxy's lenient JSON, not C strings.
    return result.stdout


def descriptor(dimension, options, version='26.3', enabled=True, dh=False):
    macros = shader.environment(version, 'iris-modern', dh=dh)
    if enabled:
        macros += '#define VOXY 3\n'
    path = shader.SHADERS / dimension / 'voxy.json'
    text = preprocess(shader.apply_options(shader.expand(path), options), macros)
    if not text.strip():
        return None
    return json.loads(text, strict=False)


def bindings(config):
    types = dict((name, kind) for kind, name in re.findall(
        r'\buniform\s+(\w+)\s+(\w+)', (shader.SHADERS / 'lib/uniforms.glsl').read_text()))
    types.update(vxRenderDistance='int', **dict.fromkeys(
        ('vxProj', 'vxProjInv', 'vxProjPrev', 'vxModelView', 'vxModelViewInv', 'vxModelViewPrev'), 'mat4'))
    types.update(fogStart='float', fogEnd='float')
    names = config['uniforms']
    if len(names) != len(set(names)):
        raise ValueError('Duplicate Voxy uniform')
    ubo = 'layout(std140, binding=7) uniform ShaderUniformBindings {\n'
    ubo += ''.join(f'{types[name]} {name};\n' for name in names) + '};\n'
    return ubo + ''.join(f'uniform {kind} {name};\n' for name, kind in config['samplers'].items())


def callback_source(dimension, stage, options, config, version='26.3'):
    macros = shader.environment(version, 'iris-modern') + '#define VOXY 3\n'
    source = shader.apply_options(shader.expand(shader.SHADERS / dimension / ('voxy_' + stage + '.glsl')), options)
    callback = preprocess(source, macros)
    return '#version 460 core\n' + bindings(config) + PARAMETERS + callback + '''
void main() {
    voxy_emitFragment(VoxyFragmentParameters(vec4(1), vec2(0), vec2(0),
                      1u, 0u, vec2(0.5), vec4(1), 0u));
}
'''


def renderer_pair(repository, dimension, stage, options, config, version='26.3'):
    """Attach the pack to Voxy's actual MDIC vertex/fragment sources.

    This reproduces source assembly and the callback's gl_FragCoord conversion,
    not the complete Java AST transformer or runtime framebuffer setup.
    """
    assets = repository / 'src/main/resources/assets/voxy/shaders'

    def expand_asset(path):
        return re.sub(r'(?m)^\s*#import\s+<voxy:([^>]+)>',
                      lambda match: expand_asset(assets / match[1]), path.read_text())

    macros = '#define PATCHED_SHADER\n#define TAA_PATCH\n#define USE_REVERSE_Z\n#define USE_ZERO_ONE_DEPTH\n'
    if stage == 'translucent':
        macros += '#define TRANSLUCENT\n'
    # Already-preprocessed pack callback; the actual struct comes from Voxy.
    patch = callback_source(dimension, stage, options, config, version)
    patch = patch.split(PARAMETERS, 1)[1].rsplit('\nvoid main() {', 1)[0]
    patch = re.sub(r'\bgl_FragCoord\b',
                   '(vec4(gl_FragCoord.xy, 1.0-gl_FragCoord.z, gl_FragCoord.w))', patch)
    fragment = expand_asset(assets / 'lod/gl46/quads.frag') + '\n' + bindings(config) + patch
    vertex = expand_asset(assets / 'lod/gl46/quads3.vert')
    vertex += '\n' + bindings(config) + '\nvec2 taaShift()\n' + config['taaOffset']
    return shader.prepare(vertex, macros), shader.prepare(fragment, macros)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default=shutil.which('glslang') or shutil.which('glslangValidator'))
    parser.add_argument('--profiles', nargs='+', choices=shader.PROFILES, default=list(shader.PROFILES))
    parser.add_argument('--versions', nargs='+', default=['26.3'])
    parser.add_argument('--option', action='append', default=[])
    parser.add_argument('--report', type=Path)
    parser.add_argument('--voxy-source', type=Path,
                        help='Also link the actual MDIC renderer from a local Voxy checkout')
    args = parser.parse_args()
    if not args.compiler:
        parser.error('Install glslang or pass --compiler')
    overrides = dict(item.split('=', 1) for item in args.option)
    failures = []
    count = 0
    for version in args.versions:
        for profile in args.profiles:
            for taa in ('0', '1'):
                options = shader.profile_options()[profile] | {'TAA_MODE': taa} | overrides
                for dimension in DIMENSIONS:
                    config = descriptor(dimension, options, version)
                    for stage in ('opaque', 'translucent', 'taa'):
                        count += 1
                        if stage == 'taa':
                            source = '#version 460 core\n' + bindings(config)
                            source += 'vec2 taaShift()\n' + config['taaOffset']
                            source += '\nvoid main() { gl_Position = vec4(taaShift(), 0, 1); }\n'
                        else:
                            source = callback_source(dimension, stage, options, config, version)
                        with tempfile.TemporaryDirectory(prefix='lumina-voxy-') as folder:
                            paths = []
                            if args.voxy_source and stage != 'taa':
                                vertex, fragment = renderer_pair(args.voxy_source, dimension, stage,
                                                                 options, config, version)
                                for suffix, content in (('vert', vertex), ('frag', fragment)):
                                    path = Path(folder) / ('shader.' + suffix)
                                    path.write_text(content)
                                    paths.append(str(path))
                            else:
                                path = Path(folder) / ('shader.vert' if stage == 'taa' else 'shader.frag')
                                path.write_text(source)
                                paths.append(str(path))
                            result = subprocess.run([args.compiler, '-l', *paths], text=True,
                                                    capture_output=True, timeout=60)
                        if result.returncode:
                            label = f'{version}/{profile}/{dimension}/TAA={taa}/{stage}'
                            failures.append({'case': label, 'output': result.stdout + result.stderr})
                            print(label + '\n' + result.stdout + result.stderr, flush=True)
    report = {'kind': __doc__, 'cases': count, 'failures': failures,
              'compiler': subprocess.check_output([args.compiler, '--version'], text=True).splitlines()[0],
              'actual_voxy_renderer': bool(args.voxy_source),
              'profiles': args.profiles, 'versions': args.versions, 'options': overrides}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    label = 'Voxy renderer links/TAA' if args.voxy_source else 'Voxy ABI harnesses'
    print(f'{label}: {count} cases, {len(failures)} failures. Runtime validation required.')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
