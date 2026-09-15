"""Klasik son işleme: ham ölçümleri yorumla ve istatistiksel sağlığı ölç.

Kuantum tarafından gelen şey bir cevap değil, bir dağılımdır. Bu dosya,
o dağılımın ne kadar güvenilir olduğunu klasik istatistikle ölçer.
Problemin kendi decode fonksiyonu cevabı çıkarır, buradaki fonksiyonlar
ise o cevaba ne kadar güvenilebileceğini söyler.
"""

from __future__ import annotations

import math
from typing import Any


def distribution_stats(counts: dict[str, int]) -> dict[str, Any]:
    """Ölçüm dağılımının temel istatistikleri."""
    total = sum(counts.values())
    if total == 0:
        return {"total_shots": 0, "unique_outcomes": 0}

    sorted_items = sorted(counts.items(), key=lambda kv: -kv[1])
    top_key, top_count = sorted_items[0]
    top_share = top_count / total
    runner_up_share = (sorted_items[1][1] / total) if len(sorted_items) > 1 else 0.0

    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)
    # Binom standart hatası: bir oranın kaç atışta ne kadar kesinleştiği.
    standard_error = math.sqrt(max(top_share * (1 - top_share), 1e-12) / total)

    return {
        "total_shots": total,
        "unique_outcomes": len(counts),
        "top_outcome": top_key,
        "top_share": round(top_share, 4),
        "runner_up_share": round(runner_up_share, 4),
        "margin": round(top_share - runner_up_share, 4),
        "entropy": round(entropy, 4),
        "standard_error": round(standard_error, 4),
        "confidence_interval_95": [
            round(max(0.0, top_share - 1.96 * standard_error), 4),
            round(min(1.0, top_share + 1.96 * standard_error), 4),
        ],
    }


def reliability_note(stats: dict[str, Any], target_confidence: float) -> str:
    """Sonucun güvenilirliğini düz Türkçe bir cümleye çevirir."""
    if not stats.get("total_shots"):
        return "Ölçüm verisi yok."

    share = stats["top_share"]
    margin = stats["margin"]
    low, high = stats["confidence_interval_95"]

    if target_confidence <= 0:
        return (
            f"Bu problemde tek bir doğru cevap aranmıyor. Dağılımda {stats['unique_outcomes']} "
            f"farklı sonuç gözlendi ve entropi {stats['entropy']}."
        )

    verdict = "yeterli" if share >= target_confidence else "hedefin altında"
    return (
        f"En olası sonuç atışların yüzde {share * 100:.1f} kadarını aldı, hedef yüzde "
        f"{target_confidence * 100:.0f} idi: {verdict}. Yüzde 95 güven aralığı "
        f"{low * 100:.1f} ile {high * 100:.1f} arasında. İkinci sıradaki sonuçla arasındaki "
        f"fark yüzde {margin * 100:.1f}."
    )


def shots_needed_for(target_error: float) -> int:
    """Belirli bir istatistik hassasiyet için gereken atış sayısı.

    Kuantum sonuçlarında hassasiyet, atış sayısının kareköküyle iyileşir.
    Yani hatayı yarıya indirmek için atış sayısını dörde katlamak gerekir.
    Bu, kuantum hesaplamanın sessiz ama önemli maliyet kalemidir.
    """
    if target_error <= 0:
        raise ValueError("Hedef hata sıfırdan büyük olmalıdır.")
    return int(math.ceil(1.0 / (target_error ** 2)))
