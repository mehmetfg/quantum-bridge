"""Dil modeli adaptörü: yönlendirme gerekçelerini zenginleştirmek için.

Bu dosya varsayılan olarak devre dışıdır ve öyle kalması kasıtlıdır.

Neden burada: projenin yapay zeka katmanı şu an kural tabanlı ve şeffaf.
Bu, öğrenmek için doğru seçim. Bir sonraki aşamada aynı kararların doğal
dille açıklanması, hatta problemin serbest metinden anlaşılması istenirse,
bağlanacak yer burasıdır.

Neden şu an kapalı: kural tabanlı yönlendiricinin her kararı okunabilir ve
tekrarlanabilir. Bir dil modeli devreye girdiğinde açıklama akıcılaşır ama
doğrulanabilirlik azalır. Altyapı kavranmadan bu takas yapılmamalıdır.

Etkinleştirmek için:
    1. ANTHROPIC_API_KEY ortam değişkenini tanımlayın. Anahtar asla depoya yazılmaz.
    2. uv add anthropic
    3. enrich() içindeki gövdeyi doldurun ve pipeline'da çağırın.
"""

from __future__ import annotations

import os

from ..core.models import RoutingDecision
from ..problems.base import ProblemSpec


def is_enabled() -> bool:
    """Dil modeli katmanı kullanılabilir mi?"""
    return bool(os.environ.get("ANTHROPIC_API_KEY")) and _sdk_available()


def _sdk_available() -> bool:
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def enrich(decision: RoutingDecision, spec: ProblemSpec) -> RoutingDecision:
    """Yönlendirme kararına doğal dille açıklama ekler.

    Anahtar veya paket yoksa kararı olduğu gibi döndürür. Sessizce geçmek
    kasıtlıdır: dil modeli bir süs katmanıdır, sistemin çalışması ona
    bağlı değildir.
    """
    if not is_enabled():
        return decision

    # Buraya gelecek uygulama şu şekilde olacak:
    #
    #   from anthropic import Anthropic
    #   client = Anthropic()
    #   response = client.messages.create(
    #       model="claude-sonnet-5",
    #       max_tokens=400,
    #       system=(
    #           "Sen bir hibrit hesaplama yönlendiricisisin. Sana verilen kural "
    #           "tabanlı kararı, yeni başlayan birine Türkçe açıkla. Kararı "
    #           "değiştirme, sadece gerekçesini derinleştir."
    #       ),
    #       messages=[{"role": "user", "content": _build_prompt(decision, spec)}],
    #   )
    #   decision.reasoning.append(response.content[0].text)
    #   decision.source = "kural-tabanlı artı dil modeli"
    #
    # Önemli kısıt: dil modeli kararı DEĞİŞTİRMEZ, sadece açıklar. Kararın
    # tekrarlanabilir kalması, eğitim değeri açısından açıklamanın
    # akıcılığından daha önemlidir.
    return decision


def _build_prompt(decision: RoutingDecision, spec: ProblemSpec) -> str:
    """Dil modeline gidecek istem metnini hazırlar."""
    return (
        f"Problem: {spec.problem_id}\n"
        f"Parametreler: {spec.params}\n"
        f"Karar: {decision.n_qubits} kubit, {decision.shots} atış, "
        f"kodlama {decision.encoding}, strateji {decision.strategy}\n"
        f"Kural tabanlı gerekçeler:\n"
        + "\n".join(f"- {r}" for r in decision.reasoning)
    )
