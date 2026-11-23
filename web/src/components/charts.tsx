import * as d3 from 'd3'
import { motion } from 'motion/react'
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { C } from '../lib/colors'

export function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [w, setW] = useState(600)
  useEffect(() => {
    if (!ref.current) return
    const ro = new ResizeObserver(([e]) => setW(Math.max(240, e.contentRect.width)))
    ro.observe(ref.current)
    return () => ro.disconnect()
  }, [])
  return [ref, w] as const
}

function Axis({ scale, orient, ticks = 5, format, transform }: {
  scale: d3.AxisScale<d3.NumberValue>
  orient: 'bottom' | 'left'
  ticks?: number
  format?: (v: number) => string
  transform?: string
}) {
  const g = useRef<SVGGElement>(null)
  useEffect(() => {
    if (!g.current) return
    const ax = orient === 'bottom' ? d3.axisBottom(scale) : d3.axisLeft(scale)
    ax.ticks(ticks).tickSizeOuter(0)
    if (format) ax.tickFormat((v) => format(+v))
    d3.select(g.current).call(ax)
  }, [scale, orient, ticks, format])
  return <g ref={g} className="axis" transform={transform} />
}

function Grid({ scale, width, ticks = 5 }: { scale: d3.ScaleLinear<number, number> | d3.ScaleLogarithmic<number, number>; width: number; ticks?: number }) {
  const g = useRef<SVGGElement>(null)
  useEffect(() => {
    if (!g.current) return
    d3.select(g.current).call(d3.axisLeft(scale).ticks(ticks).tickSize(-width).tickFormat(() => ''))
  }, [scale, width, ticks])
  return <g ref={g} className="gridline" />
}

export function Tip({ x, y, width, children }: { x: number; y: number; width: number; children: ReactNode }) {
  const left = x > width - 200 ? x - 196 : x + 14
  return (
    <div
      className="pointer-events-none absolute z-20 min-w-40 rounded-lg border border-white/10 bg-ink-800/95 px-3 py-2 text-xs shadow-xl backdrop-blur"
      style={{ left, top: Math.max(0, y - 10) }}
    >
      {children}
    </div>
  )
}

export function Legend({ items }: { items: { label: string; color: string; dashed?: boolean }[] }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-fg-muted">
      {items.map((it) => (
        <span key={it.label} className="inline-flex items-center gap-1.5">
          <svg width="18" height="8">
            <line x1="1" x2="17" y1="4" y2="4" stroke={it.color} strokeWidth="2.5" strokeLinecap="round"
              strokeDasharray={it.dashed ? '3 3' : undefined} />
          </svg>
          {it.label}
        </span>
      ))}
    </div>
  )
}

// ------------------------------------------------------------------ LineChart
export interface Series {
  key: string
  label: string
  color: string
  values: { x: number; y: number | null }[]
  dashed?: boolean
}

export function LineChart({
  series,
  height = 260,
  yDomain,
  xFormat = (v) => String(Math.round(v)),
  yFormat = (v) => d3.format('.2~f')(v),
  cursorX,
  onPickX,
  annotations = [],
  xLabel,
  animate,
  drawOnScroll = false,
}: {
  series: Series[]
  height?: number
  yDomain?: [number, number]
  xFormat?: (v: number) => string
  yFormat?: (v: number) => string
  cursorX?: number | null
  onPickX?: (x: number) => void
  annotations?: { x: number; label: string }[]
  xLabel?: string
  animate?: boolean
  drawOnScroll?: boolean
}) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const directLabels = series.length <= 4 && series.length > 1
  const m = { t: 14, r: directLabels ? 92 : 16, b: xLabel ? 40 : 28, l: 46 }
  const iw = width - m.l - m.r
  const ih = height - m.t - m.b
  const all = series.flatMap((s) => s.values)
  const xs = all.map((d) => d.x)
  const x = useMemo(() => d3.scaleLinear().domain(d3.extent(xs) as [number, number]).range([0, iw]), [iw, xs.join()])
  const ys = all.map((d) => d.y).filter((v): v is number => v !== null && Number.isFinite(v))
  const y = useMemo(() => {
    const dom = yDomain ?? (d3.extent(ys) as [number, number])
    return d3.scaleLinear().domain(dom[0] === dom[1] ? [dom[0] - 1, dom[1] + 1] : dom).nice().range([ih, 0])
  }, [ih, ys.join(), yDomain?.join()])
  const [hx, setHx] = useState<number | null>(null)
  const uniqX = useMemo(() => Array.from(new Set(xs)).sort((a, b) => a - b), [xs.join()])
  const line = d3
    .line<{ x: number; y: number | null }>()
    .defined((d) => d.y !== null && Number.isFinite(d.y))
    .x((d) => x(d.x))
    .y((d) => y(d.y as number))
    .curve(d3.curveMonotoneX)

  const nearest = (px: number) => {
    const v = x.invert(px)
    const i = d3.bisectCenter(uniqX, v)
    return uniqX[Math.max(0, Math.min(uniqX.length - 1, i))]
  }
  const shown = hx ?? cursorX ?? null
  const lastPoints = series.map((s) => {
    const v = [...s.values].reverse().find((d) => d.y !== null)
    return { s, v }
  })
  // de-collide direct labels
  const labelY = lastPoints.map((p) => (p.v ? y(p.v.y as number) : 0))
  const order = labelY.map((_, i) => i).sort((a, b) => labelY[a] - labelY[b])
  for (let k = 1; k < order.length; k++) {
    const a = order[k - 1]
    const b = order[k]
    if (labelY[b] - labelY[a] < 13) labelY[b] = labelY[a] + 13
  }

  return (
    <div ref={ref} className="relative w-full">
      {series.length > 1 && (
        <div className="mb-2">
          <Legend items={series.map((s) => ({ label: s.label, color: s.color, dashed: s.dashed }))} />
        </div>
      )}
      <svg width={width} height={height}>
        <g transform={`translate(${m.l},${m.t})`}>
          <Grid scale={y} width={iw} />
          <Axis scale={y} orient="left" format={yFormat} />
          <Axis scale={x} orient="bottom" transform={`translate(0,${ih})`} format={xFormat} ticks={Math.min(8, Math.floor(iw / 70))} />
          {xLabel && (
            <text x={iw / 2} y={ih + 34} textAnchor="middle" fill={C.subtle} fontSize={11}>
              {xLabel}
            </text>
          )}
          {annotations.map((a) => (
            <g key={a.x + a.label} transform={`translate(${x(a.x)},0)`}>
              <line y1={0} y2={ih} stroke="rgba(255,255,255,0.14)" strokeDasharray="2 4" />
              <text y={8} x={4} fill={C.subtle} fontSize={10}>
                {a.label}
              </text>
            </g>
          ))}
          {series.map((s) => (
            <motion.path
              key={s.key}
              d={line(s.values) ?? ''}
              fill="none"
              stroke={s.color}
              strokeWidth={2}
              strokeLinejoin="round"
              strokeLinecap="round"
              strokeDasharray={s.dashed ? '5 4' : undefined}
              initial={(animate ?? drawOnScroll) ? { pathLength: 0, opacity: 0.2 } : false}
              {...(drawOnScroll
                ? { whileInView: { pathLength: 1, opacity: 1 }, viewport: { once: true } }
                : { animate: { pathLength: 1, opacity: 1 } })}
              transition={{ duration: 1.6, ease: 'easeInOut' }}
            />
          ))}
          {directLabels &&
            lastPoints.map(({ s, v }, i) =>
              v ? (
                <text key={s.key} x={x(v.x) + 8} y={labelY[i] + 4} fill={C.muted} fontSize={11}>
                  {s.label.length > 13 ? s.label.slice(0, 12) + '…' : s.label}
                </text>
              ) : null,
            )}
          {shown !== null && (
            <g transform={`translate(${x(shown)},0)`} pointerEvents="none">
              <line y1={0} y2={ih} stroke="rgba(255,255,255,0.35)" />
              {series.map((s) => {
                const p = s.values.find((d) => d.x === shown)
                return p && p.y !== null ? (
                  <circle key={s.key} cy={y(p.y)} r={4.5} fill={s.color} stroke={C.surface} strokeWidth={2} />
                ) : null
              })}
            </g>
          )}
          <rect
            width={iw}
            height={ih}
            fill="transparent"
            onMouseMove={(e) => setHx(nearest(e.nativeEvent.offsetX - m.l))}
            onMouseLeave={() => setHx(null)}
            onClick={(e) => onPickX?.(nearest(e.nativeEvent.offsetX - m.l))}
            style={{ cursor: onPickX ? 'pointer' : 'crosshair' }}
          />
        </g>
      </svg>
      {hx !== null && (
        <Tip x={x(hx) + m.l} y={m.t} width={width}>
          <div className="mb-1 font-medium text-fg">{xFormat(hx)}</div>
          {series.map((s) => {
            const p = s.values.find((d) => d.x === hx)
            return (
              <div key={s.key} className="flex items-center justify-between gap-4">
                <span className="inline-flex items-center gap-1.5 text-fg-muted">
                  <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
                  {s.label}
                </span>
                <span className="tabular font-mono text-fg">{p && p.y !== null ? yFormat(p.y) : '—'}</span>
              </div>
            )
          })}
        </Tip>
      )}
    </div>
  )
}

// --------------------------------------------------------------------- Bars
export function Bars({
  data,
  height = 200,
  yFormat = (v) => d3.format('.0%')(v),
  valueFormat,
}: {
  data: { label: string; value: number; color: string; note?: string }[]
  height?: number
  yFormat?: (v: number) => string
  valueFormat?: (v: number) => string
}) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const m = { t: 18, r: 8, b: 30, l: 44 }
  const iw = width - m.l - m.r
  const ih = height - m.t - m.b
  const x = d3.scaleBand().domain(data.map((d) => d.label)).range([0, iw]).paddingInner(0.35).paddingOuter(0.2)
  const y = d3.scaleLinear().domain([0, d3.max(data, (d) => d.value) || 1]).nice().range([ih, 0])
  const [hi, setHi] = useState<number | null>(null)
  const fmtV = valueFormat ?? yFormat
  const bw = Math.min(x.bandwidth(), 56)
  return (
    <div ref={ref} className="relative w-full">
      <svg width={width} height={height}>
        <g transform={`translate(${m.l},${m.t})`}>
          <Grid scale={y} width={iw} ticks={4} />
          <Axis scale={y} orient="left" format={yFormat} ticks={4} />
          {data.map((d, i) => {
            const h = ih - y(d.value)
            const bx = x(d.label)! + (x.bandwidth() - bw) / 2
            return (
              <g key={d.label} onMouseEnter={() => setHi(i)} onMouseLeave={() => setHi(null)}>
                <rect x={x(d.label)} y={0} width={x.bandwidth()} height={ih} fill="transparent" />
                <motion.path
                  initial={{ opacity: 0, scaleY: 0 }}
                  animate={{ opacity: hi === null || hi === i ? 1 : 0.45, scaleY: 1 }}
                  style={{ originY: 1, transformBox: 'fill-box' }}
                  transition={{ duration: 0.7, delay: i * 0.05 }}
                  d={roundedTop(bx, y(d.value), bw, Math.max(h, 0), 4)}
                  fill={d.color}
                />
                <text x={x(d.label)! + x.bandwidth() / 2} y={y(d.value) - 6} textAnchor="middle" fill={C.muted} fontSize={11} className="tabular">
                  {fmtV(d.value)}
                </text>
                <text x={x(d.label)! + x.bandwidth() / 2} y={ih + 18} textAnchor="middle" fill={C.muted} fontSize={12} fontFamily="JetBrains Mono">
                  {d.label}
                </text>
              </g>
            )
          })}
        </g>
      </svg>
      {hi !== null && data[hi].note && (
        <Tip x={x(data[hi].label)! + m.l + x.bandwidth()} y={m.t + 10} width={width}>
          <div className="font-medium text-fg">{data[hi].label}</div>
          <div className="text-fg-muted">{data[hi].note}</div>
        </Tip>
      )}
    </div>
  )
}

function roundedTop(x: number, y: number, w: number, h: number, r: number) {
  r = Math.min(r, w / 2, h)
  return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`
}

// --------------------------------------------------------------- LogScatter
export function LogScatter({
  series,
  height = 240,
  xLabel,
  yLabel,
  logX = true,
}: {
  series: { label: string; color: string; points: [number, number][] }[]
  height?: number
  xLabel: string
  yLabel: string
  logX?: boolean
}) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const m = { t: 10, r: 12, b: 38, l: 50 }
  const iw = width - m.l - m.r
  const ih = height - m.t - m.b
  const pts = series.flatMap((s) => s.points).filter(([a, b]) => a > 0 && b > 0)
  const [hv, setHv] = useState<{ s: string; p: [number, number]; px: number; py: number } | null>(null)
  if (!pts.length) return <div className="py-10 text-center text-sm text-fg-subtle">No data</div>
  const xd = d3.extent(pts, (d) => d[0]) as [number, number]
  const yd = d3.extent(pts, (d) => d[1]) as [number, number]
  const x = (logX ? d3.scaleLog() : d3.scaleLinear()).domain(logX ? [Math.max(1, xd[0]), Math.max(2, xd[1])] : [0, xd[1]]).range([0, iw]).nice()
  const y = d3.scaleLog().domain([Math.max(0.8, yd[0]), Math.max(2, yd[1])]).range([ih, 0]).nice()
  const tf = (v: number) => (Math.log10(v) % 1 === 0 ? d3.format('~s')(v) : '')
  return (
    <div ref={ref} className="relative w-full">
      {series.length > 1 && <Legend items={series.map((s) => ({ label: s.label, color: s.color }))} />}
      <svg width={width} height={height}>
        <g transform={`translate(${m.l},${m.t})`}>
          <Axis scale={y} orient="left" format={tf} ticks={5} />
          <Axis scale={x} orient="bottom" transform={`translate(0,${ih})`} format={logX ? tf : (v) => (Number.isInteger(v) ? String(v) : '')} ticks={6} />
          <text x={iw / 2} y={ih + 32} textAnchor="middle" fill={C.subtle} fontSize={11}>{xLabel}</text>
          <text transform={`translate(-38,${ih / 2}) rotate(-90)`} textAnchor="middle" fill={C.subtle} fontSize={11}>{yLabel}</text>
          {series.map((s) =>
            s.points.filter(([a, b]) => a > 0 && b > 0).map((p) => (
              <circle
                key={s.label + p[0]}
                cx={x(p[0])}
                cy={y(p[1])}
                r={4}
                fill={s.color}
                fillOpacity={0.75}
                stroke={C.surface}
                strokeWidth={1.5}
                onMouseEnter={() => setHv({ s: s.label, p, px: x(p[0]) + m.l, py: y(p[1]) + m.t })}
                onMouseLeave={() => setHv(null)}
              />
            )),
          )}
        </g>
      </svg>
      {hv && (
        <Tip x={hv.px} y={hv.py} width={width}>
          <div className="font-medium text-fg">{hv.s}</div>
          <div className="tabular text-fg-muted">{xLabel}: {hv.p[0]} · {yLabel}: {hv.p[1].toLocaleString()}</div>
        </Tip>
      )}
    </div>
  )
}

// ----------------------------------------------------- diverging histogram
export function DivergingHistogram({
  bins,
  height = 160,
  leftLabel,
  rightLabel,
}: {
  bins: [number, number][]
  height?: number
  leftLabel: string
  rightLabel: string
}) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const m = { t: 8, r: 8, b: 24, l: 8 }
  const iw = width - m.l - m.r
  const ih = height - m.t - m.b
  const step = bins.length > 1 ? bins[1][0] - bins[0][0] : 0.1
  const x = d3.scaleLinear().domain([bins[0]?.[0] ?? -1.5, (bins.at(-1)?.[0] ?? 1.4) + step]).range([0, iw])
  const y = d3.scaleLinear().domain([0, d3.max(bins, (b) => b[1]) || 1]).range([ih, 0])
  const color = d3.scaleLinear<string>().domain([-1, 0, 1]).range([C.campB, '#6b7280', C.campA]).clamp(true)
  const bw = Math.max(1, x(step) - x(0) - 2)
  return (
    <div ref={ref} className="w-full">
      <svg width={width} height={height}>
        <g transform={`translate(${m.l},${m.t})`}>
          <line x1={x(0)} x2={x(0)} y1={0} y2={ih} stroke="rgba(255,255,255,0.15)" strokeDasharray="2 3" />
          {bins.map(([b0, c], i) => (
            <motion.rect
              key={b0}
              x={x(b0) + 1}
              width={bw}
              rx={2}
              fill={color(b0 + step / 2)}
              initial={{ y: ih, height: 0 }}
              animate={{ y: y(c), height: ih - y(c) }}
              transition={{ duration: 0.6, delay: i * 0.015 }}
            >
              <title>{`${b0.toFixed(2)} – ${(b0 + step).toFixed(2)}: ${c}`}</title>
            </motion.rect>
          ))}
          <line x1={0} x2={iw} y1={ih} y2={ih} stroke="rgba(255,255,255,0.15)" />
          <text x={0} y={ih + 16} fill={C.campB} fontSize={11}>← {leftLabel}</text>
          <text x={iw} y={ih + 16} fill={C.campA} fontSize={11} textAnchor="end">{rightLabel} →</text>
        </g>
      </svg>
    </div>
  )
}
