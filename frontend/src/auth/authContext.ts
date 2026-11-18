import { createContext, useContext } from 'react';
import type { AuthMeResponse } from '../api/types';

export interface AuthState {
  status: 'authenticated' | 'anonymous';
  me: AuthMeResponse | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
