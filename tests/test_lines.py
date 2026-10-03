"""Guard the active line path against the reported missing ftransform call."""
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('line_compiler', ROOT / 'scripts/compile_shader.py')
COMPILER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(COMPILER)


class LineTests(unittest.TestCase):
    def test_active_line_transforms_across_profiles_and_dimensions(self):
        clang = Path('/Library/Developer/CommandLineTools/usr/bin/clang')
        preprocessor = ([str(clang), '-E', '-x', 'c'] if clang.is_file()
                        else [shutil.which('cpp')])
        self.assertIsNotNone(preprocessor[0], 'Install cpp to run line regression checks')
        paths = sorted((ROOT / 'shaders').glob('world*/gbuffers_line.vsh'))
        self.assertEqual(len(paths), 3)
        for path in paths:
            for profile, options in COMPILER.profile_options().items():
                for taa in ('0', '1'):
                    with self.subTest(dimension=path.parent.name, profile=profile, taa=taa):
                        source = COMPILER.apply_options(COMPILER.expand(path), options | {'TAA_MODE': taa})
                        source = re.sub(r'(?m)^#version[^\n]*', '', source)
                        source = COMPILER.environment('26.3', 'iris-modern') + source
                        result = subprocess.run(preprocessor + ['-P', '-'], input=source,
                                                text=True, capture_output=True)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertNotRegex(result.stdout, r'\bftransform\s*\(')
                        self.assertIn('gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex', result.stdout)
                        self.assertEqual('gl_Position.xy = TAAJitter' in result.stdout,
                                         taa == '1' and int(options['DETAIL_QUALITY']) >= 1)


if __name__ == '__main__':
    unittest.main()
