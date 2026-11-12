import {useState} from 'react';
import type {FormEvent} from 'react';
import {Save,SlidersHorizontal} from 'lucide-react';
import {saveConfiguration} from '../services/comparison';
import type {ConfigurationCatalog,DetectionProfile} from '../services/comparison';

export default function ConfigurationEditor({catalog,onSaved}:{catalog:ConfigurationCatalog;onSaved:(profile:DetectionProfile)=>void}){
  const [template,setTemplate]=useState('baseline');
  const [name,setName]=useState('');
  const [description,setDescription]=useState('');
  const [sources,setSources]=useState<string[]>(catalog.profiles[0]?.native_sources||[]);
  const [threshold,setThreshold]=useState(3);
  const [rules,setRules]=useState<string[]>(catalog.profiles[0]?.rule_ids||[]);
  const [busy,setBusy]=useState(false);
  const [notice,setNotice]=useState('');
  const [error,setError]=useState('');
  function loadTemplate(id:string){
    setTemplate(id);const profile=catalog.profiles.find(item=>item.profile_id===id);
    if(!profile)return;
    setSources(profile.native_sources);setThreshold(profile.wazuh_min_level);
    setRules(profile.rule_ids.filter(key=>catalog.rules.some(rule=>rule.id===key)));
    setDescription(profile.description);setNotice('');setError('');
  }
  function toggle(values:string[],key:string){return values.includes(key)?values.filter(value=>value!==key):[...values,key];}
  async function save(event:FormEvent){
    event.preventDefault();setBusy(true);setError('');setNotice('');
    try{
      const profile=await saveConfiguration({name:name.trim(),description,native_sources:sources,wazuh_min_level:threshold,rule_ids:rules});
      onSaved(profile);setNotice(`Saved “${profile.name}”. Selected as the candidate configuration for your next A/B experiment.`);setName('');
    }catch{setError('Configuration could not be saved. Use a descriptive name, valid settings, and administrator access.');}
    finally{setBusy(false);}
  }
  return <section className="glass-panel panel-padding configuration-editor">
    <div className="section-heading"><div><h2><SlidersHorizontal size={15} className="inline mr-2 text-primary"/>Save a detection configuration</h2><p className="notebook-prose mt-2">Choose rules and native-alert thresholds, then save an immutable copy for future runs.</p></div><span className="simulation-pill">EXPERIMENTS ONLY</span></div>
    <form onSubmit={save}>
      <div className="config-fields"><label className="lab-field-label">Start from<select aria-label="Configuration template" className="lab-input mt-2" value={template} onChange={event=>loadTemplate(event.target.value)}>{catalog.profiles.map(profile=><option key={profile.profile_id} value={profile.profile_id}>{profile.name}{profile.builtin?' · preset':' · saved'}</option>)}</select></label><label className="lab-field-label">Configuration name<input aria-label="Configuration name" className="lab-input mt-2" value={name} required maxLength={120} onChange={event=>setName(event.target.value)} placeholder="e.g. DNS coverage / review 1"/></label><label className="lab-field-label">Minimum Wazuh native level<input aria-label="Minimum Wazuh level" className="lab-input mt-2" type="number" min="0" max="15" required value={threshold} onChange={event=>setThreshold(Number(event.target.value))}/></label></div>
      <label className="lab-field-label mt-4">Description<input aria-label="Configuration description" className="lab-input mt-2" value={description} maxLength={500} onChange={event=>setDescription(event.target.value)}/></label>
      <fieldset className="config-sources"><legend>Native source alerts</legend>{catalog.native_sources.map(source=><label key={source}><input type="checkbox" checked={sources.includes(source)} onChange={()=>setSources(toggle(sources,source))}/>{source}</label>)}</fieldset>
      <fieldset className="config-rules"><legend>Sigma rules</legend>{catalog.rules.map(rule=><div key={rule.id} className="config-rule"><label><input type="checkbox" checked={rules.includes(rule.id)} onChange={()=>setRules(toggle(rules,rule.id))}/><span><b>{rule.title}</b><small>{rule.id} · {rule.default_enabled?'Default enabled':'Optional experiment rule'}</small></span></label><details><summary>Inspect definition</summary><pre>{JSON.stringify(rule.definition,null,2)}</pre></details></div>)}</fieldset>
      <p className="experiment-note">Thresholds filter native Wazuh alerts only; independently matching Sigma rules can still emit alerts. Templates copy current catalog definitions. Saved configurations and run snapshots retain their original rule bodies. Global telemetry settings are unchanged.</p>
      <button className="lab-button" disabled={busy||!name.trim()||!Number.isInteger(threshold)||threshold<0||threshold>15}><Save size={13}/>{busy?'Saving…':'Save configuration'}</button>
      {notice&&<p role="status" className="text-primary text-xs mt-4">{notice}</p>}{error&&<p role="alert" className="text-danger text-xs mt-4">{error}</p>}
    </form>
  </section>;
}
