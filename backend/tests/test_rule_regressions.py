import pytest
from app.services.rules import RuleEngine
from app.services.parsers.wazuh import parse_wazuh
from acdt.verification.verifier import Verifier


@pytest.fixture
def engine(tmp_path):
    return RuleEngine(tmp_path)


def test_logsource_isolation(engine):
    rule = {"logsource":{"product":"windows"}, "detection":{"selection":{"Image":"cmd.exe"}, "condition":"selection"}}
    assert not engine._evaluate_rule(rule, {"product":"linux", "process_name":"cmd.exe"})


def test_contains_all_requires_every_value(engine):
    rule = {"detection":{"selection":{"CommandLine|contains|all":["alpha","beta"]},"condition":"selection"}}
    assert not engine._evaluate_rule(rule, {"command_line":"alpha"})
    assert engine._evaluate_rule(rule, {"command_line":"beta alpha"})


def test_wildcard_conditions_keep_exclusions(engine):
    rule = {"detection":{"selection":{"Image":"cmd.exe"}, "filter_legit":{"Image":"cmd.exe"}, "condition":"selection and not 1 of filter_*"}}
    assert not engine._evaluate_rule(rule, {"process_name":"cmd.exe"})
    rule["detection"]["filter_legit"] = {"Image":"other.exe"}
    rule["detection"]["condition"] = "all of selection* and not filter_legit"
    assert engine._evaluate_rule(rule, {"process_name":"cmd.exe"})


def test_unsupported_syntax_and_modifiers_fail_closed(engine):
    rule = {"detection":{"selection":{"Image|unsupported":"cmd.exe"}, "condition":"not selection"}}
    assert not engine._evaluate_rule(rule, {"process_name":"cmd.exe"})
    rule["detection"] = {"selection":{"Image":"cmd.exe"}, "condition":"selection | count() > 3"}
    assert not engine._evaluate_rule(rule, {"process_name":"cmd.exe"})


def test_null_and_cidr(engine):
    assert engine._match_selection_block({"ParentImage":None}, {})
    assert engine._match_selection_block({"SourceIp|cidr":"192.168.0.0/16"}, {"src_ip":"192.168.1.2"})


def test_wazuh_sysmon_uses_normalized_process_fields(engine):
    event = parse_wazuh({"data":{"win":{"eventdata":{"image":r"C:\Windows\cmd.exe", "commandLine":"cmd.exe /c whoami"}}}})
    rule = {"logsource":{"product":"windows","category":"process_creation"}, "detection":{"selection":{"Image|endswith":r"\cmd.exe"}, "condition":"selection"}}
    assert engine._evaluate_rule(rule, event.model_dump())


def test_no_probes_cannot_claim_containment():
    assert Verifier().run("unverified").contained is False
