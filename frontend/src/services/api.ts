import axios from 'axios';
import type { IncidentRecord, AlertRecord, HostRecord, UserRecord, TelemetryRecord } from './types';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_URL,
});

const token = localStorage.getItem('token');
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
}

// Intercept 401 responses: clear stale token and redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      delete api.defaults.headers.common['Authorization'];
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const getIncidents = async () => {
  const response = await api.get<IncidentRecord[]>('/incidents/');
  return response.data;
};

export const getIncidentDetails = async (id: string) => {
  const response = await api.get<IncidentRecord>(`/incidents/${id}`);
  return response.data;
};

export const updateOtxKey = async (key: string) => {
  const response = await api.post('/settings/otx-key', { otx_api_key: key });
  return response.data;
};

export const getAlerts = async () => {
  const response = await api.get<AlertRecord[]>('/alerts/');
  return response.data;
};

export const updateIncident = async (id: string, data: { status?: string; assignee_id?: string | null; host_id?: string | null }) => {
  const response = await api.patch<IncidentRecord>(`/incidents/${id}`, data);
  return response.data;
};

export const addIncidentNote = async (id: string, text: string) => {
  const response = await api.post<IncidentRecord>(`/incidents/${id}/notes`, { text });
  return response.data;
};

export const getUsers = async () => {
  const response = await api.get<UserRecord[]>('/auth/users');
  return response.data;
};

export const getHosts = async () => {
  const response = await api.get<HostRecord[]>('/hosts');
  return response.data;
};

export const updateHost = async (id: string, data: { tags?: HostRecord['tags']; criticality?: number }) => {
  const response = await api.patch(`/hosts/${id}`, data);
  return response.data;
};

export const getEvents = async (query?: string) => {
  const params = query ? { q: query } : {};
  const response = await api.get<TelemetryRecord[]>('/events', { params });
  return response.data;
};

export default api;
