import { useState } from 'react';
import { FlaskConical, KeyRound, Save, FileJson2 } from 'lucide-react';
import { updateOtxKey } from '../services/api';
import { PROJECT } from '../project';

export default function Settings() {
  const [key,setKey] = useState('');
  const [saving,setSaving] = useState(false);
  const [message,setMessage] = useState('');
  const [failed,setFailed] = useState(false);
  const save = async () => {
    if (!key.trim()) return;
    setSaving(true);setMessage('');setFailed(false);
    try {await updateOtxKey(key.trim());setMessage('The optional enrichment key has been saved.');setKey('');}
    catch {setMessage('The key could not be saved. Administrator access is required.');setFailed(true);}
    finally {setSaving(false);}
  };
  return <div>
    <div className="page-intro"><div><p className="eyebrow">WORKSPACE / CONFIGURATION</p><h1>Set up the experiment.</h1><p>Review the lab scope, supported data formats, and optional context used in your investigation.</p></div><span className="simulation-pill"><FlaskConical size={12} />SIMULATION ONLY</span></div>
    <div className="notebook-grid"><div className="space-y-5"><section className="glass-panel panel-padding"><div className="section-heading"><h2>Workspace identity</h2><FlaskConical size={16} className="text-primary" /></div>{[['Project',PROJECT.name],['Focus',PROJECT.tagline],['Dataset', 'Recorded or synthetic telemetry'],['Response mode','Simulated effects only'],['Purpose','Learning, experimentation, and portfolio demonstration']].map(([label,value]) => <div className="implementation-row" key={label}><span>{label}</span><span className="text-textMain text-right max-w-[65%]">{value}</span></div>)}</section>
    <section className="glass-panel panel-padding"><div className="section-heading"><h2>Optional reputation context</h2><KeyRound size={15} className="text-textMuted" /></div><p className="notebook-prose mb-5">An AlienVault OTX key can add external reputation context to public IP addresses in a lab dataset. It is optional; investigation and response simulations work without it.</p><form onSubmit={event => {event.preventDefault();void save();}}><label htmlFor="otx-key" className="lab-field-label">AlienVault OTX API key</label><div className="flex flex-wrap gap-3 mt-2"><input id="otx-key" type="password" autoComplete="off" value={key} onChange={event => setKey(event.target.value)} placeholder="Optional enrichment key" className="lab-input min-w-40 flex-1" /><button type="submit" disabled={saving || !key.trim()} className="lab-button secondary"><Save size={12} />{saving ? 'Saving…' : 'Save key'}</button></div></form><p role="status" className={`text-[11px] mt-4 ${failed ? 'text-danger' : 'text-success'}`}>{message}</p><p className="experiment-note">Keys are encrypted in the shared lab database. Credentials are never included in the downloadable project brief.</p></section></div>
    <section className="glass-panel panel-padding self-start"><div className="section-heading"><h2>Evidence inputs</h2><FileJson2 size={15} className="text-textMuted" /></div><p className="notebook-prose mb-4">The lab accepts the following JSON formats. These are supported sources, not a claim that live sensors are deployed.</p>{[['Wazuh','Endpoint alert records'],['Suricata','Network alert records'],['Zeek','Connection telemetry'],['Falco','Runtime event records'],['Lab signals','Synthetic attacker events']].map(([source,description]) => <div key={source} className="implementation-row"><span className="text-textMain">{source}</span><span className="text-[10px] text-right">{description}</span></div>)}<p className="experiment-note">Forward controlled records through the authenticated ingestion API to extend the dataset. The application does not execute attacks or deploy sensors.</p></section></div>
  </div>;
}
