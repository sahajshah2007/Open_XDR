import type { HostRecord } from '../services/types';
import { useEffect, useState } from 'react';
import { format } from 'date-fns';
import { Settings, Tag as TagIcon, X } from 'lucide-react';
import { getHosts, updateHost } from '../services/api';

const Hosts = () => {
  const [hosts, setHosts] = useState<HostRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedHost, setSelectedHost] = useState<HostRecord | null>(null);
  const [editTags, setEditTags] = useState("");
  const [editCriticality, setEditCriticality] = useState(1);

  const fetchHosts = async () => {
    try {
      const data = await getHosts();
      setHosts(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getHosts().then(setHosts).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleEditClick = (host: HostRecord) => {
    setSelectedHost(host);
    setEditCriticality(host.criticality || 1);
    const tagArray = Array.isArray(host.tags) ? host.tags : Object.values(host.tags || {});
    setEditTags(tagArray.join(", "));
  };

  const handleSave = async () => {
    if (!selectedHost) return;
    
    // Parse comma separated tags
    const tagsArray = editTags.split(",").map(t => t.trim()).filter(t => t);
    
    try {
      await updateHost(selectedHost.host_id, {
        criticality: editCriticality,
        tags: tagsArray
      });
      setSelectedHost(null);
      fetchHosts();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <div className="p-8 text-center text-textMuted">Loading recorded lab assets…</div>;

  return (
    <div className="space-y-6">
      <div className="page-intro"><div><p className="eyebrow">EVIDENCE / ASSET CONTEXT</p><h1>The assets in your experiment.</h1><p>Review hosts referenced by lab events and assign the criticality used in incident scoring and the optional twin.</p></div><span className="simulation-pill"><TagIcon size={12} />{hosts.length} LAB ASSETS</span></div>

      <div className="glass-panel rounded-xl overflow-x-auto">
        <table className="w-full min-w-[610px] text-left border-collapse">
          <thead>
            <tr className="bg-white/5 border-b border-white/10 text-sm tracking-wider text-textMuted uppercase">
              <th className="p-4 font-normal">Hostname</th>
              <th className="p-4 font-normal">Agent</th>
              <th className="p-4 font-normal">Last Seen</th>
              <th className="p-4 font-normal">Criticality</th>
              <th className="p-4 font-normal">Tags</th>
              <th className="p-4 font-normal text-right">Manage</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {hosts.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-textMuted">No assets are referenced by the current lab dataset.</td>
              </tr>
            ) : hosts.map((host) => {
              const tagArray = Array.isArray(host.tags) ? host.tags : Object.values(host.tags || {});
              return (
                <tr key={host.host_id} className="border-b border-white/5 hover:bg-white/5 transition-colors group">
                  <td className="p-4">
                    <div className="font-semibold text-white">{host.host_name}</div>
                    <div className="text-xs text-textMuted mt-1">
                      {host.os_name || "OS not supplied"} {host.os_version || ""}
                    </div>
                  </td>
                  <td className="p-4">
                    <span className="px-2 py-1 bg-white/10 rounded-md text-xs font-mono uppercase text-gray-300">
                      {host.agent_type || "Unknown"}
                    </span>
                  </td>
                  <td className="p-4 text-gray-400">
                    {format(new Date(host.last_seen), 'MMM dd HH:mm:ss')}
                  </td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                      host.criticality >= 5 ? 'bg-red-500/20 text-red-400' :
                      host.criticality >= 3 ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {host.criticality >= 5 ? 'High' : host.criticality >= 3 ? 'Medium' : 'Low'} ({host.criticality})
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex flex-wrap gap-2">
                      {tagArray.length > 0 ? tagArray.map((tag: string, idx: number) => (
                        <span key={idx} className="flex items-center text-xs bg-primary/20 text-primary px-2 py-1 rounded-md">
                          <TagIcon size={10} className="mr-1" />
                          {tag}
                        </span>
                      )) : <span className="text-textMuted text-xs italic">none</span>}
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <button 
                      aria-label={`Edit lab asset ${host.host_name}`}
                      onClick={() => handleEditClick(host)}
                      className="text-textMuted hover:text-white transition-colors"
                    >
                      <Settings size={18} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Edit Modal */}
      {selectedHost && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="glass-panel p-6 rounded-xl w-full max-w-md shadow-2xl border border-white/10">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-white flex items-center">
                <Settings className="mr-2 text-primary" size={20} />
                Edit lab asset
              </h3>
              <button onClick={() => setSelectedHost(null)} className="text-textMuted hover:text-white transition-colors">
                <X size={20} />
              </button>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm text-textMuted uppercase tracking-wider mb-2">Hostname</label>
              <div className="p-3 bg-white/5 rounded-md text-white font-mono text-sm border border-white/10">
                {selectedHost.host_name}
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm text-textMuted uppercase tracking-wider mb-2">Criticality Level (1-10)</label>
              <input 
                type="range" 
                min="1" max="10" 
                value={editCriticality} 
                onChange={(e) => setEditCriticality(parseInt(e.target.value))}
                className="w-full accent-primary"
              />
              <div className="text-right text-xs text-primary font-bold mt-1">Level: {editCriticality}</div>
              <p className="text-xs text-textMuted mt-2">
                Higher criticality increases incident priority. Levels 8–10 mark critical assets in the digital twin after fresh telemetry.
              </p>
            </div>

            <div className="mb-8">
              <label className="block text-sm text-textMuted uppercase tracking-wider mb-2">Tags (Comma Separated)</label>
              <input 
                type="text" 
                value={editTags}
                onChange={(e) => setEditTags(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSave();
                }}
                placeholder="e.g. web-lab, scenario-a, database"
                className="w-full bg-white/5 border border-white/10 rounded-md p-3 text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button 
                onClick={() => setSelectedHost(null)}
                className="px-4 py-2 rounded-md text-sm text-textMuted hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button 
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  handleSave();
                }}
                className="px-4 py-2 rounded-md text-sm bg-primary text-black font-semibold hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Hosts;
