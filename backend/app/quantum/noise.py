"""Basit gurultu (noise) modeli.

Gercek kuantum bilgisayarlar mukemmel degildir. Uc temel hata kaynagi var:

1. Kapi hatasi (gate error): uygulanan kapi tam olarak istenen donusumu yapmaz.
2. Olcum hatasi (readout error): kubit 0 iken 1 okunur veya tersi.
3. Dekoherans (decoherence): kubit, cevresiyle etkilestigi icin zamanla
   durumunu kaybeder. Devre ne kadar derinse etkisi o kadar buyuktur.

Burada bunlari tam fizikle degil, sonucu anlasilir bicimde bozan sade bir
istatistik modeliyle temsil ediyoruz. Amac gercek bir cipi taklit etmek
degil, "gurultu neden onemli" sorusunu gozle gorulur kilmaktir.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class NoiseModel:
    """Sembolik gurultu modeli.

    readout_error: her bitin olcumde ters okunma olasiligi.
    depolarizing_rate: kapi basina durumu rastgele dagitma egilimi.
    """

    readout_error: float = 0.02
    depolarizing_rate: float = 0.005
    enabled: bool = True

    @classmethod
    def ideal(cls) -> NoiseModel:
        """Gurultusuz (ideal) model: simulasyonun varsayilani."""
        return cls(readout_error=0.0, depolarizing_rate=0.0, enabled=False)

    @classmethod
    def preset(cls, level: str) -> NoiseModel:
        """Hazir gurultu seviyeleri."""
        presets = {
            "ideal": cls.ideal(),
            "low": cls(readout_error=0.005, depolarizing_rate=0.001),
            "medium": cls(readout_error=0.02, depolarizing_rate=0.005),
            "high": cls(readout_error=0.06, depolarizing_rate=0.02),
        }
        if level not in presets:
            raise ValueError(f"Bilinmeyen gürültü seviyesi: {level}")
        return presets[level]

    def effective_error(self, gate_count: int) -> float:
        """Devre boyunca biriken toplam bozulma olasiligi."""
        if not self.enabled:
            return 0.0
        return float(1.0 - (1.0 - self.depolarizing_rate) ** max(gate_count, 0))

    def apply(
        self,
        counts: dict[str, int],
        n_bits: int,
        gate_count: int,
        seed: int | None = None,
    ) -> tuple[dict[str, int], dict]:
        """Ideal sayimlari (counts) bozarak gercekci hale getirir."""
        if not self.enabled or (self.readout_error <= 0 and self.depolarizing_rate <= 0):
            return counts, {"applied": False}

        rng = np.random.default_rng(seed)
        depolarized = self.effective_error(gate_count)
        noisy: dict[str, int] = {}
        flipped_bits = 0
        randomized_shots = 0

        for bitstring, count in counts.items():
            for _ in range(count):
                # Dekoherans: belirli bir olasilikla sonuc tamamen rastgeleye doner.
                if rng.random() < depolarized:
                    result = "".join(rng.choice(["0", "1"]) for _ in range(n_bits))
                    randomized_shots += 1
                else:
                    bits = list(bitstring)
                    for i in range(len(bits)):
                        if rng.random() < self.readout_error:
                            bits[i] = "1" if bits[i] == "0" else "0"
                            flipped_bits += 1
                    result = "".join(bits)
                noisy[result] = noisy.get(result, 0) + 1

        meta = {
            "applied": True,
            "readout_error": self.readout_error,
            "depolarizing_rate": self.depolarizing_rate,
            "accumulated_error": round(depolarized, 4),
            "flipped_bits": flipped_bits,
            "randomized_shots": randomized_shots,
            "explanation": (
                f"Devrede {gate_count} kapı var. Kapı başına {self.depolarizing_rate:.3f} "
                f"bozulma oranı, toplamda yaklaşık yüzde {depolarized * 100:.1f} olasılıkla "
                "sonucun tamamen rastgeleleşmesi demektir. Ayrıca her bit, ölçüm sırasında "
                f"yüzde {self.readout_error * 100:.1f} olasılıkla ters okunur."
            ),
        }
        return dict(sorted(noisy.items(), key=lambda kv: -kv[1])), meta
