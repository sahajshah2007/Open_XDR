export interface HostRecord {
  host_id: string; host_name: string; agent_type: string | null;
  os_name: string | null; os_version: string | null;
  first_seen: string; last_seen: string; criticality: number;
  tags: string[] | Record<string, string> | null;
}
export interface UserRecord { id: string; username: string }
export interface IncidentNote { author: string; timestamp: string; text: string }
export interface AlertRecord {
  alert_id: string; rule_id: string; rule_name: string; severity: string;
  timestamp: string; enrichment: Record<string, unknown>;
}
export interface IncidentRecord {
  incident_id: string; title: string; severity: string; confidence: number;
  status: string; host_id: string | null; first_seen: string; last_seen: string;
  attack_story: string[]; mitre_techniques: string[]; assignee_id: string | null;
  notes: IncidentNote[]; alerts?: AlertRecord[];
  created_at?: string; updated_at?: string;
}
export interface TelemetryRecord {
  event_id: string; timestamp: string; source: string; event_type: string;
  src_ip: string | null; dst_ip: string | null; host_id: string | null;
  host_name: string | null; raw: Record<string, unknown>;
}
