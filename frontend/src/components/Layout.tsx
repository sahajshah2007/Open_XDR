import { useState } from 'react';
import { Outlet, useLocation, Link } from 'react-router-dom';
import { ChevronRight, FlaskConical, Menu, X, BookOpen } from 'lucide-react';
import Sidebar from './Sidebar';

const names: Record<string, string> = {'/':'Lab overview','/incidents':'Investigations','/hosts':'Lab assets','/hunting':'Evidence explorer','/defense':'Twin & response','/project':'Project notebook','/settings':'Lab settings','/experiments':'New experiment','/compare':'Compare runs','/flow':'Flow studio','/guide':'Interview guide'};
export default function Layout() {
  const { pathname } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  return <div className="lab-app">
    {menuOpen && <button aria-label="Close navigation" className="navigation-backdrop" onClick={() => setMenuOpen(false)} />}
    <div className={menuOpen ? 'sidebar-container is-open' : 'sidebar-container'}><Sidebar onNavigate={() => setMenuOpen(false)} /></div>
    <div className="lab-workspace">
      <header className="workspace-header"><div className="flex items-center gap-3"><button className="mobile-menu icon-button" onClick={() => setMenuOpen(!menuOpen)} aria-expanded={menuOpen} aria-label="Toggle navigation">{menuOpen ? <X size={19} /> : <Menu size={19} />}</button><span className="breadcrumb-root">Workspace</span><ChevronRight size={13} className="text-textMuted" /><span className="text-sm">{names[pathname] || 'Lab'}</span></div><div className="flex items-center gap-4"><Link to="/project" className="header-notebook"><BookOpen size={15} />Project notes</Link><span className="simulation-pill"><FlaskConical size={13} />SIMULATION LAB</span></div></header>
      <div className="workspace-scope"><span className="scope-dot" /><span>Educational simulation · Recorded & synthetic telemetry · Responses are simulated</span><span className="mono scope-local">LOCAL WORKSPACE</span></div>
      <main id="main-content" className="workspace-main"><Outlet /></main>
      <footer className="workspace-footer"><span>TwinTrace Lab <span className="footer-divider">/</span> Cyber defense, made explainable.</span><span>Portfolio & research project</span></footer>
    </div>
  </div>;
}
