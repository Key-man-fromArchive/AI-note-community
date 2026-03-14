import { useMemo } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { useNavigate } from 'react-router-dom'
import { useGlobalGraph } from '@/hooks/useGlobalGraph'

export default function Graph() {
  const navigate = useNavigate()
  const graph = useGlobalGraph()

  const data = useMemo(
    () => ({
      nodes: graph.data?.nodes ?? [],
      links: graph.data?.links ?? [],
    }),
    [graph.data],
  )

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Note Graph</h1>
          <p className="muted">Visualize semantic relationships between notes.</p>
        </div>
        <div className="card">
          {graph.data?.indexed_notes ?? 0} / {graph.data?.total_notes ?? 0} indexed
        </div>
      </div>
      <div className="card" style={{ height: '72vh', padding: 0, overflow: 'hidden' }}>
        <ForceGraph2D
          graphData={data}
          nodeLabel={node => `${String(node.label)} (${String(node.notebook ?? 'No notebook')})`}
          nodeCanvasObject={(node, ctx) => {
            const label = String(node.label)
            const size = Math.max(5, Number(node.size ?? 6))
            ctx.beginPath()
            ctx.arc(Number(node.x), Number(node.y), size, 0, 2 * Math.PI, false)
            ctx.fillStyle = '#1f1f1a'
            ctx.fill()
            ctx.font = '12px IBM Plex Sans'
            ctx.fillStyle = '#3d372d'
            ctx.fillText(label, Number(node.x) + size + 4, Number(node.y) + 4)
          }}
          onNodeClick={node => navigate(`/?note=${String(node.id)}`)}
          linkColor={() => 'rgba(71, 62, 47, 0.28)'}
          backgroundColor="rgba(255,252,246,0.92)"
        />
      </div>
    </div>
  )
}
