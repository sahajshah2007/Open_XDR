"""Immutable, run-pinned detector inputs. Global ingest settings are untouched."""
import copy
import hashlib
import json
import uuid
from pathlib import Path
from app.core.config import settings
from app.models.experiment import DetectionProfile
from app.services.rules import RuleEngine

NATIVE_SOURCES = ['wazuh', 'suricata', 'falco', 'attacker']
ENGINE_VERSION = 1


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def rule_catalog():
    defaults = RuleEngine().rules
    optional = RuleEngine(Path(settings.RULES_DIR).parent / 'experiments').rules
    rules = {str(rule['id']): json.loads(json.dumps(rule, default=str)) for rule in defaults}
    for rule in optional:
        rules.setdefault(str(rule['id']), json.loads(json.dumps(rule, default=str)))
    return rules, sorted({str(rule['id']) for rule in defaults})


def make_snapshot(profile_id, name, description, native_sources, wazuh_min_level, rules):
    detector = {
        'engine_version': ENGINE_VERSION,
        'native_sources': sorted(set(native_sources)),
        'wazuh_min_level': wazuh_min_level,
        'sigma_rules': sorted(copy.deepcopy(rules), key=lambda rule: str(rule['id'])),
    }
    return {**detector, 'profile_id': profile_id, 'name': name,
            'description': description, 'fingerprint': fingerprint(detector)}


def presets(catalog=None, default_ids=None):
    if catalog is None:
        catalog, default_ids = rule_catalog()
    defaults = [catalog[key] for key in default_ids]
    dns = catalog.get('twintrace-dns-fixture-v1')
    return [
        make_snapshot('baseline', 'Baseline', 'Current default rules and native source alerts, pinned when a run starts.', NATIVE_SOURCES, 3, defaults),
        make_snapshot('dns-coverage', 'DNS fixture coverage', 'Baseline plus an explicit rule for the synthetic encoded DNS fixture. This is a teaching signature, not a production detector.', NATIVE_SOURCES, 3, defaults + ([dns] if dns else [])),
        make_snapshot('high-threshold', 'Higher Wazuh threshold', 'Accept Wazuh native alerts at level 12 or above. Study noise reduction and missed lower-level alerts together.', NATIVE_SOURCES, 12, defaults),
    ]


def summarize_config(snapshot):
    if not snapshot:
        return None
    return {key: snapshot[key] for key in ['profile_id', 'name', 'description', 'fingerprint', 'engine_version', 'native_sources', 'wazuh_min_level']} | {
        'rule_ids': [str(rule['id']) for rule in snapshot['sigma_rules']],
        'pinned': True,
    }


def profile_record(profile):
    return {**summarize_config(profile.snapshot), 'builtin': False,
            'created_at': profile.created_at.isoformat(), 'snapshot': profile.snapshot}


def configuration_catalog(db):
    catalog, default_ids = rule_catalog()
    builtins = [{**summarize_config(item), 'builtin': True, 'created_at': None, 'snapshot': item} for item in presets(catalog, default_ids)]
    saved = [profile_record(profile) for profile in db.query(DetectionProfile).order_by(DetectionProfile.created_at.desc()).all()]
    return {
        'profiles': builtins + saved,
        'rules': [{'id': key, 'title': rule.get('title', key), 'level': rule.get('level', 'medium'),
                   'default_enabled': key in default_ids, 'definition': rule,
                   'fingerprint': fingerprint(rule)} for key, rule in catalog.items()],
        'native_sources': NATIVE_SOURCES,
        'description': 'Saved configurations are immutable. Every new run copies its exact rule bodies and native-alert settings; external ingest uses the global defaults.',
    }


def resolve_config(db, profile_id='baseline'):
    for preset in presets():
        if preset['profile_id'] == profile_id:
            return preset
    try:
        profile = db.get(DetectionProfile, uuid.UUID(profile_id))
    except (ValueError, TypeError):
        profile = None
    if profile is None:
        raise ValueError('Detection configuration not found')
    return copy.deepcopy(profile.snapshot)


def save_profile(db, name, description, native_sources, wazuh_min_level, rule_ids, user_id):
    catalog, _ = rule_catalog()
    unknown = set(rule_ids) - catalog.keys()
    if unknown:
        raise ValueError('Unknown rule IDs: ' + ', '.join(sorted(unknown)))
    profile_id = uuid.uuid4()
    snapshot = make_snapshot(str(profile_id), name, description, native_sources,
                             wazuh_min_level, [catalog[key] for key in sorted(set(rule_ids))])
    profile = DetectionProfile(profile_id=profile_id, name=name, description=description,
                               created_by=user_id, snapshot=snapshot)
    db.add(profile)
    db.flush()
    return profile
