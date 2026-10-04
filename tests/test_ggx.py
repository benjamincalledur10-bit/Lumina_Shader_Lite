"""Numerical checks of the actual scalar GGX area-light shader expressions."""
import math
import re
import unittest

from test_shadows import source


def area_light(radius, no_l, no_v, vo_l, legacy=False):
    text = source('lib/lighting/ggx.glsl').split('float GGX(')[0]
    # Separate the shader's paired scalar declarations for sequential evaluation.
    for name in ('VoBr', 'VoLVTr', 'q', 's'):
        text = text.replace(', ' + name + ' =', '; float ' + name + ' =')
    variables = dict(radiusTan=radius, NoL=no_l, NoV=no_v, VoL=vo_l)
    functions = {'__builtins__': {}, 'sqrt': math.sqrt, 'max': max,
                 'clamp': lambda value, low, high: min(max(value, low), high)}
    for name, formula in re.findall(r'float\s+(\w+)\s*=\s*([^;]+);', text):
        if legacy and name == 'twoX1':
            formula = '2.0 * xNum / (xDenom * xDenom + xNum * xNum)'
        elif '?' in formula:
            condition, branches = formula.split('?', 1)
            yes, no = branches.split(':', 1)
            formula = '(' + yes + ') if (' + condition + ') else (' + no + ')'
        variables[name] = eval(formula, functions, variables)
        if name == 'RoL' and variables[name] >= variables['radiusCos']:
            return 1.0
        if name == 'cosTheta':
            for target in ('NoTr', 'VoTr'):
                assignment = re.search(r'^\s*' + target + r' = ([^;]+);', text, re.MULTILINE)
                variables[target] = eval(assignment[1], functions, variables)
    formula = re.search(r'return (clamp\([^;]+);', text)[1]
    return eval(formula, functions, variables)


class GGXRegressionTests(unittest.TestCase):
    def test_parallel_grazing_directions_remain_finite(self):
        with self.assertRaises(ZeroDivisionError):
            area_light(0.01, 0.0, 0.0, 1.0, legacy=True)
        for vo_l in (-1.0, 0.0, 0.5, 1.0):
            with self.subTest(vo_l=vo_l):
                value = area_light(0.01, 0.0, 0.0, vo_l)
                self.assertTrue(math.isfinite(value))
                self.assertGreaterEqual(value, 0.0)
                self.assertLessEqual(value, 1.0)

    def test_regular_and_near_grazing_directions_preserve_results(self):
        # Unit light/view vectors with equal elevations and varying azimuths.
        for elevation in (1e-6, 0.001, 0.1, 0.5, 0.9):
            for azimuth in (0.0, 0.5, 1.5, math.pi):
                vo_l = elevation**2 + (1.0 - elevation**2) * math.cos(azimuth)
                with self.subTest(elevation=elevation, azimuth=azimuth):
                    value = area_light(0.01, elevation, elevation, vo_l)
                    self.assertTrue(math.isfinite(value))
                    self.assertEqual(value, area_light(0.01, elevation, elevation, vo_l, legacy=True))


if __name__ == '__main__':
    unittest.main()
