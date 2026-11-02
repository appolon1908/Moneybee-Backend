import copy
import hashlib
import json
from pathlib import Path
import runpy
import re

import pytest


@pytest.fixture
def authority(monkeypatch):
    root = Path(__file__).parents[1]
    module = runpy.run_path(str(root / ".codestra/validate-production-orchestrator-contract.py"))
    monkeypatch.setenv("GITHUB_REPOSITORY", "appolon1908/Moneybee-Backend")
    monkeypatch.setenv("GITHUB_REPOSITORY_ID", "1343760409")
    return module


def test_canonical_repository_retains_exact_identity_and_authority(authority):
    contract = authority["load_contract"]()
    assert authority["EXPECTED_IDENTITIES"][contract["repository"]] == (
        1343760409, "application", True, False
    )
    authority["validate"](contract)


def test_wrong_stable_repository_id_is_rejected(authority):
    contract = copy.deepcopy(authority["load_contract"]())
    contract["repository_id"] = 1343760410
    with pytest.raises(authority["ContractError"], match="stable repository ID mismatch"):
        authority["validate"](contract)


def test_former_namespace_is_replaced_and_not_added_as_an_alias(authority, monkeypatch):
    contract = copy.deepcopy(authority["load_contract"]())
    contract["repository"] = "appolon1908-hue/Moneybee-Backend"
    monkeypatch.setenv("GITHUB_REPOSITORY", contract["repository"])
    with pytest.raises(authority["ContractError"], match="outside the protected catalog identity map"):
        authority["validate"](contract)


def test_active_ssh_command_remains_rejected(authority):
    workflow = """name: synthetic
jobs:
  deploy:
    runs-on: ubuntu-24.04
    steps:
      - run: ssh runtime.example deploy
"""
    with pytest.raises(authority["ContractError"]):
        authority["require_mutating_jobs_disabled"](workflow, "synthetic-unapproved.yml")


def test_moneybee_has_its_own_exact_executable_binding(authority):
    validator = runpy.run_path(str(authority["RELEASE_VALIDATOR_PATH"]))
    assert "MONEYBEE_PRODUCTION_VALIDATOR_SHA256" in validator
    actual = hashlib.sha256(
        (authority["ROOT"] / ".codestra/validate-production-orchestrator-contract.py").read_bytes()
    ).hexdigest()
    assert validator["MONEYBEE_PRODUCTION_VALIDATOR_SHA256"] == actual
    assert validator["SHARED_PRODUCTION_VALIDATOR_SHA256"] == (
        "5f47a14a4abe13d9c91d03cdb1d301b10c043467430fddc2d9f2910156d39987"
    )
    validator["validate_workflow_executable_bytes"](
        "appolon1908/Moneybee-Backend", ".github/workflows/production-orchestrator-contract.yml",
        ".codestra/validate-production-orchestrator-contract.py",
        (authority["ROOT"] / ".codestra/validate-production-orchestrator-contract.py").read_bytes(),
    )


def test_all_other_repository_pin_maps_remain_exactly_reviewed(authority):
    validator = runpy.run_path(str(authority["RELEASE_VALIDATOR_PATH"]))

    def normalize(value):
        if isinstance(value, dict):
            return {key: normalize(item) for key, item in value.items()
                    if key != "appolon1908/Moneybee-Backend"}
        if isinstance(value, (set, frozenset)):
            return sorted(normalize(item) for item in value)
        if isinstance(value, (list, tuple)):
            return [normalize(item) for item in value]
        return value

    names = ("EXPECTED_CHECK_WORKFLOWS", "EXPECTED_CHECK_WORKFLOW_SHA256",
             "EXPECTED_CHECK_WORKFLOW_EXECUTABLE_SHA256", "EXPECTED_REQUIRED_CHECK_SOURCE_CLOSURE_SHA256")
    payload = json.dumps({name: normalize(validator[name]) for name in names},
                         sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(payload).hexdigest() == (
        "2c2481c4c993b48f41e187b6602c8fd6feb439319001d967deb0d6997e6a07b2"
    )


@pytest.mark.parametrize("damage", ["missing", "duplicate", "nonliteral", "malformed", "unknown", "map"])
def test_scoped_binding_structure_and_map_semantics_are_bound(authority, damage):
    source = authority["RELEASE_VALIDATOR_PATH"].read_text()
    pattern = r'MONEYBEE_PRODUCTION_VALIDATOR_SHA256 = \(\n    "[0-9a-f]{64}"\n\)'
    assignment = re.search(pattern, source).group()
    changes = {
        "missing": source.replace(assignment, ""),
        "duplicate": source + "\n" + assignment + "\n",
        "nonliteral": source.replace(assignment, "MONEYBEE_PRODUCTION_VALIDATOR_SHA256 = untrusted_hash()"),
        "malformed": source.replace(assignment, 'MONEYBEE_PRODUCTION_VALIDATOR_SHA256 = "' + "g" * 64 + '"'),
        "unknown": source + '\nUNKNOWN_PRODUCTION_VALIDATOR_SHA256 = "' + "a" * 64 + '"\n',
        "map": source.replace(
            '": MONEYBEE_PRODUCTION_VALIDATOR_SHA256,', '": SHARED_PRODUCTION_VALIDATOR_SHA256,'
        ),
    }
    with pytest.raises(authority["ContractError"]):
        authority["validate_release_validator_trust_root"](
            changes[damage], "appolon1908/Moneybee-Backend"
        )


def test_normalized_digest_value_still_has_to_match_actual_executable(authority):
    source = authority["RELEASE_VALIDATOR_PATH"].read_text()
    validator = runpy.run_path(str(authority["RELEASE_VALIDATOR_PATH"]))
    actual = (authority["ROOT"] / ".codestra/validate-production-orchestrator-contract.py").read_bytes()
    mutated = source.replace(validator["MONEYBEE_PRODUCTION_VALIDATOR_SHA256"], "a" * 64)
    assert authority["release_validator_security_fingerprint"](mutated) == (
        authority["release_validator_security_fingerprint"](source)
    )
    bindings = validator["EXPECTED_CHECK_WORKFLOW_EXECUTABLE_SHA256"]["appolon1908/Moneybee-Backend"]
    bindings[".github/workflows/production-orchestrator-contract.yml"][
        ".codestra/validate-production-orchestrator-contract.py"
    ] = "a" * 64
    with pytest.raises(validator["PolicyError"], match="required check executable drift"):
        validator["validate_workflow_executable_bytes"](
            "appolon1908/Moneybee-Backend", ".github/workflows/production-orchestrator-contract.yml",
            ".codestra/validate-production-orchestrator-contract.py", actual,
        )


def test_guard_body_tampering_fails_exact_scoped_executable_check(authority):
    validator = runpy.run_path(str(authority["RELEASE_VALIDATOR_PATH"]))
    actual = (authority["ROOT"] / ".codestra/validate-production-orchestrator-contract.py").read_bytes()
    mutated = actual.replace(b'"ssh",', b'"ssh-removed-from-denylist",')
    assert mutated != actual
    with pytest.raises(validator["PolicyError"], match="required check executable drift"):
        validator["validate_workflow_executable_bytes"](
            "appolon1908/Moneybee-Backend", ".github/workflows/production-orchestrator-contract.yml",
            ".codestra/validate-production-orchestrator-contract.py", mutated,
        )
