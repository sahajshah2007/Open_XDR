import api from './api';

export interface DefenseStatus {
  name: string;
  execution_mode: string;
  twin_enabled: boolean;
  processing: Record<string, number>;
  projection: Record<string, number>;
  policies: { id: string; description: string; autonomy: string }[];
}
export interface TwinNode { id: string; name: string; ip: string | null; criticality: number | null }
export interface TwinSnapshot {
  enabled: boolean;
  nodes: TwinNode[];
  edges: { source: string; target: string }[];
  description: string;
  available?: boolean;
}
export interface DefenseAction {
  action_id: string; incident_id: string; policy_id: string; action: string;
  autonomy: string; status: string; created_at: string; executed_at: string | null;
  result: { details: string; verification: string; contained: boolean } | null;
}
export interface DefenseIncident { incident_id: string; title: string; severity: string }
export interface AttackPath { nodes: string[]; hops: number }

export const loadDefense = async () => {
  const [status, twin, actions, incidents] = await Promise.all([
    api.get<DefenseStatus>('/defense/status'), api.get<TwinSnapshot>('/twin').catch(() => ({data: {
      enabled: true, available: false, nodes: [], edges: [],
      description: 'The digital twin is unavailable. Detection and response planning remain available.',
    } satisfies TwinSnapshot})),
    api.get<DefenseAction[]>('/defense/actions'), api.get<DefenseIncident[]>('/incidents/'),
  ]);
  return { status: status.data, twin: twin.data, actions: actions.data, incidents: incidents.data };
};
export const planDefense = async (id: string) => (await api.post<DefenseAction[]>(`/defense/incidents/${id}/plan`, {})).data;
export const simulateDefense = async (id: string) => (await api.post<DefenseAction>(`/defense/actions/${id}/simulate`)).data;
export const findAttackPaths = async (host: string) => (await api.get<{paths: AttackPath[]}>('/twin/paths', {params:{from_host:host}})).data.paths;
