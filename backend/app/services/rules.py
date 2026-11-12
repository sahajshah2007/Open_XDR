"""A conservative Sigma subset. Unsupported syntax never falls back to a match.

Use RULES_DIR to select an explicitly enabled collection. The bundled SigmaHQ
archive is retained for detection engineering; curated local rules are the default.
"""
import ast
import copy
import fnmatch
import ipaddress
import logging
import re
from pathlib import Path
import yaml
from app.core.config import settings

logger = logging.getLogger(__name__)
SUPPORTED = {"contains", "startswith", "endswith", "all", "re", "cidr", "exists", "cased", "gt", "gte", "lt", "lte"}
ALIASES = {
    "Image": ["process_name", "raw.data.win.eventdata.image", "raw.Image", "raw.data.Image"],
    "CommandLine": ["command_line", "raw.CommandLine", "raw.data.CommandLine"],
    "SourceIp": ["src_ip"], "DestinationIp": ["dst_ip"], "TargetUser": ["user"],
    "DestinationPort": ["raw.dest_port", "raw.id.resp_p", "raw.data.dstport"],
}


def flatten(value, prefix=""):
    result = {}
    for key, item in value.items():
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict):
            result.update(flatten(item, name))
        else:
            result[name] = item
    return result


class RuleEngine:
    def __init__(self, rules_dir=None, *, rules=None):
        self.rules_dir = Path(rules_dir or settings.RULES_DIR)
        self.rules = copy.deepcopy(rules) if rules is not None else self.load_rules()

    def reload_rules(self):
        self.rules = self.load_rules()
        return len(self.rules)

    def load_rules(self):
        rules = []
        for path in sorted(self.rules_dir.rglob("*")):
            if path.suffix not in {".yaml", ".yml"}:
                continue
            try:
                for rule in yaml.safe_load_all(path.read_text(encoding="utf-8")):
                    if isinstance(rule, dict) and rule.get("id") and rule.get("detection") and rule.get("logsource"):
                        if rule.get("status") not in {"deprecated", "unsupported"}:
                            rules.append(rule)
            except (OSError, yaml.YAMLError):
                logger.warning("Cannot load rule file %s", path)
        return rules

    def match_event(self, event_data):
        return [rule for rule in self.rules if self._evaluate_rule(rule, event_data)]

    def _evaluate_rule(self, rule, event_data):
        try:
            for key, expected in rule.get("logsource", {}).items():
                if key != "definition" and event_data.get(key) != expected:
                    return False
            detection = rule["detection"]
            selections = {k: v for k, v in detection.items() if k not in {"condition", "timeframe"}}
            # Reject unsupported modifiers across the whole rule, including exclusions.
            for block in selections.values():
                for item in block if isinstance(block, list) else [block]:
                    if not isinstance(item, dict) or any(set(key.split("|")[1:]) - SUPPORTED for key in item):
                        return False
            results = {name: self._selection(value, event_data) for name, value in selections.items()}
            condition = detection.get("condition")
            if not isinstance(condition, str):
                return False

            def quantify(match):
                count, pattern = match.groups()
                values = [v for key, v in results.items() if pattern == "them" or fnmatch.fnmatchcase(key, pattern)]
                if not values:
                    raise ValueError("condition references no selections")
                return str(all(values) if count == "all" else sum(values) >= int(count))

            expression = re.sub(r"\b(all|\d+)\s+of\s+([\w*]+)", quantify, condition)
            tree = ast.parse(expression, mode="eval")

            def boolean(node):
                if isinstance(node, ast.Expression):
                    return boolean(node.body)
                if isinstance(node, ast.Name) and node.id in results:
                    return results[node.id]
                if isinstance(node, ast.Constant) and isinstance(node.value, bool):
                    return node.value
                if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                    return not boolean(node.operand)
                if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
                    values = [boolean(child) for child in node.values]
                    return all(values) if isinstance(node.op, ast.And) else any(values)
                raise ValueError("unsupported condition")

            return boolean(tree)
        except (KeyError, ValueError, TypeError, SyntaxError, re.error):
            return False

    def _selection(self, block, event):
        if isinstance(block, list):
            return any(self._match_selection_block(item, event) for item in block)
        return self._match_selection_block(block, event)

    def _match_selection_block(self, selection, event_data):
        values = flatten(event_data)
        for key, value in list(values.items()):
            if key.startswith("raw."):
                values.setdefault(key[4:], value)
        for alias, candidates in ALIASES.items():
            for candidate in candidates:
                if values.get(candidate) is not None:
                    values.setdefault(alias, values[candidate])
                    break
        for key, expected in selection.items():
            field, *modifiers = key.split("|")
            if set(modifiers) - SUPPORTED:
                return False
            actual = values.get(field)
            expected_list = expected if isinstance(expected, list) else [expected]
            matches = [self._value(actual, item, modifiers) for item in expected_list]
            if not (all(matches) if "all" in modifiers else any(matches)):
                return False
        return True

    @staticmethod
    def _value(actual, expected, modifiers):
        if "exists" in modifiers:
            return (actual is not None) == expected
        if expected is None:
            return actual is None
        if actual is None:
            return False
        if isinstance(actual, list):
            return any(RuleEngine._value(item, expected, modifiers) for item in actual)
        text, pattern = str(actual), str(expected)
        if "re" in modifiers:
            return re.search(pattern, text, 0 if "cased" in modifiers else re.IGNORECASE) is not None
        if "cidr" in modifiers:
            return ipaddress.ip_address(text) in ipaddress.ip_network(pattern, strict=False)
        for modifier, compare in {"gt": lambda a,b:a>b, "gte":lambda a,b:a>=b, "lt":lambda a,b:a<b, "lte":lambda a,b:a<=b}.items():
            if modifier in modifiers:
                return compare(float(actual), float(expected))
        if "cased" not in modifiers:
            text, pattern = text.lower(), pattern.lower()
        if "contains" in modifiers:
            return pattern in text
        if "startswith" in modifiers:
            return text.startswith(pattern)
        if "endswith" in modifiers:
            return text.endswith(pattern)
        return fnmatch.fnmatchcase(text, pattern)


rule_engine = RuleEngine()
