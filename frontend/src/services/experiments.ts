import api from './api';
export interface Scenario {id:string;title:string;category:string;difficulty:string;duration:string;accent:string;description:string;lesson:string;techniques:string[];sources:string[];version:number}
export interface Coverage {technique:string;name:string;tactic:string;url:string;expected:boolean;observed:boolean;status:'detected'|'missed'|'unexpected'}
export interface Metrics {tp:number;fp:number;fn:number;tn:number;events:number;precision:number|null;recall:number|null;f1:number|null;accuracy:number|null;mean_detection_ms:number|null;coverage:Coverage[];coverage_ratio:number|null;methodology:string}
export interface DetectionConfig {profile_id:string;name:string;description:string;fingerprint:string;engine_version:number;native_sources:string[];wazuh_min_level:number;rule_ids:string[];pinned:boolean}
export interface ConfigSnapshot {profile_id:string;name:string;description:string;fingerprint:string;engine_version:number;native_sources:string[];wazuh_min_level:number;sigma_rules:Record<string,unknown>[]}
export interface RunSummary {run_id:string;scenario_id:string;name:string;seed:number;status:string;created_at:string;completed_at:string|null;events_total:number;events_processed:number;metrics:Metrics|null;error:string|null;detection_config:DetectionConfig|null}
export interface Topology {nodes:{id:string;name:string;kind:string;ip:string|null;criticality:number;state:string;blocked_ports:number[]}[];edges:{source:string;target:string;label:string;port:number;blocked:boolean}[];provenance:string}
export interface Trace {trace_id:string;event_id:string|null;ordinal:number;stage:string;message:string;data:Record<string,unknown>;recorded_at:string}
export interface RunEvent {event_id:string;position:number;label:string;source:string;expected_positive:boolean;expected_techniques:string[];observed_techniques:string[];classification:string;status:string;latency_ms:number|null;alerts:{alert_id:string;rule_name:string;rule_id:string;technique:string|null;incident_id:string;severity:string}[];raw:Record<string,unknown>;normalized:Record<string,unknown>;error:string|null}
export interface Verification {checks:{action:string;target:string;passed:boolean;scope:string}[];passed:number;total:number;simulated_containment:boolean;real_containment_performed:boolean;description:string}
export interface RunDetail extends RunSummary {snapshot:Scenario & {identity:string;seed:number;fixture_events:number;detection_config?:ConfigSnapshot};topology:Topology;verification:Verification|null;events:RunEvent[];traces:Trace[];simulation_only:boolean;reproducibility:string}
export const getScenarios=async()=>(await api.get<{scenarios:Scenario[]}>('/experiments/scenarios')).data.scenarios;
export const getRuns=async(limit=30)=>(await api.get<RunSummary[]>('/experiments/runs',{params:{limit}})).data;
export const getRun=async(id:string)=>(await api.get<RunDetail>(`/experiments/runs/${id}`)).data;
export const startRun=async(scenario_id:string,seed:number,name:string,options?:{profile_id?:string;replay_of?:string})=>(await api.post<RunSummary>('/experiments/runs',{scenario_id,seed,name,...options})).data;
export const retryRun=async(id:string)=>(await api.post<RunSummary>(`/experiments/runs/${id}/retry`)).data;
export const downloadReport=async(id:string,format:'html'|'json'|'csv')=>{
  const response=await api.get<Blob>(`/experiments/runs/${id}/report`,{params:{format},responseType:'blob'});
  const url=URL.createObjectURL(response.data);const a=document.createElement('a');a.href=url;a.download=`TwinTrace-${id}.${format}`;document.body.appendChild(a);a.click();a.remove();window.setTimeout(()=>URL.revokeObjectURL(url),1000);
};
