import * as d3 from 'd3'
import { motion, useInView } from 'motion/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { C } from '../../lib/colors'
import { useT } from '../../lib/i18n'

/** Harary's structure theorem in three steps: a balanced graph splits into two camps;
 *  one flipped tie becomes "frustrated" and the frustration index counts such ties. */
const N = 14
export default function CampSplit() {
  const t = useT()
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { margin: '-120px' })
  const [step, setStep] = useState(0)
  useEffect(() => {
    if (!inView) return
    const id = setInterval(() => setStep((s) => (s + 1) % 3), 3200)
    return () => clearInterval(id)
  }, [inView])

  const { nodes, edges } = useMemo(() => {
    const rnd = d3.randomLcg(42)
    const nodes = d3.range(N).map((i) => {
      const a = (i / N) * Math.PI * 2
      return { i, camp: i % 3 === 0 || i % 4 === 1 ? 1 : -1, cx: 160 + Math.cos(a) * 105, cy: 120 + Math.sin(a) * 92, jitter: rnd() }
    })
    const edges: { a: number; b: number; s: number }[] = []
    for (let a = 0; a < N; a++)
      for (let b = a + 1; b < N; b++)
        if (rnd() < 0.23) edges.push({ a, b, s: nodes[a].camp === nodes[b].camp ? 1 : -1 })
    return { nodes, edges }
  }, [])
  const flipped = edges.findIndex((e) => e.s > 0)
  const camps: Record<number, number[]> = { 1: [], [-1]: [] }
  nodes.forEach((n) => camps[n.camp].push(n.i))
  const pos = (n: (typeof nodes)[number]) => {
    if (step === 0) return [n.cx, n.cy]
    const list = camps[n.camp]
    const k = list.indexOf(n.i)
    const col = k % 3
    const row = Math.floor(k / 3)
    return [n.camp > 0 ? 60 + col * 34 + (row % 2) * 12 : 200 + col * 34 + (row % 2) * 12, 50 + row * 42]
  }
  const label = [
    t('A balanced network, drawn at random…', '一个平衡的网络，随意摆放…'),
    t('…always splits into two camps: + inside, − across.', '…总能分成两个阵营：阵营内为 +，阵营间为 −。'),
    t('Flip one tie: it is now frustrated. Frustration index = 1.', '翻转一条关系：它成为“受挫边”。受挫指数 = 1。'),
  ][step]

  return (
    <div ref={ref} className="card p-6">
      <svg viewBox="0 0 320 240" className="mx-auto w-full max-w-md">
        {step > 0 && (
          <>
            <motion.rect initial={{ opacity: 0 }} animate={{ opacity: 1 }} x={40} y={22} width={110} height={196} rx={18} fill={C.campA} fillOpacity={0.07} stroke={C.campA} strokeOpacity={0.3} />
            <motion.rect initial={{ opacity: 0 }} animate={{ opacity: 1 }} x={180} y={22} width={110} height={196} rx={18} fill={C.campB} fillOpacity={0.07} stroke={C.campB} strokeOpacity={0.3} />
          </>
        )}
        {edges.map((e, k) => {
          const [x1, y1] = pos(nodes[e.a])
          const [x2, y2] = pos(nodes[e.b])
          const s = step === 2 && k === flipped ? -1 : e.s
          const fr = step === 2 && k === flipped
          return (
            <motion.line
              key={k}
              animate={{ x1, y1, x2, y2, stroke: s > 0 ? C.pos : C.neg, strokeOpacity: fr ? 1 : s > 0 ? 0.45 : 0.6, strokeWidth: fr ? 3.5 : 1.4 }}
              transition={{ duration: 1.1, ease: 'easeInOut' }}
              strokeDasharray={s > 0 ? undefined : '4 3'}
            />
          )
        })}
        {nodes.map((n) => {
          const [x, y] = pos(n)
          return (
            <motion.circle
              key={n.i}
              r={7}
              animate={{ cx: x, cy: y, fill: step === 0 ? C.neutral : n.camp > 0 ? C.campA : C.campB }}
              transition={{ duration: 1.1, ease: 'easeInOut', delay: n.jitter * 0.15 }}
              stroke={C.surface}
              strokeWidth={2}
            />
          )
        })}
      </svg>
      <motion.p key={step} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="mt-4 text-center text-sm text-fg-muted">
        {label}
      </motion.p>
      <div className="mt-3 flex justify-center gap-1.5">
        {[0, 1, 2].map((s) => (
          <button key={s} onClick={() => setStep(s)} className={`h-1.5 rounded-full transition-all ${s === step ? 'w-6 bg-accent' : 'w-1.5 bg-white/20'}`} aria-label={`step ${s + 1}`} />
        ))}
      </div>
    </div>
  )
}
