import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Incidents from './pages/Incidents';
import Hunting from './pages/Hunting';
import Settings from './pages/Settings';
import Hosts from './pages/Hosts';
import Login from './pages/Login';
import Defense from './pages/Defense';
import Project from './pages/Project';
import Experiments from './pages/Experiments';
import CompareExperiments from './pages/CompareExperiments';
import FlowStudio from './pages/FlowStudio';
import Guide from './pages/Guide';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './context/auth';
import type { ReactNode } from 'react';

const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<Dashboard />} />
            <Route path="incidents" element={<Incidents />} />
            <Route path="hosts" element={<Hosts />} />
            <Route path="hunting" element={<Hunting />} />
            <Route path="settings" element={<Settings />} />
            <Route path="defense" element={<Defense />} />
            <Route path="project" element={<Project />} />
            <Route path="experiments" element={<Experiments />} />
            <Route path="compare" element={<CompareExperiments />} />
            <Route path="flow" element={<FlowStudio />} />
            <Route path="guide" element={<Guide />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
