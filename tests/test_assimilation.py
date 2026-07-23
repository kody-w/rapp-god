import unittest

from tools.check_assimilation import IntegrityChecker


class AssimilationIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = IntegrityChecker()

    def test_public_selection_decisions_and_exact_counts(self):
        decisions = self.checker.check_decisions()
        self.assertEqual(decisions["included"], 197)
        self.checker.check_mapping_totals()

    def test_role_based_semantic_layout_and_authority_pins(self):
        self.checker.check_semantic_layout()

    def test_every_destination_hash_mode_and_tree(self):
        validated = self.checker.check_destinations_hashes_modes_and_trees()
        self.assertEqual(validated, 41512)

    def test_immutable_grail_metadata_and_hashes(self):
        self.checker.check_grail()

    def test_private_sources_are_aggregate_quarantine_only(self):
        self.checker.check_private_quarantine()

    def test_component_licenses_remain_scoped_to_upstream(self):
        self.checker.check_component_licenses()

    def test_orphan_gitlink_is_dispositioned_without_payload(self):
        self.checker.check_orphan_gitlink()

    def test_indexes_are_deterministic_and_nested_workflows_inactive(self):
        self.checker.check_indexes()

    def test_observatory_abi_and_existing_frames_remain(self):
        self.checker.check_observatory_abi()

    def test_no_target_blob_reaches_github_hard_limit(self):
        _, size = self.checker.check_target_file_sizes()
        self.assertLess(size, 100_000_000)

    def test_no_nested_git_metadata_or_unreviewed_secret(self):
        self.checker.check_no_nested_git_metadata()
        self.checker.check_secret_scan()

    def test_archive_members_are_deterministic_and_safely_accounted(self):
        self.checker.check_archive_proof()

    def test_upstream_baselines_keep_known_failures_honest(self):
        self.checker.check_upstream_test_baselines()

    def test_remote_refs_and_release_assets_remain_metadata_only(self):
        self.checker.check_ref_release_proof()

    def test_native_baseline_selection_census_and_commit_objects(self):
        self.checker.check_native_commit_and_census_proof()

    def test_source_capture_window_is_per_repository_and_non_atomic(self):
        self.checker.check_source_capture_window()

    def test_workspace_dag_and_release_ownership_are_fail_closed(self):
        self.checker.check_workspace_graph()

    def test_offline_observatory_generator_is_current(self):
        self.checker.check_build_no_net()

    def test_every_catalog_and_provenance_artifact_is_digest_bound(self):
        self.checker.check_generated_artifact_manifest()

    def test_staged_tree_has_exact_closure_and_no_unallowlisted_secret(self):
        self.checker.check_staged_closure_and_secret_report()


if __name__ == "__main__":
    unittest.main()
