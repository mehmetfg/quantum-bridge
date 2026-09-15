# Gerçek donanıma geçiş

Bu uygulama bir simülasyondur ve öyle olduğunu saklamaz. Bu dosya, altyapı kavrandıktan
sonra gerçek yolun nereden geçtiğini adım adım yazar.

Her adımda **hangi dosyanın değişeceği** belirtilmiştir. Belirsiz bir gelecek planı
plan sayılmaz.

---

## Adım 1: Qiskit Aer (yerel, endüstri standardı simülatör)

Qiskit Aer, IBM'in açık kaynaklı simülatörüdür. Gerçek cihazların gürültü profilleriyle
çalıştırılabildiği için donanıma geçmeden önceki son duraktır.

**Kurulum**

```bash
cd backend
uv add qiskit qiskit-aer
```

**Uygulama adımları**

1. `Circuit` nesnesini `qiskit.QuantumCircuit`'e çevirin. En kolay yol, zaten
   ürettiğimiz OpenQASM 3 metnini okumaktır:

   ```python
   from qiskit.qasm3 import loads
   from app.quantum.qasm import to_qasm3

   qc = loads(to_qasm3(circuit, include_comments=False))
   ```

2. `AerSimulator(method="statevector")` oluşturun. İsterseniz bir cihazın gürültü
   modelini yükleyin.

3. `transpile(qc, simulator)` çağırın, sonra `simulator.run(qc, shots=shots)` çalıştırın.

4. `result.get_counts()` çıktısını `RawResult.counts` alanına yerleştirin.

**Dikkat: bit sırası**

Qiskit kubit 0'ı **en sağdaki** bit olarak yazar, bu proje **en soldaki** bit olarak
yazar. Çevirirken dizgiyi ters çevirmek gerekir:

```python
counts = {bits[::-1]: count for bits, count in result.get_counts().items()}
```

Bu, kuantum programlamada en sık yapılan hatalardan biridir ve sessizce yanlış sonuç
üretir. Testlerinizde mutlaka asimetrik bir durum kullanın; örneğin sadece bir kubite
X kapısı uygulayıp sonucun beklenen konumda çıktığını doğrulayın.

**Doğrulama**

Kendi simülatörümüzle Aer'i aynı devrede karşılaştırın. `tests/test_quantum_core.py`
içindeki testleri iki arka uçla da çalıştırmak, çevirimin doğruluğunu kanıtlar.

**Değişecek dosya:** `backend/app/quantum/backends/qiskit_stub.py` içindeki
`QiskitAerBackend` sınıfı. İskelet ve adımlar orada yorumlanmış halde bekliyor.

---

## Adım 2: IBM Quantum Runtime (gerçek donanım)

Buradan sonrası artık simülasyon değildir.

**Kurulum**

```bash
uv add qiskit-ibm-runtime
export QISKIT_IBM_TOKEN="..."   # anahtar asla depoya yazılmaz
```

**Uygulama adımları**

1. IBM Quantum hesabı açın ve API anahtarını `QISKIT_IBM_TOKEN` ortam değişkenine koyun.
   Anahtarı koda veya depoya yazmayın; `.env` dosyası zaten `.gitignore` içindedir.

2. Bağlanın ve en az meşgul cihazı seçin:

   ```python
   from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

   service = QiskitRuntimeService()
   backend = service.least_busy(operational=True, simulator=False)
   ```

3. Devreyi cihazın bağlantı haritasına göre transpile edin. **Burası önemlidir:** bu
   projedeki `transpiler.routing_report()` fonksiyonu tam olarak bu maliyeti sembolik
   olarak anlatır. Gerçek çipte komşu olmayan kubitler arasına SWAP kapıları eklenir ve
   devre uzar.

4. `SamplerV2(mode=backend)` ile işi gönderin. İş bir kuyruğa girer.

5. Sonuç geldiğinde sayımları `RawResult`'a doldurun.

**Gerçekçi beklenti**

- Kuyrukta bekleme süresi, çalışma süresinden kat kat uzundur. Dakikalar, bazen saatler.
- Sonuçlar gürültülüdür. Bu projedeki küçük devreler çalışır ama simülasyondaki kadar
  temiz olmaz.
- Gerçek cihazda durum vektörü **okunamaz**. Sadece ölçüm sayımları alınır. Arayüzdeki
  durum vektörü tablosu bu arka uçta gizlenmelidir.
- Ücretsiz katmanda aylık çalıştırma süresi sınırlıdır.

Simülasyon ile gerçek sonuç arasındaki farkı görmek, hata düzeltmenin (error correction)
neden bu kadar önemli olduğunu anlamanın en hızlı yoludur.

**Değişecek dosya:** `backend/app/quantum/backends/qiskit_stub.py` içindeki
`IBMQuantumRuntimeBackend` sınıfı.

---

## Alternatif: Amazon Braket

IBM yerine AWS üzerinden farklı donanım ailelerine (IonQ'nun tuzaklı iyon cihazları,
Rigetti'nin süperiletken cihazları) erişmek isterseniz:

```bash
uv add amazon-braket-sdk
```

Arayüz farklıdır ama `QuantumBackend` sözleşmesi aynı kaldığı için boru hattı yine
değişmez. Yeni bir sınıf yazıp `registry.py` dosyasına kaydetmek yeterlidir.

Tuzaklı iyon cihazlarının avantajı, tüm kubitlerin birbiriyle doğrudan etkileşebilmesidir;
yani SWAP maliyeti yoktur. Dezavantajı daha yavaş olmalarıdır. Bu takası görmek,
donanım seçiminin neden probleme bağlı olduğunu anlatır.

---

## Adım 3: Dil modeli yönlendirici

Kural tabanlı yönlendiricinin kararlarını doğal dille açıklamak, ileride serbest metinden
problem anlamak.

**Kurulum**

```bash
uv add anthropic
export ANTHROPIC_API_KEY="..."
```

**Önemli kısıt**

Dil modeli kararı **değiştirmez**, sadece açıklar. Kararların tekrarlanabilir kalması,
açıklamanın akıcılığından daha değerlidir. Bir eğitim aracında "neden böyle oldu"
sorusunun cevabı her seferinde aynı olmalıdır.

Sistem anahtar yoksa sessizce kural tabanlı çalışmaya devam eder. Dil modeli bir süs
katmanıdır; sistemin çalışması ona bağlı değildir.

**Değişecek dosya:** `backend/app/ai/llm_adapter.py`

---

## Adım 4: Giriş ve kalıcı veri

**Giriş**

Kimlik kavramı baştan yerleştirildi, bu yüzden geçiş ucuzdur:

1. Kullanıcı tablosu ve parola özeti (hash) için bir veritabanı ekleyin.
2. Giriş uç noktası ekleyin, başarılı girişte JWT üretin.
3. `backend/app/api/auth.py` içindeki `get_current_user` fonksiyonunu, Authorization
   başlığındaki jetonu doğrulayacak şekilde değiştirin. **Uç noktaların imzaları
   değişmez.**
4. Ön yüzde `frontend/src/auth/AuthContext.tsx` içindeki `login` fonksiyonu gerçekten
   jeton alsın. `RequireAuth` sarmalayıcısı zaten yerinde, koşul kendiliğinden devreye
   girer.
5. `/giris` sayfasındaki form etkinleştirilsin; yeni sayfa yazmak gerekmez.

**Kalıcı veri**

İşler şu an süreç belleğinde tutulur. Kalıcı veritabanına geçmek için değiştirilmesi
gereken tek dosya `backend/app/core/job_store.py` dosyasıdır. Boru hattı ve arayüz
`JobStore` yöntemlerini çağırır, verinin nerede durduğunu bilmez.

Her iş zaten `owner_id` alanı taşıdığı için, giriş eklendiğinde geçmiş veri bozulmaz.

---

## Adım 5: Hibrit döngü gerektiren problemler

Buraya kadar olan problemler tek yönlüdür: klasik taraf bir devre hazırlar, kuantum
çalıştırır, klasik taraf sonucu okur.

Asıl hibrit mimari, iki tarafın **defalarca gidip gelmesiyle** ortaya çıkar:

**QAOA ile küçük Max-Cut**

Bir grafı iki parçaya, kesilen kenar sayısı en çok olacak şekilde bölme problemi.
Kuantum devre parametrelidir; klasik bir iyileştirici her turda parametreleri günceller,
devre yeniden çalışır. Onlarca tur sürer.

**VQE ile küçük molekül enerjisi**

Bir molekülün en düşük enerji durumunu bulma. Kimya uygulamalarının giriş kapısıdır ve
kuantum bilgisayarların en umut verici uygulama alanı olarak görülür.

Bu iki problem, bu projedeki boru hattına döngü eklemeyi gerektirir: aşama 3'ten 5'e
kadar olan kısım tekrar tekrar çalışır. Mimari buna hazırdır çünkü her aşama ayrı bir
fonksiyondur; `pipeline.py` içine bir döngü eklemek yeterlidir.

---

## Özet tablo

| Adım | Ne | Değişecek dosya | Ek gereksinim |
|---|---|---|---|
| 1 | Qiskit Aer | `quantum/backends/qiskit_stub.py` | `qiskit`, `qiskit-aer` |
| 2 | IBM gerçek donanım | `quantum/backends/qiskit_stub.py` | `qiskit-ibm-runtime`, API anahtarı |
| 3 | Dil modeli yönlendirici | `ai/llm_adapter.py` | `anthropic`, API anahtarı |
| 4 | Giriş | `api/auth.py`, `frontend/src/auth/` | veritabanı |
| 4 | Kalıcı veri | `core/job_store.py` | veritabanı |
| 5 | QAOA ve VQE | yeni problemler, `core/pipeline.py` | yok |

---

## Bir uyarı

Bu sıra bilerek "önce öğren, sonra bağlan" şeklindedir. Gerçek donanıma erken bağlanmak
cazip gelir ama öğretici değildir: kuyrukta beklersiniz, gürültülü bir sonuç alırsınız
ve neyin neden bozulduğunu anlayamazsınız.

Simülatörde ideal sonucu görmek, sonra gürültüyü kademe kademe açmak, sonra gerçek
donanıma geçmek daha uzun yol gibi görünür. Değildir.
