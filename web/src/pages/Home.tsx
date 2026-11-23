import { motion } from 'motion/react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { LineChart } from '../components/charts'
import CampSplit from '../components/home/CampSplit'
import PolarizationHero from '../components/home/PolarizationHero'
import Triads from '../components/home/Triads'
import { api, useAsync } from '../lib/api'
import { C } from '../lib/colors'
import { useT } from '../lib/i18n'

function Section({ kicker, title, children, lead }: { kicker: string; title: string; lead?: ReactNode; children: ReactNode }) {
  return (
    <section className="mx-auto max-w-7xl px-5 py-20 md:py-28">
      <motion.div initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-80px' }} transition={{ duration: 0.6 }} className="mb-10 max-w-3xl">
        <div className="label mb-3 text-accent!">{kicker}</div>
        <h2 className="font-display text-3xl font-semibold leading-tight tracking-tight md:text-[42px]">{title}</h2>
        {lead && <p className="mt-4 text-[16px] leading-relaxed text-fg-muted">{lead}</p>}
      </motion.div>
      {children}
    </section>
  )
}

function CongressTeaser() {
  const t = useT()
  const h = useAsync(() => api.congressSeries('H'), [])
  const s = useAsync(() => api.congressSeries('S'), [])
  if (h.error || s.error)
    return (
      <div className="card p-6 text-sm text-fg-muted">
        {t('The Congress series has not been built yet. Run', '国会时间序列尚未生成，请运行')}{' '}
        <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-fg">signlens congress</code>
      </div>
    )
  if (!h.data || !s.data) return <div className="card h-[380px] animate-pulse" />
  const toSeries = (rows: typeof h.data, key: 'nominate_distance' | 'party_contrast') =>
    rows!.filter((r) => r.parties.includes('Democrat') && r.parties.includes('Republican')).map((r) => ({ x: r.start_year, y: r[key] }))
  const lastOverlap = [...h.data].reverse().find((r) => (r.nominate_overlap ?? 0) > 0)
  const latest = h.data.at(-1)
  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
      <div className="card p-5">
        <div className="mb-1 text-sm font-semibold">{t('Distance between Democrats and Republicans', '民主党与共和党之间的距离')}</div>
        <div className="mb-3 text-xs text-fg-subtle">
          {t('Difference of party means on the first DW-NOMINATE dimension, per Congress (1857 – today).', '每届国会两党在 DW-NOMINATE 第一维度上均值之差（1857 年至今）。')}
        </div>
        <LineChart
          drawOnScroll
          height={320}
          series={[
            { key: 'H', label: t('House', '众议院'), color: C.campA, values: toSeries(h.data, 'nominate_distance') },
            { key: 'S', label: t('Senate', '参议院'), color: C.campB, values: toSeries(s.data, 'nominate_distance') },
          ]}
          annotations={[
            { x: 1861, label: t('Civil War', '内战') },
            { x: 1933, label: t('New Deal', '新政') },
            { x: 1964, label: t('Civil Rights Act', '民权法案') },
            { x: 1995, label: t('“Contract with America”', '《美利坚契约》') },
          ]}
        />
      </div>
      <div className="flex flex-col gap-4">
        <div className="card flex-1 p-5">
          <div className="label">{t('House members in the ideological overlap', '处于意识形态重叠区的众议员')}</div>
          <div className="mt-2 font-display text-5xl font-semibold text-fg">{latest?.nominate_overlap ?? '—'}</div>
          <p className="mt-2 text-xs leading-relaxed text-fg-muted">
            {t(
              `In the ${latest?.congress}th Congress no Democrat sits to the right of the most liberal Republican (or vice-versa). The last Congress with any overlap began in ${lastOverlap?.start_year ?? '—'}.`,
              `第 ${latest?.congress} 届国会中，没有任何民主党人比最自由派的共和党人更偏右（反之亦然）。最后一届仍存在重叠的国会始于 ${lastOverlap?.start_year ?? '—'} 年。`,
            )}
          </p>
        </div>
        <Link to="/congress" className="card group flex items-center justify-between p-5 transition hover:border-accent/40">
          <div>
            <div className="text-sm font-semibold">{t('Explore 230 years of roll calls', '探索 230 年的唱名投票')}</div>
            <div className="text-xs text-fg-subtle">{t('Animated, Congress by Congress', '逐届国会动态呈现')}</div>
          </div>
          <span className="text-xl text-accent transition group-hover:translate-x-1">→</span>
        </Link>
      </div>
    </div>
  )
}

const AXES = [
  { icon: '△', en: ['Structure', 'How close is the whole network to two perfectly hostile camps? Triangle balance, frustration index, algebraic conflict, walk balance.'], zh: ['结构', '整个网络离“两个完全对立的阵营”有多近？三角平衡、受挫指数、代数冲突、游走平衡。'] },
  { icon: '◐', en: ['Camps', 'Who forms the opposing sides? Balance partitions and polarized communities (Bonchi et al.) — including the neutral middle.'], zh: ['阵营', '对立的双方是谁？平衡划分与极化社群（Bonchi 等）——也识别中立者。'] },
  { icon: '⇹', en: ['Separation', 'How sealed off are the camps? Signed modularity, E–I index, block contrast, random-walk controversy.'], zh: ['隔离', '阵营之间有多封闭？符号模块度、E–I 指数、块对比度、随机游走争议度。'] },
  { icon: '⟷', en: ['Positions', 'Where does everyone stand on a latent axis? Ideal points from votes, bimodality, party overlap, Esteban–Ray.'], zh: ['立场', '每个人在潜在轴上的位置？投票理想点、双峰系数、党派重叠、Esteban–Ray 指数。'] },
]

const TOOLS = [
  { to: '/polarization', en: ['Polarization Lab', 'Full polarization profile of any network, with camps, frustrated ties and bridges.'], zh: ['极化实验室', '任意网络的完整极化画像：阵营、受挫关系与桥梁人物。'] },
  { to: '/individual', en: ['Individual analysis', 'Ego networks around chosen people and the history of each relationship.'], zh: ['个体分析', '围绕指定人物的自我网络，以及每段关系的来龙去脉。'] },
  { to: '/temporal', en: ['Group analysis over time', 'Track how balance and polarization evolve across time windows.'], zh: ['群体演化分析', '追踪平衡与极化在时间窗口上的演变。'] },
  { to: '/data', en: ['Your data', 'Upload a signed edge list and get the descriptive report.'], zh: ['你的数据', '上传符号边表，获得描述性统计报告。'] },
]

export default function Home() {
  const t = useT()
  const L = (o: { en: string[]; zh: string[] }, i: number) => t(o.en[i], o.zh[i])
  return (
    <div>
      {/* HERO */}
      <section className="relative -mt-14 h-[100svh] min-h-[640px] overflow-hidden">
        <div className="grid-bg absolute inset-0 opacity-60" />
        <div className="glow-a absolute -left-40 top-20 h-[520px] w-[520px] opacity-70" />
        <div className="glow-b absolute -right-40 top-40 h-[520px] w-[520px] opacity-70" />
        <div className="absolute inset-0">
          <PolarizationHero />
        </div>
        <div className="pointer-events-none absolute inset-y-0 left-0 hidden w-[46%] bg-gradient-to-r from-ink-900/90 via-ink-900/50 to-transparent lg:block">
        </div>
        <div className="pointer-events-none relative mx-auto max-w-7xl px-5 pt-28 md:pt-32">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="max-w-2xl">
            <div className="label mb-4 text-accent!">SIGNLENS 2</div>
            <h1 className="font-display text-4xl font-semibold leading-[1.08] tracking-tight [text-wrap:balance] md:text-[56px]">
              {t('Societies don’t just disagree.', '社会不只是意见不合，')}
              <br />
              <span className="bg-gradient-to-r from-camp-a via-accent to-camp-b bg-clip-text text-transparent">{t('They split.', '它会分裂。')}</span>
            </h1>
            <p className="mt-5 max-w-md text-[15px] leading-relaxed text-fg-muted">
              {t(
                'SIGNLENS measures polarization from the signs of relationships — who cooperates, who opposes — using signed graph theory.',
                'SIGNLENS 从关系的“符号”——谁合作、谁对立——出发，用符号图理论度量和刻画社会极化。',
              )}
            </p>
            <div className="pointer-events-auto mt-7 flex flex-wrap gap-3">
              <Link to="/congress" className="btn-primary">{t('Explore the U.S. Congress', '探索美国国会')} →</Link>
              <Link to="/polarization" className="btn-ghost">{t('Open the lab', '打开实验室')}</Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* BALANCE THEORY */}
      <Section
        kicker={t('01 · Balance theory', '01 · 结构平衡理论')}
        title={t('Polarization starts in triangles.', '极化始于三角形。')}
        lead={t(
          'Heider (1946) observed that some triads of relationships are stable and others create tension. A triangle is balanced when it has an even number of negative ties.',
          'Heider（1946）发现，有些三人关系是稳定的，有些则充满张力。负向关系的数目为偶数时，三角形是平衡的。',
        )}
      >
        <Triads />
      </Section>

      {/* STRUCTURE THEOREM */}
      <Section
        kicker={t('02 · From triangles to camps', '02 · 从三角形到阵营')}
        title={t('A perfectly balanced society is a perfectly polarized one.', '完全平衡的社会，就是完全极化的社会。')}
        lead={t(
          'Cartwright & Harary (1956) proved that if every cycle is balanced, the network splits into two camps — friends inside, enemies across. Real networks are never perfect, so we measure the distance to this ideal.',
          'Cartwright 与 Harary（1956）证明：若所有环都平衡，网络必然分裂为两个阵营——内部友好，彼此敌对。真实网络从不完美，因此我们度量它与这一理想状态的距离。',
        )}
      >
        <div className="grid items-center gap-8 lg:grid-cols-2">
          <CampSplit />
          <div className="grid gap-4 sm:grid-cols-2">
            {AXES.map((a, i) => (
              <motion.div
                key={a.icon}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="card p-5"
              >
                <div className="mb-2 flex h-9 w-9 items-center justify-center rounded-lg bg-accent/15 text-lg text-accent">{a.icon}</div>
                <div className="text-sm font-semibold">{L(a, 0)}</div>
                <p className="mt-1 text-xs leading-relaxed text-fg-muted">{L(a, 1)}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </Section>

      {/* CONGRESS */}
      <Section
        kicker={t('03 · Case study', '03 · 案例')}
        title={t('Two centuries of the U.S. Congress', '美国国会两百年')}
        lead={t(
          'Every roll call since 1789, from Voteview. Members who vote together are tied +, members who vote against each other are tied −. By this measure the parties are now further apart than at any point since the Civil War.',
          '数据来自 Voteview，涵盖 1789 年以来的每一次唱名投票。经常一起投票的议员之间连正边，经常投相反票的连负边。按这一度量，两党如今的距离超过了南北战争以来的任何时期。',
        )}
      >
        <CongressTeaser />
      </Section>

      {/* TOOLS */}
      <Section kicker={t('04 · Toolkit', '04 · 工具')} title={t('Bring your own network.', '分析你自己的网络。')}>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {TOOLS.map((tool, i) => (
            <motion.div key={tool.to} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.07 }}>
              <Link to={tool.to} className="card group block h-full p-5 transition hover:-translate-y-0.5 hover:border-accent/40">
                <div className="flex items-center justify-between text-sm font-semibold">
                  {L(tool, 0)}
                  <span className="text-accent transition group-hover:translate-x-1">→</span>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-fg-muted">{L(tool, 1)}</p>
              </Link>
            </motion.div>
          ))}
        </div>
        <div className="mt-8 rounded-2xl border border-white/[0.06] bg-ink-850 p-5 font-mono text-[13px] text-fg-muted">
          <span className="text-fg-subtle">$</span> pip install signlens{'\n'}
          <br />
          <span className="text-fg-subtle">$</span> signlens polarization edges.tsv --labels parties.tsv
        </div>
      </Section>
    </div>
  )
}
