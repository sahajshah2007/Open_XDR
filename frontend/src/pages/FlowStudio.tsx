import {useEffect,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {ArrowRight,Workflow} from 'lucide-react';
import ProcessPlayer from '../components/ProcessPlayer';
import {PROCESS_STAGES} from '../components/processStages';
import {getRuns,getRun} from '../services/experiments';
import type {RunSummary,Trace} from '../services/experiments';

const sampleRaw={timestamp:'Illustrative source timestamp',rule:{id:'sample-ssh',level:8,description:'Failed SSH authentication',mitre:{id:['T1110']}},agent:{name:'web-lab'},data:{srcip:'198.51.100.42',dstip:'192.0.2.42'}};
const sample:Trace[]=PROCESS_STAGES.map((stage,index)=>({trace_id:`sample-${index}`,event_id:'example-not-stored',ordinal:index+1,stage:stage.id,message:stage.description,recorded_at:'Illustrative example',data:index===0?{source:'wazuh',raw:sampleRaw}:index===1?{source:'wazuh',host_name:'web-lab',src_ip:'198.51.100.42',dst_ip:'192.0.2.42',mitre_technique:'T1110',timestamp:'UTC normalized'}:index===2?{event_store:'PostgreSQL',processing_record:'pending',delivery:'Redis → Celery'}:index===3?{rule_id:'wazuh:sample-ssh',alert:'Source-declared authentication alert'}:index===4?{investigation:'Run-isolated SSH evidence',techniques:['T1110']}:index===5?{model:'web-lab ← client',state:'active'}:index===6?{policy:'ssh_bruteforce_lab',proposal:'BlockPort(host=web-lab, port=22)',effect:'simulation only'}:index===7?{model_port_22:'blocked',real_containment_performed:false}:{ground_truth:'Compare expected alert to event-linked observed alerts',metrics:'Computed only for an actual replay run'}}));

export default function FlowStudio(){
  const[params,setParams]=useSearchParams();const selected=params.get('run')||'';
  const[runs,setRuns]=useState<RunSummary[]>([]);const[traces,setTraces]=useState<Trace[]>(sample);const[error,setError]=useState('');
  useEffect(()=>{let active=true;getRuns().then(items=>{if(active)setRuns(items);}).catch(()=>{if(active)setError('Run history is unavailable. The guided example still works.');});return()=>{active=false;};},[]);
  useEffect(()=>{
    if(!selected)return;let active=true;
    const refresh=()=>getRun(selected).then(detail=>{if(active){setTraces(detail.traces);setError('');}}).catch(()=>{if(active)setError('Recorded traces could not be loaded.');});
    void refresh();const timer=window.setInterval(refresh,2000);return()=>{active=false;window.clearInterval(timer);};
  },[selected]);
  return <div><div className="page-intro"><div><p className="eyebrow">FLOW STUDIO / OBSERVE THE PROCESS</p><h1>Watch the evidence move.</h1><p>Follow a log from its source through normalization, storage, detection, correlation, model response, and evaluation.</p></div><Link to="/experiments" className="lab-button"><Workflow size={13}/>Run an experiment</Link></div>
    <div className="glass-panel p-4 mb-5 flex flex-wrap items-center gap-4"><label className="lab-field-label min-w-56 flex-1">Playback source<select aria-label="Flow playback source" className="lab-input mt-2" value={selected} onChange={event=>setParams(event.target.value?{run:event.target.value}:{})}><option value="">Guided example · illustrative, not stored</option>{runs.map(run=><option key={run.run_id} value={run.run_id}>{run.name} · {run.status}</option>)}</select></label><p className="text-[11px] text-textMuted max-w-md">{selected?'These frames come from the saved run journal. Playback speed does not change backend processing.':'Explore the mechanics with a sample log, then run a scenario to inspect actual recorded traces.'}</p></div>
    {error&&<p role="alert" className="text-warning text-xs mb-4">{error}</p>}<ProcessPlayer key={selected||'sample'} traces={selected?traces:sample} illustrative={!selected}/>
    <section className="glass-panel panel-padding mt-5"><div className="section-heading"><h2>What is actually happening?</h2><Link to="/guide" className="text-link">Open the full interview guide <ArrowRight size={12}/></Link></div><div className="flow-explanation-grid"><div><h3>Data is processed by the backend.</h3><p>Scenario fixtures use the same parsers, PostgreSQL records, Redis broker, Celery workers, rules, and incident correlation as imported lab evidence.</p></div><div><h3>Motion is an explanatory replay.</h3><p>The animation makes persisted stages visible. It is not a packet capture, a network probe, or an attack execution.</p></div><div><h3>Responses change a local model.</h3><p>Isolation, blocked ports, and revoked identities are modeled states. Verification asserts those states and always records real containment as false.</p></div></div></section>
  </div>;
}
