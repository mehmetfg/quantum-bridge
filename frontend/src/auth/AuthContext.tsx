/**
 * Kimlik bağlamı (auth context).
 *
 * Şu an giriş ekranı yok: uygulama doğrudan açılır. Bu bilinçli bir karardır,
 * demo sırasında kimsenin hesap açmasını beklemek istemiyoruz.
 *
 * Buna karşılık kullanıcı kavramı baştan yerinde duruyor. Arka uç
 * /api/auth/status uç noktasından giriş gerekip gerekmediğini söyler.
 * Giriş özelliği açıldığında burada değişecek tek şey, login fonksiyonunun
 * gerçekten bir jeton alması olacak; sayfaların hiçbiri değişmeyecek.
 */

import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

import { api, setAuthToken } from '../api/client';
import type { AuthStatus } from '../types';

interface AuthContextValue {
  user: AuthStatus['user'] | null;
  loginRequired: boolean;
  isAuthenticated: boolean;
  loading: boolean;
  note: string;
  login: (token: string) => void;
  logout: () => void;
}

const FALLBACK_USER: AuthStatus['user'] = {
  id: 'demo',
  display_name: 'Demo Kullanıcı',
  is_demo: true,
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .authStatus()
      .then((result) => {
        if (!cancelled) setStatus(result);
      })
      .catch(() => {
        // Arka uca ulaşılamazsa demo kullanıcıyla devam edilir.
        if (!cancelled) {
          setStatus({
            mode: 'dogrudan-giris',
            login_required: false,
            user: FALLBACK_USER,
            note: 'Arka uca ulaşılamadı, demo kullanıcıyla devam ediliyor.',
          });
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: status?.user ?? FALLBACK_USER,
      loginRequired: status?.login_required ?? false,
      isAuthenticated: true,
      loading,
      note: status?.note ?? '',
      login: (token: string) => setAuthToken(token),
      logout: () => setAuthToken(null),
    }),
    [status, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth yalnızca AuthProvider içinde kullanılabilir.');
  }
  return context;
}
