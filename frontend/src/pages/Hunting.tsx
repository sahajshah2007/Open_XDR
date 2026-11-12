import type { TelemetryRecord } from '../services/types';
import { useEffect, useState, useCallback, Fragment } from 'react';
import { Search, ChevronRight, ChevronDown, Database } from 'lucide-react';
import { format } from 'date-fns';
import { getEvents } from '../services/api';

const SOURCE_COLORS: Record<string, string> = {
  wazuh: 'bg-blue-500/20 text-blue-400',
  suricata: 'bg-orange-500/20 text-orange-400',
  zeek: 'bg-teal-500/20 text-teal-400',
  falco: 'bg-primary/10 text-primary',
  attacker: 'bg-warning/10 text-warning',
};

const Hunting = () => {
  const [events, setEvents] = useState<TelemetryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchInput, setSearchInput] = useState('');
  const [activeQuery, setActiveQuery] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchEvents = useCallback(async (query?: string) => {
    setLoading(true);
    try {
      const data = await getEvents(query || undefined);
      setEvents(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    getEvents().then(setEvents).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setActiveQuery(searchInput);
    fetchEvents(searchInput);
  };

  const toggleExpand = (id: string) => {
    setExpandedId(prev => prev === id ? null : id);
  };

  return (
    <div className="space-y-6 flex flex-col">
      <div className="page-intro"><div><p className="eyebrow">EVIDENCE / RECORDED TELEMETRY</p><h1>Inspect the original trace.</h1><p>Search recorded lab events, inspect their source payloads, and follow the evidence behind an investigation.</p></div><span className="simulation-pill"><Database size={12} />LAB DATASET</span></div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="glass-panel p-4 flex space-x-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 text-textMuted" size={20} />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            aria-label="Search lab evidence"
            placeholder='Search lab evidence (e.g. "wazuh", "192.168.1.100", "SSH", "dns")...'
            className="w-full bg-black/20 border border-white/10 rounded-lg py-2.5 pl-10 pr-4 text-white focus:outline-none focus:border-primary transition-colors"
          />
        </div>
        <button
          type="submit"
          className="px-5 py-2 bg-primary text-black font-semibold rounded-lg hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
        >
          Search
        </button>
      </form>

      {/* Results Header */}
      <div className="flex items-center justify-between text-sm text-textMuted">
        <div className="flex items-center space-x-2">
          <Database size={14} />
          <span>
            {loading ? 'Searching...' : `${events.length} event${events.length !== 1 ? 's' : ''} loaded`}
            {activeQuery && <span className="ml-2 text-primary font-mono">query: "{activeQuery}"</span>}
          </span>
        </div>
      </div>

      <p className="text-[10px] text-textMuted">Showing up to 100 matching records. Source labels identify the input format; they do not indicate active sensors.</p>

      {/* Events Table */}
      <div className="flex-1 glass-panel overflow-hidden flex flex-col rounded-xl">
        <div className="overflow-auto flex-1">
          <table className="w-full text-left text-sm">
            <thead className="bg-black/40 border-b border-white/5 sticky top-0">
              <tr>
                <th className="px-4 py-4 font-normal text-textMuted uppercase tracking-wider text-[9px] font-mono w-8"></th>
                <th className="px-4 py-4 font-normal text-textMuted uppercase tracking-wider text-[9px] font-mono">Timestamp</th>
                <th className="px-4 py-4 font-normal text-textMuted uppercase tracking-wider text-[9px] font-mono">Source</th>
                <th className="px-4 py-4 font-normal text-textMuted uppercase tracking-wider text-[9px] font-mono">Event Type</th>
                <th className="px-4 py-4 font-normal text-textMuted uppercase tracking-wider text-[9px] font-mono">Source IP</th>
                <th className="px-4 py-4 font-normal text-textMuted uppercase tracking-wider text-[9px] font-mono">Dest IP</th>
                <th className="px-4 py-4 font-normal text-textMuted uppercase tracking-wider text-[9px] font-mono">Host</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-textMuted">
                    <div className="flex flex-col items-center space-y-3">
                      <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                      <span>Reading recorded lab evidence…</span>
                    </div>
                  </td>
                </tr>
              ) : events.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-textMuted">
                    No matching evidence. Try a source name, technique, or value from a lab event.
                  </td>
                </tr>
              ) : (
                events.map(event => {
                  const isExpanded = expandedId === event.event_id;
                  return (
                    <Fragment key={event.event_id}>
                      <tr
                        onClick={() => toggleExpand(event.event_id)}
                        className={`hover:bg-white/5 cursor-pointer transition-colors ${isExpanded ? 'bg-white/5' : ''}`}
                      >
                        <td className="px-4 py-3 text-textMuted">
                          {isExpanded
                            ? <ChevronDown size={16} className="text-primary" />
                            : <ChevronRight size={16} />
                          }
                        </td>
                        <td className="px-4 py-3 font-mono text-xs text-gray-400">
                          {format(new Date(event.timestamp), 'yyyy-MM-dd HH:mm:ss')}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded-md text-xs font-semibold uppercase ${SOURCE_COLORS[event.source] || 'bg-white/10 text-gray-300'}`}>
                            {event.source}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-white max-w-xs truncate">{event.event_type}</td>
                        <td className="px-4 py-3 font-mono text-xs text-primary">{event.src_ip || '—'}</td>
                        <td className="px-4 py-3 font-mono text-xs text-gray-400">{event.dst_ip || '—'}</td>
                        <td className="px-4 py-3 text-gray-400 text-xs">{event.host_name || event.host_id || '—'}</td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan={7} className="px-0 py-0">
                            <div className="bg-black/40 border-l-2 border-primary mx-4 my-2 rounded-lg overflow-hidden">
                              <div className="px-4 py-2 bg-white/5 border-b border-white/5 text-xs text-textMuted uppercase tracking-wider font-semibold">
                                Original lab record — {event.source}
                              </div>
                              <pre className="px-4 py-3 text-xs font-mono text-gray-300 overflow-x-auto max-h-72 whitespace-pre-wrap break-words">
                                {JSON.stringify(event.raw, null, 2)}
                              </pre>
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Hunting;
