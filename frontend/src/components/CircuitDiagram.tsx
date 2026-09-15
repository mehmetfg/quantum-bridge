/**
 * Kuantum devresinin SVG çizimi.
 *
 * Her yatay çizgi bir kubittir, soldan sağa zaman akar. Kutular tek kubitlik
 * kapıları, dikey bağlantılar kontrollü kapıları gösterir. Bölüm etiketleri
 * devrenin mantıksal parçalarını adlandırır.
 */

import { useMemo, useState } from 'react';

import type { CircuitData, Operation } from '../types';

const CELL = 52;
const LEFT = 62;
const TOP = 34;
const ROW = 50;
/** Bölüm etiketleri dikey yazılır; uzun metinler bu yüzden üst üste binmez. */
const LABEL_SPACE = 150;

interface Column {
  kind: 'gate' | 'section';
  operations: Operation[];
  label?: string;
}

/** İşlemleri, aynı anda çalışabilenler tek sütun olacak şekilde gruplar. */
function buildColumns(circuit: CircuitData): Column[] {
  const columns: Column[] = [];
  let current: { ops: Operation[]; used: Set<number> } | null = null;

  const flush = () => {
    if (current && current.ops.length) {
      columns.push({ kind: 'gate', operations: current.ops });
    }
    current = null;
  };

  for (const op of circuit.operations) {
    if (op.label && op.name === 'id') {
      flush();
      columns.push({ kind: 'section', operations: [], label: op.label });
      continue;
    }
    if (!current) current = { ops: [], used: new Set() };
    const overlaps = op.qubits.some((q) => current!.used.has(q));
    // Kontrollü kapılarda arada kalan kubitler de çizimde işgal edilir.
    const span =
      op.qubits.length > 1
        ? Array.from(
            { length: Math.max(...op.qubits) - Math.min(...op.qubits) + 1 },
            (_, i) => Math.min(...op.qubits) + i,
          )
        : op.qubits;
    const spanOverlaps = span.some((q) => current!.used.has(q));

    if (overlaps || spanOverlaps) {
      flush();
      current = { ops: [], used: new Set() };
    }
    current!.ops.push(op);
    span.forEach((q) => current!.used.add(q));
  }
  flush();
  return columns;
}

const GATE_COLORS: Record<string, string> = {
  h: '#38bdf8',
  x: '#f472b6',
  y: '#f472b6',
  z: '#a78bfa',
  s: '#a78bfa',
  t: '#a78bfa',
  rx: '#fb923c',
  ry: '#fb923c',
  rz: '#fb923c',
  p: '#fb923c',
  swap: '#facc15',
};

function gateColor(name: string): string {
  return GATE_COLORS[name.toLowerCase()] ?? '#34d399';
}

export default function CircuitDiagram({ circuit }: { circuit: CircuitData }) {
  const columns = useMemo(() => buildColumns(circuit), [circuit]);
  const [hovered, setHovered] = useState<Operation | null>(null);

  const hasSections = columns.some((column) => column.kind === 'section');
  const width = LEFT + columns.length * CELL + 90;
  const wiresBottom = TOP + (circuit.n_qubits - 1) * ROW;
  const height = wiresBottom + 40 + (hasSections ? LABEL_SPACE : 0);

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950/70 p-2">
        <svg width={width} height={height} className="min-w-full">
          {/* Kubit çizgileri ve etiketleri */}
          {Array.from({ length: circuit.n_qubits }, (_, q) => {
            const y = TOP + q * ROW;
            return (
              <g key={`wire-${q}`}>
                <text x={10} y={y + 4} className="fill-slate-400 font-mono text-[11px]">
                  q[{q}]
                </text>
                <line
                  x1={LEFT - 12}
                  y1={y}
                  x2={width - 76}
                  y2={y}
                  stroke="#334155"
                  strokeWidth={1.5}
                />
              </g>
            );
          })}

          {/* Sütunlar */}
          {columns.map((column, index) => {
            const x = LEFT + index * CELL;
            if (column.kind === 'section') {
              const labelY = wiresBottom + 28;
              return (
                <g key={`section-${index}`}>
                  <line
                    x1={x}
                    y1={TOP - 18}
                    x2={x}
                    y2={labelY - 6}
                    stroke="#475569"
                    strokeWidth={1}
                    strokeDasharray="3 3"
                  />
                  <text
                    x={x + 4}
                    y={labelY}
                    className="fill-slate-500 text-[9px]"
                    transform={`rotate(90 ${x + 4} ${labelY})`}
                  >
                    {column.label}
                  </text>
                </g>
              );
            }

            return (
              <g key={`col-${index}`}>
                {column.operations.map((op, opIndex) => {
                  const color = gateColor(op.name);
                  const key = `${index}-${opIndex}`;
                  const handlers = {
                    onMouseEnter: () => setHovered(op),
                    onMouseLeave: () => setHovered(null),
                    style: { cursor: 'help' as const },
                  };

                  if (op.qubits.length === 1) {
                    const y = TOP + op.qubits[0] * ROW;
                    return (
                      <g key={key} {...handlers}>
                        <rect
                          x={x - 16}
                          y={y - 15}
                          width={32}
                          height={30}
                          rx={6}
                          fill="#0f172a"
                          stroke={color}
                          strokeWidth={1.6}
                        />
                        <text
                          x={x}
                          y={y + 4}
                          textAnchor="middle"
                          className="font-mono text-[11px] font-semibold"
                          fill={color}
                        >
                          {op.name.toUpperCase()}
                        </text>
                      </g>
                    );
                  }

                  if (op.name.toLowerCase() === 'swap') {
                    const [a, b] = op.qubits;
                    const ya = TOP + a * ROW;
                    const yb = TOP + b * ROW;
                    return (
                      <g key={key} {...handlers}>
                        <line x1={x} y1={ya} x2={x} y2={yb} stroke={color} strokeWidth={1.6} />
                        {[ya, yb].map((y, i) => (
                          <g key={i}>
                            <line
                              x1={x - 7}
                              y1={y - 7}
                              x2={x + 7}
                              y2={y + 7}
                              stroke={color}
                              strokeWidth={2}
                            />
                            <line
                              x1={x - 7}
                              y1={y + 7}
                              x2={x + 7}
                              y2={y - 7}
                              stroke={color}
                              strokeWidth={2}
                            />
                          </g>
                        ))}
                      </g>
                    );
                  }

                  // Kontrollü kapı: son kubit hedef, öncekiler kontrol.
                  const controls = op.qubits.slice(0, -1);
                  const target = op.qubits[op.qubits.length - 1];
                  const yTarget = TOP + target * ROW;
                  const ys = op.qubits.map((q) => TOP + q * ROW);
                  const isZLike = op.name.toLowerCase().endsWith('z');

                  return (
                    <g key={key} {...handlers}>
                      <line
                        x1={x}
                        y1={Math.min(...ys)}
                        x2={x}
                        y2={Math.max(...ys)}
                        stroke={color}
                        strokeWidth={1.6}
                      />
                      {controls.map((c) => (
                        <circle
                          key={`c-${c}`}
                          cx={x}
                          cy={TOP + c * ROW}
                          r={5}
                          fill={color}
                        />
                      ))}
                      {isZLike ? (
                        <circle cx={x} cy={yTarget} r={5} fill={color} />
                      ) : (
                        <g>
                          <circle
                            cx={x}
                            cy={yTarget}
                            r={11}
                            fill="#0f172a"
                            stroke={color}
                            strokeWidth={1.8}
                          />
                          <line
                            x1={x - 11}
                            y1={yTarget}
                            x2={x + 11}
                            y2={yTarget}
                            stroke={color}
                            strokeWidth={1.8}
                          />
                          <line
                            x1={x}
                            y1={yTarget - 11}
                            x2={x}
                            y2={yTarget + 11}
                            stroke={color}
                            strokeWidth={1.8}
                          />
                        </g>
                      )}
                    </g>
                  );
                })}
              </g>
            );
          })}

          {/* Ölçüm simgeleri */}
          {circuit.measured_qubits.map((q) => {
            const y = TOP + q * ROW;
            const x = width - 56;
            return (
              <g key={`m-${q}`}>
                <rect
                  x={x - 16}
                  y={y - 15}
                  width={34}
                  height={30}
                  rx={6}
                  fill="#0f172a"
                  stroke="#94a3b8"
                  strokeWidth={1.4}
                />
                <path
                  d={`M ${x - 9} ${y + 7} A 9 9 0 0 1 ${x + 11} ${y + 7}`}
                  fill="none"
                  stroke="#e2e8f0"
                  strokeWidth={1.4}
                />
                <line
                  x1={x + 1}
                  y1={y + 7}
                  x2={x + 9}
                  y2={y - 5}
                  stroke="#e2e8f0"
                  strokeWidth={1.4}
                />
              </g>
            );
          })}
        </svg>
      </div>

      <div className="min-h-[40px] rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2 text-xs text-slate-400">
        {hovered ? (
          <span>
            <span className="font-mono font-semibold text-slate-200">
              {hovered.name.toUpperCase()}
            </span>{' '}
            (kubit {hovered.qubits.join(', ')}){hovered.description ? ` — ${hovered.description}` : ''}
          </span>
        ) : (
          <span>
            Kapıların üzerine gelerek ne yaptıklarını okuyabilirsiniz. Yatay çizgiler kubitleri,
            soldan sağa akış zamanı gösterir.
          </span>
        )}
      </div>
    </div>
  );
}
