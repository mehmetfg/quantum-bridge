# Kavramlar

Bu dosya, uygulamadaki **Öğren** sayfasının yazılı hali ve biraz fazlasıdır.
Terimler İngilizce karşılıklarıyla birlikte verilir, çünkü kaynakların çoğu İngilizcedir
ve terimi tanımak arama yapabilmek demektir.

---

## 1. Kubit (qubit)

Klasik bir bit ya 0 ya 1 değerindedir. Kubit ise ölçülene kadar iki değerin bir
karışımı halinde durabilir. Bu karışım "bilinmiyor" anlamında bir belirsizlik değildir;
matematiksel olarak tam tanımlı bir durumdur. Her seçeneğin bir **genliği** (amplitude)
vardır ve genlik karmaşık bir sayıdır.

**Yaygın yanlış:** "Kubit aynı anda hem 0 hem 1 tutar, yani iki kat bilgi taşır."

**Doğrusu:** Bir kubitten okunabilecek bilgi yine tek bir bittir. Ölçüm yaptığınızda
ya 0 ya 1 alırsınız. Kazanç bilgiyi saklamakta değil, ölçümden önceki ara hesaptadır.

---

## 2. Süperpozisyon (superposition)

Hadamard kapısı bir kubiti sıfır ve bir durumlarının eşit karışımına sokar:

```
|0>  --H-->  (|0> + |1>) / karekök 2
```

n kubit süperpozisyona sokulduğunda sistem 2 üzeri n farklı durumu aynı anda temsil
eder. Üç kubit sekiz durumu, on kubit bin yirmi dört durumu temsil eder.

Burada dikkatli olmak gerekir: bu durumların hepsini **okuyamazsınız**. Ölçüm tek bir
sonuç verir. Algoritmanın işi, ölçümden önce doğru cevabın olasılığını yükseltmektir.

---

## 3. Ölçüm (measurement)

Ölçüm, kuantum durumunu klasik bitlere çökerten geri dönüşsüz bir işlemdir. Hangi
sonucun çıkacağı, o durumun genliğinin karesinin büyüklüğüyle belirlenen olasılığa
bağlıdır.

Ölçümden sonra ara durum bilgisi geri getirilemez. Bu yüzden kuantum programlamada
ölçüm her zaman en sondadır.

Bu uygulamada durum vektörünü tablo olarak görebiliyorsunuz. **Gerçek donanımda bu
mümkün değildir.** Görebiliyoruz çünkü sayıları biz hesaplıyoruz. Simülatörün en
değerli tarafı budur ve aynı zamanda en büyük yanıltıcılığıdır.

---

## 4. Atış (shot)

Bir atış, devrenin bir kez çalıştırılıp bir kez ölçülmesidir. Tek bir atış, olasılık
dağılımından tek bir örnektir.

Dağılımı görebilmek için devre yüzlerce kez çalıştırılır. Hassasiyet, atış sayısının
kareköküyle artar:

| Atış sayısı | Yaklaşık istatistik belirsizlik |
|---|---|
| 100 | yüzde 10 |
| 1.024 | yüzde 3,1 |
| 10.000 | yüzde 1 |
| 1.000.000 | yüzde 0,1 |

Hatayı yarıya indirmek için atış sayısını **dörde katlamak** gerekir. Bu, kuantum
hesaplamanın sessiz ama gerçek maliyet kalemidir.

---

## 5. Dolanıklık (entanglement)

İki veya daha çok kubit, birbirinden bağımsız tarif edilemez hale gelebilir. Dolanık
kubitlerde:

- Tek tek her birinin sonucu rastgeledir, yarı yarıya dağılır.
- Buna rağmen aralarındaki ilişki kesindir.

Bell durumunu üreten devre şudur:

```
q[0] --H--•--
          |
q[1] -----X--
```

Sonuç ya `00` ya `11` olur, hiçbir zaman `01` veya `10` olmaz. Ama hangisinin çıkacağı
önceden bilinemez.

**Klasik benzetme ve neden yetersiz kaldığı:** İki zarfa aynı rengi koyup uzağa
göndermek klasik korelasyondur; renk baştan bellidir. Dolanıklıkta renk ölçüm anında
belirlenir, yine de iki taraf uyuşur. Bu farkın deneysel olarak kanıtlanması 2022
Nobel Fizik Ödülü'nü kazandı.

---

## 6. Girişim (interference)

Kuantum algoritmalarının çalışma sebebi budur ve en az anlaşılan kavramdır.

Genlikler negatif ve karmaşık olabilir. Toplandıklarında birbirlerini **yok edebilirler**.
Klasik olasılıklarda böyle bir şey olmaz: olasılıklar hep pozitiftir, toplandıkça büyürler.

Bir algoritma şunu yapar: yanlış cevapların genliklerini birbirini götürecek şekilde
düzenler, doğru cevabın genliğini büyütür. Ölçüm yapıldığında doğru cevap yüksek
olasılıkla çıkar.

Deutsch-Jozsa algoritmasında bunu doğrudan görürsünüz: sabit fonksiyonda tüm olasılık
sıfır dizgisinde toplanır, dengeli fonksiyonda sıfır dizgisinin genliği tamamen yok olur.

---

## 7. Oracle

Algoritma, aradığı bilgiyi doğrudan görmez. Bilgi, kapıların yerleşimine gömülmüş
halde sorgulanır. Bu gömülü yapıya oracle denir.

Örnek: Bernstein-Vazirani'de gizli dizi `1011` ise, oracle içinde 0, 2 ve 3 numaralı
kubitlerden yardımcı kubite giden CNOT kapıları bulunur. Algoritma bu yerleşimi
göremez, sadece sonucunu sorgular.

---

## 8. Faz geri tepmesi (phase kickback)

Yardımcı bir kubit `(|0> - |1>) / karekök 2` durumuna hazırlanırsa, ona uygulanan
kontrollü NOT kapısı hedefi değiştirmek yerine **kontrol kubitinin fazını** değiştirir.

Bilgi böylece okunabilir bitlerden faza taşınır. Faz doğrudan okunamaz, ama Hadamard
kapıları fazı tekrar okunabilir bitlere çevirir.

Deutsch-Jozsa ve Bernstein-Vazirani'nin tek sorguda çalışmasının sebebi bu numaradır.

---

## 9. Genlik yükseltme (amplitude amplification)

Grover algoritmasının özüdür. İki adımın tekrarıdır:

1. **Oracle:** aranan cevabın genliğinin işaretini çevirir.
2. **Yayıcı (diffuser):** ortalamaya göre yansıtır; işaretli genlik büyür, diğerleri küçülür.

En iyi tekrar sayısı yaklaşık `pi / 4 × karekök(N)` kadardır.

**Yaygın yanlış:** "Daha çok tekrar daha iyi sonuç verir."

**Doğrusu:** Grover salınımlıdır. Sekiz öğelik bir listede başarı oranı:

| Tekrar | Başarı olasılığı |
|---|---|
| 0 | yüzde 12,5 |
| 1 | yüzde 78,1 |
| 2 | yüzde 94,5 |
| 3 | yüzde 33,0 |
| 4 | yüzde 1,2 |
| 5 | yüzde 54,8 |
| 6 | yüzde 100 |

Bu değerler `sin kare((2k artı 1) çarpı teta)` formülünden gelir; burada teta,
`arcsin(1 / karekök 8)` değeridir. Uygulamadaki simülatör tam olarak bu sayıları üretir,
kendiniz doğrulayabilirsiniz.

En iyi değer olan 2 aşılırsa başarı düşer, 4 tekrarda neredeyse sıfıra iner, sonra tam
tur tamamlanınca yeniden yükselir. Uygulamada tekrar sayısını elle değiştirerek bu
salınımı görebilirsiniz.

---

## 10. Transpile (transpilation)

Devrenin hedef donanıma uygun ve mümkün olduğunca kısa hale getirilmesidir. Dört iş
yapar:

1. **Sadeleştirme:** birbirini götüren kapıları silmek, açıları birleştirmek.
2. **Kapı çevirimi:** devreyi donanımın desteklediği kapı kümesine indirmek.
3. **Yerleştirme (layout):** mantıksal kubitleri fiziksel kubitlere atamak.
4. **Yönlendirme (routing):** komşu olmayan kubitler arasına SWAP kapıları eklemek.

Bu projede birinci ve dördüncüsü uygulanır, dördüncüsü rapor olarak gösterilir.

Her silinen kapı, gerçek donanımda daha az hata demektir.

---

## 11. Gürültü (noise) ve dekoherans (decoherence)

Gerçek kuantum bilgisayarlar mükemmel değildir. Üç ana hata kaynağı vardır:

- **Kapı hatası:** uygulanan kapı tam olarak istenen dönüşümü yapmaz. İki kubitlik
  kapıların hata oranı tek kubitliklerden yaklaşık on kat yüksektir.
- **Ölçüm hatası:** kubit 0 iken 1 okunur veya tersi.
- **Dekoherans:** kubit çevresiyle etkileştiği için zamanla durumunu kaybeder.
  Devre ne kadar derinse etkisi o kadar büyüktür.

Bugünün cihazlarında gürültü, kuantum avantajının önündeki temel engeldir. Hata
düzeltme (error correction) bu yüzden başlı başına bir araştırma alanıdır.

Uygulamada gürültü seviyesini değiştirip aynı işi tekrar çalıştırın. Aradaki farkı
görmek, bu paragrafı okumaktan daha öğreticidir.

---

## 12. Hibrit hesaplama (hybrid computing)

Bugün gerçekçi olan model budur. Klasik sistem ve yapay zeka işin büyük kısmını yapar;
yalnızca kuantumun avantajlı olduğu küçük alt problem kuantuma gönderilir.

**Yaygın yanlış:** "Kuantum bilgisayar klasik bilgisayarın yerini alacak."

**Doğrusu:** Kuantum genel amaçlı bir hızlandırıcı değildir. Sadece belirli problem
sınıflarında avantajlıdır: arama, faktörleme, bazı optimizasyon problemleri ve kuantum
sistemlerinin simülasyonu. Metin işleme, veritabanı sorgusu veya web sunucusu gibi
işlerde hiçbir avantajı yoktur.

Bu uygulamadaki altı aşamalı boru hattı tam olarak bu modeli gösterir: altı adımdan
yalnızca biri kuantum tarafındadır.
