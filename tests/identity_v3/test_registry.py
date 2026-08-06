import unittest

from identity_v3.registry import is_auto_resolvable, normalize_identifier, normalize_name, rule_for


class RegistryTests(unittest.TestCase):
    def test_only_explicit_stable_identifiers_auto_resolve(self):
        for scheme in ("github_id", "orcid", "viaf", "isni", "wikidata"):
            self.assertTrue(is_auto_resolvable(scheme), scheme)
        for scheme in (
            "github_login", "real_name", "company", "location", "topic",
            "biography", "followers", "website", "made_up_scheme",
        ):
            self.assertFalse(is_auto_resolvable(scheme), scheme)

    def test_registry_classifies_attributes_and_aliases(self):
        self.assertEqual(rule_for("github_login").category, "alias")
        self.assertEqual(rule_for("company").category, "attribute")
        self.assertEqual(rule_for("followers").category, "metric")
        self.assertEqual(rule_for("unregistered").category, "unknown")

    def test_unicode_comparison_key_preserves_non_latin_scripts(self):
        self.assertEqual(normalize_name(" 张伟 "), "张伟")
        self.assertEqual(normalize_name("Élodie DURAND"), "élodie durand")
        self.assertNotEqual(normalize_name("Élodie"), normalize_name("Elodie"))
        self.assertNotEqual(normalize_name("张伟"), "")

    def test_opaque_platform_ids_preserve_case(self):
        self.assertEqual(normalize_identifier("github_node_id", "MDQ6VXNlcjEwMQ=="), "MDQ6VXNlcjEwMQ==")
        self.assertNotEqual(
            normalize_identifier("github_node_id", "MDQ6VXNlcjEwMQ=="),
            normalize_identifier("github_node_id", "mdq6vxnlcjewmq=="),
        )

    def test_name_normalization_is_comparison_only_not_an_id(self):
        # Two people may share this key. The engine treats it as review evidence,
        # never as an entity identifier.
        self.assertEqual(normalize_name("Dr. Alex Lee"), normalize_name("Alex Lee"))


if __name__ == "__main__":
    unittest.main()
