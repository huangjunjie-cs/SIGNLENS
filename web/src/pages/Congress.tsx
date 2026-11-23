import * as d3 from 'd3'
import { AnimatePresence, motion } from 'motion/react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { LineChart, Tip, useWidth } from '../components/charts'
import ForceGraph, { type GNode } from '../components/ForceGraph'
import { Card, ErrorBox, Loading, Metric, PageHeader, Segmented, SignKey } from '../components/ui'
import { api, fmt, pct, useAsync, type CongressMember, type CongressSummary } from '../lib/api'
import { C, groupColorScale, partyColor } from '../lib/colors'
import { useLabels, useT } from '../lib/i18n'

type Chamber = 'H' | 'S'
type MetricKey = keyof CongressSummary

const ordinal = (n: number) => {
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return n + (s[(v - 20) % 10] || s[v] || s[0])
}

function Beeswarm({ members, axis, colorOf }: { members: CongressMember[]; axis: 'ours' | 'nominate'; colorOf: (p: string) => string }) {
  const t = useT()
  const L = useLabels()
  const [ref, width] = useWidth<HTMLDivElement>()
  const height = members.length > 200 ? 300 : 220
  const [hover, setHover] = useState<{ m: CongressMember; x: number; y: number } | null>(null)
  const pos = (m: CongressMember) => (axis === 'ours' ? m.x : m.nominate[0])
  const placed = useMemo(() => {
    const x = d3.scaleLinear().domain(axis === 'ours' ? [-1.35, 1.35] : [-1, 1]).range([24, width - 24]).clamp(true)
    const r = members.length > 200 ? 3.6 : 5.2
    const nodes = members
      .filter((m) => pos(m) !== null)
      .map((m) => ({ m, x: x(pos(m) as number), y: height / 2, tx: x(pos(m) as number) }))
    const sim = d3
      .forceSimulation(nodes)
      .force('x', d3.forceX<(typeof nodes)[number]>((d) => d.tx).strength(1))
      .force('y', d3.forceY(height / 2).strength(0.06))
      .force('c', d3.forceCollide(r + 0.6))
      .stop()
    for (let i = 0; i < 140; i++) sim.tick()
    return { nodes, x, r }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [members, axis, width, height])
  return (
    <div ref={ref} className="relative w-full">
      <svg width={width} height={height + 26}>
        <line x1={placed.x(0)} x2={placed.x(0)} y1={8} y2={height} stroke="rgba(255,255,255,0.12)" strokeDasharray="2 4" />
        {placed.nodes.map(({ m, x, y }) => (
          <motion.circle
            key={m.id}
            r={placed.r}
            initial={{ cx: placed.x(0), cy: height / 2, opacity: 0 }}
            animate={{ cx: x, cy: Math.max(placed.r, Math.min(height - placed.r, y)), opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.7, ease: 'easeInOut' }}
            fill={colorOf(m.party)}
            stroke={C.surface}
            strokeWidth={1.2}
            onMouseEnter={() => setHover({ m, x, y })}
            onMouseLeave={() => setHover(null)}
          />
        ))}
        <text x={24} y={height + 20} fill={C.subtle} fontSize={11}>← {t('liberal', '自由派')}</text>
        <text x={width - 24} y={height + 20} fill={C.subtle} fontSize={11} textAnchor="end">{t('conservative', '保守派')} →</text>
      </svg>
      {hover && (
        <Tip x={hover.x} y={hover.y} width={width}>
          <div className="font-medium text-fg">{hover.m.name}</div>
          <div className="text-fg-muted">
            {L.group(hover.m.party)} · {hover.m.state}
          </div>
          <div className="tabular mt-1 font-mono text-fg-muted">
            SIGNLENS {fmt(hover.m.x, 2)} · NOMINATE {fmt(hover.m.nominate[0], 2)}
          </div>
          {hover.m.bridging !== null && (
            <div className="text-fg-subtle">
              {t('cross-party allies', '跨党盟友占比')}: {pct(hover.m.bridging, 0)}
            </div>
          )}
        </Tip>
      )}
    </div>
  )
}

export default function Congress() {
  const t = useT()
  const L = useLabels()
  const [chamber, setChamber] = useState<Chamber>('H')
  const series = useAsync(() => api.congressSeries(chamber), [chamber])
  const other = useAsync(() => api.congressSeries(chamber === 'H' ? 'S' : 'H'), [chamber])
  const [congress, setCongress] = useState<number | null>(null)
  const [playing, setPlaying] = useState(false)
  const [axis, setAxis] = useState<'ours' | 'nominate'>('ours')
  const [metric, setMetric] = useState<MetricKey>('nominate_distance')
  const rows = series.data ?? []
  const range = rows.length ? [rows[0].congress, rows.at(-1)!.congress] : [1, 119]

  useEffect(() => {
    if (rows.length && (congress === null || congress > range[1])) setCongress(rows.at(-1)!.congress)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows.length])

  const detail = useAsync(() => (congress ? api.congress(chamber, congress) : null), [chamber, congress])
  const [shown, setShown] = useState(detail.data)
  useEffect(() => {
    if (detail.data) setShown(detail.data)
  }, [detail.data])

  useEffect(() => {
    if (!playing) return
    const id = setInterval(() => {
      setCongress((c) => {
        if (c === null || c >= range[1]) {
          setPlaying(false)
          return c
        }
        return c + 1
      })
    }, 1100)
    return () => clearInterval(id)
  }, [playing, range[0], range[1]])

  const metrics: { key: MetricKey; label: string; help: string }[] = [
    { key: 'nominate_distance', label: t('Party distance (DW-NOMINATE)', '党派距离（DW-NOMINATE）'), help: t('Difference of party means on NOMINATE dimension 1.', 'NOMINATE 第一维上两党均值之差。') },
    { key: 'party_distance', label: t('Party distance (SIGNLENS ideal points)', '党派距离（SIGNLENS 理想点）'), help: t('Same, using our vote-matrix ideal points.', '使用本工具从投票矩阵估计的理想点。') },
    { key: 'party_contrast', label: t('Party block contrast', '党派块对比度'), help: t('Positive-tie density inside parties minus across, plus negative-tie density across minus inside, halved.', '党内正边密度减党际正边密度，加上党际负边密度减党内负边密度，再除以 2。') },
    { key: 'between_agreement', label: t('Cross-party agreement', '跨党一致率'), help: t('Mean share of roll calls on which a Democrat and a Republican vote the same way.', '一名民主党人与一名共和党人投票相同的平均比例。') },
    { key: 'nominate_overlap', label: t('Members in the overlap', '重叠区成员数'), help: t('Members positioned beyond the most moderate member of the other party.', '立场越过对方党派最温和成员的人数。') },
    { key: 'frustration_ratio', label: t('Frustration ratio', '受挫比例'), help: t('Share of co-voting ties that contradict the best two-camp split.', '与最优两阵营划分相矛盾的关系比例。') },
    { key: 'polarity_norm', label: t('Polarity (normalized)', '极性（归一化）'), help: t('Bonchi et al. polarity of the best pair of opposing communities divided by (n − 1).', 'Bonchi 等提出的最佳对立社群极性，除以 (n−1)。') },
    { key: 'rwc', label: t('Random-walk controversy', '随机游走争议度'), help: t('Probability gap that a random walk from one party stays in it.', '从一党出发的随机游走停留在本党的概率差。') },
    { key: 'negative_ratio', label: t('Negative tie ratio', '负边比例'), help: t('Share of member pairs who vote against each other ≥70% of the time, among all ties.', '在所有关系中，投相反票比例 ≥70% 的议员对所占比例。') },
  ]
  const m = metrics.find((x) => x.key === metric)!
  const toSeries = (rs: CongressSummary[]) => rs.map((r) => ({ x: r.congress, y: (r[metric] as number | null) ?? null }))
  const colorOf = useMemo(() => {
    const scale = groupColorScale(shown?.members.map((x) => x.party) ?? [])
    return (p: string) => (p === 'Democrat' || p === 'Republican' ? partyColor(p) : scale(p))
  }, [shown])
  const parties = useMemo(() => {
    const c = d3.rollups(shown?.members ?? [], (v) => v.length, (d) => d.party).sort((a, b) => b[1] - a[1])
    return c
  }, [shown])

  const graphNodes = useMemo(() => (shown?.members ?? []).map((x, i) => ({ ...x, id: String(i) }) as unknown as GNode), [shown])
  const graphLinks = useMemo(() => (shown?.edges ?? []).map(([a, b, s]) => ({ source: String(a), target: String(b), sign: s })), [shown])
  const nodeColor = useCallback((n: GNode) => colorOf(String(n.party)), [colorOf])
  const s = shown?.summary
  const chamberName = chamber === 'H' ? t('House', '众议院') : t('Senate', '参议院')

  if (series.error)
    return (
      <div>
        <PageHeader kicker={t('Case study', '案例')} title={t('Polarization in the U.S. Congress', '美国国会的极化')} />
        <ErrorBox error={`${series.error}. ${t('Build the data with `signlens congress`.', '请先运行 `signlens congress` 生成数据。')}`} />
      </div>
    )

  return (
    <div>
      <PageHeader kicker={t('Case study · Voteview roll calls 1789–2026', '案例 · Voteview 唱名投票 1789–2026')} title={t('Polarization in the U.S. Congress', '美国国会的极化')}>
        {t(
          'Each Congress becomes a signed network: two members are tied + if they vote together on ≥70% of shared roll calls and − if on ≤30%. Ideal points are estimated from the vote matrix and checked against DW-NOMINATE.',
          '每届国会都被构造成一个符号网络：两名议员在共同参与的投票中一致率 ≥70% 则连正边，≤30% 则连负边。理想点由投票矩阵估计，并与 DW-NOMINATE 对照验证。',
        )}
      </PageHeader>

      <div className="mb-5 flex flex-wrap items-end gap-4">
        <Segmented value={chamber} onChange={(v) => setChamber(v)} options={[{ value: 'H', label: t('House', '众议院') }, { value: 'S', label: t('Senate', '参议院') }]} />
        <label className="flex flex-col gap-1.5">
          <span className="label">{t('Metric', '指标')}</span>
          <select className="input min-w-72" value={metric} onChange={(e) => setMetric(e.target.value as MetricKey)}>
            {metrics.map((x) => (
              <option key={x.key} value={x.key}>{x.label}</option>
            ))}
          </select>
        </label>
      </div>

      <Card title={m.label} subtitle={`${m.help} ${t('Click the chart to jump to a Congress.', '点击图表跳转到对应国会。')}`}>
        {series.loading && !rows.length ? (
          <Loading />
        ) : (
          <LineChart
            height={250}
            series={[
              { key: chamber, label: chamberName, color: C.campA, values: toSeries(rows) },
              { key: 'o', label: chamber === 'H' ? t('Senate', '参议院') : t('House', '众议院'), color: C.subtle, dashed: true, values: toSeries(other.data ?? []) },
            ]}
            xFormat={(c) => t(`${ordinal(c)} · ${1789 + 2 * (c - 1)}`, `第${c}届 · ${1789 + 2 * (c - 1)}`)}
            cursorX={congress}
            onPickX={(c) => setCongress(c)}
            animate={false}
          />
        )}
      </Card>

      {/* timeline */}
      <div className="sticky top-14 z-30 -mx-5 mt-5 border-y border-white/[0.06] bg-ink-900/85 px-5 py-3 backdrop-blur-xl">
        <div className="flex items-center gap-4">
          <button className="btn-primary w-24 justify-center" onClick={() => {
            if (!playing && congress === range[1]) setCongress(range[0])
            setPlaying((p) => !p)
          }}>
            {playing ? t('❚❚ Pause', '❚❚ 暂停') : t('▶ Play', '▶ 播放')}
          </button>
          <input type="range" min={range[0]} max={range[1]} value={congress ?? range[1]} onChange={(e) => setCongress(+e.target.value)} className="flex-1" />
          <div className="w-44 text-right">
            <div className="font-display text-lg font-semibold">{congress ? t(`${ordinal(congress)} Congress`, `第 ${congress} 届国会`) : '—'}</div>
            <div className="tabular text-xs text-fg-subtle">{congress ? `${1789 + 2 * (congress - 1)}–${1791 + 2 * (congress - 1)}` : ''}</div>
          </div>
        </div>
      </div>

      {detail.error && <div className="mt-5"><ErrorBox error={detail.error} /></div>}

      {shown && s && (
        <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_340px]">
          <div className="flex flex-col gap-5">
            <Card
              title={t(`Where ${chamberName} members stand`, `${chamberName}议员的立场分布`)}
              subtitle={t('Each dot is a member, placed on the first ideological dimension. Members keep their identity across Congresses — press Play to watch the parties pull apart.', '每个点是一位议员，位于第一意识形态维度上。议员在各届之间保持身份——点击播放，观察两党如何分离。')}
              right={<Segmented value={axis} onChange={setAxis} options={[{ value: 'ours', label: 'SIGNLENS' }, { value: 'nominate', label: 'DW-NOMINATE' }]} />}
            >
              <div className="mb-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-fg-muted">
                {parties.slice(0, 5).map(([p, n]) => (
                  <span key={p} className="inline-flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: colorOf(p) }} />
                    {L.group(p)} <span className="text-fg-subtle">{n}</span>
                  </span>
                ))}
              </div>
              <AnimatePresence>
                <Beeswarm members={shown.members} axis={axis} colorOf={colorOf} />
              </AnimatePresence>
            </Card>
            <Card
              title={t('Co-voting network', '共同投票网络')}
              subtitle={t('Strongest ties per member (4 positive, 2 negative). Positive ties pull members together; negative ties push them apart.', '每位议员最强的关系（4 条正边、2 条负边）。正边相吸，负边相斥。')}
              right={<SignKey />}
            >
              <ForceGraph
                nodes={graphNodes}
                links={graphLinks}
                height={460}
                nodeColor={nodeColor}
                nodeRadius={() => (graphNodes.length > 200 ? 3.5 : 5)}
                tooltip={(n) => (
                  <>
                    <div className="font-medium text-fg">{String(n.name)}</div>
                    <div className="text-fg-muted">{L.group(String(n.party))} · {String(n.state)}</div>
                  </>
                )}
              />
            </Card>
          </div>

          <div className="flex flex-col gap-3">
            <motion.div key={s.congress} initial={{ opacity: 0.4 }} animate={{ opacity: 1 }} className="card p-5">
              <div className="label">{t('Composition', '构成')}</div>
              <div className="mt-2 text-sm text-fg-muted">
                {s.members} {t('members', '名议员')} · {s.rollcalls.toLocaleString()} {t('roll calls', '次唱名投票')} · {s.ties.toLocaleString()} {t('ties', '条关系')}
              </div>
              <div className="mt-3 flex h-2 overflow-hidden rounded-full">
                {s.parties.map((p, i) => (
                  <motion.div key={p} animate={{ width: `${(s.party_sizes[i] / s.members) * 100}%` }} style={{ background: colorOf(p) }} className="mr-0.5 h-full last:mr-0" />
                ))}
              </div>
            </motion.div>
            <Metric label={t('Party distance (ours)', '党派距离（本工具）')} value={s.party_distance} min={0} max={2} help={t('Gap between party mean ideal points; axis scaled so 98% of members lie within ±1.', '两党平均理想点之差；坐标已缩放，使 98% 的议员位于 ±1 之内。')} />
            <Metric label={t('Members in the overlap', '重叠区成员数')} value={s.party_overlap} display={String(s.party_overlap ?? '—')} min={0} max={Math.max(40, s.members / 3)} polar="low" help={t('How many members sit beyond the most moderate member of the other party.', '立场越过对方党派最温和成员的人数。')} />
            <Metric label={t('Cross-party agreement', '跨党一致率')} value={s.between_agreement} display={pct(s.between_agreement)} polar="low" hint={`${t('within-party', '党内')}: ${pct(s.within_agreement)}`} />
            <Metric label={t('Party block contrast', '党派块对比度')} value={s.party_contrast} help={t('1 = all co-partisans allied and all opponents hostile; 0 = party says nothing about ties.', '1 = 同党全为盟友、异党全为对手；0 = 党派与关系无关。')} />
            <Metric label={t('Camps ≈ parties (ARI)', '阵营与党派一致度（ARI）')} value={s.camp_party_ari} help={t('Adjusted Rand index between the two camps found by the frustration partition (party-blind) and party membership.', '基于受挫划分（不使用党派信息）得到的两阵营与党派归属之间的调整兰德指数。')} />
            <Metric label={t('Random-walk controversy', '随机游走争议度')} value={s.rwc} min={-1} />
            <Metric label={t('Ideal points vs NOMINATE (r)', '理想点与 NOMINATE 相关系数')} value={s.nominate_correlation} polar="none" />
          </div>
        </div>
      )}
      {!shown && detail.loading && <Loading />}
    </div>
  )
}
