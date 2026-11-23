import { motion } from 'motion/react'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Bars, LogScatter } from '../components/charts'
import { Card, ErrorBox, Loading, PageHeader, Stat } from '../components/ui'
import { api, fmt, pct, useAsync } from '../lib/api'
import { C } from '../lib/colors'
import { useLabels, useT } from '../lib/i18n'

function Upload({ onDone }: { onDone: (id: string) => void }) {
  const t = useT()
  const [file, setFile] = useState<File | null>(null)
  const [name, setName] = useState('')
  const [directed, setDirected] = useState(true)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [drag, setDrag] = useState(false)
  const submit = async () => {
    if (!file) return
    setBusy(true)
    setErr(null)
    const fd = new FormData()
    fd.append('file', file)
    fd.append('name', name || file.name)
    fd.append('directed', String(directed))
    try {
      const meta = await api.upload(fd)
      onDone(meta.id)
    } catch (e) {
      setErr((e as Error).message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <Card title={t('Upload a signed network', '上传符号网络')} subtitle={t('CSV / TSV, one edge per line: source, target, sign (±1) [, time]. A header row is optional.', 'CSV / TSV，每行一条边：source, target, sign (±1) [, time]。表头可选。')}>
      <label
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); setFile(e.dataTransfer.files[0] ?? null) }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed px-4 py-8 text-center text-sm transition ${drag ? 'border-accent bg-accent/10' : 'border-white/15 hover:border-white/30'}`}
      >
        <input type="file" accept=".csv,.tsv,.txt" className="hidden" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        {file ? <span className="text-fg">{file.name} · {(file.size / 1024).toFixed(1)} KB</span> : <span className="text-fg-muted">{t('Drop a file here or click to browse', '拖入文件或点击选择')}</span>}
      </label>
      <pre className="mt-3 rounded-lg bg-ink-900 p-3 font-mono text-[11px] leading-relaxed text-fg-subtle">{`alice\tbob\t1\t2019\nbob\tcarol\t-1\t2020\n...`}</pre>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <input className="input max-w-56" placeholder={t('Name (optional)', '名称（可选）')} value={name} onChange={(e) => setName(e.target.value)} />
        <label className="inline-flex items-center gap-2 text-xs text-fg-muted">
          <input type="checkbox" checked={directed} onChange={(e) => setDirected(e.target.checked)} /> {t('directed', '有向')}
        </label>
        <button className="btn-primary ml-auto" disabled={!file || busy} onClick={submit}>{busy ? '…' : t('Upload & analyze', '上传并分析')}</button>
      </div>
      {err && <div className="mt-3"><ErrorBox error={err} /></div>}
    </Card>
  )
}

function Report({ id }: { id: string }) {
  const t = useT()
  const { data: s, loading, error } = useAsync(() => api.summary(id), [id])
  if (loading && !s) return <Loading />
  if (error) return <ErrorBox error={error} />
  if (!s) return null
  const hist = s.degree_histograms
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid gap-5 lg:grid-cols-3">
      <Card className="lg:col-span-3">
        <div className="grid grid-cols-2 gap-6 md:grid-cols-6">
          <Stat label={t('nodes', '节点')} value={s.nodes.toLocaleString()} />
          <Stat label={t('edges', '边')} value={s.edges.toLocaleString()} sub={`${s.ties.toLocaleString()} ${t('distinct ties', '个不同关系')}`} />
          <Stat label={t('positive', '正边比例')} value={pct(s.sign.positive_ratio)} />
          <Stat label={t('balanced triangles', '平衡三角形')} value={pct(s.triads.balanced_ratio)} sub={`${s.triads.total.toLocaleString()} ${t('triangles', '个三角形')}`} />
          <Stat label={t('components', '连通分量')} value={s.components} sub={`${t('largest', '最大')} ${s.largest_component.toLocaleString()}`} />
          <Stat label={t('time span', '时间跨度')} value={s.time_range ? `${fmt(s.time_range[0], 0)}–${fmt(s.time_range[1], 0)}` : '—'} />
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          <Link className="btn-ghost text-xs" to={`/polarization?dataset=${id}`}>{t('Polarization profile', '极化画像')} →</Link>
          <Link className="btn-ghost text-xs" to={`/individual?dataset=${id}`}>{t('Individual analysis', '个体分析')} →</Link>
          {s.has_time && <Link className="btn-ghost text-xs" to={`/temporal?dataset=${id}`}>{t('Over time', '时间演化')} →</Link>}
        </div>
      </Card>
      <Card title={t('Sign distribution', '符号分布')}>
        <Bars
          valueFormat={(v) => v.toLocaleString()}
          yFormat={(v) => (v >= 1000 ? `${v / 1000}k` : String(v))}
          data={[
            { label: '+', value: s.sign.positive, color: '#5b6b88' },
            { label: '−', value: s.sign.negative, color: C.neg },
          ]}
        />
      </Card>
      <Card title={t('Signed triangles', '符号三角形')} subtitle={t('share of all triangles', '占全部三角形的比例')}>
        <Bars
          data={(['+++', '++-', '+--', '---'] as const).map((k) => ({
            label: k.replace(/-/g, '−'),
            value: s.triads.distribution[k] ?? 0,
            color: k === '+++' || k === '+--' ? '#5b6b88' : C.neg,
            note: `${(s.triads.counts[k] ?? 0).toLocaleString()} ${k === '+++' || k === '+--' ? t('balanced', '平衡') : t('unbalanced', '不平衡')}`,
          }))}
        />
      </Card>
      <Card title={t('Hop plot', '跳数分布')} subtitle={t('pairs at each shortest-path distance', '各最短路径距离上的节点对数')}>
        <LogScatter logX={false} xLabel={t('hops', '跳数')} yLabel={t('pairs', '节点对')} series={[{ label: t('pairs', '节点对'), color: C.accent, points: s.hops }]} />
      </Card>
      <Card title={t('In-degree distribution', '入度分布')}>
        <LogScatter xLabel={t('in-degree', '入度')} yLabel={t('count', '数量')} series={[
          { label: t('positive', '正向'), color: '#9fb3d1', points: hist.in_positive },
          { label: t('negative', '负向'), color: C.neg, points: hist.in_negative },
        ]} />
      </Card>
      <Card title={t('Out-degree distribution', '出度分布')}>
        <LogScatter xLabel={t('out-degree', '出度')} yLabel={t('count', '数量')} series={[
          { label: t('positive', '正向'), color: '#9fb3d1', points: hist.out_positive },
          { label: t('negative', '负向'), color: C.neg, points: hist.out_negative },
        ]} />
      </Card>
      <Card title={t('Singular values', '奇异值分布')} subtitle={t('top-50 of the unsigned adjacency', '无符号邻接矩阵前 50 个')}>
        <LogScatter xLabel="k" yLabel="σ" series={[{ label: 'σ', color: C.campA, points: s.singular_values.map((v, i) => [i + 1, v] as [number, number]) }]} />
      </Card>
    </motion.div>
  )
}

export default function Data() {
  const t = useT()
  const L = useLabels()
  const [params, setParams] = useSearchParams()
  const list = useAsync(() => api.datasets(), [params.get('refresh')])
  const id = params.get('dataset') ?? 'demo-polarized'
  return (
    <div>
      <PageHeader kicker={t('Data', '数据')} title={t('Datasets & descriptive report', '数据集与描述统计')}>
        {t(
          'Built-in synthetic networks with known ground truth, the current U.S. Congress from Voteview, the original SIGNLENS release (CBDB, USCV — place the Kaggle TSVs in datas/), or your own upload.',
          '内置已知真值的合成网络、来自 Voteview 的本届美国国会、SIGNLENS 原始发布数据（CBDB、USCV——将 Kaggle 上的 TSV 放入 datas/ 目录），或你上传的数据。',
        )}
      </PageHeader>
      <div className="mb-8 grid gap-5 lg:grid-cols-[1fr_420px]">
        <div className="grid content-start gap-3 sm:grid-cols-2">
          {(list.data ?? []).map((d) => (
            <button
              key={d.id}
              onClick={() => setParams({ dataset: d.id })}
              className={`card p-4 text-left transition hover:border-white/20 ${d.id === id ? 'border-accent/60! bg-accent/[0.06]' : ''}`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold text-fg">{L.dataset(d)}</span>
                <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] uppercase tracking-wider text-fg-subtle">{d.kind}</span>
              </div>
              <p className="mt-1.5 line-clamp-3 text-xs leading-relaxed text-fg-muted">{L.description(d)}</p>
            </button>
          ))}
        </div>
        <Upload onDone={(newId) => setParams({ dataset: newId, refresh: newId })} />
      </div>
      <Report id={id} />
    </div>
  )
}
