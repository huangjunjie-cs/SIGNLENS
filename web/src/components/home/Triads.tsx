import { motion } from 'motion/react'
import { useEffect, useState } from 'react'
import { C } from '../../lib/colors'
import { useT } from '../../lib/i18n'

const P = [
  [60, 18],
  [18, 92],
  [102, 92],
] as const
const EDGES = [
  [0, 1],
  [0, 2],
  [1, 2],
] as const

function Triangle({ signs, tense }: { signs: number[]; tense: boolean }) {
  return (
    <motion.svg
      viewBox="0 0 120 112"
      className="h-28 w-32"
      animate={tense ? { rotate: [0, -2.5, 2.5, -1.5, 1.5, 0] } : { rotate: 0 }}
      transition={tense ? { duration: 0.6, repeat: Infinity, repeatDelay: 0.4 } : { duration: 0.3 }}
    >
      {EDGES.map(([a, b], i) => (
        <motion.line
          key={i}
          x1={P[a][0]}
          y1={P[a][1]}
          x2={P[b][0]}
          y2={P[b][1]}
          strokeWidth={3}
          strokeLinecap="round"
          animate={{ stroke: signs[i] > 0 ? C.pos : C.neg }}
          strokeDasharray={signs[i] > 0 ? undefined : '6 5'}
          transition={{ duration: 0.5 }}
        />
      ))}
      {EDGES.map(([a, b], i) => (
        <motion.text
          key={`s${i}`}
          x={(P[a][0] + P[b][0]) / 2 + (i === 2 ? 0 : i === 0 ? -9 : 9)}
          y={(P[a][1] + P[b][1]) / 2 + (i === 2 ? 15 : 0)}
          textAnchor="middle"
          fontSize={14}
          fontFamily="JetBrains Mono"
          animate={{ fill: signs[i] > 0 ? C.pos : C.neg }}
        >
          {signs[i] > 0 ? '+' : '−'}
        </motion.text>
      ))}
      {P.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={9} fill="#1d2638" stroke="#e8ecf4" strokeOpacity={0.6} strokeWidth={1.5} />
      ))}
    </motion.svg>
  )
}

function TriadCard({ initial, resolveTo, title, caption, delay }: {
  initial: number[]
  resolveTo?: number[]
  title: string
  caption: string
  delay: number
}) {
  const t = useT()
  const [signs, setSigns] = useState(initial)
  const key = JSON.stringify([initial, resolveTo])
  useEffect(() => {
    if (!resolveTo) return
    // hold the tense state for 3s, show the resolution for 2s, repeat
    let alive = true
    let timer: ReturnType<typeof setTimeout>
    const loop = (resolved: boolean) => {
      if (!alive) return
      setSigns(resolved ? resolveTo : initial)
      timer = setTimeout(() => loop(!resolved), resolved ? 2000 : 3000 + delay * 4000)
    }
    loop(false)
    return () => {
      alive = false
      clearTimeout(timer)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])
  const balanced = signs.filter((s) => s < 0).length % 2 === 0
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.6, delay }}
      className="card flex flex-col items-center p-6 text-center"
    >
      <Triangle signs={signs} tense={!balanced} />
      <div className="mt-3 font-mono text-sm text-fg">{signs.map((s) => (s > 0 ? '+' : '−')).join(' ')}</div>
      <motion.div
        key={String(balanced)}
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className={`mt-2 rounded-full px-2.5 py-0.5 text-[11px] font-medium ${balanced ? 'bg-emerald-400/10 text-emerald-300' : 'bg-neg/15 text-neg'}`}
      >
        {balanced ? t('✓ balanced', '✓ 平衡') : t('⚡ unbalanced — tension', '⚡ 不平衡 · 存在张力')}
      </motion.div>
      <div className="mt-4 text-sm font-medium text-fg">{title}</div>
      <p className="mt-1 text-xs leading-relaxed text-fg-muted">{caption}</p>
    </motion.div>
  )
}

export default function Triads() {
  const t = useT()
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <TriadCard initial={[1, 1, 1]} title={t('Friends of friends', '朋友的朋友')} caption={t('Everyone gets along: one cohesive camp.', '大家彼此友好：一个团结的阵营。')} delay={0} />
      <TriadCard initial={[1, -1, -1]} title={t('The enemy of my enemy', '敌人的敌人是朋友')} caption={t('Two allies share a common opponent: the seed of two camps.', '两个盟友有共同的对手：两大阵营的雏形。')} delay={0.1} />
      <TriadCard
        initial={[1, 1, -1]}
        resolveTo={[1, -1, -1]}
        title={t('A friend of my friend is my enemy', '朋友的朋友是我的敌人')}
        caption={t('Unstable. Someone must switch sides — watch a tie flip.', '不稳定：总要有人选边站——看一条关系翻转。')}
        delay={0.2}
      />
      <TriadCard
        initial={[-1, -1, -1]}
        resolveTo={[1, -1, -1]}
        title={t('Everyone against everyone', '所有人彼此敌对')}
        caption={t('Unstable. Two of them will team up against the third.', '不稳定：其中两人会联手对付第三人。')}
        delay={0.3}
      />
    </div>
  )
}
