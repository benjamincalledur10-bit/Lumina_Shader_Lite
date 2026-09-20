"""Numerical regressions using expressions read directly from the shader source.

These tests validate coordinate/depth arithmetic, not rendered GPU images.
"""
import math
from pathlib import Path
import re
import unittest

from test_compatibility import COMPILER

ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / 'shaders' / path).read_text()


def expression(text, name):
    match = re.search(r'\b' + re.escape(name) + r'\s*=\s*([^;]+);', text)
    if not match:
        raise AssertionError('Missing shader expression: ' + name)
    return match[1]


def scalar(text, **variables):
    return eval(text, {'__builtins__': {}, 'max': max, 'min': min, 'int': int}, variables)


class Matrix:
    def __init__(self, rows):
        self.rows = rows

    def __mul__(self, other):
        if isinstance(other, Matrix):
            return Matrix([[sum(self.rows[i][k] * other.rows[k][j] for k in range(3))
                            for j in range(3)] for i in range(3)])
        return tuple(sum(row[k] * other[k] for k in range(3)) for row in self.rows)

    def transpose(self):
        return Matrix(list(zip(*self.rows)))


class ShadowRegressionTests(unittest.TestCase):
    def test_all_shadow_depth_consumers_use_the_writer_transform(self):
        # A depth-map writer/reader mismatch compiles cleanly but reverses occlusion.
        helper = source('lib/util/shadowProjection.glsl')
        scale = scalar(expression(helper, 'shadowDepthScale'))
        self.assertGreater(scale, 0.0)
        self.assertLessEqual(scale, 1.0)
        self.assertIn('clipPos.z *= shadowDepthScale;', helper)
        consumers = {
            'program/shadow.glsl': 'gl_Position.xyz = DistortShadowClip(gl_Position.xyz);',
            'lib/lighting/shadowSampling.glsl': 'DistortShadowClip(PlayerToShadow(playerPos))',
            'lib/atmospherics/clouds/mainClouds.glsl': 'DistortShadowClip(PlayerToShadow(tracePos - cameraPos))',
            'lib/atmospherics/volumetricLight.glsl': 'DistortShadowClip(shadowPosition.xyz)',
        }
        for path, call in consumers.items():
            with self.subTest(path=path):
                text = source(path)
                self.assertIn('#include "/lib/util/shadowProjection.glsl"', text)
                self.assertIn(call, text)
                self.assertNotRegex(text, r'\.z\s*\*=?\s*0\.[23]')
        for occluder, receiver in ((0.6, 0.7), (-0.7, -0.8), (0.0, 0.0)):
            stored = occluder * scale * 0.5 + 0.5
            sampled = receiver * scale * 0.5 + 0.5
            self.assertEqual(sampled <= stored, receiver <= occluder)
        # The old 0.2 reader incorrectly lights a point behind the 0.3 writer.
        self.assertLess(0.7 * 0.2 * 0.5 + 0.5, 0.6 * scale * 0.5 + 0.5)

    def test_cloud_projection_hits_the_plane_along_the_light_ray(self):
        text = source('lib/lighting/cloudShadows.glsl')
        formula = expression(text, 'cloudProjection')
        self.assertIn('if (worldLight.y <= 0.0001) return 1.0;', text)
        self.assertIn('cloudProjection.x, 0.0, cloudProjection.y) * distToCloudLayer1', text)
        self.assertIn('cloudProjection.x, 0.0, cloudProjection.y) * distToCloudLayer2', text)
        for light in ((0.6, 0.8, 0.0), (0.6, 0.6, math.sqrt(0.28)),
                      (-0.6, 0.6, -math.sqrt(0.28)), (0.0, 1.0, 0.0), (0.0, 0.5, math.sqrt(0.75))):
            for height in (16.0, 128.0, 300.0):
                offsets = []
                for axis in (0, 2):
                    component = formula.replace('worldLight.xz', 'horizontal').replace('worldLight.y', 'vertical')
                    offsets.append(scalar(component, horizontal=light[axis], vertical=light[1]) * height)
                hit = (offsets[0], height, offsets[1])
                # Collinearity is an independent geometric invariant.
                for i, j in ((0, 1), (1, 2), (2, 0)):
                    self.assertAlmostEqual(hit[i] * light[j] - hit[j] * light[i], 0.0, places=10)

    def test_foliage_shadow_offset_is_independent_of_light_view_rotation(self):
        text = source('program/shadow.glsl')
        match = re.search(r'vec3 normal = ([^;]+);\s*position.xyz \+= normal \* 0.35;', text)
        self.assertIsNotNone(match)
        normal = (1.0, 0.0, 0.0)
        for angle in (0, 30, 60, 90, 150):
            c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
            rotation = Matrix(((c, -s, 0), (s, c, 0), (0, 0, 1)))
            result = eval(match[1], {'__builtins__': {}, 'mat3': lambda x: x},
                          {'shadowModelViewInverse': rotation.transpose(),
                           'gl_NormalMatrix': rotation, 'gl_Normal': normal})
            for actual, expected in zip(result, normal):
                self.assertAlmostEqual(actual, expected, places=12)

    def test_scene_aware_update_interval_is_valid_at_low_fps_and_startup(self):
        text = source('lib/atmospherics/volumetricLight.glsl')
        formula = expression(text, 'updateInterval')
        for seconds in (0.0, 0.001, 1 / 60, 1 / 15, 1 / 7.5, 0.2, 1.0, 5.0):
            interval = scalar(formula, frameTimeSmooth=seconds)
            with self.subTest(frame_time=seconds):
                self.assertGreaterEqual(interval, 1)
                self.assertTrue(math.isfinite(interval))
                self.assertIsInstance(120 % interval, int)
        self.assertIn('frameCounter % updateInterval', text)

    def test_scene_aware_empty_shadow_samples_remain_finite(self):
        formula = expression(source('lib/atmospherics/volumetricLight.glsl'), 'salsCheck')
        self.assertEqual(scalar(formula, salsSampleSum=0.0, salsSampleCount=0), 0.0)
        self.assertEqual(scalar(formula, salsSampleSum=18.0, salsSampleCount=3), 6.0)

    def test_boolean_options_enable_previously_uncompiled_shadow_paths(self):
        text = '// #define CLOUD_SHADOWS\n#define SHADOW_FILTERING\n'
        result = COMPILER.apply_options(text, {'CLOUD_SHADOWS': 'true', 'SHADOW_FILTERING': 'false'})
        self.assertIn('\n#define CLOUD_SHADOWS\n', '\n' + result)
        self.assertIn('//#define SHADOW_FILTERING', result)
        with self.assertRaises(ValueError):
            COMPILER.apply_options(text, {'MISSING_OPTION': 'true'})


if __name__ == '__main__':
    unittest.main()
