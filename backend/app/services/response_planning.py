"""Shared transactional policy planning; every adapter remains simulation-only."""
from datetime import datetime, timezone
from acdt.policy_engine.engine import PolicyEngine
from acdt.response.executor import ResponseExecutor
from app.core.config import settings
from app.models.host import Host
from app.models.pipeline import ResponseAction


def propose_actions(db,incident,user_id,identity=''):
    host = db.get(Host,incident.host_id) if incident.host_id else None
    context = {'attack_techniques':incident.mitre_techniques or [], 'risk_score':incident.confidence/100,
               'host':host.host_name if host else '', 'target_host':host.host_name if host else '', 'user':identity}
    executor = ResponseExecutor()
    for decision in PolicyEngine(settings.POLICY_FILE).evaluate(context):
        for action in decision.actions:
            verb,params = executor._parse(action)
            required = {'IsolateHost':['host'],'BlockPort':['host','port'],'RevokeCredentials':['user'],'KillContainer':['container'],'CordonNode':['node']}.get(verb)
            if not required or any(not params.get(key) or '%' in params[key] for key in required):
                continue
            if not db.query(ResponseAction).filter_by(incident_id=incident.incident_id,policy_id=decision.policy_id,action=action).first():
                db.add(ResponseAction(incident_id=incident.incident_id,policy_id=decision.policy_id,
                                     action=action,autonomy=decision.autonomy,requested_by=user_id))
                db.flush()
    return db.query(ResponseAction).filter_by(incident_id=incident.incident_id).all()


def simulate_proposal(action,username):
    if action.status != 'proposed':
        return
    result = ResponseExecutor().perform(action.action)
    action.status = result.result
    action.result = {'action':result.action,'target':result.target,'details':result.details,
                     'simulated_by':username,'contained':False,'verification':'No real containment was performed'}
    action.executed_at = datetime.now(timezone.utc)
