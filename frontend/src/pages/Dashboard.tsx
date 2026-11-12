import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ArrowUpRight, Database, Fingerprint, Files, FlaskConical, CircleHelp, GitBranch } from 'lucide-react';
import api, { getIncidents } from '../services/api';
import type { IncidentRecord } from '../services/types';
import LabPipeline from '../components/LabPipeline';

interface Overview {
  total_events: number; total_alerts: number; total_incidents: number; simulated_actions: number;
  active_incidents: number; critical_incidents: number; hosts: number; failed_events: number;
  chart: { date: string; incidents: number; critical: number }[];
}

function TwinArt() {
  return <svg viewBox="0 0 310 220" className="hero-twin-art" fill="none" aria-hidden="true">
    <path d="m150 22 100 57-100 57L50 79 150 22Z" stroke="#d7ad6e" strokeOpacity=".2" /><path d="m150 72 100 57-100 57-100-57 100-57Z" stroke="#d7ad6e" strokeOpacity=".2" /><path d="m150 22 0 50m100 7v50M50 79v50M150 136v50" stroke="#d7ad6e" strokeOpacity=".18" />
    <path d="m150 53 47 27-47 27-47-27 47-27Z" fill="#e8b45b0a" stroke="#e8b45b" strokeWidth="1.4" /><path d="m103 80 0 28 47 27 47-27V80m-47 27v28" stroke="#e8b45b" strokeOpacity=".6" />
    <path d="M50 129 22 145l0 25 42 24 42-24v-25L64 121l-14 8Zm14 17 42 24M64 146v48M22 145l42 25m186-41 38 22v25l-42 24-42-24v-25l42-24 4 2Zm-4 23v48m-42-49 42 25 42-25" stroke="#7a9fbc" strokeOpacity=".55" />
    <path d="m106 145 44-25 54 31" stroke="#e8b45b" strokeWidth="1.5" strokeDasharray="3 5" /><circle cx="150" cy="120" r="3" fill="#e8b45b" /><circle cx="106" cy="145" r="3" fill="#91b0c9" /><circle cx="204" cy="151" r="3" fill="#91b0c9" />
    <text x="145" y="84" fill="#e8b45b" fontSize="10" fontFamily="monospace">T</text><text x="35" y="214" fill="#6f879e" fontSize="7" fontFamily="monospace" letterSpacing="2">TRACE / MODEL / LEARN</text>
  </svg>;
}

const formatCount = (value: number | undefined) => value === undefined ? '—' : value.toLocaleString();

export default function Dashboard() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [incidents, setIncidents] = useState<IncidentRecord[]>([]);
  const [connected, setConnected] = useState(false);
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    let active = true;
    const refresh = () => Promise.all([api.get<Overview>('/defense/overview'), getIncidents()]).then(([{data},cases]) => {
      if (!active) return;
      setOverview(data); setIncidents(cases); setConnected(true); setLoaded(true);
    }).catch(() => { if (active) {setConnected(false); setLoaded(true);} });
    void refresh();
    const timer = window.setInterval(refresh, 15000);
    return () => {active = false; window.clearInterval(timer);};
  }, []);
  const metrics = [
    {label:'Telemetry events', value:overview?.total_events, icon:Database, note:'Recorded in the lab dataset'},
    {label:'Detection alerts', value:overview?.total_alerts, icon:Fingerprint, note:'Stored upstream & rule matches'},
    {label:'Investigations', value:overview?.total_incidents, icon:Files, note:'Correlated lab evidence'},
    {label:'Response simulations', value:overview?.simulated_actions, icon:FlaskConical, note:'Recorded dry-run outcomes'},
  ];
  const maxActivity = Math.max(1,...(overview?.chart.map(day => day.incidents) ?? []));
  const windowTotal = overview?.chart.reduce((sum,day) => sum + day.incidents,0) ?? 0;
  return <div>
    <div className="page-intro"><div><p className="eyebrow">RESEARCH WORKSPACE / OVERVIEW</p><h1>Inside the lab.</h1><p>Explore the evidence, reconstruct an attack chain, and inspect the decisions behind a simulated defense.</p></div><span className="lab-status"><span className={`status-dot ${connected ? '' : 'disconnected'}`} />{connected ? 'Lab dataset connected' : loaded ? 'Dataset connection unavailable' : 'Connecting to the lab…'}</span></div>
    <section className="overview-hero"><div className="overview-hero-content"><p className="eyebrow">TWINTRACE LAB · CYBER DEFENSE SIMULATION</p><h2>Every event leaves a trace.<br /><span>Follow the whole story.</span></h2><p>A hands-on experiment in telemetry correlation, digital twins, and policy-driven response. Built to make security decisions understandable.</p><div className="hero-actions"><Link to="/experiments" className="lab-button">New experiment <ArrowRight size={13} /></Link><Link to="/guide" className="lab-button secondary">Interview walkthrough <ArrowUpRight size={13} /></Link></div></div><TwinArt /></section>
    {!connected && loaded && <p role="alert" className="mb-5 text-xs text-warning">The API could not be reached. Any retained counts below are from the last successful refresh.</p>}
    <section className="overview-metrics" aria-label="Recorded lab dataset">{metrics.map(({label,value,icon:Icon,note}) => <div key={label} className="metric-cell"><div className="metric-top"><span>{label}</span><Icon size={15} /></div><div className="metric-value">{formatCount(value)}</div><p className="metric-foot">{note}</p></div>)}</section>
    <div className="overview-grid"><section className="glass-panel panel-padding"><div className="section-heading"><h2>From signal to simulated response</h2><span className="eyebrow">THE EXPERIMENT</span></div><LabPipeline /><div className="source-strip"><span className="eyebrow">SUPPORTED FORMATS</span>{['WAZUH','SURICATA','ZEEK','FALCO','LAB SIGNALS'].map(source => <span className="source-label" key={source}>{source}</span>)}</div></section>
      <section className="glass-panel panel-padding"><div className="section-heading"><h2>A three-step walkthrough</h2><CircleHelp size={15} className="text-textMuted" /></div><div className="check-list">{[
        {number:'01',title:'Inspect the evidence',copy:'Search source events and compare the original payload with normalized fields.',to:'/hunting'},
        {number:'02',title:'Reconstruct the chain',copy:'Review linked alerts, ATT&CK techniques, and the investigation timeline.',to:'/incidents'},
        {number:'03',title:'Study the response',copy:'Evaluate a policy and record its simulated outcome without taking real action.',to:'/defense'},
      ].map(step => <Link key={step.number} to={step.to} className="check-row"><span className="check-number">{step.number}</span><div><h3>{step.title} <ArrowUpRight size={11} className="inline ml-1 text-textMuted" /></h3><p>{step.copy}</p></div></Link>)}</div></section></div>
    <div className="overview-grid"><section className="glass-panel panel-padding"><div className="section-heading"><h2>Saved investigations</h2><Link to="/incidents" className="text-link">View all cases <ArrowRight size={12} /></Link></div><div className="overflow-x-auto"><table className="investigations-table"><thead><tr><th>INVESTIGATION</th><th className="optional-column">TECHNIQUE</th><th>PRIORITY</th><th className="optional-column">STATE</th></tr></thead><tbody>{incidents.slice(0,4).map(incident => <tr key={incident.incident_id}><td><Link to="/incidents" className="case-title">{incident.title}</Link><p className="case-meta">Last evidence · {new Date(incident.last_seen).toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'})}</p></td><td className="optional-column"><span className="case-technique">{incident.mitre_techniques?.[0] || 'Unmapped'}</span></td><td><span className={`badge badge-${incident.severity}`}>{incident.severity}</span></td><td className="optional-column"><span className="case-meta">{incident.status}</span></td></tr>)}</tbody></table>{incidents.length === 0 && <div className="empty-panel">{loaded ? 'No investigations in this dataset yet. Add recorded lab events to begin tracing a case.' : 'Loading recorded investigations…'}</div>}</div><p className="experiment-note">These counts describe the stored lab dataset. They are not measures of real-world detection accuracy or successful containment.</p></section>
      <section className="glass-panel panel-padding"><div className="section-heading"><h2>Recent observations</h2><span className="eyebrow">7 DAYS · UTC</span></div><p className="text-[28px] font-mono tracking-tight text-textMain">{overview ? windowTotal : '—'} <span className="text-[10px] font-sans text-textMuted tracking-normal">investigations opened</span></p><div className="flex items-end gap-2 h-[110px] mt-3" aria-label="Daily investigation counts">{overview?.chart.map(day => <div key={day.date} className="flex-1 text-center"><span className="block text-[8px] font-mono text-textMuted mb-2">{day.incidents}</span><div className="mx-auto rounded-t-sm bg-primary/30 border-t border-primary/50 w-full max-w-7" style={{height:Math.max(3,day.incidents/maxActivity*55)}} /><span className="block text-[8px] text-textMuted mt-2">{new Date(`${day.date}T12:00:00Z`).toLocaleDateString(undefined,{weekday:'short'})}</span></div>)}</div><p className="experiment-note">{windowTotal ? 'Based on the first-seen timestamps of recorded investigations.' : 'No activity recorded in this window. Earlier evidence is still available in saved investigations.'}</p><Link to="/project" className="text-link mt-4"><GitBranch size={12} />Explore the architecture & replay scenarios <ArrowUpRight size={11} /></Link></section></div>
  </div>;
}
