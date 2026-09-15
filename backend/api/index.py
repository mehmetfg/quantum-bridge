"""Vercel sunucusuz (serverless) giriş noktası.

Vercel, `api/` klasöründeki dosyaları fonksiyon olarak çalıştırır. Bu dosya
ASGI uyumlu `app` nesnesini dışa aktarır; Vercel'in Python çalışma zamanı
bunu doğrudan tanır.

`vercel.json` içindeki yeniden yazma kuralı tüm istekleri bu fonksiyona
yönlendirir, böylece FastAPI kendi iç yönlendirmesini (`/api/health`,
`/api/jobs` gibi) olduğu gibi kullanabilir.

Önemli sınır: sunucusuz fonksiyonlar durumsuzdur (stateless). Bellek içi iş
deposu (`core/job_store.py`) istekler arasında güvenilir şekilde kalıcı
değildir. Bu yüzden dağıtılan sürümde iş her zaman eşzamanlı (senkron)
uç noktayla çalıştırılır; sonuç tek istekte tam olarak döner.
"""

from app.main import app  # noqa: F401
