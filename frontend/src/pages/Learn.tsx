/**
 * Öğren sayfası: kavram kartları.
 *
 * Buradaki metinler docs/01-kavramlar.md ile aynı çizgide tutulur. Amaç,
 * laboratuvarda karşılaşılan terimlerin tek bir yerde açıklanmasıdır.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';

import { cx } from '../lib/style';

interface Concept {
  term: string;
  english: string;
  short: string;
  detail: string;
  wrong?: string;
  category: 'temel' | 'algoritma' | 'donanım';
}

const CONCEPTS: Concept[] = [
  {
    term: 'Kubit',
    english: 'qubit',
    category: 'temel',
    short: 'Kuantum bilgisinin en küçük birimi.',
    detail:
      'Klasik bir bit ya 0 ya 1 değerindedir. Kubit ise ölçülene kadar iki değerin bir karışımı halinde durabilir. Bu karışım rastgelelik değil, matematiksel olarak tanımlı bir durumdur: her seçeneğin bir genliği vardır.',
    wrong:
      'Yaygın yanlış: kubit aynı anda hem 0 hem 1 tutar, yani iki kat bilgi taşır. Doğrusu, bir kubitten okunabilecek bilgi yine tek bir bittir. Kazanç bilgiyi saklamakta değil, ara hesapta.',
  },
  {
    term: 'Süperpozisyon',
    english: 'superposition',
    category: 'temel',
    short: 'Bir kubitin birden fazla temel durumun karışımı halinde bulunması.',
    detail:
      'Hadamard kapısı bir kubiti sıfır ve bir durumlarının eşit karışımına sokar. n kubit süperpozisyona sokulduğunda sistem 2 üzeri n farklı durumu aynı anda temsil eder. Algoritmalar bu genişliği kullanır.',
  },
  {
    term: 'Ölçüm',
    english: 'measurement',
    category: 'temel',
    short: 'Kuantum durumunu klasik bitlere çökerten geri dönüşsüz işlem.',
    detail:
      'Ölçüm yapıldığında süperpozisyon kaybolur ve tek bir sonuç okunur. Hangi sonucun çıkacağı, o durumun genliğinin karesiyle belirlenen olasılığa bağlıdır. Ölçümden sonra ara durum bilgisi geri getirilemez.',
    wrong:
      'Yaygın yanlış: ölçüm yapmadan da durumu okuyabiliriz. Gerçek donanımda bu mümkün değildir. Bu uygulamada durum vektörünü görebiliyoruz çünkü sayıları biz hesaplıyoruz.',
  },
  {
    term: 'Dolanıklık',
    english: 'entanglement',
    category: 'temel',
    short: 'İki veya daha çok kubitin birbirinden bağımsız tarif edilememesi.',
    detail:
      'Dolanık kubitlerde tek tek her birinin sonucu rastgeledir ama aralarındaki ilişki kesindir. Birini ölçtüğünüzde diğerinin sonucunu da anlarsınız. Klasik bir sistemde bu iki özellik aynı anda sağlanamaz.',
  },
  {
    term: 'Atış',
    english: 'shot',
    category: 'temel',
    short: 'Devrenin bir kez çalıştırılıp bir kez ölçülmesi.',
    detail:
      'Tek bir atış, olasılık dağılımından tek bir örnektir. Dağılımı görebilmek için devre yüzlerce kez çalıştırılır. Hassasiyet atış sayısının kareköküyle artar: hatayı yarıya indirmek için atışı dörde katlamak gerekir.',
  },
  {
    term: 'Girişim',
    english: 'interference',
    category: 'algoritma',
    short: 'Genliklerin birbirini güçlendirmesi veya götürmesi.',
    detail:
      'Genlikler negatif ve karmaşık olabildiği için toplandıklarında birbirlerini yok edebilirler. Kuantum algoritmalarının çalışma sebebi budur: yanlış cevapların genlikleri götürülür, doğru cevabınki büyütülür.',
  },
  {
    term: 'Oracle',
    english: 'oracle',
    category: 'algoritma',
    short: 'Problemi devreye gömen kara kutu.',
    detail:
      'Algoritma, aradığı bilgiyi doğrudan görmez; onu kapıların yerleşimine gömülmüş halde sorgular. Deutsch-Jozsa, Bernstein-Vazirani ve Grover bu yapıyı kullanır.',
  },
  {
    term: 'Faz geri tepmesi',
    english: 'phase kickback',
    category: 'algoritma',
    short: 'Fonksiyonun cevabının genliğin işaretine yazılması.',
    detail:
      'Yardımcı bir kubit özel bir duruma hazırlandığında, kontrollü kapı hedefi değiştirmek yerine kontrol kubitinin fazını değiştirir. Bilgi böylece okunabilir bitlerden faza taşınır, sonra Hadamard ile geri okunur.',
  },
  {
    term: 'Genlik yükseltme',
    english: 'amplitude amplification',
    category: 'algoritma',
    short: 'Aranan cevabın olasılığını adım adım büyütme.',
    detail:
      'Grover algoritmasının özüdür. Oracle doğru cevabı işaretler, yayıcı adımı ortalamaya göre yansıtır. Dikkat: gereğinden fazla tekrar başarıyı düşürür, çünkü genlik hedefi aşıp geri döner.',
    wrong:
      'Yaygın yanlış: daha çok tekrar daha iyi sonuç verir. Grover salınımlıdır; en iyi tekrar sayısı aşılırsa başarı düşer.',
  },
  {
    term: 'Transpile',
    english: 'transpilation',
    category: 'donanım',
    short: 'Devreyi hedef donanıma uygun ve kısa hale getirme.',
    detail:
      'Birbirini götüren kapılar silinir, açılar birleştirilir, kapılar donanımın desteklediği kümeye çevrilir ve kubitler çipin bağlantı haritasına yerleştirilir. Her silinen kapı, daha az hata demektir.',
  },
  {
    term: 'Gürültü',
    english: 'noise',
    category: 'donanım',
    short: 'Gerçek donanımda sonucu bozan hatalar.',
    detail:
      'Üç ana kaynağı vardır: kapı hatası, ölçüm hatası ve dekoherans. Devre ne kadar derinse etkisi o kadar büyür. Bugünün cihazlarında gürültü, kuantum avantajının önündeki temel engeldir.',
  },
  {
    term: 'Dekoherans',
    english: 'decoherence',
    category: 'donanım',
    short: 'Kubitin çevresiyle etkileşerek durumunu kaybetmesi.',
    detail:
      'Kubit yalıtılmış tutulmalıdır ama mükemmel yalıtım yoktur. Belirli bir süre sonra durum bozulur. Devrenin derinliği bu süreyle yarışır: derin devreler bitmeden bozulur.',
  },
  {
    term: 'Hibrit hesaplama',
    english: 'hybrid computing',
    category: 'donanım',
    short: 'Klasik ve kuantum işlemcinin birlikte çalışması.',
    detail:
      'Bugün gerçekçi olan model budur. Klasik sistem ve yapay zeka işin büyük kısmını yapar; yalnızca kuantumun avantajlı olduğu küçük alt problem kuantuma gönderilir. Bu uygulamadaki altı aşamalı boru hattı tam olarak bunu modeller.',
    wrong:
      'Yaygın yanlış: kuantum bilgisayar klasik bilgisayarın yerini alacak. Kuantum genel amaçlı bir hızlandırıcı değildir; sadece belirli problem sınıflarında avantajlıdır.',
  },
];

const CATEGORIES = [
  { id: 'hepsi', label: 'Hepsi' },
  { id: 'temel', label: 'Temel olgular' },
  { id: 'algoritma', label: 'Algoritma' },
  { id: 'donanım', label: 'Donanım' },
] as const;

export default function Learn() {
  const [filter, setFilter] = useState<string>('hepsi');
  const visible = CONCEPTS.filter((c) => filter === 'hepsi' || c.category === filter);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-slate-100">Kavramlar</h1>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-400">
          Laboratuvarda karşılaştığınız terimlerin karşılığı. Her kart kısa tanımla başlar,
          ardından ayrıntıya iner. Bazı kartlarda yaygın yanlış anlamalar ayrıca işaretlenmiştir,
          çünkü bu konuda yanlış öğrenmek, hiç öğrenmemekten daha çok yavaşlatır.
        </p>
      </header>

      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((category) => (
          <button
            key={category.id}
            type="button"
            onClick={() => setFilter(category.id)}
            className={cx(
              'rounded-lg px-3 py-1.5 text-sm font-medium transition',
              filter === category.id
                ? 'bg-slate-800 text-slate-100'
                : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200',
            )}
          >
            {category.label}
          </button>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {visible.map((concept) => (
          <article key={concept.term} className="card">
            <div className="mb-2 flex flex-wrap items-baseline gap-2">
              <h2 className="text-base font-semibold text-slate-100">{concept.term}</h2>
              <span className="font-mono text-xs text-slate-500">({concept.english})</span>
            </div>
            <p className="mb-2 text-sm font-medium text-slate-300">{concept.short}</p>
            <p className="text-xs leading-relaxed text-slate-400">{concept.detail}</p>
            {concept.wrong && (
              <p className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-xs leading-relaxed text-amber-200/80">
                {concept.wrong}
              </p>
            )}
          </article>
        ))}
      </div>

      <div className="card">
        <p className="text-sm text-slate-400">
          Kavramları çalışırken görmek en hızlı yol.{' '}
          <Link to="/laboratuvar" className="text-sky-400 hover:text-sky-300">
            Laboratuvarda
          </Link>{' '}
          bir problem çalıştırıp her aşamanın gerekçesini okuyabilirsiniz.
        </p>
      </div>
    </div>
  );
}
