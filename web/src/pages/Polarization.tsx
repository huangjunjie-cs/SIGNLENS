import { useCallback, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Bars, DivergingHistogram } from '../components/charts'
import ForceGraph, { type GNode } from '../components/ForceGraph'
import { Card, DatasetPicker, ErrorBox, Loading, Metric, PageHeader, Segmented, SignKey } from '../components/ui'
import { api, fmt, pct, useAsync, type PolNode } from '../lib/api'
import { C, campColor, groupColorScale } from '../lib/colors'
import { useLabels, useT } from '../lib/i18n'

type ColorMode = 'camp' | 'community' | 'group'

export default function Polarization() {
  const t = useT()
  const L = useLabels()
  const [params, setParams] = useSearchParams()
  const id = params.get('dataset') ?? 'demo-polarized'
  const { data, error, loading } = useAsync(() => api.polarization(id), [id])
  const [color, setColor] = useState<ColorMode>('camp')
  const [layout, setLayout] = useState<'force' | 'axis'>('force')
  const [showFrus, setShowFrus] = useState(false)

  const groupColor = useMemo(() => groupColorScale(data?.nodes.map((n) => n.group) ?? []), [data])
  const nodes = useMemo(() => (data?.nodes ?? []).map((n, i) => ({ ...n, id: String(i), key: n.id }) as unknown as GNode), [data])
  const links = useMemo(
    () => (data?.links ?? []).map((l) => ({ source: String(l.source), target: String(l.target), sign: l.sign, frustrated: l.frustrated })),
    [data],
  )
  const nodeColor = useCallback(
    (n: GNode) => {
      const p = n as unknown as PolNode
      if (color === 'camp') return campColor(p.camp)
      if (color === 'community') return p.community === 1 ? C.campA : p.community === -1 ? C.campB : C.neutral
      return groupColor(p.group)
    },
    [color, groupColor],
  )
  const fixed = useCallback((n: GNode) => [(n as unknown as PolNode).x, (n as unknown as PolNode).y * 0.8] as [number, number], [])
  const maxDeg = useMemo(() => Math.max(1, ...(data?.nodes ?? []).map((n) => (n.positive ?? 0) + (n.negative ?? 0))), [data])
  const radius = useCallback((n: GNode) => 2.5 + 5 * Math.sqrt(((n.positive as number) + (n.negative as number)) / maxDeg), [maxDeg])

  const p = data?.profile
  const fr = p?.balance.frustration
  const hasGroups = !!p?.declared_groups

  return (
    <div>
      <PageHeader kicker={t('Polarization Lab', '极化实验室')} title={t('How polarized is this network?', '这个网络有多极化？')}>
        {t(
          'Four complementary lenses: how balanced the structure is, who the opposing camps are, how sealed off they are from each other, and how far apart they stand.',
          '四个互补的视角：结构有多平衡、对立阵营是谁、阵营之间有多隔绝、立场相距多远。',
        )}
      </PageHeader>

      <div className="mb-6 flex flex-wrap items-end gap-4">
        <DatasetPicker value={id} onChange={(v) => setParams({ dataset: v })} />
        {data?.truncated && <span className="pb-2 text-xs text-fg-subtle">{t(`Showing the ${data.nodes.length} highest-degree nodes; metrics use the full graph.`, `仅展示度数最高的 ${data.nodes.length} 个节点；指标基于完整网络计算。`)}</span>}
      </div>

      {error && <ErrorBox error={error} />}
      {loading && !data && <Loading label={t('Solving frustration, spectra and random walks…', '正在求解受挫指数、谱与随机游走…')} />}

      {p && fr && (
        <>
          <h2 className="label mb-3">① {t('Structure — distance to perfect balance', '结构 — 与完美平衡的距离')}</h2>
          <div className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Metric delay={0} label={t('Triangle balance', '三角平衡度')} value={p.balance.triangle_balance} help={t('Share of signed triangles with an even number of negative ties (+++ or +−−).', '负边数为偶数（+++ 或 +−−）的三角形所占比例。')} />
            <Metric delay={0.05} label={t('Frustration index', '受挫指数')} value={fr.index} display={`${fmt(fr.index)}`}
              hint={`${fr.frustration} / ${fr.total} ${t('ties frustrated', '条关系受挫')} · ${fr.exact ? t('exact optimum', '精确最优') : t('upper bound', '上界')}`}
              help={t('1 − 2F/m where F is the minimum number of ties violating any two-camp split (Aref & Wilson 2018). 1 = perfectly balanced.', '1 − 2F/m，F 为违反任意两阵营划分的最少关系数（Aref & Wilson 2018）。1 表示完全平衡。')} />
            <Metric delay={0.1} label={t('Algebraic conflict', '代数冲突')} value={p.balance.algebraic_conflict} max={0.5} polar="low" help={t('Smallest eigenvalue of the normalized signed Laplacian (Kunegis 2010). 0 iff balanced.', '归一化符号拉普拉斯矩阵的最小特征值（Kunegis 2010）。当且仅当平衡时为 0。')} />
            <Metric delay={0.15} label={t('Walk-based balance', '游走平衡度')} value={p.balance.walk_balance} polar="none"
              hint={t('β = 1 · drops quickly with density; compare similar-sized networks', 'β = 1 · 随密度增加快速下降；宜在规模相近的网络间比较')}
              help={t('tr e^A / tr e^|A| (Estrada & Benzi 2014): weighs closed walks of every length, not only triangles. 1 = balanced.', 'tr e^A / tr e^|A|（Estrada & Benzi 2014）：考虑所有长度的闭合游走，而不只是三角形。1 表示平衡。')} />
          </div>

          <div className="mb-8 grid gap-5 lg:grid-cols-[1fr_330px]">
            <Card
              title={t('The network, split into camps', '分裂为阵营的网络')}
              subtitle={layout === 'force'
                ? t('Force layout: positive ties attract, negative ties repel.', '力导向布局：正边相吸，负边相斥。')
                : t('Spectral layout: horizontal axis = leading eigenvector of the signed adjacency (the polarization axis).', '谱布局：横轴为符号邻接矩阵的主特征向量（极化轴）。')}
              right={<SignKey />}
            >
              <div className="mb-3 flex flex-wrap items-center gap-3">
                <Segmented value={color} onChange={setColor} options={[
                  { value: 'camp', label: t('Balance camps', '平衡阵营') },
                  { value: 'community', label: t('Polarized communities', '极化社群') },
                  ...(hasGroups ? [{ value: 'group' as ColorMode, label: t('Declared groups', '既有分组') }] : []),
                ]} />
                <Segmented value={layout} onChange={setLayout} options={[{ value: 'force', label: t('Force', '力导向') }, { value: 'axis', label: t('Spectral axis', '谱轴') }]} />
                <label className="inline-flex cursor-pointer items-center gap-2 text-xs text-fg-muted">
                  <input type="checkbox" checked={showFrus} onChange={(e) => setShowFrus(e.target.checked)} className="accent-[#8b7cf6]" />
                  {t('Highlight frustrated ties', '高亮受挫关系')}
                </label>
              </div>
              <ForceGraph
                nodes={nodes}
                links={links}
                height={520}
                nodeColor={nodeColor}
                nodeRadius={radius}
                fixed={layout === 'axis' ? fixed : null}
                highlightFrustrated={showFrus}
                tooltip={(n) => {
                  const q = n as unknown as PolNode
                  return (
                    <>
                      <div className="font-medium text-fg">{q.name}</div>
                      {q.group && <div className="text-fg-muted">{L.group(q.group)}</div>}
                      <div className="tabular mt-1 font-mono text-fg-muted">+{q.positive} / −{q.negative}</div>
                      <div className="text-fg-subtle">
                        {t('camp', '阵营')} {q.camp ? 'A' : 'B'} · {t('frustrated', '受挫')} {q.frustrated} · {t('bridging', '桥接')} {pct(q.bridging, 0)}
                      </div>
                    </>
                  )
                }}
              />
              <div className="mt-2 flex flex-wrap gap-4 text-xs text-fg-muted">
                {color !== 'group' ? (
                  <>
                    <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ background: C.campA }} />{color === 'camp' ? t('Camp A', '阵营 A') : 'S₁'}</span>
                    <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ background: C.campB }} />{color === 'camp' ? t('Camp B', '阵营 B') : 'S₂'}</span>
                    {color === 'community' && <span className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ background: C.neutral }} />{t('Neutral', '中立')}</span>}
                  </>
                ) : (
                  Array.from(new Set(data.nodes.map((n) => n.group))).slice(0, 6).map((g) => (
                    <span key={g} className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ background: groupColor(g) }} />{L.group(g)}</span>
                  ))
                )}
              </div>
            </Card>

            <div className="flex flex-col gap-5">
              <Card title={t('Signed triangles', '符号三角形')} subtitle={t('Balanced: +++ and +−−', '平衡：+++ 与 +−−')}>
                <Bars
                  height={190}
                  valueFormat={(v) => v.toLocaleString()}
                  yFormat={(v) => (v >= 1000 ? `${v / 1000}k` : String(v))}
                  data={(['+++', '++-', '+--', '---'] as const).map((k) => ({
                    label: k.replace(/-/g, '−'),
                    value: p.balance.triads[k] ?? 0,
                    color: k === '+++' || k === '+--' ? '#5b6b88' : C.neg,
                    note: k === '+++' || k === '+--' ? t('balanced', '平衡') : t('unbalanced', '不平衡'),
                  }))}
                />
              </Card>
              <Card title={t('Position on the polarization axis', '极化轴上的位置分布')} subtitle={t(`Bimodality coefficient ${fmt(p.positions.bimodality)} (> 0.555 suggests two modes)`, `双峰系数 ${fmt(p.positions.bimodality)}（> 0.555 提示双峰）`)}>
                <DivergingHistogram bins={data.position_histogram} leftLabel={t('Camp B', '阵营 B')} rightLabel={t('Camp A', '阵营 A')} />
              </Card>
            </div>
          </div>

          <h2 className="label mb-3">② {t('Camps — who opposes whom', '阵营 — 谁与谁对立')}</h2>
          <div className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label={t('Polarity', '极性')} value={p.polarized_communities.polarity} polar="none"
              hint={`|S₁| = ${p.polarized_communities.size[0]}, |S₂| = ${p.polarized_communities.size[1]} · ${t('coverage', '覆盖')} ${pct(p.polarized_communities.coverage, 0)}`}
              help={t('max xᵀAx / xᵀx over x ∈ {−1,0,1}ⁿ (Bonchi et al. 2019): two cohesive, mutually hostile communities; nodes outside both are neutral.', '在 x ∈ {−1,0,1}ⁿ 上最大化 xᵀAx / xᵀx（Bonchi 等 2019）：两个内部团结、彼此敌对的社群；不属于二者的节点为中立。')} />
            <Metric label={t('Camp sizes', '阵营规模')} value={null} polar="none" display={`${p.detected_camps.sizes[0]} : ${p.detected_camps.sizes[1]}`} hint={t('from the frustration-minimizing split', '来自最小受挫划分')} />
            <Metric label={t('Consistent ties', '一致关系占比')} value={p.detected_camps.stats.consistency} help={t('Ties that agree with the camps: positive inside or negative across.', '与阵营一致的关系：阵营内为正或阵营间为负。')} />
            {hasGroups ? (
              <Metric label={t('Groups ≈ camps (ARI)', '分组与阵营一致度（ARI）')} value={p.declared_groups!.agreement_with_camps} help={t('Do the declared groups (e.g. parties) coincide with the structurally detected camps?', '既有分组（如党派）是否与结构上检测出的阵营一致？')} />
            ) : (
              <Metric label={t('Negative tie ratio', '负边比例')} value={p.negative_ratio} />
            )}
          </div>

          <h2 className="label mb-3">③ {t('Separation — how sealed off are the camps', '隔离 — 阵营之间有多封闭')}</h2>
          <div className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label={t('Signed modularity', '符号模块度')} value={p.detected_camps.signed_modularity} max={0.6} help={t('Gómez et al. (2009): positive ties within and negative ties between camps beyond chance.', 'Gómez 等（2009）：阵营内正边、阵营间负边超出随机期望的程度。')} />
            <Metric label={t('Block contrast', '块对比度')} value={p.detected_camps.stats.contrast} help={t('Density-based: (d⁺in − d⁺out + d⁻out − d⁻in)/2. Rewards camps that simply avoid each other.', '基于密度：(d⁺内 − d⁺间 + d⁻间 − d⁻内)/2。阵营间互不往来也会得分。')} />
            <Metric label={t('E–I index of positive ties', '正边 E–I 指数')} value={p.detected_camps.stats.ei_positive} min={1} max={-1}
              help={t('(external − internal)/(total) for positive ties. −1: all cooperation stays inside camps.', '正边的（外部 − 内部）/ 总数。−1：所有合作都发生在阵营内部。')} />
            <Metric label={t('Random-walk controversy', '随机游走争议度')} value={p.detected_camps.rwc} min={-1} help={t('Garimella et al. (2018): probability that a random walk along positive ties stays in the camp it started in, minus crossing.', 'Garimella 等（2018）：沿正边的随机游走停留在出发阵营的概率减去跨越的概率。')} />
          </div>

          {hasGroups && (
            <>
              <h2 className="label mb-3">④ {t('Declared groups', '既有分组')}</h2>
              <div className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <Metric label={t('Positive-tie gap', '正边差距')} value={p.declared_groups!.stats.gap} min={-1} help={t('P(+ | same group) − P(+ | different groups).', 'P(+ | 同组) − P(+ | 不同组)。')} />
                <Metric label={t('Signed modularity', '符号模块度')} value={p.declared_groups!.signed_modularity} max={0.6} />
                <Metric label={t('Random-walk controversy', '随机游走争议度')} value={p.declared_groups!.rwc} min={-1} />
                <Metric label={t('Esteban–Ray polarization', 'Esteban–Ray 极化指数')} value={p.declared_groups!.esteban_ray} polar="none" help={t('Group identification × alienation along the polarization axis (Esteban & Ray 1994).', '沿极化轴的群体认同 × 疏离（Esteban & Ray 1994）。')} />
              </div>
            </>
          )}

          <h2 className="label mb-3">{t('Who matters', '关键人物')}</h2>
          <div className="grid gap-5 md:grid-cols-3">
            {([
              ['bridging', t('Bridges', '桥梁人物'), t('Share of positive ties that cross camps', '跨阵营正边的比例')],
              ['frustrated', t('Most frustrated', '最受挫者'), t('Share of ties contradicting the camp split', '与阵营划分矛盾的关系比例')],
              ['dissent', t('Dissenters', '异见者'), t('Share of negative ties aimed at own camp', '指向本阵营的负边比例')],
            ] as const).map(([key, title, sub]) => (
              <Card key={key} title={title} subtitle={sub}>
                <ol className="space-y-1.5">
                  {data.rankings[key].filter((r) => (r.value ?? 0) > 0).slice(0, 8).map((r, i) => (
                    <li key={r.id} className="flex items-center gap-3 text-sm">
                      <span className="w-4 text-right text-xs text-fg-subtle">{i + 1}</span>
                      <span className="flex-1 truncate text-fg">{r.name}</span>
                      <span className="h-1.5 w-16 overflow-hidden rounded-full bg-white/5">
                        <span className="block h-full rounded-full bg-accent" style={{ width: `${(r.value ?? 0) * 100}%` }} />
                      </span>
                      <span className="tabular w-10 text-right font-mono text-xs text-fg-muted">{pct(r.value, 0)}</span>
                    </li>
                  ))}
                  {!data.rankings[key].some((r) => (r.value ?? 0) > 0) && <li className="text-xs text-fg-subtle">{t('Nobody — perfectly sorted.', '无——完全分化。')}</li>}
                </ol>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
