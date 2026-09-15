/**
 * Durum vektörü tablosu: genlikler ve olasılıklar.
 *
 * Bu tablo gerçek donanımda ASLA okunamaz. Ölçüm yapmadan durumu görmek
 * kuantum mekaniğinin kurallarına aykırıdır. Simülasyonda görebiliyoruz
 * çünkü sayıları biz hesaplıyoruz ve bu, öğrenmek açısından simülatörün
 * en değerli tarafıdır.
 */

interface Props {
  statevector: { re: number; im: number }[];
  nQubits: number;
}

export default function StateVectorTable({ statevector, nQubits }: Props) {
  const rows = statevector
    .map((amplitude, index) => {
      const probability = amplitude.re ** 2 + amplitude.im ** 2;
      return {
        basis: index.toString(2).padStart(nQubits, '0'),
        re: amplitude.re,
        im: amplitude.im,
        probability,
      };
    })
    .filter((row) => row.probability > 1e-9)
    .sort((a, b) => b.probability - a.probability);

  return (
    <div className="space-y-2">
      <div className="overflow-hidden rounded-lg border border-slate-800">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-900 text-slate-400">
            <tr>
              <th className="px-3 py-2 font-medium">Temel durum</th>
              <th className="px-3 py-2 font-medium">Genlik</th>
              <th className="px-3 py-2 font-medium">Olasılık</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/70">
            {rows.map((row) => (
              <tr key={row.basis} className="bg-slate-950/40">
                <td className="px-3 py-2 font-mono text-slate-200">|{row.basis}&gt;</td>
                <td className="px-3 py-2 font-mono text-slate-400">
                  {row.re.toFixed(4)}
                  {row.im >= 0 ? ' + ' : ' - '}
                  {Math.abs(row.im).toFixed(4)}i
                </td>
                <td className="px-3 py-2 font-mono text-emerald-300">
                  {(row.probability * 100).toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-500">
        Olasılık, genliğin karesinin büyüklüğüdür. Negatif ve karmaşık genlikler önemlidir:
        birbirini götürerek girişim yaratırlar ve algoritmaların çalışma sebebi budur.
        Gerçek donanımda bu tablo okunamaz, yalnızca ölçüm sonuçları görülür.
      </p>
    </div>
  );
}
