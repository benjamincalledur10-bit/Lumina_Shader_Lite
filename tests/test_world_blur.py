"""Check the blur pass gate and its source-level buffer dependencies.

Preprocessing does not emulate loader transformations, framebuffer binding or GPUs.
"""
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('blur_compiler', ROOT / 'scripts/compile_shader.py')
COMPILER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(COMPILER)


class WorldBlurTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        clang = Path('/Library/Developer/CommandLineTools/usr/bin/clang')
        cls.preprocessor = ([str(clang), '-E', '-x', 'c'] if clang.is_file()
                            else [shutil.which('cpp')])
        if cls.preprocessor[0] is None:
            raise RuntimeError('Install cpp to run world blur regression checks')

    def preprocess(self, source, macros):
        source = re.sub(r'(?m)^#version[^\n]*', '', source)
        result = subprocess.run(self.preprocessor + ['-P', '-'], input=macros + source,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_gate_and_dependencies_across_blur_dimensions_taa_and_profiles(self):
        properties = (ROOT / 'shaders/shaders.properties').read_text()
        # Property section headings/comments are not C preprocessor directives.
        properties = re.sub(r'(?m)^[ \t]*#(?!if\b|ifdef\b|ifndef\b|elif\b|else\b|endif\b|define\b|undef\b)[^\n]*',
                            '', properties)
        dimensions = ('world0', 'world-1', 'world1')
        self.assertNotRegex(properties, r'flip\.composite3\.')
        for profile, options in COMPILER.profile_options().items():
            # Low excludes TAA; High exercises the active temporal path.
            if profile not in ('LOW', 'HIGH'):
                continue
            for blur in ('0', '1', '2'):
                for taa in ('0', '1'):
                    selected = options | {'WORLD_BLUR': blur, 'TAA_MODE': taa}
                    for loader in ('optifine', 'iris-modern'):
                        macros = COMPILER.environment('26.3', loader)
                        property_macros = macros + ''.join(
                            f'#define {name} {value}\n' for name, value in selected.items())
                        active = self.preprocess(properties, property_macros)
                        for dimension in dimensions:
                            with self.subTest(profile=profile, blur=blur, taa=taa,
                                              loader=loader, dimension=dimension):
                                gate = f'program.{dimension}/composite3.enabled=false'
                                self.assertEqual(gate in active, blur == '0')
                                sources = {}
                                for program in ('composite1', 'composite3', 'composite4', 'composite5', 'composite6'):
                                    path = ROOT / 'shaders' / dimension / (program + '.fsh')
                                    source = COMPILER.apply_options(COMPILER.expand(path), selected)
                                    sources[program] = self.preprocess(source, macros)
                                self.assertEqual('DoWorldBlur(color, z1, lViewPos);' in sources['composite3'],
                                                 blur != '0')
                                self.assertEqual('const bool colortex0MipmapEnabled = true;' in sources['composite3'],
                                                 blur != '0')
                                self.assertIn('const bool colortex0MipmapEnabled = true;', sources['composite4'])
                                self.assertIn('texture2D(colortex0, bloomCoord).rgb', sources['composite4'])
                                self.assertIn('texture2D(colortex0, texCoord).rgb', sources['composite5'])
                                self.assertEqual('DoTAA' in sources['composite6'],
                                                 taa == '1' and int(options['DETAIL_QUALITY']) >= 1)
                                if blur == '0':
                                    # The last writer and the skipped copy both set alpha to one.
                                    self.assertIn('gl_FragData[0] = vec4(color, 1.0);', sources['composite1'])
                                    main = sources['composite3'].split('void main() {', 1)[1]
                                    self.assertEqual(re.sub(r'\s+', ' ', main).strip(),
                                                     'vec3 color = texelFetch(colortex0, texelCoord, 0).rgb; '
                                                     'gl_FragData[0] = vec4(color, 1.0); }')
                                    self.assertEqual('color *= GetBloomFog(lViewPos);' in sources['composite1'],
                                                     dimension != 'world1')
                                else:
                                    self.assertEqual('color *= GetBloomFog(lViewPos);' in sources['composite3'],
                                                     dimension != 'world1')


if __name__ == '__main__':
    unittest.main()
