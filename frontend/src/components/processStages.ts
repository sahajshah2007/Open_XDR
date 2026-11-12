import {Radio,Layers3,Database,Fingerprint,Files,GitBranch,ShieldCheck,CheckCheck,ChartNoAxesCombined} from 'lucide-react';

export const PROCESS_STAGES=[
  {id:'source',label:'Source logs',tech:'Wazuh / Falco / network',icon:Radio,description:'A synthetic or recorded source emits a JSON event.'},
  {id:'normalize',label:'Normalize',tech:'FastAPI + Pydantic',icon:Layers3,description:'Parsers convert timestamps, asset identity, IPs, and ATT&CK metadata into the common event schema.'},
  {id:'queue',label:'Store & queue',tech:'PostgreSQL → Redis',icon:Database,description:'The event and processing intent commit together. Redis delivers work to a Celery worker; the scheduler recovers pending jobs.'},
  {id:'detect',label:'Detect',tech:'Native alerts + Sigma',icon:Fingerprint,description:'The worker preserves source alerts and evaluates enabled rules. Ordinary connections are not automatically attacks.'},
  {id:'correlate',label:'Investigate',tech:'Run-isolated incidents',icon:Files,description:'Related alerts form a persistent investigation, with source evidence and ATT&CK techniques.'},
  {id:'twin',label:'Update twin',tech:'Local model / Neo4j',icon:GitBranch,description:'The experiment maintains a topology model. Recorded connectivity can also be projected into the digital twin.'},
  {id:'policy',label:'Simulate response',tech:'YAML policy decisions',icon:ShieldCheck,description:'Policies propose actions. Adapters record simulated outcomes and change only this run’s model state.'},
  {id:'verify',label:'Verify model',tech:'State assertions',icon:CheckCheck,description:'Assertions check simulated isolation, blocked ports, or revoked identities. Real containment remains false.'},
  {id:'evaluate',label:'Evaluate',tech:'Ground truth & coverage',icon:ChartNoAxesCombined,description:'Actual event-linked detections are compared with independent fixture labels to compute precision, recall, misses, and coverage.'},
];
