import { AnimatePresence, motion } from 'motion/react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import ForceGraph, { type GLink, type GNode } from '../components/ForceGraph'
import { Card, DatasetPicker, ErrorBox, Loading, PageHeader, Segmented, SignKey, Stat } from '../components/ui'
import { api, fmt, pct, useAsync, type EgoNode, type NodeRef } from '../lib/api'
import { C, campColor, groupColorScale } from '../lib/colors'
import { useLabels, useT } from '../lib/i18n'

function NodeSearch({ dataset, selected, onChange }: { dataset: string; selected: NodeRef[]; onChange: (n: NodeRef[]) => void }) {
  const t = useT()
  const L = useLabels()
  const [q, setQ] = useState('')
  const [debounced, setDebounced] = useState('')
  const [open, setOpen] = useState(false)
  useEffect(() => {
    const id = setTimeout(() => setDebounced(q), 220)
    return () => clearTimeout(id)
  }, [q])
  const { data } = useAsync(() => api.nodes(dataset, debounced), [dataset, debounced])
  const sel = new Set(selected.map((s) => s.id))
  return (
    <div className="relative flex-1">
      <span className="label">{t('People / nodes', '人物 / 节点')}</span>
      <div className="input mt-1.5 flex min-h-10 flex-wrap items-center gap-1.5 py-1.5!">
        {selected.map((s) => (
          <span key={s.id} className="inline-flex items-center gap-1 rounded-md bg-accent/20 px-2 py-0.5 text-xs text-fg">
            {s.name}
            <button className="text-fg-subtle hover:text-fg" onClick={() => onChange(selected.filter((x) => x.id !== s.id))}>×</button>
          </span>
        ))}
        <input
          className="min-w-32 flex-1 bg-transparent text-sm outline-none placeholder:text-fg-subtle"
          placeholder={selected.length ? '' : t('Search by name or id…', '按姓名或 ID 搜索…')}
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
        />
      </div>
      <AnimatePresence>
        {open && data && data.length > 0 && (
          <motion.ul
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="absolute z-40 mt-1 max-h-72 w-full overflow-auto rounded-xl border border-white/10 bg-ink-800 p-1 shadow-2xl"
          >
            {!debounced && <li className="px-3 py-1.5 text-[11px] text-fg-subtle">{t('Most connected', '连接最多的节点')}</li>}
            {data.map((n) => (
              <li key={n.id}>
                <button
                  disabled={sel.has(n.id)}
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => {
                    onChange([...selected, n])
                    setQ('')
                  }}
                  className="flex w-full items-center justify-between rounded-lg px-3 py-1.5 text-left text-sm hover:bg-white/5 disabled:opacity-40"
                >
                  <span className="truncate">
                    {n.name} {n.group && <span className="text-xs text-fg-subtle">· {L.group(n.group)}</span>}
                  </span>
                  <span className="tabular font-mono text-xs text-fg-subtle">
                    +{n.positive} −{n.negative}
                  </span>
                </button>
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  )
}

function RelationPanel({ dataset, link, onClose }: { dataset: string; link: GLink; onClose: () => void }) {
  const t = useT()
  const { data, loading, error } = useAsync(() => api.relationship(dataset, link.source, link.target), [dataset, link.source, link.target])
  return (
    <Card title={data ? `${data.x.name} ↔ ${data.y.name}` : t('Relationship', '关系')} right={<button className="text-fg-subtle hover:text-fg" onClick={onClose}>×</button>}>
      {loading && <Loading />}
      {error && <ErrorBox error={error} />}
      {data && (
        <>
          <div className="mb-3 text-xs text-fg-subtle">
            {data.relations.length} {t('recorded interactions', '条记录的互动')} · {t('net sign', '净符号')}{' '}
            <span className={link.sign > 0 ? 'text-pos' : 'text-neg'}>{link.sign > 0 ? '+' : '−'}</span>
          </div>
          <ul className="max-h-80 space-y-2 overflow-auto pr-1">
            {data.relations.map((r, i) => (
              <li key={i} className="rounded-lg border border-white/[0.06] bg-ink-900/60 px-3 py-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-fg-muted">{r.from} → {r.to}</span>
                  <span className={`font-mono ${r.sign > 0 ? 'text-pos' : 'text-neg'}`}>{r.sign > 0 ? '+' : '−'}</span>
                </div>
                {r.info && <div className="mt-1 text-fg">{String((r.info as Record<string, unknown>).Info ?? JSON.stringify(r.info))}</div>}
                {r.time !== null && <div className="mt-0.5 text-fg-subtle">{t('time', '时间')}: {r.time}</div>}
              </li>
            ))}
          </ul>
        </>
      )}
    </Card>
  )
}

function NodePanel({ dataset, node, onAdd, onClose }: { dataset: string; node: string; onAdd: (n: NodeRef) => void; onClose: () => void }) {
  const t = useT()
  const L = useLabels()
  const { data, loading, error } = useAsync(() => api.node(dataset, node), [dataset, node])
  const pol = data?.polarization as Record<string, number | string | null> | undefined
  return (
    <Card title={data?.name ?? node} subtitle={L.group(data?.group)} right={<button className="text-fg-subtle hover:text-fg" onClick={onClose}>×</button>}>
      {loading && <Loading />}
      {error && <ErrorBox error={error} />}
      {data && pol && (
        <>
          <div className="grid grid-cols-3 gap-3">
            <Stat label={t('positive', '正向')} value={data.positive} />
            <Stat label={t('negative', '负向')} value={data.negative} />
            <Stat label={t('camp', '阵营')} value={String(pol.camp)} />
          </div>
          <div className="mt-4 grid grid-cols-3 gap-3">
            <Stat label={t('bridging', '桥接')} value={pct(pol.bridging as number, 0)} />
            <Stat label={t('dissent', '异见')} value={pct(pol.dissent as number, 0)} />
            <Stat label={t('position', '位置')} value={fmt(pol.position as number, 2)} />
          </div>
          {data.info && (
            <dl className="mt-4 grid max-h-52 grid-cols-[auto_1fr] gap-x-3 gap-y-1 overflow-auto text-xs">
              {Object.entries(data.info)
                .filter(([, v]) => v !== '' && v !== null && typeof v !== 'object')
                .slice(0, 16)
                .map(([k, v]) => (
                  <div key={k} className="contents">
                    <dt className="text-fg-subtle">{k}</dt>
                    <dd className="truncate text-fg-muted">{String(v)}</dd>
                  </div>
                ))}
            </dl>
          )}
          <button className="btn-ghost mt-4 w-full justify-center text-xs" onClick={() => onAdd({ id: data.id, name: data.name, group: data.group })}>
            + {t('add to query', '加入查询')}
          </button>
        </>
      )}
    </Card>
  )
}

export default function Individual() {
  const t = useT()
  const L = useLabels()
  const [params, setParams] = useSearchParams()
  const dataset = params.get('dataset') ?? 'demo-polarized'
  const [selected, setSelected] = useState<NodeRef[]>([])
  const [depth, setDepth] = useState(1)
  const [query, setQuery] = useState<{ nodes: string[]; depth: number } | null>(null)
  const [colorBy, setColorBy] = useState<'camp' | 'group'>('camp')
  const [link, setLink] = useState<GLink | null>(null)
  const [node, setNode] = useState<string | null>(null)

  // preselect the two most connected nodes so the page is never empty
  const top = useAsync(() => api.nodes(dataset), [dataset])
  useEffect(() => {
    if (top.data && top.data.length >= 2) {
      const init = top.data.slice(0, 2)
      setSelected(init)
      setQuery({ nodes: init.map((n) => n.id), depth: 1 })
      setLink(null)
      setNode(null)
    }
  }, [top.data])

  const ego = useAsync(() => (query && query.nodes.length ? api.ego(dataset, query.nodes, query.depth) : null), [dataset, JSON.stringify(query)])
  const groupColor = useMemo(() => groupColorScale(ego.data?.nodes.map((n) => n.group) ?? []), [ego.data])
  const nodes = useMemo(() => (ego.data?.nodes ?? []) as unknown as GNode[], [ego.data])
  const links = useMemo(() => (ego.data?.links ?? []) as unknown as GLink[], [ego.data])
  const nodeColor = useCallback(
    (n: GNode) => (colorBy === 'camp' ? campColor((n as unknown as EgoNode).camp) : groupColor((n as unknown as EgoNode).group)),
    [colorBy, groupColor],
  )
  const info = ego.data?.info
  const hasGroups = nodes.some((n) => n.group)

  return (
    <div>
      <PageHeader kicker={t('Individual analysis', '个体分析')} title={t('Who stands with whom?', '谁与谁站在一起？')}>
        {t(
          'Pick one or more people to see their signed neighbourhood: allies, opponents, and how the local network splits into camps. Click a tie to read its history, or a person for their profile.',
          '选择一个或多个人物，查看他们的符号邻域：盟友、对手，以及局部网络如何分裂为阵营。点击关系查看其记录，点击人物查看其画像。',
        )}
      </PageHeader>

      <Card className="mb-5">
        <div className="flex flex-wrap items-end gap-4">
          <DatasetPicker value={dataset} onChange={(v) => setParams({ dataset: v })} />
          <NodeSearch dataset={dataset} selected={selected} onChange={setSelected} />
          <label className="flex flex-col gap-1.5">
            <span className="label">{t('Depth', '深度')}</span>
            <Segmented value={String(depth)} onChange={(v) => setDepth(+v)} options={[0, 1, 2].map((d) => ({ value: String(d), label: d === 0 ? t('only them', '仅自身') : `${d}-hop` }))} />
          </label>
          <button className="btn-primary" disabled={!selected.length} onClick={() => { setQuery({ nodes: selected.map((s) => s.id), depth }); setLink(null) }}>
            {t('Analyze', '分析')}
          </button>
        </div>
      </Card>

      {ego.error && <ErrorBox error={ego.error} />}
      <div className="grid gap-5 lg:grid-cols-[1fr_340px]">
        <Card
          title={t('Signed ego network', '符号自我网络')}
          subtitle={t('Query people are labelled. Colours show the two camps that best explain this neighbourhood.', '查询人物带标签。颜色表示最能解释该邻域的两个阵营。')}
          right={<SignKey />}
        >
          {hasGroups && (
            <div className="mb-3">
              <Segmented value={colorBy} onChange={setColorBy} options={[{ value: 'camp', label: t('Camps', '阵营') }, { value: 'group', label: t('Groups', '分组') }]} />
            </div>
          )}
          {ego.loading && !ego.data ? (
            <Loading />
          ) : (
            <ForceGraph
              nodes={nodes}
              links={links}
              height={560}
              nodeColor={nodeColor}
              nodeRadius={(n) => ((n as unknown as EgoNode).seed ? 9 : 4.5)}
              showLabel={(n) => !!(n as unknown as EgoNode).seed || nodes.length < 30}
              selected={node}
              onNodeClick={(n) => { setNode(n.id); setLink(null) }}
              onLinkClick={(l) => { setLink(l); setNode(null) }}
              tooltip={(n) => (
                <>
                  <div className="font-medium text-fg">{String(n.name)}</div>
                  {n.group ? <div className="text-fg-muted">{L.group(String(n.group))}</div> : null}
                  <div className="tabular font-mono text-fg-subtle">+{String(n.positive)} / −{String(n.negative)}</div>
                </>
              )}
            />
          )}
        </Card>
        <div className="flex flex-col gap-4">
          {info && (
            <Card title={t('Neighbourhood', '邻域概况')}>
              <div className="grid grid-cols-3 gap-3">
                <Stat label={t('people', '人数')} value={info.nodes} />
                <Stat label={t('ties', '关系')} value={info.ties} sub={`${info.raw_edges} ${t('records', '条记录')}`} />
                <Stat label={t('negative', '负向')} value={pct(info.negative / Math.max(1, info.ties), 0)} />
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <Stat label={t('triangle balance', '三角平衡')} value={fmt(info.triangle_balance)} />
                <Stat label={t('frustration index', '受挫指数')} value={fmt(info.frustration?.index)} sub={info.frustration ? `${info.frustration.frustration} ${t('frustrated', '条受挫')}` : undefined} />
              </div>
              <div className="mt-4 flex h-2 overflow-hidden rounded-full">
                <motion.div animate={{ width: `${(info.positive / Math.max(1, info.ties)) * 100}%` }} className="h-full" style={{ background: C.pos }} />
                <motion.div animate={{ width: `${(info.negative / Math.max(1, info.ties)) * 100}%` }} className="ml-0.5 h-full" style={{ background: C.neg }} />
              </div>
            </Card>
          )}
          {link && <RelationPanel dataset={dataset} link={link} onClose={() => setLink(null)} />}
          {node && (
            <NodePanel
              dataset={dataset}
              node={String((nodes.find((n) => n.id === node) ?? { id: node }).id)}
              onClose={() => setNode(null)}
              onAdd={(n) => !selected.some((s) => s.id === n.id) && setSelected([...selected, n])}
            />
          )}
          {!link && !node && (
            <div className="rounded-xl border border-dashed border-white/10 p-5 text-center text-xs text-fg-subtle">
              {t('Click a tie or a person in the graph for details.', '点击图中的关系或人物查看详情。')}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
