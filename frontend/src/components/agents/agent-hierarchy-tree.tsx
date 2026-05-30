/**
 * AgentHierarchyTree — the flagship org-chart view of the agent roster, rendered
 * with React Flow. A 3-tier layered tree with MANUAL positions (no dagre):
 *   tier 0 — a single CEO node at top center (the `ceo-manager` agent or a
 *            synthetic "CEO" root when it's absent),
 *   tier 1 — a row of DEPARTMENT nodes (unique `agent.department` values, ordered),
 *   tier 2 — the AGENT leaf nodes grouped beneath their department.
 * Edges fan out CEO -> department -> agents with cyan arrow markers. Nodes are
 * small on-brand glass cards tinted by their accent (via `accentClasses`).
 * Purely presentational — no data fetching happens inside.
 */
import { useMemo } from 'react'
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  MarkerType,
  Position,
  type Edge,
  type Node,
} from 'reactflow'
import 'reactflow/dist/style.css'

import { accentClasses } from '@/lib/accents'
import { accentHex, departmentAccent } from '@/styles/tokens'
import type { Accent, AgentSummary } from '@/types'

export interface AgentHierarchyTreeProps {
  agents: AgentSummary[]
}

/** A node label is a tinted glass chip: bold name over a faint sublabel. */
interface NodeLabelData {
  label: string
  sublabel: string
  accent: Accent
  tier: 'ceo' | 'department' | 'agent'
}

const TIER_Y: Record<NodeLabelData['tier'], number> = {
  ceo: 0,
  department: 160,
  agent: 320,
}

/** Horizontal spacing between agent leaves (px) and between department columns. */
const AGENT_GAP = 196
const NODE_WIDTH = 176

/** Render the on-brand label for a node — a tinted card matching its accent. */
function NodeLabel({ label, sublabel, accent, tier }: NodeLabelData) {
  const ac = accentClasses(accent)
  return (
    <div className="flex flex-col gap-0.5 px-1 py-0.5 text-left">
      <span className={`truncate text-[12px] font-semibold leading-tight ${tier === 'ceo' ? ac.text : 'text-zinc-100'}`}>
        {label}
      </span>
      <span className={`truncate text-[10px] leading-tight ${tier === 'department' ? ac.text : 'text-zinc-500'}`}>
        {sublabel}
      </span>
    </div>
  )
}

/**
 * Build the manual 3-tier layout. Agent leaves are laid out left-to-right in a
 * single row; each department centers over its own agents; the CEO centers over
 * everything. This keeps columns spread horizontally and tiers stacked vertically.
 */
function buildGraph(agents: AgentSummary[]): { nodes: Node[]; edges: Edge[] } {
  // Unique departments in first-seen order (skip the synthetic Executive root dept).
  const departments: string[] = []
  for (const a of agents) {
    if (!departments.includes(a.department)) departments.push(a.department)
  }

  const ceo = agents.find((a) => a.id === 'ceo-manager')
  const ceoAccent: Accent = ceo?.accent ?? 'cyan'

  const nodes: Node[] = []
  const edges: Edge[] = []

  // Tier 2 — agent leaves, laid out in a single row grouped by department.
  let leafIndex = 0
  const deptCenterX: Record<string, number> = {}
  for (const dept of departments) {
    const deptAgents = agents.filter((a) => a.department === dept)
    const startIndex = leafIndex
    for (const agent of deptAgents) {
      const x = leafIndex * AGENT_GAP
      nodes.push({
        id: `agent-${agent.id}`,
        position: { x, y: TIER_Y.agent },
        data: {
          label: <NodeLabel label={agent.name} sublabel={agent.modelLabel} accent={agent.accent} tier="agent" />,
        },
        targetPosition: Position.Top,
        sourcePosition: Position.Bottom,
        style: nodeStyle(agent.accent),
        connectable: false,
        draggable: true,
      })
      leafIndex += 1
    }
    // Department column center = midpoint of its agents' x span.
    const firstX = startIndex * AGENT_GAP
    const lastX = (leafIndex - 1) * AGENT_GAP
    deptCenterX[dept] = deptAgents.length > 0 ? (firstX + lastX) / 2 : startIndex * AGENT_GAP
  }

  const totalWidth = Math.max(0, (leafIndex - 1) * AGENT_GAP)

  // Tier 1 — department nodes, each centered over its agents.
  for (const dept of departments) {
    const accent: Accent = departmentAccent[dept] ?? 'cyan'
    const count = agents.filter((a) => a.department === dept).length
    nodes.push({
      id: `dept-${dept}`,
      position: { x: deptCenterX[dept], y: TIER_Y.department },
      data: {
        label: (
          <NodeLabel
            label={dept}
            sublabel={`${count} agent${count === 1 ? '' : 's'}`}
            accent={accent}
            tier="department"
          />
        ),
      },
      targetPosition: Position.Top,
      sourcePosition: Position.Bottom,
      style: nodeStyle(accent),
      connectable: false,
      draggable: true,
    })

    // department -> each of its agents
    for (const agent of agents.filter((a) => a.department === dept)) {
      edges.push(edge(`dept-${dept}`, `agent-${agent.id}`))
    }
  }

  // Tier 0 — CEO root, centered over the full span.
  const ceoId = 'ceo-root'
  nodes.push({
    id: ceoId,
    position: { x: totalWidth / 2, y: TIER_Y.ceo },
    data: {
      label: (
        <NodeLabel
          label={ceo?.name ?? 'CEO'}
          sublabel={ceo?.modelLabel ?? 'Orchestrator'}
          accent={ceoAccent}
          tier="ceo"
        />
      ),
    },
    sourcePosition: Position.Bottom,
    style: nodeStyle(ceoAccent),
    connectable: false,
    draggable: true,
  })

  // CEO -> each department
  for (const dept of departments) {
    edges.push(edge(ceoId, `dept-${dept}`))
  }

  return { nodes, edges }
}

/** On-brand glass node style tinted by accent (transparent panel bg via React Flow theme). */
function nodeStyle(accent: Accent): React.CSSProperties {
  const hex = accentHex[accent]
  return {
    width: NODE_WIDTH,
    padding: '8px 10px',
    borderRadius: 14,
    border: `1px solid ${hex}59`,
    background: 'rgba(12,16,24,0.78)',
    boxShadow: `0 0 0 1px rgba(255,255,255,0.04), 0 8px 24px -12px ${hex}80`,
    backdropFilter: 'blur(8px)',
  }
}

/** A cyan arrow-closed edge between two tiers. */
function edge(source: string, target: string): Edge {
  return {
    id: `${source}__${target}`,
    source,
    target,
    type: 'smoothstep',
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed, color: accentHex.cyan, width: 16, height: 16 },
    style: { stroke: `${accentHex.cyan}99`, strokeWidth: 1.5 },
  }
}

export function AgentHierarchyTree({ agents }: AgentHierarchyTreeProps) {
  const { nodes, edges } = useMemo(() => buildGraph(agents), [agents])

  return (
    <div className="omnivra-flow h-[520px] w-full overflow-hidden rounded-omnivra border border-white/[0.08] bg-omnivra-surface">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{ padding: 0.18 }}
        minZoom={0.25}
        maxZoom={1.5}
        panOnDrag
        zoomOnScroll
        nodesConnectable={false}
        elementsSelectable={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={22} size={1} color="rgba(255,255,255,0.08)" />
        <Controls
          showInteractive={false}
          className="!border-white/10 !bg-omnivra-surface-2/80 [&_button]:!border-white/10 [&_button]:!bg-transparent [&_button]:!text-zinc-300 [&_button:hover]:!bg-white/5"
        />
        <MiniMap
          pannable
          zoomable
          className="!bg-omnivra-surface-2/80"
          maskColor="rgba(7,10,15,0.7)"
          nodeColor={(n) => {
            const id = n.id
            if (id.startsWith('dept-')) {
              const dept = id.slice('dept-'.length)
              return accentHex[departmentAccent[dept] ?? 'cyan']
            }
            return accentHex.cyan
          }}
          nodeStrokeWidth={2}
        />
      </ReactFlow>
    </div>
  )
}
