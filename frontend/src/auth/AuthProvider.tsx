import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { getMe, login as loginRequest, logout as logoutRequest } from '../api/auth';
import { setAuthToken, setUnauthorizedHandler } from '../api/client';
import type { AuthMeResponse } from '../api/types';
import { AuthContext } from './authContext';
import type { AuthState } from './authContext';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<AuthMeResponse | null>(null);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setAuthToken(null);
      setMe(null);
    });
    return () => setUnauthorizedHandler(null);
  }, []);

  const logout = useCallback(() => {
    void logoutRequest().catch(() => {});
    setAuthToken(null);
    setMe(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const result = await loginRequest({ email, password });
    setAuthToken(result.accessToken);
    // Roles and memberships come from the server; they are never inferred in the UI.
    setMe(await getMe());
  }, []);

  const value = useMemo<AuthState>(
    () => ({ status: me ? 'authenticated' : 'anonymous', me, login, logout }),
    [me, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
