"""Gercek donanim arka uclari icin iskelet (stub).

Bu dosya bilerek calismaz. Amaci, altyapiyi kavradiktan sonraki adimin
tam olarak nereye baglanacagini gostermektir: eklenmesi gereken tek sey
bu siniflarin govdesidir, boru hattinin geri kalani aynen kalir.

Neden simdiden burada duruyor: projenin yonunu belirsiz birakmamak icin.
"Sonra gercek donanima gecilir" cumlesi yerine, gecisin tam olarak hangi
dosyada ve hangi satirda olacagi gorunur durumda.
"""

from __future__ import annotations

from ..circuit import Circuit
from .base import BackendInfo, RawResult


class QiskitAerBackend:
    """Qiskit Aer: yerel ama endustri standardi simulator.

    Kurulum:
        uv add qiskit qiskit-aer

    Uygulama adimlari:
        1. `app.quantum.circuit.Circuit` nesnesini `qiskit.QuantumCircuit`'e cevir.
           En kolay yol: `app.quantum.qasm.to_qasm3()` ciktisini
           `qiskit.qasm3.loads()` ile okumak. QASM ciktisini bu yuzden uretiyoruz.
        2. `AerSimulator(method="statevector")` olustur, gurultu modeli eklenebilir.
        3. `transpile(qc, simulator)` cagir ve `simulator.run(qc, shots=shots)` calistir.
        4. `result.get_counts()` ciktisini `RawResult.counts` alanina yerlestir.

    Bit sirasi uyarisi: Qiskit kubit 0'i en sagdaki bit olarak yazar, bu proje
    ise en soldaki bit olarak yazar. Cevirirken dizgiyi ters cevirmek gerekir.
    """

    id = "qiskit-aer"

    @property
    def info(self) -> BackendInfo:
        return BackendInfo(
            id=self.id,
            name="Qiskit Aer (henüz bağlı değil)",
            kind="simulator",
            max_qubits=30,
            available=False,
            description=(
                "IBM'in açık kaynaklı simülatörü. Gerçek cihazların gürültü profilleri "
                "ile çalıştırılabildiği için donanıma geçmeden önce son duraktır."
            ),
            supports_statevector=True,
            supports_noise=True,
            notes=[
                "Etkinleştirmek için: uv add qiskit qiskit-aer",
                "Devre çevirimi OpenQASM 3 üzerinden yapılır, bu proje OpenQASM 3 üretmektedir.",
                "Bit sırası bu projeye göre terstir, çevirimde dikkat edilmelidir.",
            ],
        )

    def run(
        self,
        circuit: Circuit,
        shots: int = 1024,
        seed: int | None = None,
        noise_level: str = "ideal",
        collect_snapshots: bool = False,
    ) -> RawResult:
        raise NotImplementedError(
            "Qiskit Aer arka ucu henüz bağlanmadı. Bu, altyapı kavrandıktan sonraki "
            "ilk adımdır. Adımlar bu sınıfın açıklamasında yazılıdır."
        )


class IBMQuantumRuntimeBackend:
    """IBM Quantum Runtime: bulut uzerinden gercek kuantum cipi.

    Kurulum:
        uv add qiskit-ibm-runtime

    Uygulama adimlari:
        1. IBM Quantum hesabi ac ve API anahtarini `QISKIT_IBM_TOKEN` ortam
           degiskenine koy. Anahtar asla depoya yazilmaz.
        2. `QiskitRuntimeService()` ile baglan, `service.least_busy()` ile
           en az mesgul cihazi sec.
        3. Devreyi cihazin baglanti haritasina (coupling map) gore transpile et.
           Burasi onemlidir: bu projedeki `transpiler.routing_report()` fonksiyonu
           tam olarak bu maliyeti sembolik olarak anlatir.
        4. `SamplerV2(mode=backend)` ile isi gonder, is bir kuyruga girer.
        5. Sonuc geldiginde sayimlari `RawResult`'a doldur.

    Gercekci beklenti: gunumuz cihazlarinda gurultu yuksektir. Bu projedeki
    kucuk devreler calisir ama sonuclar simulasyondaki kadar temiz olmaz.
    Aradaki farki gormek, hata duzeltmenin (error correction) neden bu kadar
    onemli oldugunu anlamanin en hizli yoludur.
    """

    id = "ibm-runtime"

    @property
    def info(self) -> BackendInfo:
        return BackendInfo(
            id=self.id,
            name="IBM Quantum Runtime (henüz bağlı değil)",
            kind="hardware",
            max_qubits=127,
            available=False,
            description=(
                "Bulut üzerinden erişilen gerçek süperiletken kuantum işlemcisi. "
                "İş bir kuyruğa girer, sonuç gürültülüdür ve her çalıştırma ücretlendirilebilir."
            ),
            supports_statevector=False,
            supports_noise=True,
            notes=[
                "Etkinleştirmek için: uv add qiskit-ibm-runtime ve QISKIT_IBM_TOKEN ortam değişkeni.",
                "Gerçek cihazda durum vektörü okunamaz; sadece ölçüm sayımları alınır.",
                "Ücretsiz katmanda aylık çalıştırma süresi sınırlıdır.",
            ],
        )

    def run(
        self,
        circuit: Circuit,
        shots: int = 1024,
        seed: int | None = None,
        noise_level: str = "ideal",
        collect_snapshots: bool = False,
    ) -> RawResult:
        raise NotImplementedError(
            "IBM Quantum Runtime arka ucu henüz bağlanmadı. Adımlar bu sınıfın "
            "açıklamasında yazılıdır; önce QISKIT_IBM_TOKEN gereklidir."
        )
