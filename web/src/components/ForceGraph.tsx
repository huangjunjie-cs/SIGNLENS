import * as d3 from 'd3'
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { C } from '../lib/colors'

export interface GNode {
  id: string
  [k: string]: unknown
}
export interface GLink {
  source: string
  target: string
  sign: number
  frustrated?: boolean
  [k: string]: unknown
}

type SimNode = d3.SimulationNodeDatum & { id: string; data: GNode }
type SimLink = d3.SimulationLinkDatum<SimNode> & { data: GLink }

interface Props {
  nodes: GNode[]
  links: GLink[]
  height?: number
  nodeColor: (n: GNode) => string
  nodeRadius?: (n: GNode) => number
  nodeLabel?: (n: GNode) => string
  showLabel?: (n: GNode) => boolean
  tooltip?: (n: GNode) => ReactNode
  /** Fixed target layout in [-1.5, 1.5]^2; when set nodes glide there. */
  fixed?: ((n: GNode) => [number, number] | null) | null
  highlightFrustrated?: boolean
  dimPositive?: boolean
  selected?: string | null
  onNodeClick?: (n: GNode) => void
  onLinkClick?: (l: GLink) => void
  /** Pull nodes horizontally by group: returns -1..1 or null */
  sideOf?: ((n: GNode) => number | null) | null
}

export default function ForceGraph({
  nodes,
  links,
  height = 520,
  nodeColor,
  nodeRadius = () => 5,
  nodeLabel = (n) => String(n.name ?? n.id),
  showLabel = () => false,
  tooltip,
  fixed = null,
  highlightFrustrated = false,
  dimPositive = false,
  selected = null,
  onNodeClick,
  onLinkClick,
  sideOf = null,
}: Props) {
  const wrap = useRef<HTMLDivElement>(null)
  const canvas = useRef<HTMLCanvasElement>(null)
  const [width, setWidth] = useState(800)
  const [hover, setHover] = useState<{ n: GNode; x: number; y: number } | null>(null)
  const posMemo = useRef(new Map<string, { x: number; y: number }>())
  const transform = useRef(d3.zoomIdentity)
  const sim = useRef<d3.Simulation<SimNode, SimLink> | null>(null)
  const drawRef = useRef<() => void>(() => {})
  const props = useRef({ nodeColor, nodeRadius, nodeLabel, showLabel, highlightFrustrated, dimPositive, selected })
  props.current = { nodeColor, nodeRadius, nodeLabel, showLabel, highlightFrustrated, dimPositive, selected }

  useEffect(() => {
    const el = wrap.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => setWidth(Math.max(320, e.contentRect.width)))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const graph = useMemo(() => {
    const prev = posMemo.current
    const simNodes: SimNode[] = nodes.map((n) => {
      const p = prev.get(n.id)
      return { id: n.id, data: n, x: p?.x ?? (Math.random() - 0.5) * 200, y: p?.y ?? (Math.random() - 0.5) * 200 }
    })
    const idx = new Map(simNodes.map((n) => [n.id, n]))
    const simLinks: SimLink[] = links
      .filter((l) => idx.has(String(l.source)) && idx.has(String(l.target)))
      .map((l) => ({ source: idx.get(String(l.source))!, target: idx.get(String(l.target))!, data: l }))
    return { simNodes, simLinks }
  }, [nodes, links])

  // draw
  useEffect(() => {
    const cv = canvas.current
    if (!cv) return
    const dpr = window.devicePixelRatio || 1
    cv.width = width * dpr
    cv.height = height * dpr
    cv.style.width = `${width}px`
    cv.style.height = `${height}px`
    const ctx = cv.getContext('2d')!
    drawRef.current = () => {
      const p = props.current
      const t = transform.current
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, width, height)
      ctx.translate(width / 2 + t.x, height / 2 + t.y)
      ctx.scale(t.k, t.k)
      const lw = 1 / Math.sqrt(t.k)
      const density = Math.max(0.12, Math.min(1, 900 / Math.max(900, graph.simLinks.length)))
      // positive ties first, then negative on top
      for (const pass of [1, -1]) {
        for (const l of graph.simLinks) {
          if (Math.sign(l.data.sign) !== pass) continue
          const s = l.source as SimNode
          const d = l.target as SimNode
          const fr = !!l.data.frustrated
          let alpha = (pass > 0 ? 0.22 : 0.4) * density
          if (p.dimPositive && pass > 0) alpha = 0.07
          if (p.highlightFrustrated) alpha = fr ? 0.95 : alpha * 0.35
          if (p.selected && (s.id === p.selected || d.id === p.selected)) alpha = 0.95
          ctx.globalAlpha = alpha
          ctx.strokeStyle = pass > 0 ? C.pos : C.neg
          ctx.lineWidth = (p.highlightFrustrated && fr ? 2.2 : 1.1) * lw
          ctx.setLineDash(pass > 0 ? [] : [4 * lw, 3 * lw])
          ctx.beginPath()
          ctx.moveTo(s.x!, s.y!)
          ctx.lineTo(d.x!, d.y!)
          ctx.stroke()
        }
      }
      ctx.setLineDash([])
      ctx.globalAlpha = 1
      for (const n of graph.simNodes) {
        const r = p.nodeRadius(n.data)
        ctx.beginPath()
        ctx.arc(n.x!, n.y!, r, 0, Math.PI * 2)
        ctx.fillStyle = p.nodeColor(n.data)
        ctx.fill()
        ctx.lineWidth = 1.5 * lw
        ctx.strokeStyle = n.id === p.selected ? '#ffffff' : C.surface
        if (n.id === p.selected) ctx.lineWidth = 2.5 * lw
        ctx.stroke()
      }
      ctx.font = `${11 / Math.sqrt(t.k)}px Inter, sans-serif`
      ctx.textAlign = 'center'
      for (const n of graph.simNodes) {
        if (!p.showLabel(n.data) && n.id !== p.selected) continue
        const r = p.nodeRadius(n.data)
        const txt = p.nodeLabel(n.data)
        ctx.lineWidth = 3 * lw
        ctx.strokeStyle = 'rgba(11,15,23,0.85)'
        ctx.strokeText(txt, n.x!, n.y! - r - 4)
        ctx.fillStyle = C.fg
        ctx.fillText(txt, n.x!, n.y! - r - 4)
      }
    }
    drawRef.current()
  }, [width, height, graph])

  useEffect(() => {
    drawRef.current()
  }, [nodeColor, highlightFrustrated, dimPositive, selected, showLabel])

  // simulation
  useEffect(() => {
    const { simNodes, simLinks } = graph
    const n = simNodes.length
    const scale = Math.min(width, height) * 0.42
    const s = d3
      .forceSimulation<SimNode, SimLink>(simNodes)
      .force(
        'link',
        d3
          .forceLink<SimNode, SimLink>(simLinks)
          .distance((l) => (l.data.sign > 0 ? 26 : Math.min(width, height) * 0.55))
          .strength((l) => (l.data.sign > 0 ? 0.3 : 0.06)),
      )
      .force('charge', d3.forceManyBody<SimNode>().strength(n > 400 ? -14 : -40).distanceMax(320))
      .force('collide', d3.forceCollide<SimNode>((d) => props.current.nodeRadius(d.data) + 1.5))
      .alphaDecay(0.03)
    if (fixed) {
      s.force('link', null)
      s.force('charge', d3.forceManyBody<SimNode>().strength(-2))
      s.force('x', d3.forceX<SimNode>((d) => (fixed(d.data)?.[0] ?? 0) * scale).strength(0.25))
      s.force('y', d3.forceY<SimNode>((d) => (fixed(d.data)?.[1] ?? 0) * scale).strength(0.25))
    } else if (sideOf) {
      s.force('x', d3.forceX<SimNode>((d) => (sideOf(d.data) ?? 0) * scale * 0.55).strength(0.05))
      s.force('y', d3.forceY<SimNode>(0).strength(0.04))
    } else {
      s.force('x', d3.forceX<SimNode>(0).strength(0.04))
      s.force('y', d3.forceY<SimNode>(0).strength(0.04))
    }
    s.on('tick', () => {
      for (const nd of simNodes) posMemo.current.set(nd.id, { x: nd.x!, y: nd.y! })
      drawRef.current()
    })
    s.alpha(posMemo.current.size ? 0.6 : 1).restart()
    sim.current = s
    return () => {
      s.stop()
    }
  }, [graph, fixed, sideOf, width, height])

  // interaction: zoom, drag, hover, click
  useEffect(() => {
    const cv = canvas.current
    if (!cv) return
    const sel = d3.select(cv)
    const toWorld = (ev: { offsetX: number; offsetY: number }) => {
      const t = transform.current
      return [(ev.offsetX - width / 2 - t.x) / t.k, (ev.offsetY - height / 2 - t.y) / t.k] as const
    }
    const findNode = (ev: { offsetX: number; offsetY: number }) => {
      const [x, y] = toWorld(ev)
      let best: SimNode | null = null
      let bd = Infinity
      for (const nd of graph.simNodes) {
        const d = Math.hypot(nd.x! - x, nd.y! - y)
        const r = props.current.nodeRadius(nd.data) + 4 / transform.current.k
        if (d < r && d < bd) {
          best = nd
          bd = d
        }
      }
      return best
    }
    const findLink = (ev: { offsetX: number; offsetY: number }) => {
      const [x, y] = toWorld(ev)
      const tol = 5 / transform.current.k
      let best: SimLink | null = null
      let bd = tol
      for (const l of graph.simLinks) {
        const a = l.source as SimNode
        const b = l.target as SimNode
        const dx = b.x! - a.x!
        const dy = b.y! - a.y!
        const len2 = dx * dx + dy * dy || 1
        const t = Math.max(0, Math.min(1, ((x - a.x!) * dx + (y - a.y!) * dy) / len2))
        const d = Math.hypot(x - (a.x! + t * dx), y - (a.y! + t * dy))
        if (d < bd) {
          bd = d
          best = l
        }
      }
      return best
    }
    const zoom = d3
      .zoom<HTMLCanvasElement, unknown>()
      .scaleExtent([0.2, 8])
      .filter((ev) => {
        if (ev.type === 'wheel') return true
        return !findNode(ev)
      })
      .on('zoom', (ev) => {
        transform.current = ev.transform
        drawRef.current()
      })
    sel.call(zoom)
    const drag = d3
      .drag<HTMLCanvasElement, unknown>()
      .subject((ev) => {
        const nd = findNode(ev.sourceEvent)
        return nd ?? undefined
      })
      .on('start', (ev) => {
        if (!ev.active) sim.current?.alphaTarget(0.2).restart()
        const nd = ev.subject as SimNode
        nd.fx = nd.x
        nd.fy = nd.y
      })
      .on('drag', (ev) => {
        const nd = ev.subject as SimNode
        const [x, y] = toWorld(ev.sourceEvent)
        nd.fx = x
        nd.fy = y
      })
      .on('end', (ev) => {
        if (!ev.active) sim.current?.alphaTarget(0)
        const nd = ev.subject as SimNode
        nd.fx = null
        nd.fy = null
      })
    sel.call(drag)
    sel.on('mousemove.hover', (ev: MouseEvent) => {
      const nd = findNode(ev)
      cv.style.cursor = nd ? 'pointer' : onLinkClick && findLink(ev) ? 'pointer' : 'grab'
      setHover(nd ? { n: nd.data, x: ev.offsetX, y: ev.offsetY } : null)
    })
    sel.on('mouseleave.hover', () => setHover(null))
    sel.on('click.pick', (ev: MouseEvent) => {
      const nd = findNode(ev)
      if (nd) return onNodeClick?.(nd.data)
      const l = findLink(ev)
      if (l) onLinkClick?.({ ...l.data, source: (l.source as SimNode).id, target: (l.target as SimNode).id })
    })
    return () => {
      sel.on('.zoom', null).on('.drag', null).on('.hover', null).on('.pick', null)
    }
  }, [graph, width, height, onNodeClick, onLinkClick])

  return (
    <div ref={wrap} className="relative w-full select-none" style={{ height }}>
      <canvas ref={canvas} className="block rounded-xl" />
      {hover && (
        <div
          className="pointer-events-none absolute z-10 min-w-36 rounded-lg border border-white/10 bg-ink-800/95 px-3 py-2 text-xs shadow-xl backdrop-blur"
          style={{ left: Math.min(hover.x + 14, width - 200), top: hover.y + 14 }}
        >
          {tooltip ? tooltip(hover.n) : <div className="font-medium text-fg">{nodeLabel(hover.n)}</div>}
        </div>
      )}
    </div>
  )
}
