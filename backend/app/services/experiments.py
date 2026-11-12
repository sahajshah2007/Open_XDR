"""Replay fixtures through the real durable pipeline, then evaluate their evidence."""
import copy
import statistics
import uuid
from datetime import datetime, timezone
from sqlalchemy import func, select
from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.experiment import ExperimentRun, ExperimentEvent, ExperimentTrace, EventAlert
from app.models.event import Event
from app.models.alert import Alert
from app.models.host import Host
from app.models.incident import Incident
from app.models.pipeline import PipelineJob, ResponseAction
from app.models.user import User
from app.schemas.event import RawIngestEvent
from app.services.scenarios import build_scenario, TECHNIQUES
from app.services.parsers.common import utc_timestamp
from app.services.response_planning import propose_actions, simulate_proposal
from acdt.response.executor import ResponseExecutor
from app.services.detection_profiles import resolve_config, summarize_config


def trace(db,run_id,key,stage,message,payload=None,event_id=None):
    if db.query(ExperimentTrace).filter_by(run_id=run_id,trace_key=key).first():
        return
    ordinal=(db.query(func.max(ExperimentTrace.ordinal)).filter_by(run_id=run_id).scalar() or 0)+1
    db.add(ExperimentTrace(run_id=run_id,trace_key=key,ordinal=ordinal,stage=stage,message=message,payload=payload or {},event_id=event_id))
    db.flush()


def create_experiment(db,scenario_id,seed,name,user_id,*,detection_config=None,replay_of=None,comparison_group=None):
    from app.api.ingest import persist_event
    run_id=uuid.uuid4()
    start=datetime.now(timezone.utc)
    snapshot,topology,steps=build_scenario(scenario_id,seed,run_id,start)
    snapshot['detection_config'] = copy.deepcopy(detection_config if detection_config is not None else resolve_config(db))
    if replay_of:
        snapshot['replay_of'] = str(replay_of)
    if comparison_group:
        snapshot['comparison_group'] = str(comparison_group)
    run=ExperimentRun(run_id=run_id,scenario_id=scenario_id,name=name or snapshot['title'],seed=seed,created_by=user_id,snapshot=snapshot,topology=topology,status='queued')
    db.add(run);db.flush()
    for position,step in enumerate(steps):
        event_id=uuid.uuid5(run_id,f'event:{position}')
        stored=persist_event(db,RawIngestEvent(source=step['source'],data=step['data']),event_id)
        if stored.host_id:
            asset=db.get(Host,stored.host_id)
            node=next((node for node in topology['nodes'] if node['name']==asset.host_name),None)
            if node: asset.criticality=node['criticality']
        db.add(ExperimentEvent(event_id=event_id,run_id=run_id,position=position,label=step['label'],expected_positive=step['expected_positive'],expected_techniques=step['expected_techniques']))
        trace(db,run_id,f'{position}:source','source',step['label'],{'source':step['source'],'raw':stored.raw},event_id)
        trace(db,run_id,f'{position}:normalize','normalize','Normalized into the shared event schema',{'normalized':stored.normalized},event_id)
        trace(db,run_id,f'{position}:queue','queue','Event and processing intent stored; dispatch scheduled through Redis/Celery',{'event_id':str(event_id),'delivery':'durable outbox + broker','detection_configuration':summarize_config(snapshot['detection_config'])},event_id)
    db.flush()
    return run


def dispatch_experiment(db,run_id):
    from app.services.detection import evaluate_and_alert
    for event in db.query(ExperimentEvent).filter_by(run_id=run_id).order_by(ExperimentEvent.position):
        try:
            evaluate_and_alert.apply_async(args=[str(event.event_id)],retry=False)
        except Exception:
            # The existing recovery scheduler dispatches durable pending jobs.
            pass
    try:
        finalize_experiment.apply_async(args=[str(run_id)],retry=False)
    except Exception:
        pass


def event_evidence(db,run_id):
    rows=[]
    for expected in db.query(ExperimentEvent).filter_by(run_id=run_id).order_by(ExperimentEvent.position):
        event=db.get(Event,expected.event_id)
        job=db.get(PipelineJob,expected.event_id)
        alerts=db.query(Alert).join(EventAlert,EventAlert.alert_id==Alert.alert_id).filter(EventAlert.event_id==expected.event_id).all()
        observed=sorted({alert.mitre_technique for alert in alerts if alert.mitre_technique})
        actual=bool(alerts)
        classification=('tp' if actual else 'fn') if expected.expected_positive else ('fp' if actual else 'tn')
        latency=None
        if actual and job.processed_at:
            latency=max(0,(utc_timestamp(job.processed_at)-utc_timestamp(job.created_at)).total_seconds()*1000)
        rows.append({'event_id':str(event.event_id),'position':expected.position,'label':expected.label,'source':event.source,
                     'expected_positive':expected.expected_positive,'expected_techniques':expected.expected_techniques,
                     'observed_techniques':observed,'classification':classification,'status':job.status,'latency_ms':round(latency,3) if latency is not None else None,
                     'alerts':[{'alert_id':str(alert.alert_id),'rule_id':alert.rule_id,'rule_name':alert.rule_name,'severity':alert.severity,'technique':alert.mitre_technique,'incident_id':str(alert.incident_id)} for alert in alerts],
                     'raw':event.raw,'normalized':event.normalized,'error':job.error})
    return rows


def evaluate_evidence(rows):
    counts={key:sum(row['classification']==key for row in rows) for key in ['tp','fp','fn','tn']}
    tp,fp,fn,tn=(counts[key] for key in ['tp','fp','fn','tn'])
    precision=tp/(tp+fp) if tp+fp else None
    recall=tp/(tp+fn) if tp+fn else None
    f1=2*precision*recall/(precision+recall) if precision is not None and recall is not None and precision+recall else (0.0 if precision is not None and recall is not None else None)
    expected=set(technique for row in rows for technique in row['expected_techniques'])
    observed=set(technique for row in rows for technique in row['observed_techniques'])
    coverage=[{'technique':key,**TECHNIQUES.get(key,{'name':key,'tactic':'Unmapped','url':''}),
               'expected':key in expected,'observed':key in observed,
               'status':'detected' if key in expected and key in observed else 'missed' if key in expected else 'unexpected'} for key in sorted(expected|observed)]
    latencies=[row['latency_ms'] for row in rows if row['classification']=='tp' and row['latency_ms'] is not None]
    return {**counts,'events':len(rows),'precision':precision,'recall':recall,'f1':f1,'accuracy':(tp+tn)/len(rows) if rows else None,
            'mean_detection_ms':round(statistics.mean(latencies),3) if latencies else None,'coverage':coverage,
            'coverage_ratio':len(expected&observed)/len(expected) if expected else None,
            'methodology':'Event-level classification: expected alert vs any actual alert linked to that event. ATT&CK coverage is an exact-ID comparison, evaluated separately. Latency measures durable ingestion to processing completion for true positives; virtual fixture timestamps are not used. Null means no applicable denominator. These are synthetic-fixture results, not production efficacy.'}


def apply_model_actions(topology,actions):
    world=copy.deepcopy(topology)
    checks=[]
    parser=ResponseExecutor()
    for action in actions:
        verb,params=parser._parse(action.action)
        target=params.get('host') or params.get('user') or params.get('container') or params.get('node')
        node=next((node for node in world['nodes'] if node['name']==target),None)
        passed=False
        if action.status=='simulated' and node:
            if verb=='IsolateHost':
                node['state']='isolated'
                for edge in world['edges']:
                    if node['id'] in [edge['source'],edge['target']]: edge['blocked']=True
                passed=node['state']=='isolated'
            elif verb=='BlockPort':
                port=int(params['port'])
                node['blocked_ports']=sorted(set(node.get('blocked_ports',[])+[port]))
                for edge in world['edges']:
                    if node['id'] in [edge['source'],edge['target']] and edge['port']==port: edge['blocked']=True
                passed=port in node['blocked_ports']
            elif verb=='RevokeCredentials':
                node['state']='revoked';passed=node['state']=='revoked'
        checks.append({'action':action.action,'target':target,'passed':passed,'scope':'simulation model only'})
    return world,{'checks':checks,'passed':sum(check['passed'] for check in checks),'total':len(checks),
                  'simulated_containment':bool(checks) and all(check['passed'] for check in checks),'real_containment_performed':False,
                  'description':'State assertions against the run-local model. No firewall, host, container, or identity provider was changed.'}


@celery_app.task(name='experiments.finalize_run',acks_late=True)
def finalize_experiment(run_id):
    run_id=uuid.UUID(str(run_id))
    with SessionLocal.begin() as db:
        run=db.get(ExperimentRun,run_id,with_for_update=True)
        if run is None or run.status=='completed': return
        rows=event_evidence(db,run_id)
        run.status='running'
        for row in rows:
            if row['status']=='processed':
                trace(db,run_id,f"{row['position']}:detect",'detect',f"{len(row['alerts'])} actual alert(s) recorded",{'alerts':row['alerts']},uuid.UUID(row['event_id']))
                trace(db,run_id,f"{row['position']}:correlate",'correlate','Linked detections to run-isolated investigations' if row['alerts'] else 'No alert: event retained as telemetry',{'incident_ids':sorted({alert['incident_id'] for alert in row['alerts']})},uuid.UUID(row['event_id']))
        failed=[row for row in rows if row['status']=='failed' and db.get(PipelineJob,uuid.UUID(row['event_id'])).attempts>=settings.PIPELINE_MAX_ATTEMPTS]
        if failed:
            run.status='failed';run.error='One or more events exhausted processing retries.'
            trace(db,run_id,'processing-failure','error',run.error,{'events':[row['event_id'] for row in failed]})
            return
        if any(row['status']!='processed' for row in rows): return
        incident_ids={uuid.UUID(alert['incident_id']) for row in rows for alert in row['alerts']}
        actor=db.get(User,run.created_by)
        actions=[]
        for incident_id in incident_ids:
            proposals=propose_actions(db,db.get(Incident,incident_id),run.created_by,run.snapshot['identity'])
            for action in proposals:
                simulate_proposal(action,actor.username if actor else 'lab-runner')
            actions.extend(proposals)
        db.flush()
        run.topology,run.verification=apply_model_actions(run.topology,actions)
        trace(db,run_id,'twin','twin','Updated the run-local digital twin model',{'topology':run.topology})
        trace(db,run_id,'policy','policy',f'{len(actions)} simulated response action(s)',{'actions':[action.action for action in actions]})
        trace(db,run_id,'verify','verify','Verified model state; no real containment performed',run.verification)
        run.metrics=evaluate_evidence(rows)
        trace(db,run_id,'evaluation','evaluate','Compared observed evidence with independent fixture labels',{'metrics':run.metrics})
        run.status='completed';run.error=None;run.completed_at=datetime.now(timezone.utc)


@celery_app.task(name='experiments.finalize_pending')
def finalize_pending():
    with SessionLocal() as db:
        for run in db.query(ExperimentRun).filter(ExperimentRun.status.in_(['queued','running'])).limit(50):
            finalize_experiment.apply_async(args=[str(run.run_id)],retry=False)


def run_summary(db,run):
    total=db.query(ExperimentEvent).filter_by(run_id=run.run_id).count()
    processed=db.query(ExperimentEvent).join(PipelineJob,PipelineJob.event_id==ExperimentEvent.event_id).filter(ExperimentEvent.run_id==run.run_id,PipelineJob.status=='processed').count()
    return {'run_id':str(run.run_id),'scenario_id':run.scenario_id,'name':run.name,'seed':run.seed,'status':run.status,
            'created_at':run.created_at.isoformat(),'completed_at':run.completed_at.isoformat() if run.completed_at else None,
            'events_total':total,'events_processed':processed,'metrics':run.metrics,'error':run.error,
            'detection_config':summarize_config(run.snapshot.get('detection_config'))}


def run_detail(db,run):
    rows=event_evidence(db,run.run_id)
    traces=db.query(ExperimentTrace).filter_by(run_id=run.run_id).order_by(ExperimentTrace.ordinal).all()
    return {**run_summary(db,run),'snapshot':run.snapshot,'topology':run.topology,'verification':run.verification,
            'events':rows,'traces':[{'trace_id':str(item.trace_id),'event_id':str(item.event_id) if item.event_id else None,'ordinal':item.ordinal,'stage':item.stage,'message':item.message,'data':item.payload,'recorded_at':item.recorded_at.isoformat()} for item in traces],
            'simulation_only':True,'reproducibility':'Seed fixes logical patterns and ordering. Run IDs, asset names, and wall-clock timestamps are isolated for each replay.'}
