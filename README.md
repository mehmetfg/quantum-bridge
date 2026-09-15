# Quantum Bridge

Klasik bilgisayar, yapay zeka yönlendirici ve kuantum bilgisayar arasındaki köprünün
eğitim amaçlı simülasyonu. Web arayüzlü, çalışan bir erken aşama demo ürünü.

Bu proje tek bir soruyu görünür kılmak için var:

> Bir iş kuantum bilgisayara nasıl gider, oradan ne döner ve dönen şey klasik programın
> içine nasıl yerleşir?

Cevap altı aşamalı bir boru hattı olarak modellenmiştir. Altı aşamadan yalnızca biri
kuantum tarafında çalışır. Bu oran kasıtlıdır ve bugünün gerçeğini yansıtır.

```
[1] Klasik giriş        →  problem ve veri doğrulanır
[2] Yapay zeka yönlendirme →  hangi parça kuantuma gitmeli, hangi parametrelerle
[3] Kodlama ve sadeleştirme →  devre kurulur, kısaltılır, OpenQASM 3 üretilir
[4] Kuantum çalıştırma  →  devre çalışır, ham ölçüm sayımları döner   ← tek kuantum adımı
[5] Çözümleme           →  sayımlar bir cevaba ve güven skoruna çevrilir
[6] Klasik birleştirme  →  cevap doğrulanır ve asıl iş akışına girer
```

Her aşama, ne yaptığını ve **neden** yaptığını arayüzde metin olarak anlatır.
Öncelik sırası: önce öğrenmek, sonra gösterebilmek, sonra gerçek yola bağlanmak.

---

## Baştan söylenmesi gereken bir şey

Kuantum bilgisayar genel amaçlı bir hızlandırıcı **değildir**. Bir yapay zeka modelini
kuantum bilgisayarda eğitmek bugün pratik değildir, araştırma aşamasındadır.

Bugün gerçekçi olan model **hibrit hesaplamadır**: klasik sistem ve yapay zeka işin
büyük kısmını yapar, yalnızca kuantumun avantajlı olduğu küçük alt problem kuantuma
gönderilir. Bu projedeki yapay zeka katmanı, "her şeyi kuantuma gönderen" bir yapı
değil, **hangi parçanın kuantuma gitmesi gerektiğine karar veren bir yönlendiricidir**.

Bu ayrım hem doğru öğretir hem de gerçek yola daha iyi bağlanır.

---

## Kurulum ve çalıştırma

Gereksinimler: Python 3.11 veya üzeri, Node.js 20 veya üzeri, `uv` ve `pnpm`.

Tek komutla ikisini birden başlatmak için:

```bash
./scripts/dev.sh
```

Arka uç `http://127.0.0.1:8000`, ön yüz `http://localhost:5173` adresinde açılır.
API belgeleri `http://127.0.0.1:8000/docs` adresindedir.

Elle başlatmak isterseniz:

```bash
# Arka uç
cd backend
uv venv --python 3.11
uv pip install -e ".[dev]"
.venv/bin/python -m uvicorn app.main:app --reload --port 8000

# Ön yüz (ayrı bir terminalde)
cd frontend
pnpm install
pnpm dev
```

Giriş ekranı yoktur, uygulama doğrudan açılır. Bu bilinçli bir karardır: demo sırasında
kimsenin hesap açmasını beklemek istemiyoruz. Giriş altyapısı yine de yerinde duruyor,
ayrıntısı aşağıda.

---

## Beş dakikalık demo senaryosu

Tanıtımda anlatılacak sıra:

1. **Genel bakış** sayfasını açın. Altı aşamayı ve renk kodunu gösterin: mavi klasik,
   mor yapay zeka, yeşil kuantum. Tek bir yeşil kutu olduğuna dikkat çekin.

2. **Laboratuvar → Grover: sırasız listede arama**. Sekiz öğelik listeden birini seçin,
   sunum hızı açık kalsın, çalıştırın.

3. Aşamaların tek tek akışını izletin. Yapay zeka kararının gerekçesini okuyun: en iyi
   tekrar sayısı neden iki, atış sayısı neden 1024, hangi seçenekler neden elendi.
   Yönlendiricinin dürüst uyarısını gösterin: "bu ölçekte klasik çözüm daha hızlıdır".

4. **Devre çizimine** gidin. Kapıların üzerine gelerek ne yaptıklarını okuyun.
   Sadeleştirme raporunu ve komşuluk maliyetini gösterin.

5. **Ham ölçüm sonuçları**. Kuantumun bir cevap değil bir dağılım döndürdüğünü
   vurgulayın. Sarı çizgi kuramsal olasılık, çubuk gözlenen sonuç.

6. **Sonuç kartı**. Klasik doğrulamanın neden şart olduğunu anlatın: Grover en olası
   cevabı verir, kesin cevabı değil. Klasik tek bir karşılaştırma hatalı cevabı anında
   yakalar.

7. Aynı işi **gürültü seviyesi yüksek** olarak tekrar çalıştırın. Güvenin düştüğünü ve
   dağılımın dağıldığını gösterin. Hata düzeltmenin neden bir araştırma alanı olduğu
   burada kendiliğinden anlaşılır.

8. **Yol haritası** sayfasıyla kapatın: gerçek donanıma geçişin hangi dosyada, hangi
   adımlarla olacağı yazılı.

İpucu: tekrarlanabilir bir sunum için **tohum değeri** alanına sabit bir sayı yazın.
Aynı tohum her seferinde aynı sonucu üretir.

---

## Problemler

| Problem | Ne gösteriyor | Kuantum kazancı |
|---|---|---|
| Gerçek rastgele sayı üretimi | Süperpozisyon ve ölçüm | Hesaplanamayan rastgelelik |
| Dolanıklık: Bell ve GHZ | Dolanıklık ve korelasyon | Klasik üretilemeyen korelasyon |
| Deutsch-Jozsa | Girişim ve faz geri tepmesi | Üstel sorgu kazancı |
| Bernstein-Vazirani | Faz geri tepmesiyle veri kurtarma | n sorgu yerine 1 sorgu |
| Grover araması | Genlik yükseltme | Karesel hızlanma |

Yeni problem eklemek için `backend/app/problems/base.py` içindeki `Problem` sınıfından
türetip `registry.py` dosyasına kaydetmek yeterlidir. Boru hattı, arayüz ve yönlendirici
değişmez; girdi formu bile şemadan kendiliğinden üretilir.

---

## Proje yapısı

```
backend/
  app/
    quantum/      Kapılar, devre temsili, durum vektörü simülatörü, transpiler,
                  gürültü modeli, OpenQASM 3 üretimi ve arka uç adaptörleri
    problems/     Beş problem: her biri kodlama, çözümleme ve birleştirmeyi kendi bilir
    ai/           Kural tabanlı yönlendirici ve dil modeli adaptörü (şimdilik kapalı)
    classical/    Klasik ön işleme ve istatistiksel son işleme
    core/         Veri modelleri, boru hattı orkestratörü, izleme, iş deposu
    api/          FastAPI uç noktaları ve canlı olay akışı
  tests/          100 test: kuantum çekirdeği, problemler, uçtan uca API
frontend/
  src/
    pages/        Genel bakış, laboratuvar, iş ayrıntısı, öğren, yol haritası, giriş
    components/   Devre çizimi, histogram, durum vektörü, aşama çubuğu, izleme kaydı
    auth/         Kimlik bağlamı (şimdilik doğrudan giriş)
docs/             Kavramlar, mimari ve gerçek donanıma geçiş rehberi
```

---

## Simülatör hakkında dürüst notlar

- Simülatör kasıtlı olarak kendimiz yazıldı, Qiskit kullanılmadı. Sebep: öğrenmek
  için kara kutu olmaması. Her kapının duruma ne yaptığı izlenebilir.
- En fazla on iki kubit çalışır. Bu bir eksiklik değil fiziğin kendisidir: n kubit,
  klasik bellekte 2 üzeri n genlik demektir. Elli kubitin ötesinde gereken bellek
  dünyadaki tüm bilgisayarların toplamını aşar. Kuantum bilgisayarın varlık sebebi
  tam olarak bu eşiktir.
- Bit sırası kuralı: **kubit 0 en soldaki bittir**. Qiskit bunun tersini kullanır,
  çeviri yaparken dikkat gerekir. Devre çiziminin yukarıdan aşağıya sırası ile
  ölçüm dizgisinin soldan sağa sırasının aynı kalması için bu seçim yapıldı.
- Gürültü modeli fiziksel değil sembolikdir. Amacı gerçek bir çipi taklit etmek değil,
  "gürültü neden önemli" sorusunu gözle görülür kılmaktır.

---

## Giriş özelliği

Şu an kapalı. Sistem tek bir demo kullanıcısıyla çalışır. Buna karşılık kimlik kavramı
baştan yerleştirildi:

- Her iş bir sahip kimliği taşır, bu yüzden giriş eklendiğinde geçmiş veri bozulmaz.
- Arka uçta değişecek tek yer `backend/app/api/auth.py` içindeki `get_current_user`
  bağımlılığıdır. Uç noktaların imzaları değişmez.
- Arayüzde değişecek tek yer `frontend/src/auth/` altındaki bağlam ve sarmalayıcıdır.
- `/giris` sayfası ve formu zaten duruyor, sadece etkinleştirilmesi gerekir.

---

## Testler

```bash
cd backend && .venv/bin/python -m pytest      # 100 test
cd frontend && pnpm build                     # tür denetimi ve derleme
```

---

## Sonraki adımlar

Ayrıntılı sıra uygulamadaki **Yol haritası** sayfasında ve
[docs/03-gercek-donanima-gecis.md](docs/03-gercek-donanima-gecis.md) dosyasındadır.
Özetle: Qiskit Aer, sonra IBM Quantum Runtime, sonra dil modeli yönlendirici, sonra
giriş ve kalıcı veri, sonra hibrit döngü gerektiren problemler (QAOA ve VQE).

Her adımın hangi dosyayı değiştireceği yazılıdır. Belirsiz bir gelecek planı plan
sayılmaz.
