import api from './api';
import type {ConfigSnapshot, DetectionConfig, Metrics, RunSummary, Verification} from './experiments';

export interface DetectionProfile extends DetectionConfig {
  builtin:boolean;
  created_at:string|null;
  snapshot:ConfigSnapshot;
}
export interface RuleDefinition {
  id:string;title:string;level:string;default_enabled:boolean;
  definition:Record<string,unknown>;fingerprint:string;
}
export interface ConfigurationCatalog {
  profiles:DetectionProfile[];rules:RuleDefinition[];native_sources:string[];description:string;
}
export interface ProfileInput {
  name:string;description:string;native_sources:string[];wazuh_min_level:number;rule_ids:string[];
}
interface ComparedRun {
  run_id:string;scenario_id:string;name:string;seed:number;status:string;created_at:string;
  metrics:Metrics;detection_config:DetectionConfig|null;configuration_snapshot:ConfigSnapshot|null;verification:Verification;
}
export interface Comparison {
  baseline:ComparedRun;candidate:ComparedRun;comparable:boolean;reasons:string[];warnings:string[];
  metric_deltas:Record<string,number|null>;
  configuration_changes:{known:boolean;same_fingerprint?:boolean;added_rules:string[];removed_rules:string[];changed_rules:string[];added_native_sources:string[];removed_native_sources:string[];wazuh_threshold_change:number|null};
  event_changes:{position:number;label:string;source:string;expected_positive:boolean;baseline_class:string;candidate_class:string;baseline_rules:string[];candidate_rules:string[];added_techniques:string[];removed_techniques:string[];changed:boolean;outcome:string}[];
  coverage_changes:{technique:string;name:string;url:string;baseline_status:string;candidate_status:string}[];
  model_changes:{asset:string;baseline_name:string;candidate_name:string;baseline_state:string;candidate_state:string;baseline_ports:number[];candidate_ports:number[];changed:boolean}[];
  summary:{improved:number;regressed:number;changed:number};methodology:string;simulation_only:boolean;
}
export const getConfigurations=async()=>(await api.get<ConfigurationCatalog>('/experiments/configurations')).data;
export const saveConfiguration=async(input:ProfileInput)=>(await api.post<DetectionProfile>('/experiments/configurations',input)).data;
export const startComparison=async(scenario_id:string,seed:number,baseline_profile_id:string,candidate_profile_id:string)=>(await api.post<{baseline:RunSummary;candidate:RunSummary}>('/experiments/compare/runs',{scenario_id,seed,baseline_profile_id,candidate_profile_id})).data;
export const getComparison=async(baseline:string,candidate:string)=>(await api.get<Comparison>('/experiments/compare',{params:{baseline,candidate}})).data;
export const downloadComparison=async(baseline:string,candidate:string,format:'html'|'json')=>{
  const response=await api.get<Blob>('/experiments/compare/report',{params:{baseline,candidate,format},responseType:'blob'});
  const url=URL.createObjectURL(response.data);const anchor=document.createElement('a');
  anchor.href=url;anchor.download=`TwinTrace-Comparison-${baseline}-${candidate}.${format}`;
  document.body.appendChild(anchor);anchor.click();anchor.remove();window.setTimeout(()=>URL.revokeObjectURL(url),1000);
};
