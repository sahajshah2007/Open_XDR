import { useEffect, useState } from 'react';
import { GitBranch, FlaskConical, Play, Search, ArrowRight, RotateCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { loadDefense, planDefense, simulateDefense, findAttackPaths } from '../services/defense';
import type { DefenseStatus, TwinSnapshot, DefenseAction, DefenseIncident, AttackPath } from '../services/defense';

export default function Defense() {
  const [status,setStatus] = useState<DefenseStatus | null>(null);
  const [twin,setTwin] = useState<TwinSnapshot | null>(null);
  const [actions,setActions] = useState<DefenseAction[]>([]);
  const [incidents,setIncidents] = useState<DefenseIncident[]>([]);
  const [selectedIncident,setSelectedIncident] = useState('');
  const [selectedHost,setSelectedHost] = useState('');
  const [paths,setPaths] = useState<AttackPath[] | null>(null);
  const [error,setError] = useState('');
  const [message,setMessage] = useState('');
  const [busy,setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    const refresh = () => loadDefense().then(data => {
      if (!active) return;
      setStatus(data.status);setTwin(data.twin);setActions(data.actions);setIncidents(data.incidents);setError('');
    }).catch(() => {if (active) setError('The simulation workspace could not be loaded.');});
    void refresh();const timer = window.setInterval(refresh,15000);
    return () => {active = false;window.clearInterval(timer);};
  },[]);
  const runPlan = async () => {
    if (!selectedIncident) return;
    setBusy(true);setMessage('');setError('');
    try {const proposed = await planDefense(selectedIncident);setActions((await loadDefense()).actions);setMessage(proposed.length ? `${proposed.length} simulated response proposal(s) available below.` : 'No policy matched with the available technique and asset information.');}
    catch {setError('The policy study could not be created. Administrator access is required.');}
    finally {setBusy(false);}
  };
  const runSimulation = async (id:string) => {
    setBusy(true);setError('');
    try {const result = await simulateDefense(id);setActions(previous => previous.map(action => action.action_id === id ? result : action));}
    catch {setError('The response simulation could not be recorded.');}
    finally {setBusy(false);}
  };
  const searchPaths = async () => {
    if (!selectedHost) return;
    setBusy(true);setError('');
    try {setPaths(await findAttackPaths(selectedHost));}
    catch {setError('The optional connectivity model is unavailable.');}
    finally {setBusy(false);}
  };
  const nodes = (twin?.nodes ?? []).slice(0,20);
  const positions = new Map(nodes.map((node,index) => {const angle = index*2*Math.PI/Math.max(nodes.length,1);return [node.id,{x:350+230*Math.cos(angle),y:150+105*Math.sin(angle)}];}));
  return <div>
    <div className="page-intro"><div><p className="eyebrow">EXPERIMENT / MODEL & RESPONSE</p><h1>Study the defense decision.</h1><p>Explore recorded connectivity, evaluate a policy, and inspect a simulated response. All effects stay inside the experiment record.</p></div><span className="simulation-pill"><FlaskConical size={12} />DRY-RUN ONLY</span></div>
    {error && <p role="alert" className="text-danger text-xs mb-5">{error}</p>}
    {!status && !error && <p className="text-textMuted text-xs mb-5">Loading the simulation workspace…</p>}
    <div className="defense-grid mb-5"><section className="glass-panel panel-padding"><div className="section-heading"><h2><GitBranch size={15} className="inline mr-2 text-primary" />Connectivity twin</h2><span className={`state-label ${twin?.enabled ? '' : 'optional'}`}>{twin?.available === false ? 'Unavailable' : twin?.enabled ? 'Enabled' : 'Optional module'}</span></div>
      {twin?.enabled && nodes.length > 0 ? <><div className="twin-canvas"><svg viewBox="0 0 700 300" className="w-full" role="img" aria-label="Recorded connectivity between lab assets">{twin.edges.map((edge,index) => {const from = positions.get(edge.source), to = positions.get(edge.target);return from && to ? <line key={index} x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="#879fb7" strokeOpacity=".35" /> : null;})}{nodes.map(node => {const point = positions.get(node.id)!;return <g key={node.id}><circle cx={point.x} cy={point.y} r="17" fill="#192738" stroke={(node.criticality ?? 0)>=8 ? '#e8b45b' : '#86a8c5'} /><circle cx={point.x} cy={point.y} r="4" fill={(node.criticality ?? 0)>=8 ? '#e8b45b' : '#86a8c5'} /><text x={point.x} y={point.y+34} textAnchor="middle" fill="#aebdd0" fontSize="10" fontFamily="monospace">{node.name.length>22 ? `${node.name.slice(0,19)}…` : node.name}</text></g>;})}</svg></div><p className="text-[9px] text-textMuted my-4">Up to 20 assets · Amber marks criticality 8–10 · Observed connections are not verified attack paths</p><div className="flex flex-wrap gap-3"><select aria-label="Starting lab asset" value={selectedHost} onChange={event => {setSelectedHost(event.target.value);setPaths(null);}} className="lab-input flex-1 min-w-40"><option value="">Choose a starting asset</option>{twin.nodes.map(node => <option key={node.id} value={node.name}>{node.name}</option>)}</select><button disabled={!selectedHost || busy} onClick={searchPaths} className="lab-button secondary"><Search size={12} />Explore paths</button></div>{paths && <div className="mt-4 space-y-2 text-xs">{paths.length ? paths.map((path,index) => <div key={index} className="p-3 bg-white/[.03] rounded-md font-mono text-textMuted text-[10px]">{path.nodes.join(' → ')} · {path.hops} hops</div>) : <p className="text-textMuted">No recorded path to a critical asset was found.</p>}</div>}</> : <div className="twin-empty"><div className="empty-twin-symbol"><GitBranch size={30} /></div><h3>{twin?.available === false ? 'The model is unavailable.' : 'Add a model to the experiment.'}</h3><p>{twin?.available === false ? 'Check the Neo4j service. Policy studies and recorded evidence remain available.' : 'The optional Neo4j module projects lab telemetry into a connectivity graph. Enable it when you are ready to explore relationships between assets.'}</p><Link to="/project" className="text-link mt-5">Read the system design <ArrowRight size={12} /></Link></div>}
      <p className="experiment-note">A digital twin here is an observational lab model. It does not scan networks or establish exploitability.</p></section>
      <section className="glass-panel panel-padding"><div className="section-heading"><h2>Policy study</h2><span className="eyebrow">PROPOSE → SIMULATE → REVIEW</span></div><p className="notebook-prose mb-5">Choose a recorded investigation to evaluate its techniques and priority against the lab policies.</p><label className="lab-field-label">Investigation<select aria-label="Investigation to study" value={selectedIncident} onChange={event => setSelectedIncident(event.target.value)} className="lab-input mt-2"><option value="">Choose a recorded investigation</option>{incidents.map(incident => <option key={incident.incident_id} value={incident.incident_id}>{incident.title}</option>)}</select></label><button disabled={!selectedIncident || busy} onClick={runPlan} className="lab-button mt-4"><RotateCw size={12} />Evaluate policies</button>{message && <p role="status" className="text-[11px] leading-relaxed text-primary mt-4">{message}</p>}<div className="mt-7 border-t border-white/5 pt-5"><p className="eyebrow text-textMuted mb-3">AVAILABLE LAB POLICIES</p>{status?.policies.map(policy => <div key={policy.id} className="py-3 border-b border-white/5 last:border-0"><p className="text-[11px] text-textMain">{policy.description}</p><p className="mono text-[8px] text-textMuted mt-2">{policy.id} <span className="text-slate-600">/</span> design intent: {policy.autonomy.replace('_',' ')}</p></div>)}</div><p className="experiment-note">Policy autonomy is metadata for the experiment. Every response is a simulation, including policies labeled “auto”.</p></section></div>
    <section className="glass-panel panel-padding"><div className="section-heading"><h2>Simulation journal</h2><span className="eyebrow">{actions.filter(action => action.status==='simulated').length} RECORDED DRY RUNS</span></div>{actions.length ? <div className="space-y-3">{actions.map(action => <div key={action.action_id} className="simulation-journal-entry"><span className="journal-icon"><FlaskConical size={16} /></span><div className="min-w-0 flex-1"><p className="mono text-[11px] text-textMain break-all">{action.action}</p><p className="mono text-[8px] text-textMuted mt-2">{action.policy_id} · {new Date(action.created_at).toLocaleString()}</p>{action.result && <p className="text-[10px] leading-relaxed text-textMuted mt-3">{action.result.details} · Containment was not performed.</p>}</div><span className={`state-label ${action.status === 'proposed' ? 'optional' : ''}`}>{action.status}</span>{action.status==='proposed' && <button disabled={busy} onClick={() => runSimulation(action.action_id)} className="lab-button secondary"><Play size={11} />Simulate</button>}</div>)}</div> : <div className="empty-panel"><FlaskConical size={25} className="mx-auto mb-3 text-primary/60" />Your simulation journal starts here.<br /><span className="text-[11px]">Evaluate an investigation, then simulate an available proposal.</span></div>}</section>
  </div>;
}
