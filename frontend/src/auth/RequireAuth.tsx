/**
 * Korumalı sayfa sarmalayıcısı.
 *
 * Şu an herkesi geçirir, çünkü giriş kapalı. Giriş açıldığında yapılacak
 * tek değişiklik, aşağıdaki koşulun devreye girmesidir. Sayfaları
 * sarmalayan yapı baştan kurulu olduğu için o gün yönlendirme mantığı
 * her sayfaya tek tek eklenmek zorunda kalmaz.
 */

import { Navigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';

import { useAuth } from './AuthContext';

export default function RequireAuth({ children }: { children: ReactNode }) {
  const { loginRequired, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-slate-500">
        Yükleniyor...
      </div>
    );
  }

  if (loginRequired && !isAuthenticated) {
    return <Navigate to="/giris" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
