"""Voxy descriptors, buffer contracts and isolated distant-depth preprocessing."""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import compile_shader as SHADER
import compile_voxy as VOXY


class VoxyTests(unittest.TestCase):
    def test_descriptors_and_taa_across_profiles_dimensions_and_modes(self):
        for profile, settings in SHADER.profile_options().items():
            for dimension in VOXY.DIMENSIONS:
                for taa in ('0', '1'):
                    with self.subTest(profile=profile, dimension=dimension, taa=taa):
                        options = settings | {'TAA_MODE': taa, 'TAA_JITTER': '3'}
                        config = VOXY.descriptor(dimension, options)
                        self.assertEqual(config['version'], 1)
                        self.assertTrue(config['excludeLodsFromVanillaDepth'])
                        self.assertEqual(config['opaqueDrawBuffers'], [0, 6])
                        self.assertEqual(config['translucentDrawBuffers'], [0])
                        self.assertEqual(config['blending']['0'],
                                         'SRC_ALPHA ONE_MINUS_SRC_ALPHA ONE ONE_MINUS_SRC_ALPHA')
                        self.assertIn('vxProjInv', config['uniforms'])
                        self.assertIn('vxModelViewPrev', config['uniforms'])
                        VOXY.bindings(config)  # All requested fields must have a known type.
                        self.assertEqual('offsets[' in config['taaOffset'],
                                         taa == '1' and int(settings['DETAIL_QUALITY']) >= 1)
        # The native callback uses the same eight subpixel offsets as near geometry.
        pattern = r'vec2\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)'
        near = re.findall(pattern, (SHADER.SHADERS / 'lib/antialiasing/jitter.glsl').read_text())
        far = re.findall(pattern, (SHADER.SHADERS / 'program/voxy_taa.glsl').read_text())
        self.assertEqual(near, far)
        self.assertEqual(len(near), 8)

    def test_no_descriptor_without_voxy_or_with_real_distant_horizons(self):
        for dimension in VOXY.DIMENSIONS:
            self.assertIsNone(VOXY.descriptor(dimension, {}, enabled=False))
            self.assertIsNone(VOXY.descriptor(dimension, {}, dh=True))
            source = SHADER.expand(SHADER.SHADERS / dimension / 'voxy.json')
            macros = SHADER.environment('26.3', 'iris-modern') + '#define VOXY 2\n'
            self.assertEqual(VOXY.preprocess(source, macros).strip(), '')

    def test_all_jitter_scales_match_near_geometry(self):
        options = SHADER.profile_options()['HIGH'] | {'TAA_MODE': '1'}
        for jitter in ('0', '1', '2', '3'):
            body = VOXY.descriptor('world0', options | {'TAA_JITTER': jitter})['taaOffset']
            with self.subTest(jitter=jitter):
                self.assertEqual('offsets[' in body, jitter != '0')
                self.assertEqual('offset *= 0.125;' in body, jitter == '1')
                self.assertEqual('offset *= 0.33;' in body, jitter == '2')

    def test_depth_and_reprojection_bind_the_selected_renderer(self):
        settings = SHADER.profile_options()['HIGH']
        properties = (SHADER.SHADERS / 'shaders.properties').read_text()
        properties = re.sub(r'(?m)^[ \t]*#(?!if\b|ifdef\b|ifndef\b|elif\b|else\b|endif\b|define\b|undef\b)[^\n]*',
                            '', properties)
        for dimension in VOXY.DIMENSIONS:
            path = SHADER.SHADERS / dimension / 'composite6.fsh'
            source = re.sub(r'(?m)^#version[^\n]*', '', SHADER.expand(path))
            source = SHADER.apply_options(source, settings)
            for dh, voxy in ((False, False), (True, False), (False, True), (True, True)):
                macros = SHADER.environment('26.3', 'iris-modern', dh=dh)
                if voxy:
                    macros += '#define VOXY 3\n'
                with self.subTest(dimension=dimension, dh=dh, voxy=voxy):
                    active = VOXY.preprocess(source, macros)
                    active_properties = VOXY.preprocess(properties, macros)
                    self.assertEqual('blend.gbuffers_water=SRC_ALPHA ONE_MINUS_SRC_ALPHA ONE ONE_MINUS_SRC_ALPHA'
                                     in active_properties, dh or voxy)
                    if voxy and not dh:
                        self.assertIn('uniform sampler2D vxDepthTexTrans;', active)
                        self.assertIn('uniform sampler2D vxDepthTexOpaque;', active)
                        self.assertIn('vxProjInv * vec4(screenPos, 1.0)', active)
                        self.assertIn('vxModelViewPrev * previousPosition', active)
                        self.assertIn('vxModelViewInv * viewPosPrev', active)
                        self.assertIn('vxRenderDistance * 16', active)
                        self.assertNotRegex(active, r'\bdh(?:Projection|DepthTex|RenderDistance)\b')
                    elif dh:
                        self.assertIn('uniform sampler2D dhDepthTex;', active)
                        self.assertIn('dhProjectionInverse * vec4(screenPos, 1.0)', active)
                        self.assertNotIn('vxProj', active)
                    else:
                        self.assertNotIn('ReprojectionDH', active)
                        self.assertNotIn('vxDepthTex', active)


if __name__ == '__main__':
    unittest.main()
