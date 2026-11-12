import { useEffect, useState } from 'react';
import { Files, ChevronDown, ChevronRight, Fingerprint, MessageSquare, Search, ArrowDown } from 'lucide-react';
import { getIncidents, getIncidentDetails, getUsers, updateIncident, addIncidentNote, getHosts } from '../services/api';
import type { IncidentRecord, HostRecord, UserRecord } from '../services/types';
import { useAuth } from '../context/auth';

export default function Incidents() {
  const [incidents,setIncidents] = useState<IncidentRecord[]>([]);
  const [hosts,setHosts] = useState<HostRecord[]>([]);
  const [users,setUsers] = useState<UserRecord[]>([]);
  const [expandedId,setExpandedId] = useState<string | null>(null);
  const [details,setDetails] = useState<IncidentRecord | null>(null);
  const [loading,setLoading] = useState(true);
  const [query,setQuery] = useState('');
  const [note,setNote] = useState('');
  const [error,setError] = useState('');
  const [busy,setBusy] = useState(false);
  const {token} = useAuth();
  useEffect(() => {
    let active = true;
    Promise.all([getIncidents(),getHosts(),getUsers()]).then(([cases,assets,people]) => {
      if (active) {setIncidents(cases);setHosts(assets);setUsers(people);setError('');}
    }).catch(() => {if (active) setError('The lab investigations could not be loaded.');}).finally(() => {if (active) setLoading(false);});
    const address = new URL(import.meta.env.VITE_API_URL || '/api/v1',window.location.origin);
    address.protocol = address.protocol === 'https:' ? 'wss:' : 'ws:';
    const socket = new WebSocket(`${address.toString().replace(/\/$/,'')}/ws/incidents?token=${encodeURIComponent(token || '')}`);
    socket.onmessage = event => {
      try {
        const payload: {type:string;data:IncidentRecord} = JSON.parse(event.data);
        if (!active || payload.type !== 'INCIDENT_UPDATE') return;
        const updated = payload.data;
        setIncidents(previous => (previous.some(item => item.incident_id === updated.incident_id)
          ? previous.map(item => item.incident_id === updated.incident_id ? {...item,...updated} : item)
          : [updated,...previous]).sort((a,b) => Date.parse(b.last_seen)-Date.parse(a.last_seen)));
        setDetails(current => current?.incident_id === updated.incident_id ? {...current,...updated} : current);
      } catch { /* A malformed notification must not clear recorded evidence. */ }
    };
    return () => {active = false;socket.close();};
  },[token]);
  const expand = async (id:string) => {
    if (expandedId === id) {setExpandedId(null);setDetails(null);return;}
    setExpandedId(id);setDetails(null);setNote('');
    try {setDetails(await getIncidentDetails(id));}
    catch {setError('The investigation details could not be loaded.');}
  };
  const merge = (updated:IncidentRecord) => {
    setIncidents(previous => previous.map(item => item.incident_id === updated.incident_id ? {...item,...updated} : item));
    setDetails(current => current?.incident_id === updated.incident_id ? {...current,...updated} : current);
  };
  const change = async (id:string,data:{status?:string;assignee_id?:string | null;host_id?:string | null}) => {
    setError('');
    try {merge(await updateIncident(id,data));}
    catch {setError('The investigation could not be updated.');}
  };
  const addNote = async (id:string) => {
    if (!note.trim()) return;
    setBusy(true);setError('');
    try {merge(await addIncidentNote(id,note.trim()));setNote('');}
    catch {setError('The experiment note could not be saved.');}
    finally {setBusy(false);}
  };
  const filtered = incidents.filter(item => `${item.title} ${item.mitre_techniques.join(' ')} ${item.status}`.toLowerCase().includes(query.toLowerCase()));
  return <div>
    <div className="page-intro"><div><p className="eyebrow">EVIDENCE / CORRELATED CASES</p><h1>Follow the investigation.</h1><p>Reconstruct a lab attack chain from linked detections. Review the timeline, map techniques, and record your reasoning.</p></div><span className="simulation-pill"><Files size={12} />{incidents.length} LOADED CASES</span></div>
    <div className="glass-panel p-4 mb-5 flex flex-wrap items-center justify-between gap-3"><div className="relative flex-1 min-w-48 max-w-md"><Search size={14} className="absolute left-3 top-3 text-textMuted" /><input aria-label="Filter investigations" value={query} onChange={event => setQuery(event.target.value)} placeholder="Filter by case, technique, or state…" className="lab-input pl-9" /></div><span className="text-[10px] text-textMuted">Recorded cases · Priority is a lab heuristic</span></div>
    {error && <p role="alert" className="text-xs text-danger mb-5">{error}</p>}
    {loading ? <div className="glass-panel empty-panel">Loading recorded investigations…</div> : filtered.length === 0 ? <div className="glass-panel empty-panel"><Files className="mx-auto mb-3 text-textMuted" size={25} />No investigations match this view.</div> : <div className="space-y-3">{filtered.map(incident => <section key={incident.incident_id} className="glass-panel overflow-hidden">
      <button className="case-trigger" onClick={() => expand(incident.incident_id)} aria-expanded={expandedId === incident.incident_id}><span className="case-chevron">{expandedId === incident.incident_id ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</span><span className="min-w-0 flex-1 text-left"><span className="case-id mono">CASE / {incident.incident_id.slice(0,8).toUpperCase()}</span><span className="block text-[13px] text-textMain mt-1 truncate">{incident.title}</span><span className="block text-[10px] text-textMuted mt-2">{hosts.find(host => host.host_id === incident.host_id)?.host_name || 'Unmapped lab asset'} <span className="mx-2 text-slate-600">/</span>{new Date(incident.last_seen).toLocaleString()}</span></span><span className="hidden lg:flex flex-wrap justify-end gap-1 max-w-48">{incident.mitre_techniques.slice(0,3).map(tech => <span key={tech} className="source-label">{tech}</span>)}</span><span className={`badge badge-${incident.severity}`}>{incident.severity}</span></button>
      {expandedId === incident.incident_id && <div className="case-expanded">{!details ? <p className="text-xs text-textMuted">Loading evidence…</p> : <>
        <div className="min-w-0"><div className="section-heading"><h2><Fingerprint size={15} className="inline mr-2 text-primary" />Evidence timeline</h2><span className="eyebrow">RECORDED OBSERVATIONS</span></div><div className="evidence-timeline">{details.attack_story.map((item,index) => {
          const match = item.match(/^\[(.*?)\]\s*(.*)/);
          return <div className="evidence-entry" key={index}><span className="evidence-node" /><span className="mono text-[9px] text-textMuted block mb-2">{match ? match[1] : `Observation ${index+1}`}</span><p className="text-[12px] leading-relaxed text-textMain">{match ? match[2] : item}</p></div>;
        })}{details.attack_story.length === 0 && <p className="text-xs text-textMuted">No timeline observations are stored for this case.</p>}</div><p className="experiment-note"><ArrowDown size={11} className="inline mr-1" />Timeline entries describe recorded evidence, not verified attacker intent.</p></div>
        <div className="case-worksheet"><div className="section-heading"><h2>Investigation worksheet</h2><span className="eyebrow">LAB NOTES</span></div><div className="grid gap-4 mb-6"><label className="lab-field-label">Case state<select aria-label="Case state" value={incident.status} onChange={event => change(incident.incident_id,{status:event.target.value})} className="lab-input mt-2"><option value="open">Open</option><option value="triage">Under study</option><option value="closed">Reviewed</option><option value="false-positive">False positive</option></select></label><label className="lab-field-label">Assigned researcher<select aria-label="Assigned researcher" value={incident.assignee_id || ''} onChange={event => change(incident.incident_id,{assignee_id:event.target.value || null})} className="lab-input mt-2"><option value="">Unassigned</option>{users.map(user => <option key={user.id} value={user.id}>{user.username}</option>)}</select></label><label className="lab-field-label">Mapped lab asset<select aria-label="Mapped lab asset" value={incident.host_id || ''} onChange={event => change(incident.incident_id,{host_id:event.target.value || null})} className="lab-input mt-2"><option value="">Unmapped network evidence</option>{hosts.map(host => <option key={host.host_id} value={host.host_id}>{host.host_name}</option>)}</select></label></div>
        <h3 className="text-xs mb-3"><MessageSquare size={13} className="inline mr-2 text-primary" />Experiment notes</h3><div className="space-y-3 mb-4 max-h-64 overflow-y-auto">{incident.notes.length ? incident.notes.map((item,index) => <div className="rounded-md border border-white/5 bg-white/[.02] p-3" key={index}><p className="flex justify-between gap-2 text-[9px] text-textMuted mb-2"><span className="text-primary">{item.author}</span><span>{new Date(item.timestamp).toLocaleDateString()}</span></p><p className="text-xs leading-relaxed text-textMain break-words">{item.text}</p></div>) : <p className="text-[11px] text-textMuted">Record your hypothesis, supporting evidence, or next step.</p>}</div><form onSubmit={event => {event.preventDefault();void addNote(incident.incident_id);}}><label htmlFor={`note-${incident.incident_id}`} className="sr-only">Experiment note</label><textarea id={`note-${incident.incident_id}`} value={note} onChange={event => setNote(event.target.value)} placeholder="What does the evidence suggest?" rows={3} className="lab-input resize-y" /><button disabled={!note.trim() || busy} className="lab-button mt-3">{busy ? 'Saving…' : 'Save experiment note'}</button></form></div>
      </>}</div>}
    </section>)}</div>}
  </div>;
}
