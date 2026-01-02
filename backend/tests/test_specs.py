import unittest


class SpecDefaultsTest(unittest.TestCase):
    def test_defaults_non_null(self):
        from photonflow.blocks import registry
        from photonflow.core.composites import composites

        specs = {}
        specs.update(registry.specs())
        specs.update(composites.specs())

        bad = []
        for name, info in specs.items():
            spec = info.get("spec", {})
            for section in ("params", "nonideal"):
                for key, entry in spec.get(section, {}).items():
                    default = entry.get("default", None)
                    if default is None or not isinstance(default, (int, float, bool, str)):
                        bad.append((name, section, key, default))
        self.assertEqual(bad, [], f"Defaults must be number/bool/string: {bad}")


if __name__ == "__main__":
    unittest.main()
