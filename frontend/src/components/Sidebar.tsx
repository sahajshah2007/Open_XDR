import { LayoutDashboard, Files, ScanSearch, SlidersHorizontal, Server, LogOut, GitBranch, BookOpen, FlaskConical, ArrowUpRight, Play, Workflow, Presentation, ArrowLeftRight } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/auth';
import Brand from './Brand';
import { PROJECT } from '../project';

const groups = [
  { label: 'WORKSPACE', links: [
    { to: '/', label: 'Lab overview', icon: LayoutDashboard, number: '01' },
    { to: '/incidents', label: 'Investigations', icon: Files, number: '02' },
    { to: '/hosts', label: 'Lab assets', icon: Server, number: '03' },
    { to: '/hunting', label: 'Evidence explorer', icon: ScanSearch, number: '04' },
  ] },
  { label: 'EXPERIMENTS', links: [
    { to: '/experiments', label: 'New experiment', icon: Play, number: '05' },
    { to: '/compare', label: 'Compare runs', icon: ArrowLeftRight, number: '06' },
    { to: '/flow', label: 'Flow studio', icon: Workflow, number: '07' },
    { to: '/defense', label: 'Twin & response', icon: GitBranch, number: '08' },
    { to: '/guide', label: 'Interview guide', icon: Presentation, number: '09' },
    { to: '/project', label: 'Project notebook', icon: BookOpen, number: '10' },
  ] },
];

export default function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { logout } = useAuth();
  return <aside className="lab-sidebar">
    <NavLink to="/" onClick={onNavigate} className="brand-link" aria-label="TwinTrace Lab home"><Brand /></NavLink>
    <div className="sidebar-workspace"><span className="status-dot" /><span>Personal research workspace</span><span className="mono text-[10px] ml-auto">LOCAL</span></div>
    <nav className="sidebar-navigation" aria-label="Main navigation">
      {groups.map(group => <div key={group.label} className="nav-group"><p className="eyebrow nav-group-label">{group.label}</p>{group.links.map(({ to, label, icon: Icon, number }) => <NavLink key={to} to={to} end={to === '/'} onClick={onNavigate} className={({isActive}) => `nav-item ${isActive ? 'active' : ''}`}><Icon size={17} /><span>{label}</span><span className="nav-number">{number}</span></NavLink>)}</div>)}
    </nav>
    <div className="sidebar-lab-note"><FlaskConical size={19} /><p className="eyebrow">SIMULATION ONLY</p><p>Replay scenarios, follow the evidence, and verify simulated defense decisions.</p><NavLink to="/project" onClick={onNavigate}>About the experiment <ArrowUpRight size={13} /></NavLink></div>
    <div className="sidebar-bottom"><NavLink to="/settings" onClick={onNavigate} className="nav-item"><SlidersHorizontal size={17} /><span>Lab settings</span></NavLink><button onClick={logout} className="nav-item w-full"><LogOut size={17} /><span>Leave workspace</span><span className="nav-number">v{PROJECT.version}</span></button></div>
  </aside>;
}
