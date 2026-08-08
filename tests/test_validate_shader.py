import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_shader", ROOT / "scripts/validate_shader.py"
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

SHADER_SOURCE = """\
#define QUALITY 1 //[0 1]
#define SPEED 1.0 //[0.5 1.0 2.0]
#define HIDDEN 0
"""

VALID_PROPERTIES = """\
profile.DEFAULT=QUALITY=1 SPEED=1.0
screen=[DETAILS] QUALITY
screen.DETAILS=SPEED
sliders=SPEED
"""


class MenuConfigurationTests(unittest.TestCase):
    def assert_invalid(self, properties: str, message: str) -> None:
        with self.assertRaisesRegex(RuntimeError, message):
            VALIDATOR.validate_menu_configuration(properties, SHADER_SOURCE)

    def test_valid_configuration(self) -> None:
        self.assertEqual(
            VALIDATOR.validate_menu_configuration(VALID_PROPERTIES, SHADER_SOURCE),
            (2, 1, 1),
        )

    def test_rejects_obsolete_profile_controls(self) -> None:
        properties = VALID_PROPERTIES.replace("SPEED=1.0", "SPEED=1.0 HIDDEN=0")
        self.assert_invalid(properties, "Profile options are not exposed")

    def test_rejects_missing_menu_options(self) -> None:
        properties = VALID_PROPERTIES.replace("QUALITY\n", "MISSING\n")
        self.assert_invalid(properties, "Menu options do not exist")

    def test_rejects_missing_and_orphaned_screens(self) -> None:
        self.assert_invalid(
            VALID_PROPERTIES.replace("[DETAILS]", "[MISSING]"),
            "Referenced screens do not exist",
        )
        self.assert_invalid(
            VALID_PROPERTIES + "screen.ORPHAN=QUALITY\n",
            "Orphaned screens",
        )

    def test_rejects_duplicate_and_invalid_sliders(self) -> None:
        self.assert_invalid(
            VALID_PROPERTIES.replace("sliders=SPEED", "sliders=SPEED SPEED"),
            "Duplicate sliders",
        )
        self.assert_invalid(
            VALID_PROPERTIES.replace("screen.DETAILS=SPEED", "screen.DETAILS=SPEED HIDDEN").replace(
                "sliders=SPEED", "sliders=HIDDEN"
            ),
            "Sliders do not have configurable value lists",
        )


if __name__ == "__main__":
    unittest.main()
