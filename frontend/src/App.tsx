import { NavLink, Navigate, Route, Routes } from 'react-router-dom';

import RequireAuth from './auth/RequireAuth';
import { useAuth } from './auth/AuthContext';
import Dashboard from './pages/Dashboard';
import JobDetail from './pages/JobDetail';
import Learn from './pages/Learn';
import Login from './pages/Login';
import ProblemLab from './pages/ProblemLab';
import Roadmap from './pages/Roadmap';
import { cx } from './lib/style';

const NAV = [
  { to: '/', label: 'Genel bakış', end: true },
  { to: '/laboratuvar', label: 'Laboratuvar' },
  { to: '/ogren', label: 'Öğren' },
  { to: '/yol-haritasi', label: 'Yol haritası' },
];

export default function App() {
  const { user, loginRequired } = useAuth();

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-slate-800 bg-slate-950/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-4 py-3">
          <NavLink to="/" className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-sky-500 via-violet-500 to-emerald-500 text-sm font-bold text-slate-950">
              QB
            </span>
            <span>
              <span className="block text-sm font-bold leading-tight text-slate-100">
                Quantum Bridge
              </span>
              <span className="block text-[10px] leading-tight text-slate-500">
                Klasik, yapay zeka ve kuantum arasındaki köprü
              </span>
            </span>
          </NavLink>

          <nav className="flex flex-wrap items-center gap-1">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cx(
                    'rounded-lg px-3 py-1.5 text-sm font-medium transition',
                    isActive
                      ? 'bg-slate-800 text-slate-100'
                      : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200',
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-3">
            <span className="hidden text-xs text-slate-500 sm:block">
              {user?.display_name}
              {!loginRequired && ' (giriş kapalı)'}
            </span>
            <NavLink
              to="/giris"
              className="rounded-lg border border-slate-800 px-3 py-1.5 text-xs text-slate-400 transition hover:border-slate-700 hover:text-slate-200"
            >
              Giriş
            </NavLink>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        <Routes>
          <Route
            path="/"
            element={
              <RequireAuth>
                <Dashboard />
              </RequireAuth>
            }
          />
          <Route
            path="/laboratuvar"
            element={
              <RequireAuth>
                <ProblemLab />
              </RequireAuth>
            }
          />
          <Route
            path="/laboratuvar/:problemId"
            element={
              <RequireAuth>
                <ProblemLab />
              </RequireAuth>
            }
          />
          <Route
            path="/isler/:jobId"
            element={
              <RequireAuth>
                <JobDetail />
              </RequireAuth>
            }
          />
          <Route path="/ogren" element={<Learn />} />
          <Route path="/yol-haritasi" element={<Roadmap />} />
          <Route path="/giris" element={<Login />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <footer className="border-t border-slate-800 py-6">
        <div className="mx-auto max-w-7xl px-4 text-xs leading-relaxed text-slate-600">
          Quantum Bridge, eğitim ve erken aşama tanıtım amaçlı bir simülasyondur. Kuantum
          hesaplama burada klasik bir iş akışının ortasındaki özel bir durak olarak modellenir.
          Gerçek donanım henüz bağlı değildir; bağlanacağı yer yol haritası sayfasında yazılıdır.
        </div>
      </footer>
    </div>
  );
}
