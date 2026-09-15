/**
 * Yol haritası: altyapı kavrandıktan sonra gerçek yolun nereden geçtiği.
 *
 * Bu sayfa tanıtım için önemli. "Sonra gerçek donanıma geçilir" demek yerine,
 * geçişin hangi dosyada ve hangi adımlarla olacağını açıkça gösterir.
 */

import { useEffect, useState } from 'react';

import { api } from '../api/client';
import { cx } from '../lib/style';
import type { BackendInfo } from '../types';

interface Phase {
  order: number;
  title: string;
  status: 'tamam' | 'sırada' | 'sonra';
  summary: string;
  items: string[];
  where?: string;
}

const PHASES: Phase[] = [
  {
    order: 1,
    title: 'Altyapıyı kavramak',
    status: 'tamam',
    summary:
      'Simülasyon üzerinden hibrit boru hattının her adımını görünür kılmak. Bu aşamanın çıktısı bu uygulamadır.',
    items: [
      'Kendi yazdığımız durum vektörü simülatörü, kara kutu değil',
      'Altı aşamalı boru hattı ve her aşama için gerekçe metni',
      'Beş problem: rastgele sayı, dolanıklık, Deutsch-Jozsa, Bernstein-Vazirani, Grover',
      'Devre sadeleştirme, gürültü modeli ve OpenQASM 3 çıktısı',
    ],
  },
  {
    order: 2,
    title: 'Endüstri standardı simülatöre geçmek',
    status: 'sırada',
    summary:
      'Qiskit Aer, IBM cihazlarının gerçek gürültü profilleriyle çalışabilir. Donanıma gitmeden önceki son duraktır.',
    items: [
      'Kurulum: uv add qiskit qiskit-aer',
      'Devre çevirimi zaten ürettiğimiz OpenQASM 3 metni üzerinden yapılır',
      'Bit sırası bu projeye göre ters olduğu için çevirimde dizgi çevrilir',
      'Kendi simülatörümüzle sonuçlar karşılaştırılarak doğrulama yapılır',
    ],
    where: 'backend/app/quantum/backends/qiskit_stub.py içindeki QiskitAerBackend',
  },
  {
    order: 3,
    title: 'Gerçek kuantum donanımına bağlanmak',
    status: 'sonra',
    summary:
      'IBM Quantum Runtime üzerinden bulut cihazına iş göndermek. Buradan sonrası artık simülasyon değildir.',
    items: [
      'IBM Quantum hesabı ve QISKIT_IBM_TOKEN ortam değişkeni, anahtar asla depoya yazılmaz',
      'Cihazın bağlantı haritasına göre transpile, SWAP maliyeti burada gerçek olur',
      'İş bir kuyruğa girer; bekleme süresi çalışma süresinden kat kat uzundur',
      'Sonuçlar gürültülü gelir, aradaki fark hata düzeltmenin neden gerekli olduğunu gösterir',
    ],
    where: 'backend/app/quantum/backends/qiskit_stub.py içindeki IBMQuantumRuntimeBackend',
  },
  {
    order: 4,
    title: 'Yönlendiriciyi dil modeline bağlamak',
    status: 'sonra',
    summary:
      'Kural tabanlı yönlendiricinin kararlarını doğal dille açıklamak, ileride serbest metinden problem anlamak.',
    items: [
      'Kurulum: uv add anthropic ve ANTHROPIC_API_KEY ortam değişkeni',
      'Önemli kısıt: dil modeli kararı değiştirmez, sadece açıklar',
      'Kararların tekrarlanabilir kalması, açıklamanın akıcılığından daha değerlidir',
    ],
    where: 'backend/app/ai/llm_adapter.py',
  },
  {
    order: 5,
    title: 'Giriş ve kalıcı veri',
    status: 'sonra',
    summary:
      'Kullanıcı hesapları ve iş geçmişinin kalıcı saklanması. Altyapısı baştan hazır bırakıldı.',
    items: [
      'Her iş zaten bir sahip kimliği taşıyor, geçmiş veri bozulmayacak',
      'Arka uçta değişecek tek yer get_current_user bağımlılığı',
      'Arayüzde değişecek tek yer AuthContext ve RequireAuth',
      'Bellek içi iş deposu kalıcı veritabanıyla değiştirilir',
    ],
    where: 'backend/app/api/auth.py ve frontend/src/auth/',
  },
  {
    order: 6,
    title: 'Hibrit döngü gerektiren problemler',
    status: 'sonra',
    summary:
      'Klasik ve kuantum tarafın tek seferlik değil, defalarca gidip gelerek çalıştığı algoritmalar.',
    items: [
      'QAOA ile küçük Max-Cut: klasik iyileştirici, kuantum devreyi her turda yeniden ayarlar',
      'VQE ile küçük molekül enerjisi: kimya uygulamalarının giriş kapısı',
      'Bu problemler, hibrit mimarinin asıl gücünü gösterir',
    ],
  },
];

const STATUS_STYLE: Record<Phase['status'], string> = {
  tamam: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
  sırada: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
  sonra: 'bg-slate-700/40 text-slate-400 border-slate-700',
};

export default function Roadmap() {
  const [backends, setBackends] = useState<BackendInfo[]>([]);

  useEffect(() => {
    api
      .backends()
      .then((data) => setBackends(data.backends))
      .catch(() => undefined);
  }, []);

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-bold text-slate-100">Yol haritası</h1>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-400">
          Bu uygulama bir simülasyondur ve öyle olduğunu saklamaz. Aşağıda, altyapı
          kavrandıktan sonra gerçek yolun nereden geçtiği yazılı. Her adımda hangi dosyanın
          değişeceği de belirtildi, çünkü belirsiz bir gelecek planı plan sayılmaz.
        </p>
      </header>

      <section className="space-y-4">
        {PHASES.map((phase) => (
          <article
            key={phase.order}
            className={cx(
              'card',
              phase.status === 'tamam' && 'border-emerald-500/30',
              phase.status === 'sırada' && 'border-amber-500/30',
            )}
          >
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-800 text-xs font-bold text-slate-300">
                {phase.order}
              </span>
              <h2 className="text-base font-semibold text-slate-100">{phase.title}</h2>
              <span className={cx('chip border', STATUS_STYLE[phase.status])}>{phase.status}</span>
            </div>
            <p className="mb-3 text-sm leading-relaxed text-slate-400">{phase.summary}</p>
            <ul className="space-y-1.5">
              {phase.items.map((item, index) => (
                <li key={index} className="flex gap-2 text-xs leading-relaxed text-slate-400">
                  <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-slate-600" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            {phase.where && (
              <p className="mt-3 border-t border-slate-800 pt-2 font-mono text-[11px] text-slate-500">
                Değişecek yer: {phase.where}
              </p>
            )}
          </article>
        ))}
      </section>

      {backends.length > 0 && (
        <section>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
            Arka uçların bugünkü durumu
          </h2>
          <div className="grid gap-3 md:grid-cols-3">
            {backends.map((backend) => (
              <div
                key={backend.id}
                className={cx('card', backend.available ? 'border-emerald-500/30' : 'opacity-70')}
              >
                <div className="mb-2 flex items-start justify-between gap-2">
                  <h3 className="text-sm font-semibold leading-tight text-slate-100">
                    {backend.name}
                  </h3>
                  <span
                    className={cx(
                      'chip shrink-0',
                      backend.available
                        ? 'bg-emerald-500/15 text-emerald-300'
                        : 'bg-slate-700/50 text-slate-400',
                    )}
                  >
                    {backend.available ? 'hazır' : 'yakında'}
                  </span>
                </div>
                <p className="mb-2 text-xs leading-relaxed text-slate-400">
                  {backend.description}
                </p>
                <p className="text-[11px] text-slate-500">
                  {backend.kind === 'hardware' ? 'Gerçek donanım' : 'Simülatör'} · en fazla{' '}
                  {backend.max_qubits} kubit
                </p>
                <ul className="mt-2 space-y-1">
                  {backend.notes.map((note, index) => (
                    <li key={index} className="text-[11px] leading-relaxed text-slate-500">
                      · {note}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="card border-slate-700">
        <h2 className="mb-2 text-sm font-semibold text-slate-200">Dürüst bir sınır notu</h2>
        <p className="text-sm leading-relaxed text-slate-400">
          Bu simülatör en fazla on iki kubit çalıştırır ve bu bir eksiklik değil, fiziğin
          kendisidir: n kubit klasik bellekte 2 üzeri n genlik demektir. Elli kubitin ötesinde
          gereken bellek, dünyadaki tüm bilgisayarların toplamını aşar. Kuantum bilgisayarın
          varlık sebebi tam olarak bu eşiktir. Buradaki küçük devreler gerçek donanımda da
          çalışır; fark, sonuçların gürültülü gelmesidir.
        </p>
      </section>
    </div>
  );
}
