import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/auth';
import { ArrowRight, FlaskConical, LockKeyhole } from 'lucide-react';
import Brand from '../components/Brand';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const apiUrl = import.meta.env.VITE_API_URL || '/api/v1';
      const params = new URLSearchParams();
      params.append('username', username);
      params.append('password', password);

      const response = await fetch(`${apiUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: params,
      });

      const data = await response.json();

      if (response.ok) {
        login(data.access_token);
        navigate('/');
      } else {
        setError(data.detail || 'Login failed');
      }
    } catch {
      setError('An error occurred during login');
    } finally {
      setIsLoading(false);
    }
  };

  return <div className="login-shell">
    <section className="login-story"><Brand large /><div className="login-story-content"><p className="eyebrow">A CYBER DEFENSE SIMULATION LAB</p><h1>Trace the attack.<br />Model the defense.<br /><span>Understand the why.</span></h1><p>An educational workbench for exploring telemetry, reconstructing attack chains, and studying simulated response decisions.</p><div className="login-steps"><span>01<b>Collect evidence</b></span><span>02<b>Connect the events</b></span><span>03<b>Simulate a response</b></span></div></div><p className="login-story-footer"><FlaskConical size={14} />Portfolio project · Recorded & synthetic datasets</p></section>
    <section className="login-access"><p className="eyebrow">YOUR RESEARCH WORKSPACE</p><h2>Enter the lab.</h2><p>Sign in to explore your saved investigations and continue the experiment.</p>
      {error && <div role="alert" className="mb-5 rounded-md border border-danger/20 bg-danger/5 p-3 text-xs text-danger">{error}</div>}
      <form onSubmit={handleLogin}>
        <div className="login-field"><label htmlFor="username">Username</label><input id="username" name="username" autoComplete="username" value={username} onChange={event => setUsername(event.target.value)} placeholder="Your lab username" required /></div>
        <div className="login-field"><label htmlFor="password">Password</label><input id="password" name="password" type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} placeholder="Your lab password" required /></div>
        <button type="submit" disabled={isLoading} className="lab-button w-full mt-1 py-3">{isLoading ? 'Opening workspace…' : 'Open workspace'}<ArrowRight size={14} /></button>
      </form>
      <div className="login-form-note"><LockKeyhole size={16} className="shrink-0 mt-1" /><p>Use the administrator credentials configured for this lab. All response actions are simulations; the application does not perform real containment.</p></div>
    </section>
  </div>;
};

export default Login;
