import * as d3 from 'd3'
import { useEffect, useRef, useState } from 'react'
import { C } from '../../lib/colors'
import { useT } from '../../lib/i18n'

/**
 * A toy society. Every tie has a fixed random "conformity threshold" u.
 * At polarization level p the noise is ν = (1 - p) / 2: a tie conforms to the
 * camp structure (positive inside, negative across) iff u > ν. Agents drift
 * towards their camp's side as p grows. At p = 0 signs are random — there are
 * no camps; at p = 1 the society is perfectly balanced and split in two.
 */
interface Agent {
  camp: 1 | -1
  bx: number
  by: number
  x: number
  y: number
  r: number
  phase: number
}
interface Tie {
  a: number
  b: number
  u: number
  s: number // current rendered sign in [-1, 1] (animated)
}

const N = 150

function makeWorld(seed = 3) {
  const rnd = d3.randomLcg(seed)
  const agents: Agent[] = d3.range(N).map(() => {
    const ang = rnd() * Math.PI * 2
    const rad = Math.sqrt(rnd()) * 0.9
    // camps lean towards a side of the plane, with 20% of people living "on the other side"
    const side = Math.cos(ang) * rad + (rnd() - 0.5) * 0.35
    const camp: 1 | -1 = (side > 0) !== rnd() < 0.2 ? 1 : -1
    return {
      camp,
      bx: Math.cos(ang) * rad,
      by: Math.sin(ang) * rad * 0.75,
      x: 0,
      y: 0,
      r: 2.2 + rnd() * 2.6,
      phase: rnd() * Math.PI * 2,
    }
  })
  agents.forEach((a) => {
    a.x = a.bx
    a.y = a.by
  })
  const ties: Tie[] = []
  // geometric-ish: connect near neighbours in the base layout so the drawing is readable
  for (let i = 0; i < N; i++) {
    const near = d3
      .range(N)
      .filter((j) => j !== i)
      .sort((p, q) => Math.hypot(agents[p].bx - agents[i].bx, agents[p].by - agents[i].by) - Math.hypot(agents[q].bx - agents[i].bx, agents[q].by - agents[i].by))
      .slice(0, 3)
    for (const j of near) if (i < j || !near.includes(i)) ties.push({ a: i, b: j, u: rnd(), s: 0 })
  }
  for (let k = 0; k < 22; k++) {
    const a = Math.floor(rnd() * N)
    const b = Math.floor(rnd() * N)
    if (a !== b) ties.push({ a, b, u: rnd(), s: 0 })
  }
  return { agents, ties }
}

export default function PolarizationHero({ onLevel }: { onLevel?: (p: number) => void }) {
  const t = useT()
  const ref = useRef<HTMLCanvasElement>(null)
  const wrap = useRef<HTMLDivElement>(null)
  const world = useRef(makeWorld())
  const [p, setP] = useState(0)
  const [auto, setAuto] = useState(true)
  const pRef = useRef(0)
  const autoRef = useRef(true)
  autoRef.current = auto
  const [stats, setStats] = useState({ neg: 0, frus: 0 })

  useEffect(() => {
    const cv = ref.current!
    const ctx = cv.getContext('2d')!
    let raf = 0
    let w = 0
    let h = 0
    const resize = () => {
      const r = wrap.current!.getBoundingClientRect()
      w = r.width
      h = r.height
      const dpr = window.devicePixelRatio || 1
      cv.width = w * dpr
      cv.height = h * dpr
      cv.style.width = `${w}px`
      cv.style.height = `${h}px`
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(wrap.current!)
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const t0 = performance.now()
    let lastStat = 0
    const campCol = (c: number, p: number) => d3.interpolateRgb(C.neutral, c > 0 ? C.campA : C.campB)(Math.min(1, p * 1.3))
    const posCol = d3.color(C.pos)!
    const negCol = d3.color(C.neg)!

    const frame = (now: number) => {
      const time = (now - t0) / 1000
      if (autoRef.current && !reduce) {
        // 14 s loop: calm → polarize → hold → relax
        const c = (time % 14) / 14
        const target = c < 0.12 ? 0 : c < 0.55 ? d3.easeCubicInOut((c - 0.12) / 0.43) : c < 0.85 ? 1 : 1 - d3.easeCubicInOut((c - 0.85) / 0.15)
        pRef.current = target
      }
      const p = pRef.current
      const { agents, ties } = world.current
      const wide = w > 1024
      const sx = wide ? Math.min(w * 0.3, h * 0.62) : Math.min(w * 0.42, h * 0.5)
      const cx = wide ? w * 0.64 : w / 2
      const cy = wide ? h * 0.46 : h * 0.58
      // move agents
      for (const a of agents) {
        const drift = 0.012 * Math.sin(time * 0.6 + a.phase)
        const tx = a.bx * (1 - 0.55 * p) + a.camp * 0.62 * p
        const ty = a.by * (1 - 0.15 * p) + drift
        a.x += (tx - a.x) * 0.06
        a.y += (ty - a.y) * 0.06
      }
      ctx.clearRect(0, 0, w, h)
      const nu = (1 - p) / 2
      let neg = 0
      let frus = 0
      for (const tie of ties) {
        const A = agents[tie.a]
        const B = agents[tie.b]
        const same = A.camp === B.camp
        const conforms = tie.u > nu
        const target = same === conforms ? 1 : -1
        tie.s += (target - tie.s) * 0.08
        if (target < 0) neg++
        if (!conforms) frus++
        const x1 = cx + A.x * sx
        const y1 = cy + A.y * sx
        const x2 = cx + B.x * sx
        const y2 = cy + B.y * sx
        const k = (tie.s + 1) / 2 // 0 = negative, 1 = positive
        const col = d3.interpolateRgb(negCol.formatRgb(), posCol.formatRgb())(k)
        ctx.strokeStyle = col
        ctx.globalAlpha = k > 0.5 ? 0.16 + 0.1 * k : 0.38
        ctx.lineWidth = k > 0.5 ? 1 : 1.1
        ctx.setLineDash(k > 0.5 ? [] : [3, 3])
        ctx.beginPath()
        ctx.moveTo(x1, y1)
        ctx.lineTo(x2, y2)
        ctx.stroke()
      }
      ctx.setLineDash([])
      ctx.globalAlpha = 1
      for (const a of agents) {
        const x = cx + a.x * sx
        const y = cy + a.y * sx
        const col = campCol(a.camp, p)
        const g = ctx.createRadialGradient(x, y, 0, x, y, a.r * 4)
        g.addColorStop(0, col.replace('rgb', 'rgba').replace(')', ',0.35)'))
        g.addColorStop(1, 'rgba(0,0,0,0)')
        ctx.fillStyle = g
        ctx.beginPath()
        ctx.arc(x, y, a.r * 4, 0, Math.PI * 2)
        ctx.fill()
        ctx.fillStyle = col
        ctx.beginPath()
        ctx.arc(x, y, a.r, 0, Math.PI * 2)
        ctx.fill()
      }
      if (now - lastStat > 120) {
        lastStat = now
        setStats({ neg: neg / ties.length, frus: frus / ties.length })
        setP(p)
        onLevel?.(p)
      }
      raf = requestAnimationFrame(frame)
    }
    raf = requestAnimationFrame(frame)
    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
    }
  }, [onLevel])

  const phase = p < 0.25 ? t('Mixed society', '混合的社会') : p < 0.7 ? t('Sorting…', '分化中…') : t('Polarized', '极化')

  return (
    <div className="relative h-full w-full">
      <div ref={wrap} className="absolute inset-0">
        <canvas ref={ref} />
      </div>
      <div className="absolute bottom-6 left-1/2 w-[min(560px,92%)] -translate-x-1/2 rounded-2xl border border-white/10 bg-ink-900/70 px-5 py-4 backdrop-blur-md">
        <div className="flex items-center justify-between text-xs">
          <span className="font-medium text-fg">{phase}</span>
          <button className="text-fg-subtle hover:text-fg" onClick={() => setAuto((a) => !a)}>
            {auto ? t('❚❚ pause · drag the slider', '❚❚ 暂停 · 拖动滑块') : t('▶ autoplay', '▶ 自动播放')}
          </button>
        </div>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={p}
          onChange={(e) => {
            setAuto(false)
            pRef.current = +e.target.value
            setP(+e.target.value)
          }}
          className="mt-2 w-full"
          aria-label={t('polarization level', '极化程度')}
        />
        <div className="mt-2 grid grid-cols-3 gap-3 text-center text-[11px] text-fg-subtle">
          <div>
            <div className="tabular font-mono text-base text-fg">{(p * 100).toFixed(0)}%</div>
            {t('polarization', '极化程度')}
          </div>
          <div>
            <div className="tabular font-mono text-base text-neg">{(stats.neg * 100).toFixed(0)}%</div>
            {t('negative ties', '负向关系')}
          </div>
          <div>
            <div className="tabular font-mono text-base text-fg">{(stats.frus * 100).toFixed(0)}%</div>
            {t('frustrated ties', '受挫关系')}
          </div>
        </div>
      </div>
    </div>
  )
}
