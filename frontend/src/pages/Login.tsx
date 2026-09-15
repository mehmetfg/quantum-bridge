/**
 * Giriş sayfası: şimdilik yer tutucu.
 *
 * Giriş özelliği kapalı ve bu bilinçli bir karar: demo sırasında kimsenin
 * hesap açmasını beklemek istemiyoruz. Sayfa yine de var, çünkü rota,
 * form yerleşimi ve yönlendirme mantığı hazır dursun istiyoruz. Giriş
 * açıldığında bu dosyadaki formun gerçekten jeton alması yeterli olacak.
 */

import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '../auth/AuthContext';

export default function Login() {
  const { user, loginRequired, note } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="mx-auto max-w-md space-y-5">
      <div className="card">
        <h1 className="text-lg font-bold text-slate-100">Giriş</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-400">
          Giriş özelliği henüz açık değil. Uygulama şu an doğrudan açılıyor ve tek bir demo
          kullanıcısıyla çalışıyor.
        </p>

        <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/60 p-3">
          <p className="text-xs uppercase tracking-wide text-slate-500">Geçerli kullanıcı</p>
          <p className="mt-1 text-sm font-semibold text-slate-200">{user?.display_name}</p>
          <p className="mt-0.5 font-mono text-xs text-slate-500">{user?.id}</p>
        </div>

        {note && <p className="mt-3 text-xs leading-relaxed text-slate-500">{note}</p>}

        <fieldset disabled className="mt-5 space-y-3 opacity-50">
          <div>
            <label className="label" htmlFor="email">
              E-posta
            </label>
            <input id="email" type="email" className="input" placeholder="ornek@ornek.com" />
          </div>
          <div>
            <label className="label" htmlFor="password">
              Parola
            </label>
            <input id="password" type="password" className="input" placeholder="••••••••" />
          </div>
          <button type="button" className="btn-primary w-full">
            Giriş yap (yakında)
          </button>
        </fieldset>

        <button
          type="button"
          onClick={() => navigate('/')}
          className="btn-ghost mt-4 w-full"
        >
          {loginRequired ? 'Geri dön' : 'Demo kullanıcıyla devam et'}
        </button>
      </div>

      <div className="card">
        <h2 className="mb-2 text-sm font-semibold text-slate-200">
          Giriş açıldığında ne değişecek
        </h2>
        <ul className="space-y-1.5 text-xs leading-relaxed text-slate-400">
          <li>· Arka uçta kimlik doğrulaması tek bir bağımlılık fonksiyonuna eklenecek</li>
          <li>· Uç noktaların imzaları değişmeyecek, çünkü kullanıcı zaten oradan alınıyor</li>
          <li>· İş kayıtları baştan sahip bilgisi taşıdığı için geçmiş veri bozulmayacak</li>
          <li>· Bu sayfadaki form etkinleşecek, yeni sayfa yazmak gerekmeyecek</li>
        </ul>
        <p className="mt-3 text-xs text-slate-500">
          Ayrıntılı sıra{' '}
          <Link to="/yol-haritasi" className="text-sky-400 hover:text-sky-300">
            yol haritası
          </Link>{' '}
          sayfasının beşinci adımında.
        </p>
      </div>
    </div>
  );
}
