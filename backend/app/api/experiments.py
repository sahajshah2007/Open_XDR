import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
from sqlalchemy.orm import Session
from app.api.auth import get_current_user, require_admin
from app.core.database import get_db
from app.models.experiment import ExperimentRun, ExperimentEvent
from app.models.pipeline import PipelineJob
from app.services.scenarios import SCENARIOS, TECHNIQUES, scenario_by_id
from app.services.experiments import create_experiment,dispatch_experiment,run_summary,run_detail
from app.services.experiment_reports import html_report,csv_report
from app.services.detection_profiles import configuration_catalog, save_profile, profile_record, resolve_config
from app.services.experiment_comparison import compare_runs
from app.services.comparison_reports import html_comparison

router=APIRouter(dependencies=[Depends(get_current_user)])


class CreateRun(BaseModel):
    scenario_id:str=Field(min_length=1,max_length=80)
    seed:int=Field(42,ge=0,le=2_147_483_647)
    name:str=Field('',max_length=120)
    profile_id:str=Field('baseline',min_length=1,max_length=80)
    replay_of:uuid.UUID|None=None


class CreateProfile(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    name:str=Field(min_length=1,max_length=120)
    description:str=Field('',max_length=500)
    native_sources:list[Literal['wazuh','suricata','falco','attacker']]=Field(default_factory=lambda:['wazuh','suricata','falco','attacker'],max_length=4)
    wazuh_min_level:int=Field(3,ge=0,le=15)
    rule_ids:list[str]=Field(default_factory=list,max_length=100)


class CreatePair(BaseModel):
    scenario_id:str=Field(min_length=1,max_length=80)
    seed:int=Field(42,ge=0,le=2_147_483_647)
    baseline_profile_id:str=Field('baseline',min_length=1,max_length=80)
    candidate_profile_id:str=Field('dns-coverage',min_length=1,max_length=80)


def find_run(db,run_id):
    run=db.get(ExperimentRun,run_id)
    if run is None: raise HTTPException(status_code=404,detail='Experiment run not found')
    return run


def config_or_422(db,profile_id):
    try:
        return resolve_config(db,profile_id)
    except ValueError as exc:
        raise HTTPException(status_code=422,detail=str(exc)) from exc


@router.get('/configurations')
def configurations(db:Session=Depends(get_db)):
    return configuration_catalog(db)


@router.post('/configurations',status_code=201)
def create_configuration(request:CreateProfile,db:Session=Depends(get_db),user=Depends(require_admin)):
    try:
        profile=save_profile(db,request.name,request.description,request.native_sources,request.wazuh_min_level,request.rule_ids,user.id)
    except ValueError as exc:
        raise HTTPException(status_code=422,detail=str(exc)) from exc
    db.commit();db.refresh(profile)
    return profile_record(profile)


@router.post('/compare/runs',status_code=202)
def start_pair(request:CreatePair,db:Session=Depends(get_db),user=Depends(require_admin)):
    if not scenario_by_id(request.scenario_id):
        raise HTTPException(status_code=422,detail='Unknown scenario')
    if db.query(ExperimentRun).filter(ExperimentRun.status.in_(['queued','running'])).count()>8:
        raise HTTPException(status_code=409,detail='Wait until two experiment slots are available')
    left=config_or_422(db,request.baseline_profile_id)
    right=config_or_422(db,request.candidate_profile_id)
    group=uuid.uuid4()
    title=scenario_by_id(request.scenario_id)['title']
    baseline=create_experiment(db,request.scenario_id,request.seed,f'A: {title} / {left["name"]}',user.id,detection_config=left,comparison_group=group)
    candidate=create_experiment(db,request.scenario_id,request.seed,f'B: {title} / {right["name"]}',user.id,detection_config=right,comparison_group=group)
    db.commit()
    for run in [baseline,candidate]:
        dispatch_experiment(db,run.run_id)
    return {'baseline':run_summary(db,baseline),'candidate':run_summary(db,candidate)}


def completed_comparison(db,baseline,candidate):
    if baseline==candidate:
        raise HTTPException(status_code=422,detail='Choose two different experiment runs')
    left,right=find_run(db,baseline),find_run(db,candidate)
    if left.status=='failed' or right.status=='failed':
        raise HTTPException(status_code=409,detail={'state':'failed','message':'A selected run failed processing. Open its saved evidence and retry failed processing before comparing.'})
    if left.status!='completed' or right.status!='completed':
        raise HTTPException(status_code=409,detail='Both experiment runs must complete before comparison')
    return compare_runs(db,left,right)


@router.get('/compare')
def comparison(baseline:uuid.UUID,candidate:uuid.UUID,db:Session=Depends(get_db)):
    return completed_comparison(db,baseline,candidate)


@router.get('/compare/report')
def comparison_report(baseline:uuid.UUID,candidate:uuid.UUID,format:str=Query('html',pattern='^(html|json)$'),db:Session=Depends(get_db)):
    detail=completed_comparison(db,baseline,candidate)
    content=html_comparison(detail) if format=='html' else json.dumps(detail,indent=2)
    return Response(content,media_type='text/html' if format=='html' else 'application/json',headers={'Content-Disposition':f'attachment; filename="TwinTrace-Comparison-{baseline}-{candidate}.{format}"'})


@router.get('/scenarios')
def scenarios():
    return {'scenarios':[dict(item,version=1) for item in SCENARIOS],'techniques':TECHNIQUES,'simulation_only':True}


@router.post('/runs',status_code=202)
def start_run(request:CreateRun,db:Session=Depends(get_db),user=Depends(require_admin)):
    if not scenario_by_id(request.scenario_id): raise HTTPException(status_code=422,detail='Unknown scenario')
    active=db.query(ExperimentRun).filter(ExperimentRun.status.in_(['queued','running'])).count()
    if active>=10: raise HTTPException(status_code=409,detail='Wait for existing experiments to finish before starting another run')
    if request.replay_of:
        previous=find_run(db,request.replay_of)
        if (previous.scenario_id,previous.seed,previous.snapshot['version'])!=(request.scenario_id,request.seed,scenario_by_id(request.scenario_id)['version']):
            raise HTTPException(status_code=422,detail='A replay must keep the original scenario, seed and fixture version')
        if not previous.snapshot.get('detection_config'):
            raise HTTPException(status_code=409,detail='This legacy run has no saved rules. Start a new run with an explicit configuration.')
        config=previous.snapshot['detection_config']
    else:
        config=config_or_422(db,request.profile_id)
    run=create_experiment(db,request.scenario_id,request.seed,request.name,user.id,detection_config=config,replay_of=request.replay_of)
    db.commit();db.refresh(run)
    dispatch_experiment(db,run.run_id)
    return run_summary(db,run)


@router.get('/runs')
def list_runs(db:Session=Depends(get_db),limit:int=Query(30,ge=1,le=100)):
    return [run_summary(db,run) for run in db.query(ExperimentRun).order_by(ExperimentRun.created_at.desc()).limit(limit)]


@router.get('/runs/{run_id}')
def get_run(run_id:uuid.UUID,db:Session=Depends(get_db)):
    return run_detail(db,find_run(db,run_id))


@router.post('/runs/{run_id}/retry')
def retry_run(run_id:uuid.UUID,db:Session=Depends(get_db),user=Depends(require_admin)):
    run=find_run(db,run_id)
    if run.status=='completed': return run_summary(db,run)
    for event in db.query(ExperimentEvent).filter_by(run_id=run_id):
        job=db.get(PipelineJob,event.event_id,with_for_update=True)
        if job.status=='failed': job.status='pending';job.attempts=0;job.error=None
    run.status='queued';run.error=None;db.commit()
    dispatch_experiment(db,run_id)
    return run_summary(db,run)


@router.get('/runs/{run_id}/report')
def report(run_id:uuid.UUID,format:str=Query('html',pattern='^(html|json|csv)$'),db:Session=Depends(get_db)):
    run=find_run(db,run_id)
    if run.status!='completed': raise HTTPException(status_code=409,detail='Wait for run completion before exporting an evaluation report')
    detail=run_detail(db,run)
    content=html_report(detail) if format=='html' else csv_report(detail) if format=='csv' else json.dumps(detail,indent=2)
    media={'html':'text/html','csv':'text/csv','json':'application/json'}[format]
    return Response(content,media_type=media,headers={'Content-Disposition':f'attachment; filename="TwinTrace-{run_id}.{format}"'})
