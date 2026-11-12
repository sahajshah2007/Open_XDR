import { Database, Fingerprint, Layers3, Route, FlaskConical, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
const stages = [
  { label: 'Collect', detail: 'Recorded telemetry', icon: Database, to: '/hunting' },
  { label: 'Normalize', detail: 'Common event schema', icon: Layers3, to: '/hunting' },
  { label: 'Detect', detail: 'Rules & ATT&CK tags', icon: Fingerprint, to: '/incidents' },
  { label: 'Correlate', detail: 'Cases & optional twin', icon: Route, to: '/incidents' },
  { label: 'Simulate', detail: 'Policy response study', icon: FlaskConical, to: '/defense' },
];
export default function LabPipeline() {
  return <div className="pipeline-view" aria-label="Lab architecture: collect, normalize, detect, correlate, simulate">{stages.map(({label,detail,icon:Icon,to},index) => <div key={label} className="contents"><Link to={to} className={`pipeline-stage ${index === stages.length - 1 ? 'is-simulation' : ''}`}><div className="pipeline-stage-icon"><Icon size={19} /></div><p className="pipeline-stage-label">{label}</p><p className="pipeline-stage-detail">{detail}</p></Link>{index < stages.length - 1 && <ArrowRight size={17} className="pipeline-arrow" />}</div>)}</div>;
}
