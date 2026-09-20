"""Regression checks for versioned material maps and custom uniform expressions."""
import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


COMPILER = module('compile_shader')
VALIDATOR = module('validate_shader')
# All stable Minecraft releases in the requested interval, including patch releases.
VERSIONS = ['1.16.5', '1.17', '1.17.1', '1.18', '1.18.1', '1.18.2',
            '1.19', '1.19.1', '1.19.2', '1.19.3', '1.19.4',
            '1.20', '1.20.1', '1.20.2', '1.20.3', '1.20.4', '1.20.5', '1.20.6',
            '1.21', '1.21.1', '1.21.2', '1.21.3', '1.21.4', '1.21.5', '1.21.6',
            '1.21.7', '1.21.8', '1.21.9', '1.21.10', '1.21.11',
            '26.1', '26.1.1', '26.1.2', '26.2', '26.3']


def version_lines(source, version):
    """Select only simple MC_VERSION branches used in these property sections.

    Fail on unsupported directives rather than silently ignoring new conditions.
    This is not a replacement for the loader's preprocessor.
    """
    active = True
    stack = []
    result = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith('#if '):
            match = re.fullmatch(r'#if MC_VERSION >= (\d+)', stripped)
            if not match:
                raise ValueError('Unsupported test condition: ' + stripped)
            condition = version >= int(match[1])
            stack.append((active, condition))
            active = active and condition
        elif stripped == '#else':
            parent, condition = stack[-1]
            active = parent and not condition
        elif stripped == '#endif':
            active, _ = stack.pop()
        elif re.match(r'#(?:ifdef|ifndef|elif)\b', stripped):
            raise ValueError('Unsupported test directive: ' + stripped)
        elif active:
            result.append(line)
    if stack:
        raise ValueError('Unclosed conditional')
    return '\n'.join(result)


def mapping(source):
    result = {}
    for match in re.finditer(r'(?m)^(block|entity)\.(\d+)=(.*)$', source):
        for token in match[3].split():
            if token in result:
                raise ValueError('Duplicate material mapping: ' + token)
            result[token] = int(match[2])
    return result


class CompatibilityTests(unittest.TestCase):
    def test_calendar_macro_encoding(self):
        self.assertEqual(COMPILER.version_number('1.16.5'), 11605)
        self.assertEqual(COMPILER.version_number('26.3'), 260300)
        self.assertEqual(COMPILER.version_number('26.1.2'), 260102)

    def test_uniforms_only_reference_available_game_features(self):
        source = (ROOT / 'shaders/shaders.properties').read_text().split('# Custom Uniforms', 1)[1]
        for version in VERSIONS:
            number = COMPILER.version_number(version)
            active = version_lines(source, number)
            with self.subTest(version=version):
                self.assertEqual('BIOME_PALE_GARDEN' in active, number >= 12104)
                self.assertEqual('darknessFactor' in active, number >= 11900)
                self.assertEqual(len(re.findall(r'uniform.float.inPaleGarden=', active)), 1)
                self.assertEqual(len(re.findall(r'uniform.float.maxBlindnessDarkness=', active)), 1)
                if number < 12104:
                    self.assertIn('uniform.float.inPaleGarden=0.0', active)
                if number < 11900:
                    self.assertIn('uniform.float.maxBlindnessDarkness=blindness', active)

    def test_cauldron_and_creaking_heart_states_across_releases(self):
        source = (ROOT / 'shaders/block.properties').read_text()
        for version in VERSIONS:
            number = COMPILER.version_number(version)
            active = mapping(version_lines(source, number))
            with self.subTest(version=version):
                self.assertEqual(active['hopper'], 10045)
                if number < 11700:
                    self.assertEqual(active['cauldron:level=0'], 10045)
                    for level in (1, 2, 3):
                        self.assertEqual(active[f'cauldron:level={level}'], 10049)
                    self.assertNotIn('cauldron', active)
                    self.assertNotIn('water_cauldron', active)
                else:
                    self.assertEqual(active['cauldron'], 10045)
                    self.assertEqual(active['water_cauldron'], 10049)
                if number >= 12105:
                    self.assertEqual(active['creaking_heart:creaking_heart_state=uprooted'], 10944)
                    self.assertEqual(active['creaking_heart:creaking_heart_state=awake'], 10948)
                    self.assertNotIn('creaking_heart:active=true', active)
                else:
                    self.assertEqual(active['creaking_heart:active=false'], 10944)
                    self.assertEqual(active['creaking_heart:active=true'], 10948)

    def test_modern_foliage_signs_and_boats_have_correct_materials(self):
        blocks = mapping(version_lines((ROOT / 'shaders/block.properties').read_text(), 260300))
        for color in ('red', 'orange', 'yellow'):
            self.assertEqual(blocks[color + '_poplar_leaves'], blocks['oak_leaves'])
        self.assertEqual(blocks['poplar_sapling'], blocks['oak_sapling'])
        self.assertEqual(blocks['red_shrub'], blocks['fern'])
        self.assertEqual(blocks['shelf_mushroom'], blocks['brown_mushroom'])
        self.assertEqual(blocks['potted_poplar_sapling'], blocks['potted_oak_sapling'])
        for wood in ('poplar', 'pale_oak'):
            for variant in ('sign', 'wall_sign', 'hanging_sign', 'wall_hanging_sign'):
                self.assertEqual(blocks[wood + '_' + variant], 5004)
        self.assertNotIn('works', blocks)
        entities = mapping(version_lines((ROOT / 'shaders/entity.properties').read_text(), 260300))
        for boat in ('bamboo_raft', 'bamboo_chest_raft', 'poplar_boat', 'poplar_chest_boat'):
            self.assertEqual(entities[boat], entities['oak_boat'])

    def test_partial_wool_and_concrete_preserve_material_families(self):
        blocks = mapping(version_lines((ROOT / 'shaders/block.properties').read_text(), 260300))
        colors = 'white orange magenta light_blue yellow lime pink gray light_gray cyan purple blue brown green red black'.split()
        for color in colors:
            for material in ('wool', 'concrete'):
                for shape in ('stairs', 'slab'):
                    full = blocks[f'{color}_{material}']
                    partial = blocks[f'{color}_{material}_{shape}']
                    self.assertEqual(partial // 4, full // 4)
                    self.assertEqual(partial % 4, 1)

    def test_smoothing_expressions_do_not_share_state(self):
        source = (ROOT / 'shaders/shaders.properties').read_text()
        self.assertGreater(VALIDATOR.validate_smoothing_ids(source), 0)
        with self.assertRaisesRegex(RuntimeError, 'Shared smoothing IDs'):
            VALIDATOR.validate_smoothing_ids(source.replace('smooth(55,', 'smooth(54,'))
        with self.assertRaisesRegex(RuntimeError, 'Shared smoothing IDs'):
            VALIDATOR.validate_smoothing_ids(source.replace('smooth(6,', 'smooth(4,'))

    def test_profile_overrides_replace_every_duplicate_definition(self):
        source = '#define CLOUD_QUALITY 1 //[0 1 2 3]\n#define CLOUD_QUALITY 1\nconst float shadowDistance = 64.0;\n'
        updated = COMPILER.apply_options(source, {'CLOUD_QUALITY': '3', 'shadowDistance': '224.0'})
        self.assertEqual(updated.count('#define CLOUD_QUALITY 3'), 2)
        self.assertIn('shadowDistance = 224.0;', updated)


if __name__ == '__main__':
    unittest.main()
