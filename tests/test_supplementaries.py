"""State mapping and numerical emission checks for Supplementaries lights.

RGB samples and state semantics were reviewed against upstream 068439132a76dc.
The pure GLSL scalar helper is also compiled as C99 to execute its arithmetic;
this is not a GPU rendering test.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_compatibility import ROOT, VERSIONS, mapping, version_lines, COMPILER
sys.path.insert(0, str(ROOT / 'scripts'))
from compile_voxy import preprocess

LAMPS = {'stone_lamp': 10992, 'deepslate_lamp': 10992,
         'blackstone_lamp': 10996, 'end_stone_lamp': 11000}
SCONCES = {'sconce': 11005, 'sconce_wall': 11005, 'sconce_lever': 11005,
           'sconce_soul': 11009, 'sconce_wall_soul': 11009,
           'sconce_green': 11013, 'sconce_wall_green': 11013}


def resolve(blocks, name, **state):
    """Resolve namespace and state selectors, detecting accidental overlaps."""
    matches = []
    for selector, material in blocks.items():
        fields = selector.split(':')
        if len(fields) < 2 or ':'.join(fields[:2]) != 'supplementaries:' + name:
            continue
        if all(state.get(key) in values.split(',')
               for key, values in (field.split('=', 1) for field in fields[2:])):
            matches.append(material)
    if len(matches) > 1:
        raise AssertionError('Overlapping Supplementaries selectors: ' + name)
    return matches[0] if matches else 0


class SupplementariesMappingTests(unittest.TestCase):
    def test_all_lights_and_off_states_across_game_branches(self):
        source = (ROOT / 'shaders/block.properties').read_text()
        for version in VERSIONS:
            active = mapping(version_lines(source, COMPILER.version_number(version)))
            with self.subTest(version=version):
                for name, material in LAMPS.items():
                    self.assertEqual(resolve(active, name, rune='z', axis='y'), material)
                    self.assertEqual(material % 4, 0)
                for name, material in SCONCES.items():
                    for powered in ('true', 'false'):
                        self.assertEqual(resolve(active, name, lit='true', powered=powered,
                                                 waterlogged='false', facing='north'), material)
                        self.assertEqual(resolve(active, name, lit='false', powered=powered), 0)
                    self.assertEqual(material % 4, 1)
                self.assertEqual(resolve(active, 'redstone_lantern', powered='false', hanging='true'), 11017)
                self.assertEqual(resolve(active, 'redstone_lantern', powered='true'), 0)
                self.assertEqual(active['lantern'], 10560)
                self.assertEqual(active['glowstone'], 10412)
                self.assertEqual(active['copper_lantern'], 10988)
                names = {selector.split(':')[1] for selector in active if selector.startswith('supplementaries:')}
                self.assertEqual(names, set(LAMPS) | set(SCONCES) | {'redstone_lantern'})

    def test_integrated_pbr_and_voxy_use_the_same_helper(self):
        for dimension in ('world0', 'world-1', 'world1'):
            path = ROOT / 'shaders' / dimension / 'gbuffers_terrain.fsh'
            source = re.sub(r'(?m)^#version[^\n]*', '', COMPILER.expand(path))
            macros = COMPILER.environment('1.21.1', 'iris-modern')
            for mode in ('0', '1', '2', '3'):
                with self.subTest(dimension=dimension, rp_mode=mode):
                    active = preprocess(COMPILER.apply_options(source, {'RP_MODE': mode}), macros)
                    self.assertEqual('float GetSupplementariesEmission(' in active, mode == '1')
                    self.assertEqual('emission = GetSupplementariesEmission(color.rgb, mat);' in active,
                                     mode == '1')
        native = COMPILER.expand(ROOT / 'shaders/world0/voxy_opaque.glsl')
        native = preprocess(native, COMPILER.environment('26.3', 'iris-modern') + '#define VOXY 3\n')
        self.assertIn('emission = GetSupplementariesEmission(color.rgb, material);', native)


class SupplementariesEmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        local = Path('/Library/Developer/CommandLineTools/usr/bin/clang')
        compiler = str(local) if local.is_file() else shutil.which('cc')
        if not compiler:
            raise unittest.SkipTest('A C compiler is required to execute the scalar GLSL emission helper')
        folder = tempfile.TemporaryDirectory(prefix='lumina-supp-math-')
        cls.addClassCleanup(folder.cleanup)
        source = Path(folder.name) / 'emission.c'
        cls.executable = Path(folder.name) / 'emission'
        helper = (ROOT / 'shaders/lib/materials/materialMethods/supplementariesEmission.glsl').read_text()
        source.write_text('''#include <stdio.h>
typedef struct { float r, g, b; } vec3;
float min(float a, float b) { return a < b ? a : b; }
float max(float a, float b) { return a > b ? a : b; }
float smoothstep(float lo, float hi, float x) {
    float t = max(0.0, min(1.0, (x-lo)/(hi-lo)));
    return t*t*(3.0-2.0*t);
}
''' + helper + '''
int main() {
    vec3 c; int material;
    while (scanf("%f %f %f %d", &c.r, &c.g, &c.b, &material) == 4)
        printf("%.9g ", GetSupplementariesEmission(c, material));
}
''')
        sdk = Path('/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk')
        sdk_options = ['-isysroot', str(sdk)] if sys.platform == 'darwin' and sdk.is_dir() else []
        result = subprocess.run([compiler, *sdk_options, '-std=c99', str(source), '-o', str(cls.executable)],
                                text=True, capture_output=True)
        if result.returncode:
            raise AssertionError(result.stderr)

    def evaluate(self, samples):
        data = ' '.join(f'{r/255} {g/255} {b/255} {material}' for material, (r, g, b) in samples)
        result = subprocess.run([str(self.executable)], input=data, text=True, capture_output=True, check=True)
        return [float(value) for value in result.stdout.split()]

    def test_default_texture_light_pixels_emit_and_frames_stay_dark(self):
        # Independent samples from the upstream base textures, not shader constants.
        lit = [(10992, (252, 244, 205)), (10992, (252, 189, 125)),
               (10996, (12, 223, 231)), (11000, (255, 64, 226)),
               (11005, (255, 170, 0)), (11005, (255, 255, 255)),
               (11009, (50, 232, 238)), (11013, (73, 160, 81)),
               (11017, (255, 59, 31))]
        for emission in self.evaluate(lit):
            self.assertGreater(emission, 0.0)
            self.assertLessEqual(emission, 3.0)
        frames = [(10992, (156, 153, 156)), (10992, (131, 115, 91)),
                  (10996, (78, 75, 84)), (11000, (232, 244, 178)),
                  (11000, (221, 200, 165)), (11005, (136, 142, 154)),
                  (11009, (136, 142, 154)), (11013, (150, 118, 68)),
                  (11017, (73, 80, 101))]
        self.assertEqual(self.evaluate(frames), [0.0] * len(frames))

    def test_unmapped_blocks_never_receive_supplementaries_emission(self):
        values = self.evaluate([(material, (255, 255, 255))
                                for material in (0, 10028, 10412, 10988, 11020)])
        self.assertEqual(values, [0.0] * len(values))


if __name__ == '__main__':
    unittest.main()
