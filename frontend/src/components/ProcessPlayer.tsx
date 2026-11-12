import { useEffect,useState } from 'react';
import { Play,Pause,SkipBack,SkipForward } from 'lucide-react';
import {PROCESS_STAGES} from './processStages';
import type {Trace} from '../services/experiments';

export default function ProcessPlayer({traces,illustrative=false}:{traces:Trace[];illustrative?:boolean}) {
  const [cursor,setCursor]=useState(0);
  const [playing,setPlaying]=useState(()=>!window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const [speed,setSpeed]=useState(1);
  useEffect(()=>{
    if(!playing||!traces.length)return;
    const timer=window.setInterval(()=>setCursor(value=>(value+1)%traces.length),1400/speed);
    return()=>window.clearInterval(timer);
  },[playing,speed,traces.length]);
  const frame=traces[Math.min(cursor,Math.max(0,traces.length-1))];
  const active=Math.max(0,PROCESS_STAGES.findIndex(stage=>stage.id===frame?.stage));
  return <section className="glass-panel process-player">
    <div className="section-heading"><div><h2>Follow the log.</h2><p className="text-[10px] text-textMuted mt-2">{illustrative?'Illustrative walkthrough · sample data is not stored':'Time-compressed playback of persisted processing traces · not live packet traffic'}</p></div><span className="simulation-pill">{illustrative?'GUIDED EXAMPLE':'RECORDED FLOW'}</span></div>
    <div className="signal-conveyor"><svg viewBox="0 0 980 70" role="img" aria-label="Animated signal through nine processing stages"><defs><linearGradient id="signal-gradient"><stop stopColor="#8caecc"/><stop offset="1" stopColor="#e8b45b"/></linearGradient></defs><path d="M35 35 H945" stroke="#344459" strokeWidth="2"/>{PROCESS_STAGES.map((stage,index)=><g key={stage.id}><circle cx={35+index*113.75} cy="35" r={index===active?10:6} fill={index===active?'#e8b45b':'#1b2a3d'} stroke={index<=active?'#e8b45b':'#59718c'} strokeWidth="2"/><text x={35+index*113.75} y="63" textAnchor="middle" fill="#8a9fb7" fontSize="9" fontFamily="monospace">0{index+1}</text></g>)}{playing&&<circle r="4" fill="#e8b45b"><animateMotion path="M35 35 H945" dur={`${3/speed}s`} repeatCount="indefinite"/></circle>}</svg></div>
    <div className="process-stages">{PROCESS_STAGES.map((stage,index)=>{const Icon=stage.icon;const found=traces.findIndex(item=>item.stage===stage.id);return <button key={stage.id} className={`process-stage ${active===index?'is-current':''}`} disabled={found<0} onClick={()=>{setCursor(found);setPlaying(false);}} aria-pressed={active===index}><Icon size={18}/><span>{stage.label}</span><small>{stage.tech}</small></button>;})}</div>
    <div className="process-controls"><button className="icon-button" aria-label="Previous trace" disabled={!traces.length} onClick={()=>{setPlaying(false);setCursor(value=>(value-1+traces.length)%traces.length);}}><SkipBack size={14}/></button><button className="lab-button secondary" onClick={()=>setPlaying(value=>!value)} disabled={!traces.length}>{playing?<Pause size={12}/>:<Play size={12}/>} {playing?'Pause flow':'Play flow'}</button><button className="icon-button" aria-label="Next trace" disabled={!traces.length} onClick={()=>{setPlaying(false);setCursor(value=>(value+1)%traces.length);}}><SkipForward size={14}/></button><input aria-label="Replay position" type="range" min="0" max={Math.max(0,traces.length-1)} value={Math.min(cursor,Math.max(0,traces.length-1))} onChange={event=>{setPlaying(false);setCursor(Number(event.target.value));}}/><span className="mono text-[9px] text-textMuted">{traces.length?Math.min(cursor+1,traces.length):0}/{traces.length}</span><select aria-label="Playback speed" className="lab-input" value={speed} onChange={event=>setSpeed(Number(event.target.value))}><option value="0.5">0.5×</option><option value="1">1×</option><option value="2">2×</option></select></div>
    <div className="process-inspector"><div><p className="eyebrow text-primary mb-2">{PROCESS_STAGES[active].label}</p><h3 className="text-sm mb-3">{frame?.message||'Waiting for processing traces…'}</h3><p className="notebook-prose">{PROCESS_STAGES[active].description}</p>{frame&&<p className="mono text-[9px] text-textMuted mt-4">Trace {frame.ordinal} · {frame.event_id?frame.event_id.slice(0,8):'Run summary'}</p>}</div><pre aria-label="Selected processing data">{JSON.stringify(frame?.data||{},null,2)}</pre></div>
  </section>;
}
