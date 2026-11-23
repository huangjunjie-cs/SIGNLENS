import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { LineChart } from '../components/charts'
import { Card, DatasetPicker, ErrorBox, Loading, PageHeader } from '../components/ui'
import { api, useAsync } from '../lib/api'
import { SERIES } from '../lib/colors'
import { useLabels, useT } from '../lib/i18n'

const DEFAULT = ['negative_ratio', 'unbalanced_triangle_ratio', 'frustration_ratio', 'polarity']

export default function Temporal() {
  const t = useT()
  const L = useLabels()
  const [params, setParams] = useSearchParams()
  const dataset = params.get('dataset') ?? 'demo-polarizing'
  const metrics = useAsync(() => api.metrics(), [])
  const summary = useAsync(() => api.summary(dataset), [dataset])
  const [chosen, setChosen] = useState<string[]>(DEFAULT)
  const [win, setWin] = useState(1)
  const [step, setStep] = useState<number | ''>('')
  const [range, setRange] = useState<[number, number] | null>(null)
  const [cumulative, setCumulative] = useState(false)
  const [query, setQuery] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    const tr = summary.data?.time_range
    if (!tr) return
    const span = tr[1] - tr[0]
    const w = span > 200 ? 10 : span > 40 ? 5 : 1
    setWin(w)
    setRange([Math.floor(tr[0]), Math.ceil(tr[1]) + 1])
    setQuery({ metrics: chosen, window: w, start: Math.floor(tr[0]), end: Math.ceil(tr[1]) + 1, cumulative: false })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [summary.data])

  const res = useAsync(() => (query ? api.temporal(dataset, query) : null), [dataset, JSON.stringify(query)])
  const label = (id: string) => L.metric(id, metrics.data?.find((m) => m.id === id)?.label)
  const rows = res.data?.rows ?? []
  const noTime = summary.data && !summary.data.has_time

  return (
    <div>
      <PageHeader kicker={t('Group analysis over time', '群体演化分析')} title={t('When did the split happen?', '分裂发生在何时？')}>
        {t(
          'Slice a timestamped signed network into windows and follow balance and polarization through time. Each metric gets its own panel so scales never mix.',
          '将带时间戳的符号网络切分为时间窗口，追踪平衡与极化随时间的变化。每个指标单独成图，避免不同量纲混在一起。',
        )}
      </PageHeader>

      <Card className="mb-5">
        <div className="flex flex-wrap items-end gap-4">
          <DatasetPicker value={dataset} onChange={(v) => setParams({ dataset: v })} filter={(d) => d.tags.includes('temporal') || !!d.has_time} />
          <label className="flex w-28 flex-col gap-1.5">
            <span className="label">{t('Window', '窗口')}</span>
            <input className="input" type="number" min={0.1} step="any" value={win} onChange={(e) => setWin(+e.target.value)} />
          </label>
          <label className="flex w-28 flex-col gap-1.5">
            <span className="label">{t('Step', '步长')}</span>
            <input className="input" type="number" min={0.1} step="any" placeholder={String(win)} value={step} onChange={(e) => setStep(e.target.value === '' ? '' : +e.target.value)} />
          </label>
          {range && (
            <>
              <label className="flex w-28 flex-col gap-1.5">
                <span className="label">{t('From', '起')}</span>
                <input className="input" type="number" value={range[0]} onChange={(e) => setRange([+e.target.value, range[1]])} />
              </label>
              <label className="flex w-28 flex-col gap-1.5">
                <span className="label">{t('To', '止')}</span>
                <input className="input" type="number" value={range[1]} onChange={(e) => setRange([range[0], +e.target.value])} />
              </label>
            </>
          )}
          <label className="inline-flex items-center gap-2 pb-2.5 text-xs text-fg-muted">
            <input type="checkbox" checked={cumulative} onChange={(e) => setCumulative(e.target.checked)} />
            {t('cumulative', '累积')}
          </label>
          <button
            className="btn-primary"
            disabled={!range || !chosen.length}
            onClick={() => setQuery({ metrics: chosen, window: win, step: step || null, start: range![0], end: range![1], cumulative })}
          >
            {t('Run', '运行')}
          </button>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {(metrics.data ?? []).map((m) => {
            const on = chosen.includes(m.id)
            return (
              <button
                key={m.id}
                onClick={() => setChosen(on ? chosen.filter((x) => x !== m.id) : [...chosen, m.id])}
                className={`rounded-full border px-3 py-1 text-xs transition ${on ? 'border-accent/60 bg-accent/15 text-fg' : 'border-white/10 text-fg-subtle hover:text-fg-muted'}`}
              >
                {L.metric(m.id, m.label)}
              </button>
            )
          })}
        </div>
      </Card>

      {noTime && <ErrorBox error={t('This dataset has no timestamps.', '该数据集没有时间戳。')} />}
      {res.error && <ErrorBox error={res.error} />}
      {res.loading && <Loading />}
      {!res.loading && rows.length > 0 && (
        <div className="grid gap-5 md:grid-cols-2">
          <Card title={t('Ties per window', '每个窗口的关系数')} subtitle={t('Context: small windows give noisy estimates.', '参考：关系过少的窗口估计噪声较大。')}>
            <LineChart height={200} series={[{ key: 'edges', label: t('edges', '边数'), color: '#6f7a93', values: rows.map((r) => ({ x: r.start as number, y: r.edges })) }]} yFormat={(v) => (v >= 1000 ? `${v / 1000}k` : String(v))} />
          </Card>
          {(query?.metrics as string[]).map((m, i) => (
            <Card key={m} title={label(m)}>
              <LineChart
                height={200}
                series={[{ key: m, label: label(m), color: SERIES[i % SERIES.length], values: rows.map((r) => ({ x: r.start as number, y: r[m] })) }]}
                xFormat={(v) => String(+v.toFixed(1))}
              />
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
