# Mimari

Bu dosya, sistemin nasıl kurulduğunu ve neden böyle kurulduğunu anlatır.

---

## Temel fikir

Kuantum hesaplama, tek başına bir çözüm değil, klasik bir iş akışının ortasındaki özel
bir duraktır. Sistem bu fikri altı aşamalı bir boru hattı olarak kodlar:

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ 1 INTAKE     │──▶│ 2 AI_ROUTING │──▶│ 3 ENCODE     │
│   klasik     │   │   yapay zeka │   │   klasik     │
└──────────────┘   └──────────────┘   └──────┬───────┘
                                              │
                                              ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ 6 MERGE      │◀──│ 5 DECODE     │◀──│ 4 QUANTUM    │
│   klasik     │   │   klasik     │   │   kuantum    │
└──────────────┘   └──────────────┘   └──────────────┘
```

Altı adımdan yalnızca biri kuantum tarafındadır. Bu oran kasıtlı olarak görünür kılınır,
çünkü hibrit sistemlerin gerçek şekli budur.

---

## Aşamalar

### 1. INTAKE (klasik giriş)

Kullanıcı girdisi doğrulanır ve `ProblemSpec` adlı iç biçime çevrilir.

Bu adım ucuz görünür ama kritiktir. Gerçek donanımda hatalı bir iş göndermek kuyrukta
beklemek, çalışma süresi harcamak ve çoğu zaman ücret ödemek demektir. Doğrulama bu
yüzden en başta, en ucuz yerde yapılır.

**Dosya:** `backend/app/classical/preprocess.py`

### 2. AI_ROUTING (yapay zeka yönlendirme)

Problemin kuantuma uygun olup olmadığına ve hangi parametrelerle gideceğine karar
verilir: kaç kubit, kaç atış, hangi kodlama, hangi strateji.

Yönlendirici kural tabanlıdır ve bilerek tamamen şeffaftır. Her kararın gerekçesi metin
olarak üretilir. Reddedilen seçenekler de listelenir, çünkü bir yönlendiricinin dürüstlük
ölçüsü elediği seçenekleri söylemesidir.

Yönlendirici, problemden `RoutingHints` alır. Bu sayede yeni bir problem eklendiğinde
yönlendiriciyi değiştirmek gerekmez.

**Dosya:** `backend/app/ai/router.py`

### 3. ENCODE_OPTIMIZE (kodlama ve sadeleştirme)

Problem bir `Circuit` nesnesine çevrilir, transpiler ile sadeleştirilir ve OpenQASM 3
metni üretilir.

Sadeleştirme anlamsal olarak güvenlidir: çıkan devre, girenle aynı durumu üretir, sadece
daha az kapı kullanır. Üç geçiş uygulanır:

- Kendi tersi olan kapıların iptali (`H H` → hiçbir şey)
- Aynı eksendeki döndürme açılarının birleştirilmesi (`rz(0.3) rz(0.4)` → `rz(0.7)`)
- Sıfır açılı döndürmelerin atılması

Ayrıca bir yönlendirme raporu üretilir: devrede kaç adet iki kubitlik kapı, doğrusal bir
çipte komşu olmayan kubitler arasında kaç SWAP gerekirdi.

**Dosyalar:** `backend/app/quantum/transpiler.py`, `qasm.py`

### 4. QUANTUM_EXEC (kuantum çalıştırma)

Devre kuantum arka ucunda `shots` kadar çalıştırılır ve ham ölçüm sayımları toplanır.

Arka uç arayüzü (`QuantumBackend`) bilerek IBM Qiskit Runtime `Sampler` çıktısına
benzetildi: girdi bir devre ve atış sayısı, çıktı ölçüm sayımları. Böylece yerel
simülatörden gerçek donanıma geçerken boru hattının geri kalanı hiç değişmez.

**Dosyalar:** `backend/app/quantum/backends/`, `simulator.py`, `noise.py`

### 5. DECODE (çözümleme)

Ham sayımlar bir cevaba ve güven skoruna çevrilir.

Burada iki iş ayrı tutulur:
- Problemin kendi `decode` fonksiyonu cevabı çıkarır.
- `classical/postprocess.py` o cevaba ne kadar güvenilebileceğini istatistikle ölçer:
  en olası sonucun payı, ikinciyle farkı, yüzde 95 güven aralığı, entropi.

**Dosya:** `backend/app/classical/postprocess.py`

### 6. CLASSICAL_MERGE (klasik birleştirme)

Cevap klasik olarak doğrulanır ve asıl iş akışının içine yerleştirilir.

Hibrit hesaplamanın kapanış adımı budur. Kuantumdan gelen sonuç, klasik programın bir
değişkeni haline gelmedikçe hiçbir işe yaramaz.

Örnekler:
- Rastgele sayılar bir listeyi karıştırır ve tek kullanımlık şifre üretir.
- Grover'ın bulduğu adres, tek bir klasik karşılaştırmayla doğrulanır.
- Bernstein-Vazirani'nin kurtardığı dizi, bit bit gizli diziyle karşılaştırılır.

---

## Katmanlar ve sorumlulukları

| Katman | Sorumluluk | Neyi bilmez |
|---|---|---|
| `quantum/` | Kapılar, devre, simülasyon, sadeleştirme | Problemlerin ne olduğunu |
| `problems/` | Kodlama, çözümleme, birleştirme | Simülatörün nasıl çalıştığını |
| `ai/` | Hangi parça kuantuma gitmeli | Devrenin nasıl kurulduğunu |
| `classical/` | Doğrulama ve istatistik | Kuantumu |
| `core/` | Sıralama ve izleme | Problemlerin içeriğini |
| `api/` | HTTP ve canlı akış | Hesabın nasıl yapıldığını |

Bu ayrım, yeni problem eklemeyi ucuzlatmak için yapıldı.

---

## Yeni problem eklemek

`Problem` sınıfından türetin ve `registry.py` dosyasına kaydedin. Uygulamak zorunda
olduğunuz altı şey var:

```python
class YeniProblem(Problem):
    id = "yeni-problem"
    title = "..."
    # ... tanıtım alanları

    @property
    def default_input(self): ...      # arayüzün önceden dolduracağı örnek
    @property
    def input_schema(self): ...       # arayüz formu bundan üretilir
    def validate(self, raw_input): ...       # girdiyi doğrula
    def routing_hints(self, spec): ...       # yönlendiriciye ipucu ver
    def build_circuit(self, spec, n_qubits): ...   # devreyi kur
    def decode(self, raw, spec): ...         # sayımları cevaba çevir
    def merge(self, decoded, spec): ...      # klasik akışa yerleştir
```

Boru hattı, yönlendirici ve arayüz değişmez. Girdi formu bile şemadan kendiliğinden
üretilir.

---

## İzleme (trace)

Her aşama bir `TraceEvent` üretir. Bu olay şunları taşır:

- Ne yapıldı (`summary`, `details`)
- **Neden yapıldı** (`why`)
- Hangi taraf çalıştı (`side`: klasik, yapay zeka, kuantum)
- Ne kadar sürdü (`duration_ms`)
- O aşamaya özgü veri (`data`)

Arayüzdeki canlı anlatım bu olaylardan üretilir. Eğitim önceliği somut olarak burada
karşılığını bulur: sonuç kadar, sonuca nasıl varıldığı da kaydedilir.

**Dosya:** `backend/app/core/trace.py`

---

## Canlı akış (Server-Sent Events)

Boru hattı sayısal hesap yaptığı için ayrı bir iş parçacığında çalışır; aksi halde olay
döngüsünü bloke eder. Olaylar `JobEventBus` üzerinden asenkron dünyaya taşınır.

`GET /api/jobs/{id}/events` uç noktası önce halihazırda kaydedilmiş aşamaları tekrar
gönderir, sonra yeni olayları akıtır. Bu sayede istemci geç bağlansa bile hiçbir adımı
kaçırmaz.

**Dosyalar:** `backend/app/api/events.py`, `jobs.py`

---

## Uç noktalar

| Yöntem | Yol | İş |
|---|---|---|
| GET | `/api/health` | Sağlık kontrolü |
| GET | `/api/auth/status` | Giriş gerekli mi |
| GET | `/api/stages` | Altı aşamanın tanımı |
| GET | `/api/backends` | Arka uçlar, bağlı olmayanlar dahil |
| GET | `/api/problems` | Problem listesi |
| GET | `/api/problems/{id}` | Tek problem |
| POST | `/api/jobs` | Yeni iş; `?stream=true` ile arka planda |
| GET | `/api/jobs` | İş listesi |
| GET | `/api/jobs/{id}` | İş ayrıntısı |
| GET | `/api/jobs/{id}/events` | Canlı aşama akışı |

---

## Bit sırası kuralı

**Kubit 0 en soldaki bittir.** Üç kubitte `011` dizgisi `q0=0, q1=1, q2=1` demektir.

Bu seçim, devre çiziminin yukarıdan aşağıya sırası ile ölçüm dizgisinin soldan sağa
sırasının aynı kalması için yapıldı.

Qiskit bunun **tersini** kullanır. Qiskit arka ucu bağlandığında dizgiyi çevirmek
gerekecektir. Bu, kuantum programlamada en sık yapılan hatalardan biridir.

---

## Kasıtlı olarak yapılmayanlar

- **Kalıcı veritabanı yok.** İşler süreç belleğinde tutulur. Demo için kurulum
  gerektirmemesi bir avantajdır. Değişecek tek dosya `core/job_store.py`.
- **Giriş yok.** Kimlik kavramı yerinde, doğrulama kapalı. Değişecek tek dosya
  `api/auth.py`.
- **Qiskit bağımlılığı yok.** Simülatör kendimiz yazıldı ki kara kutu olmasın.
- **Dil modeli kapalı.** Kural tabanlı yönlendiricinin her kararı okunabilir ve
  tekrarlanabilir. Bu takas, altyapı kavranmadan yapılmamalıdır.

Bu kararların her biri, gerçek yola çıkarken değiştirilecek noktalar olarak
[03-gercek-donanima-gecis.md](03-gercek-donanima-gecis.md) dosyasında listelenmiştir.
