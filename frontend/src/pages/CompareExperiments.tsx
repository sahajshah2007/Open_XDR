import {useEffect,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {isAxiosError} from 'axios';
import {ArrowLeftRight,ArrowRight,Download,FlaskConical,Play} from 'lucide-react';
import {getRuns,getScenarios} from '../services/experiments';
import type {RunSummary,Scenario} from '../services/experiments';
import {getConfigurations,startComparison,getComparison,downloadComparison} from '../services/comparison';
import type {Comparison,ConfigurationCatalog,DetectionProfile} from '../services/comparison';
import ConfigurationEditor from '../components/ConfigurationEditor';

const metrics=[
  {key:'precision',label:'Precision',ratio:true,lower:false},
  {key:'recall',label:'Recall',ratio:true,lower:false},
  {key:'f1',label:'F1',ratio:true,lower:false},
  {key:'fp',label:'False positives',ratio:false,lower:true},
  {key:'fn',label:'False negatives',ratio:false,lower:true},
  {key:'mean_detection_ms',label:'Mean processing latency',ratio:false,lower:true},
];
function format(value:number|null|undefined,ratio=false){return value==null?'N/A':ratio?`${(value*100).toFixed(1)}%`:value.toLocaleString(undefined,{maximumFractionDigits:2});}
function delta(value:number|null|undefined,ratio=false,latency=false){return value==null?'N/A':`${value>0?'+':''}${(value*(ratio?100:1)).toLocaleString(undefined,{maximumFractionDigits:2})}${ratio?' pp':latency?' ms':''}`;}

export default function CompareExperiments(){
  const [params,setParams]=useSearchParams();
  const baselineId=params.get('baseline')||'',candidateId=params.get('candidate')||'';
  const [runs,setRuns]=useState<RunSummary[]>([]);
  const [scenarios,setScenarios]=useState<Scenario[]>([]);
  const [catalog,setCatalog]=useState<ConfigurationCatalog|null>(null);
  const [scenario,setScenario]=useState('dns-detection-gap');
  const [seed,setSeed]=useState(42);
  const [profileA,setProfileA]=useState('baseline');
  const [profileB,setProfileB]=useState('dns-coverage');
  const [comparison,setComparison]=useState<Comparison|null>(null);
  const [tab,setTab]=useState('results');
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const [waiting,setWaiting]=useState(false);
  const [changedOnly,setChangedOnly]=useState(false);
  const detail=comparison?.baseline.run_id===baselineId&&comparison?.candidate.run_id===candidateId?comparison:null;
  useEffect(()=>{
    let active=true;
    Promise.all([getRuns(100),getScenarios(),getConfigurations()]).then(([history,items,configs])=>{if(active){setRuns(history);setScenarios(items);setCatalog(configs);}}).catch(()=>{if(active)setError('The comparison workspace could not be loaded.');});
    return()=>{active=false;};
  },[]);
  useEffect(()=>{
    if(!baselineId||!candidateId||baselineId===candidateId)return;
    let active=true;let timer:number|undefined;
    async function refresh(){
      try{
        const result=await getComparison(baselineId,candidateId);
        if(active){setComparison(result);setWaiting(false);setError('');getRuns(100).then(history=>{if(active)setRuns(history);}).catch(()=>{});}
      }catch(reason){
        if(!active)return;
        if(isAxiosError(reason)&&reason.response?.status===409){
          if(reason.response.data?.detail?.state==='failed'){setWaiting(false);setError(reason.response.data.detail.message);}
          else{setWaiting(true);setError('');timer=window.setTimeout(refresh,1600);}
        }
        else{setWaiting(false);setError('The selected runs could not be compared. Check that both saved runs exist.');}
      }
    }
    void refresh();return()=>{active=false;window.clearTimeout(timer);};
  },[baselineId,candidateId]);
  async function launch(){
    setBusy(true);setError('');
    try{
      const pair=await startComparison(scenario,seed,profileA,profileB);
      setRuns(previous=>[pair.candidate,pair.baseline,...previous]);setWaiting(true);setTab('results');
      setParams({baseline:pair.baseline.run_id,candidate:pair.candidate.run_id});
    }catch{setError('The A/B experiment could not start. Administrator access and two free experiment slots are required.');}
    finally{setBusy(false);}
  }
  function selectRun(side:'baseline'|'candidate',id:string){setError('');setWaiting(false);setParams(current=>{const next=new URLSearchParams(current);if(id)next.set(side,id);else next.delete(side);return next;});}
  async function download(format:'html'|'json'){
    try{await downloadComparison(baselineId,candidateId,format);}catch{setError('The comparison report could not be downloaded.');}
  }
  function saved(profile:DetectionProfile){setCatalog(previous=>previous?{...previous,profiles:[...previous.profiles,profile]}:previous);setProfileB(profile.profile_id);}
  const selectedRuns=runs.filter(run=>run.status==='completed'||run.run_id===baselineId||run.run_id===candidateId);
  const eventRows=detail?.event_changes.filter(row=>!changedOnly||row.changed)||[];
  const peak=detail?Math.max(1,...(['tp','fp','fn','tn'] as const).flatMap(key=>[detail.baseline.metrics[key],detail.candidate.metrics[key]])):1;
  return <div>
    <div className="page-intro"><div><p className="eyebrow">EXPERIMENT COMPARISON / DETECTION ENGINEERING</p><h1>Measure what changed.</h1><p>Replay the same synthetic scenario with two detection configurations. Inspect gains, regressions, and the evidence behind each difference.</p></div><Link to="/experiments" className="lab-button secondary"><FlaskConical size={13}/>Single experiment</Link></div>
    {error&&<p role="alert" className="text-danger text-xs mb-5">{error}</p>}
    <section className="glass-panel panel-padding mb-5"><div className="section-heading"><h2>Run an A/B experiment</h2><span className="simulation-pill">SAME FIXTURE · TWO CONFIGURATIONS</span></div>
      <form onSubmit={event=>{event.preventDefault();void launch();}}>
        <div className="compare-launch-grid"><label className="lab-field-label">Scenario<select aria-label="Comparison scenario" className="lab-input mt-2" value={scenario} onChange={event=>setScenario(event.target.value)}>{scenarios.map(item=><option key={item.id} value={item.id}>{item.title}</option>)}</select></label><label className="lab-field-label">Seed<input aria-label="Comparison seed" className="lab-input mt-2" type="number" min="0" max="2147483647" required value={seed} onChange={event=>setSeed(Number(event.target.value))}/></label><label className="lab-field-label">A / Baseline configuration<select aria-label="Baseline configuration" className="lab-input mt-2" value={profileA} onChange={event=>setProfileA(event.target.value)}>{catalog?.profiles.map(profile=><option key={profile.profile_id} value={profile.profile_id}>{profile.name}</option>)}</select></label><label className="lab-field-label">B / Candidate configuration<select aria-label="Candidate configuration" className="lab-input mt-2" value={profileB} onChange={event=>setProfileB(event.target.value)}>{catalog?.profiles.map(profile=><option key={profile.profile_id} value={profile.profile_id}>{profile.name}</option>)}</select></label></div>
        <div className="compare-launch-footer"><p className="notebook-prose">Try DNS fixture coverage to close a known miss. Then try the higher Wazuh threshold on noisy sensor and SSH scenarios to expose its tradeoff.</p><button className="lab-button" disabled={busy||!catalog||!Number.isInteger(seed)||seed<0||seed>2147483647}><Play size={13}/>{busy?'Creating two runs…':'Run A/B experiment'}</button></div>
      </form>
    </section>
    <section className="glass-panel panel-padding mb-5"><div className="section-heading"><h2>Compare saved runs</h2><ArrowLeftRight size={16} className="text-primary"/></div><div className="comparison-selectors">{([['baseline','A / Baseline run',baselineId],['candidate','B / Candidate run',candidateId]] as const).map(([side,label,id])=><label key={side} className="lab-field-label">{label}<select aria-label={label} className="lab-input mt-2" value={id} onChange={event=>selectRun(side,event.target.value)}><option value="">Choose a saved run</option>{selectedRuns.map(run=><option key={run.run_id} value={run.run_id}>{run.name} · seed {run.seed} · {run.run_id.slice(0,8)}{run.status==='completed'?'':` · ${run.status}`}</option>)}</select></label>)}</div>
      {baselineId&&candidateId&&baselineId===candidateId&&<p role="alert" className="text-warning text-xs mt-4">Choose two different experiment runs.</p>}
      {waiting&&!detail&&baselineId!==candidateId&&<p role="status" className="comparison-waiting"><span className="status-dot"/>Both runs are processing through the lab workers. Their saved results will appear here automatically.</p>}
      {(!baselineId||!candidateId)&&<p className="experiment-note">Choose two saved runs, or launch an A/B experiment above. Matching scenario, seed, fixture version, and independent labels are required for event-level deltas.</p>}
      <div className="flex flex-wrap gap-5 mt-4">{baselineId&&<Link className="text-link" to={`/experiments?run=${baselineId}`}>Open baseline run <ArrowRight size={12}/></Link>}{candidateId&&<Link className="text-link" to={`/experiments?run=${candidateId}`}>Open candidate run <ArrowRight size={12}/></Link>}</div>
    </section>
    {detail&&<>
      <div className={`comparison-verdict ${detail.comparable?'matched':'mismatched'}`}><div><p className="eyebrow">{detail.comparable?'FIXTURES MATCH':'FIXTURES DO NOT MATCH'}</p><h2>{detail.comparable?`${detail.summary.improved} improved · ${detail.summary.regressed} regressed`:'Select matching runs to measure a change.'}</h2><p>{detail.comparable?`${detail.summary.changed} event(s) changed classification, rule matches, or technique attribution.`:detail.reasons.join(' ')}</p></div><div className="flex flex-wrap gap-2"><button onClick={()=>download('html')} className="lab-button secondary"><Download size={12}/>Comparison HTML</button><button onClick={()=>download('json')} className="lab-button secondary"><Download size={12}/>Comparison JSON</button></div></div>
      {detail.warnings.map(warning=><p className="comparison-warning" key={warning}>{warning}</p>)}
      <div className="comparison-run-cards">{([['A / BASELINE',detail.baseline],['B / CANDIDATE',detail.candidate]] as const).map(([label,run])=><section key={label} className="glass-panel p-5"><p className="eyebrow mb-3">{label}</p><h2 className="text-sm mb-3 break-words">{run.name}</h2><p className="mono text-[10px] text-textMuted">{run.detection_config?.name||'Legacy / settings not captured'} · Seed {run.seed}</p><p className="config-fingerprint">{run.detection_config?`SHA256 ${run.detection_config.fingerprint.slice(0,16)}…`:'No configuration fingerprint available'}</p><Link to={`/experiments?run=${run.run_id}`} className="text-link mt-4">Inspect saved evidence <ArrowRight size={12}/></Link></section>)}</div>
      <div className="experiment-tabs" role="tablist" aria-label="Comparison views">{[['results','Results'],['events','Event changes'],['coverage','ATT&CK changes'],['models','Model outcomes'],['config','Configuration']].map(([id,label])=><button key={id} role="tab" aria-selected={tab===id} onClick={()=>setTab(id)}>{label}</button>)}</div>
      {tab==='results'&&<section className="glass-panel panel-padding mb-5"><div className="section-heading"><h2>Candidate minus baseline</h2><span className="eyebrow">SYNTHETIC FIXTURE RESULTS</span></div>{detail.comparable?<><div className="comparison-metrics">{metrics.map(metric=>{const change=detail.metric_deltas[metric.key];const a=detail.baseline.metrics[metric.key as keyof typeof detail.baseline.metrics] as number|null;const b=detail.candidate.metrics[metric.key as keyof typeof detail.candidate.metrics] as number|null;const isLatency=metric.key==='mean_detection_ms';const tone=change==null||change===0||isLatency?'neutral':(metric.lower?change<0:change>0)?'improved':'regressed';return <div key={metric.key} className={`comparison-metric ${tone}`}><span>{metric.label}</span><strong>{delta(change,metric.ratio,isLatency)}</strong><small>{format(a,metric.ratio)} → {format(b,metric.ratio)}{isLatency?' ms':''}</small></div>;})}</div><div className="comparison-chart" role="img" aria-label="True positives, false positives, false negatives and true negatives for baseline and candidate"><div className="comparison-chart-legend"><span className="baseline">A / Baseline</span><span className="candidate">B / Candidate</span></div>{(['tp','fp','fn','tn'] as const).map(key=><div className="comparison-chart-row" key={key}><span>{key.toUpperCase()}</span><div>{(['baseline','candidate'] as const).map(side=><div key={side} className={`comparison-bar ${side}`}><span style={{width:`${detail[side].metrics[key]/peak*100}%`}}/><b>{detail[side].metrics[key]}</b></div>)}</div></div>)}</div></>:<p className="empty-panel">Metric deltas are withheld because these fixtures differ. You can inspect each saved run individually.</p>}<p className="experiment-note">{detail.methodology} Percentage-point changes use “pp”. N/A indicates an undefined denominator; a missing baseline precision is not zero.</p></section>}
      {tab==='events'&&<section className="glass-panel panel-padding mb-5"><div className="section-heading"><h2>Follow each changed observation</h2><label className="comparison-filter"><input type="checkbox" checked={changedOnly} onChange={event=>setChangedOnly(event.target.checked)}/>Changed events only</label></div>{eventRows.map(row=><details className="comparison-event" key={row.position}><summary><span className={`comparison-outcome ${row.outcome}`}>{row.outcome}</span><span>{row.label}<small>{row.source} · {row.expected_positive?'Expected alert':'Expected benign'}</small></span><span className="comparison-classes"><b>{row.baseline_class.toUpperCase()}</b><ArrowRight size={12}/><b>{row.candidate_class.toUpperCase()}</b></span></summary><div className="comparison-event-rules"><div><p className="eyebrow">A / OBSERVED RULES</p><pre>{row.baseline_rules.join('\n')||'No event-linked alerts'}</pre></div><div><p className="eyebrow">B / OBSERVED RULES</p><pre>{row.candidate_rules.join('\n')||'No event-linked alerts'}</pre></div></div></details>)}{!eventRows.length&&<p className="empty-panel">No aligned events match this view.</p>}</section>}
      {tab==='coverage'&&<section className="glass-panel panel-padding mb-5"><div className="section-heading"><h2>ATT&CK attribution changes</h2><span className="eyebrow">EXACT-ID COMPARISON</span></div>{detail.coverage_changes.map(item=><div key={item.technique} className="comparison-coverage-row"><a href={item.url} target="_blank" rel="noreferrer"><span className="mono text-primary">{item.technique}</span><b>{item.name}</b></a><span>A: {item.baseline_status}</span><ArrowRight size={13}/><span>B: {item.candidate_status}</span></div>)}{!detail.coverage_changes.length&&<p className="empty-panel">No technique comparison is available for these runs.</p>}</section>}
      {tab==='models'&&<section className="glass-panel panel-padding mb-5"><div className="section-heading"><h2>Compare simulated model outcomes</h2><span className="simulation-pill">REAL CONTAINMENT: FALSE</span></div>{detail.model_changes.map(node=><div key={node.asset} className={`comparison-model-row ${node.changed?'changed':''}`}><b>{node.asset}</b><span>A: {node.baseline_state}{node.baseline_ports.length?` · blocked ${node.baseline_ports.join(', ')}`:''}</span><ArrowRight size={13}/><span>B: {node.candidate_state}{node.candidate_ports.length?` · blocked ${node.candidate_ports.join(', ')}`:''}</span></div>)}<p className="experiment-note">Assets align by their scenario role. Each run keeps its own asset identity. Model-state changes and assertion results are simulated; application code and response-policy versions are not controlled by this comparison.</p></section>}
      {tab==='config'&&<section className="glass-panel panel-padding mb-5"><div className="section-heading"><h2>Inspect the saved detector inputs</h2><span className="eyebrow">IMMUTABLE RUN SNAPSHOTS</span></div><div className="config-diff-summary"><p>Added rules: <b>{detail.configuration_changes.added_rules.join(', ')||'None'}</b></p><p>Removed rules: <b>{detail.configuration_changes.removed_rules.join(', ')||'None'}</b></p><p>Changed rule bodies: <b>{detail.configuration_changes.changed_rules.join(', ')||'None'}</b></p><p>Wazuh threshold change: <b>{detail.configuration_changes.wazuh_threshold_change==null?'Unknown':delta(detail.configuration_changes.wazuh_threshold_change)}</b></p><p>Native sources added: <b>{detail.configuration_changes.added_native_sources.join(', ')||'None'}</b> · Removed: <b>{detail.configuration_changes.removed_native_sources.join(', ')||'None'}</b></p></div><div className="comparison-event-rules">{(['baseline','candidate'] as const).map(side=><div key={side}><p className="eyebrow">{side==='baseline'?'A / BASELINE':'B / CANDIDATE'}</p><pre>{JSON.stringify(detail[side].configuration_snapshot,null,2)}</pre></div>)}</div></section>}
    </>}
    {catalog&&<ConfigurationEditor catalog={catalog} onSaved={saved}/>}
  </div>;
}
