import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { errorMessage } from '../api/client';
import { useAuth } from '../auth/authContext';
import { WorkspacePage } from './WorkspacePage';

export function LoginPage() {
  const { login, status } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email.trim(), password);
      navigate('/');
      window.requestAnimationFrame(() => document.getElementById('main-content')?.focus());
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspacePage
      title="Sign in"
      description="Sign in to view records within your permitted scope. Roles and permissions are enforced by the server, not by this interface."
    >
      {status === 'authenticated' && (
        <p className="muted">You are already signed in. Use Sign out in the header to change account.</p>
      )}
      <form className="card form-grid" onSubmit={onSubmit}>
        {error && (
          <p className="notice notice-danger" role="alert">
            Sign-in failed: {error}
          </p>
        )}
        <div className="field">
          <label htmlFor="login-email">Email</label>
          <input
            id="login-email"
            name="email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="login-password">Password</label>
          <input
            id="login-password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        <div>
          <button type="submit" className="btn" disabled={busy} aria-busy={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </div>
        <p className="muted">Accounts are provisioned by an administrator. There is no self-service sign-up.</p>
      </form>
    </WorkspacePage>
  );
}
