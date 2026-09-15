/**
 * Problem girdisi formu.
 *
 * Alanlar arka uçtan gelen şemadan üretilir. Yeni bir problem eklendiğinde
 * bu dosyada değişiklik gerekmez; şema alanları kendiliğinden görünür.
 */

import type { ProblemInfo, SchemaField } from '../types';

interface Props {
  problem: ProblemInfo;
  value: Record<string, unknown>;
  onChange: (next: Record<string, unknown>) => void;
}

export default function ProblemForm({ problem, value, onChange }: Props) {
  const set = (key: string, next: unknown) => onChange({ ...value, [key]: next });

  return (
    <div className="space-y-4">
      {Object.entries(problem.input_schema).map(([key, field]) => (
        <div key={key}>
          <label className="label" htmlFor={`field-${key}`}>
            {field.label}
            {field.optional && <span className="ml-1 text-slate-500">(isteğe bağlı)</span>}
          </label>
          {renderField(key, field, value, set)}
          {field.help && <p className="help-text">{field.help}</p>}
        </div>
      ))}
    </div>
  );
}

function renderField(
  key: string,
  field: SchemaField,
  value: Record<string, unknown>,
  set: (key: string, next: unknown) => void,
) {
  const id = `field-${key}`;
  const current = value[key];

  switch (field.type) {
    case 'integer':
      return (
        <input
          id={id}
          type="number"
          className="input"
          min={field.min}
          max={field.max}
          value={current === null || current === undefined ? '' : String(current)}
          placeholder={field.optional ? 'Boş bırakılırsa en iyi değer hesaplanır' : undefined}
          onChange={(event) => {
            const raw = event.target.value;
            set(key, raw === '' ? null : Number(raw));
          }}
        />
      );

    case 'select':
      return (
        <select
          id={id}
          className="input"
          value={String(current ?? '')}
          onChange={(event) => set(key, event.target.value)}
        >
          {field.options?.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );

    case 'bitstring':
      return (
        <input
          id={id}
          type="text"
          inputMode="numeric"
          className="input font-mono"
          maxLength={field.max_length}
          value={String(current ?? '')}
          onChange={(event) => set(key, event.target.value.replace(/[^01]/g, ''))}
        />
      );

    case 'string_list': {
      const items = Array.isArray(current) ? (current as string[]) : [];
      return (
        <textarea
          id={id}
          className="input min-h-[80px] font-mono"
          value={items.join('\n')}
          onChange={(event) => {
            const next = event.target.value
              .split('\n')
              .map((line) => line.trim())
              .filter(Boolean);
            set(key, next);
          }}
        />
      );
    }

    case 'select_from_items': {
      const items = Array.isArray(value.items) ? (value.items as string[]) : [];
      return (
        <select
          id={id}
          className="input"
          value={String(current ?? '')}
          onChange={(event) => set(key, event.target.value)}
        >
          {items.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      );
    }

    default:
      return (
        <input
          id={id}
          type="text"
          className="input"
          value={String(current ?? '')}
          onChange={(event) => set(key, event.target.value)}
        />
      );
  }
}
