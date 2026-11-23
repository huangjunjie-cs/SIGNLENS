import katex from 'katex'
import { motion } from 'motion/react'
import { PageHeader } from '../components/ui'
import { useT } from '../lib/i18n'

function TeX({ children, block = true }: { children: string; block?: boolean }) {
  return (
    <span
      className={block ? 'my-3 block overflow-x-auto text-fg' : ''}
      dangerouslySetInnerHTML={{ __html: katex.renderToString(children, { displayMode: block, throwOnError: false }) }}
    />
  )
}

interface Item {
  id: string
  en: [string, string]
  zh: [string, string]
  tex: string
  ref: string
  fn: string
}

const ITEMS: { group: [string, string]; items: Item[] }[] = [
  {
    group: ['Structure (balance)', '结构（平衡）'],
    items: [
      { id: 'tri', en: ['Triangle balance', 'Share of signed triangles with an even number of negative ties.'], zh: ['三角平衡度', '负边数为偶数的符号三角形所占比例。'],
        tex: 'T_{+++} = \\tfrac{1}{6}\\operatorname{tr}P^3,\\; T_{++-} = \\tfrac{1}{2}\\operatorname{tr}P^2N,\\; T_{+--} = \\tfrac{1}{2}\\operatorname{tr}PN^2,\\; T_{---} = \\tfrac{1}{6}\\operatorname{tr}N^3', ref: 'Heider 1946; Cartwright & Harary 1956', fn: 'basic.triad_census' },
      { id: 'fr', en: ['Frustration index', 'Minimum weight of ties that violate a two-camp split; solved exactly as a binary program (HiGHS) or by spectral + local search.'], zh: ['受挫指数', '违反某个两阵营划分的关系的最小权重；可用二值规划（HiGHS）精确求解，或用谱方法加局部搜索近似。'],
        tex: 'F(G)=\\min_{s\\in\\{\\pm1\\}^n}\\sum_{(i,j)\\in E}\\mathbb{1}[A_{ij}s_is_j<0],\\qquad \\text{index}=1-\\frac{2F}{m}', ref: 'Harary 1959; Aref & Wilson 2018; Aref, Mason & Porter 2018', fn: 'balance.frustration' },
      { id: 'ac', en: ['Algebraic conflict', 'Smallest eigenvalue of the (normalized) signed Laplacian on the largest component. Zero iff balanced.'], zh: ['代数冲突', '最大连通分量上（归一化）符号拉普拉斯矩阵的最小特征值。当且仅当平衡时为零。'],
        tex: '\\lambda_{\\min}\\big(I-\\bar D^{-1/2}A\\bar D^{-1/2}\\big),\\qquad \\bar D_{ii}=\\textstyle\\sum_j|A_{ij}|', ref: 'Kunegis et al. 2010', fn: 'balance.algebraic_conflict' },
      { id: 'wb', en: ['Walk-based balance', 'Ratio of weighted closed walks in the signed vs. unsigned graph; counts cycles of every length.'], zh: ['游走平衡度', '符号图与无符号图中加权闭合游走之比，统计所有长度的环。'],
        tex: 'K=\\frac{\\operatorname{tr}e^{\\beta A}}{\\operatorname{tr}e^{\\beta|A|}}\\in(0,1]', ref: 'Estrada & Benzi 2014', fn: 'balance.walk_balance' },
    ],
  },
  {
    group: ['Camps', '阵营'],
    items: [
      { id: 'pol', en: ['Polarity & polarized communities', 'Two internally cohesive, mutually hostile communities; everyone else is neutral. Eigenvector sweep + local search.'], zh: ['极性与极化社群', '两个内部团结、相互敌对的社群，其余为中立者。主特征向量扫描 + 局部搜索。'],
        tex: '\\max_{x\\in\\{-1,0,1\\}^n}\\;\\frac{x^\\top A x}{x^\\top x}', ref: 'Bonchi et al. 2019; Tzeng et al. 2020', fn: 'polarization.polarized_communities' },
    ],
  },
  {
    group: ['Separation', '隔离'],
    items: [
      { id: 'mod', en: ['Signed modularity', 'Modularity of positive ties minus modularity of negative ties.'], zh: ['符号模块度', '正边模块度减去负边模块度。'],
        tex: 'Q=\\frac{1}{2w^++2w^-}\\sum_{ij}\\Big[\\big(A^+_{ij}-\\tfrac{k^+_ik^+_j}{2w^+}\\big)-\\big(A^-_{ij}-\\tfrac{k^-_ik^-_j}{2w^-}\\big)\\Big]\\delta(c_i,c_j)', ref: 'Gómez, Jensen & Arenas 2009', fn: 'polarization.signed_modularity' },
      { id: 'con', en: ['Block contrast', 'Density-based contrast between within- and between-camp ties; also captures camps that simply ignore each other.'], zh: ['块对比度', '阵营内与阵营间关系密度的对比；也能刻画彼此漠视的阵营。'],
        tex: '\\tfrac{1}{2}\\big[(d^+_{\\text{in}}-d^+_{\\text{out}})+(d^-_{\\text{out}}-d^-_{\\text{in}})\\big]\\in[-1,1]', ref: 'SIGNLENS', fn: 'polarization.camp_statistics' },
      { id: 'rwc', en: ['Random-walk controversy', 'Walks along positive ties absorbed at the k most central nodes of each camp.'], zh: ['随机游走争议度', '沿正边游走，在各阵营度数最高的 k 个节点处被吸收。'],
        tex: '\\mathrm{RWC}=P_{XX}P_{YY}-P_{XY}P_{YX}', ref: 'Garimella et al. 2018', fn: 'polarization.random_walk_controversy' },
    ],
  },
  {
    group: ['Positions', '立场'],
    items: [
      { id: 'ip', en: ['Ideal points', 'Low-rank fit to observed, item-centred votes by alternating least squares; lopsided votes removed as in NOMINATE.'], zh: ['理想点', '对已观测、按议案中心化的投票做交替最小二乘低秩拟合；与 NOMINATE 一样剔除一边倒的投票。'],
        tex: '\\min_{x,v}\\sum_{(i,j)\\in\\Omega}\\big(X_{ij}-\\mu_j-x_i^\\top v_j\\big)^2', ref: 'Poole & Rosenthal; Lewis et al. (Voteview)', fn: 'polarization.ideal_points' },
      { id: 'bc', en: ['Bimodality & overlap', 'Sarle’s bimodality coefficient; overlap = members beyond the most moderate member of the other group.'], zh: ['双峰性与重叠', 'Sarle 双峰系数；重叠数 = 越过对方最温和成员的人数。'],
        tex: 'BC=\\frac{g^2+1}{\\kappa+\\frac{3(n-1)^2}{(n-2)(n-3)}}', ref: 'Pfister et al. 2013', fn: 'polarization.bimodality_coefficient' },
      { id: 'er', en: ['Esteban–Ray index', 'Identification within groups × alienation between them.'], zh: ['Esteban–Ray 指数', '组内认同 × 组间疏离。'],
        tex: 'ER=\\sum_{i,j}\\pi_i^{1+\\alpha}\\pi_j\\,|\\mu_i-\\mu_j|', ref: 'Esteban & Ray 1994', fn: 'polarization.esteban_ray' },
    ],
  },
]

export default function Methods() {
  const t = useT()
  return (
    <div className="max-w-4xl">
      <PageHeader kicker={t('Methods', '方法')} title={t('What SIGNLENS measures', 'SIGNLENS 度量什么')}>
        {t(
          'Notation: A is the signed adjacency matrix (sign-aggregated, undirected), P and N its positive and negative parts, m the number of ties. Every measure is available in the Python package; the function is given for each.',
          '记号：A 为符号邻接矩阵（按符号聚合、无向），P、N 分别为其正、负部分，m 为关系数。每个指标都可在 Python 包中调用，下面给出对应函数。',
        )}
      </PageHeader>
      {ITEMS.map((g) => (
        <section key={g.group[0]} className="mb-10">
          <h2 className="label mb-4">{t(g.group[0], g.group[1])}</h2>
          <div className="space-y-4">
            {g.items.map((it, i) => (
              <motion.div key={it.id} initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.05 }} className="card p-5">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="font-semibold">{t(it.en[0], it.zh[0])}</h3>
                  <code className="font-mono text-xs text-accent">signlens.{it.fn}</code>
                </div>
                <p className="mt-1 text-sm text-fg-muted">{t(it.en[1], it.zh[1])}</p>
                <TeX>{it.tex}</TeX>
                <div className="text-xs text-fg-subtle">{it.ref}</div>
              </motion.div>
            ))}
          </div>
        </section>
      ))}
      <section className="card p-5 text-sm text-fg-muted">
        <h3 className="mb-2 font-semibold text-fg">{t('Cite', '引用')}</h3>
        <pre className="overflow-x-auto rounded-lg bg-ink-900 p-4 font-mono text-xs leading-relaxed">{`@inproceedings{huang2021signlens,
  title     = {SIGNLENS: A Tool for Analyzing People's Polarization Social Relationship
               Based on Signed Graph Modeling},
  author    = {Huang, Junjie and Shen, Huawei and Cheng, Xueqi},
  booktitle = {Proceedings of the International AAAI Conference on Web and Social Media},
  volume    = {15}, pages = {1091--1093}, year = {2021}
}`}</pre>
      </section>
    </div>
  )
}
