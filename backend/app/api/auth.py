"""Kimlik doğrulama: şimdilik doğrudan giriş, yeri ileriye hazır.

Şu an giriş ekranı yok ve olmaması bilinçli bir karar. Demo sırasında
kimsenin hesap açmasını beklemek istemiyoruz.

Buna karşılık kimlik kavramı sisteme baştan yerleştirildi: her iş bir
sahip kimliği taşır ve her uç nokta kullanıcıyı bu bağımlılık üzerinden
alır. Giriş özelliği eklendiğinde değişecek tek yer bu dosyadır;
uç noktaların imzaları aynı kalır.

Giriş eklemek için yapılacaklar:
    1. Kullanıcı tablosu ve parola özeti (hash) için bir veritabanı ekle.
    2. Giriş uç noktası ekle, başarılı girişte JWT üret.
    3. Aşağıdaki get_current_user fonksiyonunu, Authorization başlığındaki
       jetonu doğrulayacak şekilde değiştir.
    4. İş listeleme sorgularını sahibe göre filtrele; altyapısı hazır.
"""

from __future__ import annotations

from fastapi import Header

from ..core.models import User

DEMO_USER = User(id="demo", display_name="Demo Kullanıcı", is_demo=True)


async def get_current_user(authorization: str | None = Header(default=None)) -> User:
    """Geçerli kullanıcıyı döndürür.

    Şu anki davranış: her istek demo kullanıcısı olarak kabul edilir.
    Authorization başlığı okunur ama henüz doğrulanmaz; ileride jeton
    doğrulaması tam olarak buraya gelecek.
    """
    return DEMO_USER


def auth_status() -> dict:
    """Arayüzün giriş durumunu öğrenmek için kullandığı bilgi."""
    return {
        "mode": "dogrudan-giris",
        "login_required": False,
        "user": DEMO_USER.model_dump(),
        "note": (
            "Giriş özelliği henüz açık değil. Sistem tek bir demo kullanıcısıyla "
            "çalışıyor ama iş kayıtları baştan sahip bilgisi taşıyor, bu yüzden "
            "giriş eklendiğinde geçmiş veriler bozulmayacak."
        ),
    }
