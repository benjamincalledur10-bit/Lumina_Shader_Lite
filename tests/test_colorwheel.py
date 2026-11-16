"""Regressions for Flywheel material opacity, tint, OIT and pass contracts."""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import compile_shader as SHADER
import compile_colorwheel as COLORWHEEL
from compile_voxy import preprocess


def active_program(dimension, program, suffix, options=None, loader='iris-modern'):
    source = SHADER.expand(SHADER.SHADERS / dimension / (program + suffix))
    source = re.sub(r'(?m)^#version[^\n]*', '', source)
    options = SHADER.profile_options()['HIGH'] | (options or {})
    return preprocess(SHADER.apply_options(source, options), SHADER.environment('1.21.1', loader))


class ColorwheelTests(unittest.TestCase):
    def test_program_coverage_and_color_only_effects(self):
        for dimension in COLORWHEEL.DIMENSIONS:
            for program in COLORWHEEL.PROGRAMS:
                for suffix in ('.vsh', '.fsh'):
                    path = SHADER.SHADERS / dimension / (program + suffix)
                    self.assertTrue(path.read_text().startswith('#version 330 compatibility\n'))
                fragment = active_program(dimension, program, '.fsh')
                self.assertIn('clrwl_computeFragment(', fragment)
                self.assertIn('gl_FragData[0]', fragment)
                if program not in ('clrwl_gbuffers', 'clrwl_gbuffers_translucent', 'clrwl_shadow'):
                    self.assertNotRegex(fragment, r'gl_FragData\[[1-9]')
                    self.assertIn('color.rgb = mix(color.rgb, overlayColor.rgb, overlayColor.a);', fragment)

    def test_material_overlay_preserves_translucent_opacity(self):
        # Evaluate the channels selected by the actual GLSL assignment, so the
        # old vec4 mix fails even though it is perfectly legal GLSL.
        source = active_program('world0', 'clrwl_gbuffers_translucent', '.fsh')
        prefix = COLORWHEEL.extract_function(source, 'main').split('vec3 screenPos', 1)[0]
        assignment = re.search(r'color(\.rgb)? = mix\((?:colorP|color)(?:\.rgb)?, '
                               r'overlayColor(?:\.rgb)?, overlayColor.a\);', prefix)
        self.assertIsNotNone(assignment)
        count = 3 if assignment[1] else 4
        overlay = (0.8, 0.1, 0.6, 0.5)
        for opacity in (0.0, 0.15, 0.7, 1.0):
            sample = (0.2, 0.4, 0.3, opacity)
            result = list(sample)
            for index in range(count):
                result[index] = sample[index] * (1.0 - overlay[3]) + overlay[index] * overlay[3]
            for actual, expected in zip(result[:3], (0.5, 0.25, 0.45)):
                self.assertAlmostEqual(actual, expected)
            self.assertEqual(result[3], opacity)

    def test_material_cutout_owns_discard_and_shadow_tint_is_applied_once(self):
        for dimension in COLORWHEEL.DIMENSIONS:
            fragment = active_program(dimension, 'clrwl_gbuffers', '.fsh')
            main = COLORWHEEL.extract_function(fragment, 'main')
            before_material = main.split('clrwl_computeFragment(', 1)[0]
            self.assertNotIn('discard;', before_material)
            vanilla = active_program(dimension, 'gbuffers_terrain', '.fsh')
            self.assertIn('if (color.a <= 0.00001) discard;', vanilla)
            for program, tinted_in_callback in (('clrwl_shadow', True), ('shadow', False)):
                fragment = active_program(dimension, program, '.fsh')
                natural = COLORWHEEL.extract_function(fragment, 'DoNaturalShadowCalculation')
                self.assertEqual('color1.rgb *= glColor.rgb;' in natural, not tinted_in_callback)

    def test_instanced_vertex_alpha_is_not_ao_and_chunk_fade_is_not_required(self):
        for dimension in COLORWHEEL.DIMENSIONS:
            for program in ('clrwl_gbuffers', 'clrwl_gbuffers_translucent'):
                for loader in ('iris-legacy', 'iris-modern'):
                    vertex = active_program(dimension, program, '.vsh', loader=loader)
                    self.assertNotIn('mc_chunkFade', vertex)
                    self.assertIn('glColorRaw.a = 1.0;' if program == 'clrwl_gbuffers'
                                  else 'glColor.a = 1.0;', vertex)
                    self.assertEqual('chunkFade = 1.0;' in vertex, loader == 'iris-modern')

    def test_oit_alpha_formats_and_shadow_profile_gates(self):
        properties = (SHADER.SHADERS / 'colorwheel.properties').read_text()
        for line in properties.splitlines():
            if '.format' in line:
                self.assertRegex(line.split('=', 1)[1].strip(), r'^RGBA')
        self.assertIn('oit.gbuffers.colortex0 = 0', properties)
        self.assertIn('oit.gbuffers.colortex3 = 1', properties)
        for entity in ('-1', '1', '2'):
            for shadow in ('-1', '0', '3'):
                macros = f'#define ENTITY_SHADOW {entity}\n#define SHADOW_QUALITY {shadow}\n'
                active = preprocess(properties, macros)
                self.assertEqual('shadow.enabled = false' in active, entity == '-1' or shadow == '-1')


if __name__ == '__main__':
    unittest.main()
