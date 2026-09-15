/**
 * OpenQASM 3 metni.
 *
 * Bu metin simülasyon için gerekli değil. Bilerek üretiliyor: ekranda
 * görünen bu metin, gerçek donanıma gönderilecek olanın aynısıdır.
 */

import { useState } from 'react';

export default function QasmViewer({ qasm }: { qasm: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(qasm);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">
          IBM Quantum'a iş gönderirken kullanılan standart biçim. Bugün simülatöre gidiyor,
          yarın aynı metin gerçek çipe gidecek.
        </p>
        <button type="button" onClick={copy} className="btn-ghost shrink-0 px-3 py-1 text-xs">
          {copied ? 'Kopyalandı' : 'Kopyala'}
        </button>
      </div>
      <pre className="max-h-80 overflow-auto rounded-lg border border-slate-800 bg-slate-950 p-4 font-mono text-xs leading-relaxed text-slate-300">
        {qasm}
      </pre>
    </div>
  );
}
