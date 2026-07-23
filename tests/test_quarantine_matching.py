import unittest

from tools.apply_private_quarantine import contains_identifier, identifier_patterns


class QuarantineIdentifierTests(unittest.TestCase):
    def setUp(self):
        self.patterns = identifier_patterns(
            {
                "matched_private_repository_identifiers": [
                    {
                        "name": "boundary-example",
                        "name_with_owner": "owner/boundary-example",
                    }
                ]
            }
        )

    def test_git_suffix_is_a_valid_identifier_delimiter(self):
        self.assertTrue(
            contains_identifier(
                "https://example.invalid/owner/boundary-example.git",
                self.patterns,
            )
        )

    def test_identifier_prefix_is_not_a_false_match(self):
        self.assertFalse(
            contains_identifier("owner/boundary-example-extra", self.patterns)
        )


if __name__ == "__main__":
    unittest.main()
