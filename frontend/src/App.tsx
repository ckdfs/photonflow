import React, { useCallback, useEffect, useMemo, useState } from 'react'
import dagre from 'dagre'
import { Box, Stack, Paper, Typography, FormControl, InputLabel, Select, MenuItem, TextField, Button, Slider, IconButton } from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import OpenInFullIcon from '@mui/icons-material/OpenInFull'
import DeleteIcon from '@mui/icons-material/Delete'
import ClearAllIcon from '@mui/icons-material/ClearAll'
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh'
import ReactFlow, {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  Connection,
  Edge,
  Node,
  ReactFlowProvider,
  Background,
  Controls
} from 'reactflow'
import { api } from './api'
import { blockLabel, buildLabels, Lang } from './i18n'
import NavRail, { PageId } from './components/NavRail'
import HomePage from './pages/HomePage'
import EditorPage from './pages/EditorPage'
import ResultsPage from './pages/ResultsPage'
import SettingsPage from './pages/SettingsPage'



const defaultSim = {
  backend: 'torch',
  device: 'cpu',
  fs_min: 0,
  fs_max: 0,
  oversample: 4,
  seed: 0,
  window: 'hann',
  chunk: 0,
  duration_s: 1e-6,
  min_samples: 0,
  max_samples: 0
}

const probeTypeMap: Record<string, { kind: 'osa' | 'esa' | 'time'; inputPort: string; isOptical: boolean }> = {
  OSAProbe: { kind: 'osa', inputPort: 'opt_in', isOptical: true },
  ESAProbe: { kind: 'esa', inputPort: 'elec_in', isOptical: false },
  ScopeProbe: { kind: 'time', inputPort: 'elec_in', isOptical: false }
}

const isOutputPort = (name: string) => name.includes('out')

type LayoutOpts = {
  nodesep: number
  ranksep: number
}

const estimateNodeSize = (node: Node) => {
  const ports: Record<string, string> = node?.data?.ports || {}
  const entries = Object.entries(ports)
  const inputs = entries.filter(([name]) => !isOutputPort(name))
  const outputs = entries.filter(([name]) => isOutputPort(name))
  const rows = Math.max(inputs.length, outputs.length, 1)
  const titleLen = String(node?.data?.label || '').length
  const subtitleLen = String(node?.data?.subtitle || '').length
  const longestPortLen = entries.reduce((m, [name]) => Math.max(m, name.length), 0)

  const width = Math.max(180, 170 + Math.min(18, Math.max(titleLen, subtitleLen)) * 7, 150 + longestPortLen * 7)
  const height = 54 + rows * 22
  return { width, height }
}

const layoutWithDagre = (flowNodes: Node[], flowEdges: Edge[], opts: LayoutOpts) => {
  if (!flowNodes.length) return flowNodes
  if (!flowEdges.length) return flowNodes

  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({
    rankdir: 'LR',
    nodesep: opts.nodesep,
    ranksep: opts.ranksep,
    marginx: 40,
    marginy: 40
  })

  flowNodes.forEach((n) => {
    const { width, height } = estimateNodeSize(n)
    g.setNode(n.id, { width, height })
  })
  flowEdges.forEach((e) => {
    if (e.source && e.target) g.setEdge(e.source, e.target)
  })

  dagre.layout(g)

  return flowNodes.map((n) => {
    const p = g.node(n.id)
    if (!p) return n
    const { width, height } = p
    return {
      ...n,
      position: { x: p.x - width / 2, y: p.y - height / 2 }
    }
  })
}

export default function App() {
  const [lang, setLang] = useState<Lang>('zh')
  const [specs, setSpecs] = useState<Record<string, any>>({})
  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [layoutGap, setLayoutGap] = useState<number>(20)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)
  const [expanded, setExpanded] = useState<any>(null)
  const [showExpanded, setShowExpanded] = useState(false)
  const [status, setStatus] = useState<string>('')
  const [simConfig, setSimConfig] = useState(defaultSim)
  const [fsMode, setFsMode] = useState<'auto' | 'custom'>('auto')
  const [fsCustom, setFsCustom] = useState<number>(1e10)
  const [nSamples, setNSamples] = useState<string>('')


  const { t } = useMemo(() => buildLabels(lang), [lang])
  const msg = useCallback(
    (en: string, zh: string) => (lang === 'zh' ? zh : en),
    [lang]
  )

  const layoutOpts = useMemo<LayoutOpts>(() => ({
    nodesep: layoutGap,
    ranksep: layoutGap * 2
  }), [layoutGap])

  const lastLaserCenterHz = useMemo(() => {
    for (let i = nodes.length - 1; i >= 0; i -= 1) {
      const node = nodes[i]
      if (node?.data?.type === 'Laser') {
        const value = Number(node.data?.params?.center_freq_hz)
        return Number.isFinite(value) ? value : null
      }
    }
    return null
  }, [nodes])

  useEffect(() => {
    const fetchSpecs = () => {
      api.get('/blocks/specs')
        .then((res) => {
          setSpecs(res.data)
          setStatus('Connected to backend')
        })
        .catch((err) => {
          console.error('Failed to fetch specs:', err)
          setStatus(`Connecting... (${err.message})`)
          setTimeout(fetchSpecs, 1000)
        })
    }
    fetchSpecs()
  }, [])

  useEffect(() => {
    if (Object.keys(specs).length === 0) return
    setNodes((nds) =>
      nds.map((node) => {
        const spec = specs[node.data.type]?.spec
        if (!spec) return node
        let changed = false
        const params = { ...(node.data.params || {}) }
        const nonideal = { ...(node.data.nonideal || {}) }
        Object.entries(spec.params || {}).forEach(([key, entry]: any) => {
          if (!(key in params)) {
            params[key] = entry.default ?? null
            changed = true
          }
        })
        Object.entries(spec.nonideal || {}).forEach(([key, entry]: any) => {
          if (!(key in nonideal)) {
            nonideal[key] = entry.default ?? null
            changed = true
          }
        })
        if (!changed) return node
        return {
          ...node,
          data: {
            ...node.data,
            params,
            nonideal
          }
        }
      })
    )
  }, [specs])

  const getPortType = useCallback((nodeId: string, handle?: string | null) => {
    if (!handle) return null
    const node = nodes.find((n) => n.id === nodeId)
    return node?.data?.ports?.[handle] || null
  }, [nodes])

  const labelForType = useCallback((type: string) => blockLabel(type, lang), [lang])

  const probeOutputs = useMemo(() => {
    return nodes
      .filter((node) => probeTypeMap[node.data.type])
      .map((node) => {
        const probeInfo = probeTypeMap[node.data.type]
        const label = node.data?.label || labelForType(node.data.type)
        const title = node.data?.label ? `${label} (${node.id})` : node.id
        return {
          id: node.id,
          kind: probeInfo.kind,
          isOptical: probeInfo.isOptical,
          title
        }
      })
  }, [labelForType, nodes])



  const toFlowGraph = useCallback((graph: any) => {
    const flowNodes: Node[] = (graph.nodes || []).map((node: any, index: number) => {
      const spec = specs[node.type] || {}
      const parent = node.meta?.composite_parent
      return {
        id: String(node.id),
        type: 'block',
        position: { x: 60 + (index % 6) * 180, y: 60 + Math.floor(index / 6) * 120 },
        data: {
          label: labelForType(node.type),
          subtitle: parent ? (lang === 'zh' ? `来自 ${parent}` : `from ${parent}`) : null,
          type: node.type,
          params: node.params || {},
          nonideal: node.nonideal || {},
          ports: spec.ports || {}
        }
      }
    })
    const flowEdges: Edge[] = (graph.edges || []).map((edge: any, index: number) => ({
      id: `${edge.src}-${edge.src_port}-${edge.dst}-${edge.dst_port}-${index}`,
      source: String(edge.src),
      target: String(edge.dst),
      sourceHandle: edge.src_port,
      targetHandle: edge.dst_port
    }))
    const laidOut = layoutWithDagre(flowNodes, flowEdges, layoutOpts)
    return { flowNodes: laidOut, flowEdges }
  }, [labelForType, lang, layoutOpts, specs])

  const makeNode = useCallback((type: string, id: string, position: { x: number; y: number }, params?: Record<string, any>) => {
    const spec = specs[type]
    if (!spec) return null
    const p: Record<string, any> = {}
    const n: Record<string, any> = {}
    Object.entries(spec.spec?.params || {}).forEach(([k, v]: any) => {
      p[k] = v.default
    })
    Object.entries(spec.spec?.nonideal || {}).forEach(([k, v]: any) => {
      n[k] = v.default
    })
    if (params) {
      Object.assign(p, params)
    }
    return {
      id,
      type: 'block',
      position,
      data: { label: labelForType(type), type, params: p, nonideal: n, ports: spec.ports }
    } as Node
  }, [labelForType, specs])

  const addNode = useCallback(
    (type: string) => {
      setNodes((nds) => {
        const id = `${type}_${nds.length + 1}`
        const node = makeNode(type, id, { x: 80 + nds.length * 30, y: 80 + nds.length * 30 })
        if (!node) return nds
        return nds.concat(node)
      })
    },
    [makeNode]
  )

  const loadExample = useCallback((kind: 'pm' | 'mzm' | 'dpmzm') => {
    const baseNodes: Node[] = []
    const baseEdges: Edge[] = []
    const laser = makeNode('Laser', 'laser1', { x: 60, y: 80 }, { power_dbm: 0.0 })
    const rf = makeNode('RFSource', 'rf1', { x: 60, y: 220 }, { freq_hz: 1e9, amplitude: 1.0 })
    const osa = makeNode('OSAProbe', 'osa1', { x: 420, y: 140 })
    const pd = makeNode('PD', 'pd1', { x: 600, y: 160 }, { responsivity: 1.0 })
    const esa = makeNode('ESAProbe', 'esa1', { x: 780, y: 160 })
    if (!laser || !rf || !pd || !osa || !esa) return

    if (kind === 'pm') {
      const pm = makeNode('PM', 'pm1', { x: 240, y: 140 }, { Vpi: 4.0, phi_bias: 0.0 })
      if (!pm) return
      baseNodes.push(laser, rf, pm, osa, pd, esa)
      baseEdges.push(
        { id: 'e1', source: 'laser1', target: 'pm1', sourceHandle: 'opt_out', targetHandle: 'opt_in' },
        { id: 'e2', source: 'rf1', target: 'pm1', sourceHandle: 'elec_out', targetHandle: 'elec_in' },
        { id: 'e3', source: 'pm1', target: 'pd1', sourceHandle: 'opt_out', targetHandle: 'opt_in' },
        { id: 'e4', source: 'pm1', target: 'osa1', sourceHandle: 'opt_out', targetHandle: 'opt_in' },
        { id: 'e5', source: 'pd1', target: 'esa1', sourceHandle: 'elec_out', targetHandle: 'elec_in' }
      )
    } else if (kind === 'mzm') {
      const mzm = makeNode('MZMComposite', 'mzm1', { x: 240, y: 140 }, { Vpi: 4.0, phi_bias: 0.1 })
      if (!mzm) return
      baseNodes.push(laser, rf, mzm, osa, pd, esa)
      baseEdges.push(
        { id: 'e1', source: 'laser1', target: 'mzm1', sourceHandle: 'opt_out', targetHandle: 'opt_in' },
        { id: 'e2', source: 'rf1', target: 'mzm1', sourceHandle: 'elec_out', targetHandle: 'elec_in' },
        { id: 'e3', source: 'mzm1', target: 'pd1', sourceHandle: 'opt_out', targetHandle: 'opt_in' },
        { id: 'e4', source: 'mzm1', target: 'osa1', sourceHandle: 'opt_out', targetHandle: 'opt_in' },
        { id: 'e5', source: 'pd1', target: 'esa1', sourceHandle: 'elec_out', targetHandle: 'elec_in' }
      )
    } else {
      const dpmzm = makeNode('DPMZMComposite', 'dpmzm1', { x: 240, y: 140 }, { Vpi: 4.0, phi_bias_i: 0.0, phi_bias_q: 0.0 })
      if (!dpmzm) return
      baseNodes.push(laser, rf, dpmzm, osa, pd, esa)
      baseEdges.push(
        { id: 'e1', source: 'laser1', target: 'dpmzm1', sourceHandle: 'opt_out', targetHandle: 'opt_in' },
        { id: 'e2', source: 'rf1', target: 'dpmzm1', sourceHandle: 'elec_out', targetHandle: 'elec_i' },
        { id: 'e3', source: 'dpmzm1', target: 'pd1', sourceHandle: 'opt_out', targetHandle: 'opt_in' },
        { id: 'e4', source: 'dpmzm1', target: 'osa1', sourceHandle: 'opt_out', targetHandle: 'opt_in' },
        { id: 'e5', source: 'pd1', target: 'esa1', sourceHandle: 'elec_out', targetHandle: 'elec_in' }
      )
    }
    setNodes(layoutWithDagre(baseNodes, baseEdges, layoutOpts))
    setEdges(baseEdges)
    setSelectedId(null)
    setResult(null)
    setExpanded(null)
    setShowExpanded(false)
    setStatus(msg('Example loaded', '示例已加载'))
  }, [layoutOpts, makeNode, msg])

  const autoLayout = useCallback(() => {
    setNodes((nds) => layoutWithDagre(nds, edges, layoutOpts))
    setStatus(msg('Auto layout applied', '已自动排布'))
  }, [edges, layoutOpts, msg])

  const isValidConnection = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return false
      const srcType = getPortType(connection.source, connection.sourceHandle)
      const dstType = getPortType(connection.target, connection.targetHandle)
      return Boolean(srcType && dstType && srcType === dstType)
    },
    [getPortType]
  )

  const onConnect = useCallback(
    (connection: Edge | Connection) => {
      if (!isValidConnection(connection as Connection)) return
      setEdges((eds) => addEdge(connection, eds))
    },
    [isValidConnection]
  )

  const deleteSelected = useCallback(() => {
    if (selectedEdgeId) {
      setEdges((eds) => eds.filter((edge) => edge.id !== selectedEdgeId))
      setSelectedEdgeId(null)
      setStatus(msg('Edge deleted', '连线已删除'))
      return
    }
    if (!selectedId) {
      setStatus(msg('No selection', '未选择节点或连线'))
      return
    }
    setNodes((nds) => nds.filter((node) => node.id !== selectedId))
    setEdges((eds) => eds.filter((edge) => edge.source !== selectedId && edge.target !== selectedId))
    setSelectedId(null)
    setStatus(msg('Node deleted', '节点已删除'))
  }, [msg, selectedEdgeId, selectedId])

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Delete' && !showExpanded) {
        deleteSelected()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [deleteSelected, showExpanded])



  const buildGraph = () => {
    const graphNodes = nodes.map((node) => ({
      id: node.id,
      type: node.data.type,
      params: node.data.params,
      nonideal: node.data.nonideal
    }))
    const graphEdges = edges.map((edge) => {
      let dstPort = edge.targetHandle || 'opt_in'
      if (!edge.targetHandle) {
        const targetNode = nodes.find((node) => node.id === edge.target)
        const probeInfo = targetNode ? probeTypeMap[targetNode.data.type] : null
        if (probeInfo) {
          dstPort = probeInfo.inputPort
        }
      }
      return {
        src: edge.source,
        src_port: edge.sourceHandle || 'opt_out',
        dst: edge.target,
        dst_port: dstPort
      }
    })
    const probeNodes = nodes.filter((node) => probeTypeMap[node.data.type])
    const probeIssues = { missing: [] as string[], multiple: [] as string[] }
    const probeOutputs = probeNodes.map((node) => {
      const probeInfo = probeTypeMap[node.data.type]
      const incoming = edges.filter((edge) => edge.target === node.id)
      const matching = incoming.filter(
        (edge) => !edge.targetHandle || edge.targetHandle === probeInfo.inputPort
      )
      if (matching.length === 0) {
        probeIssues.missing.push(node.id)
      } else if (matching.length > 1) {
        probeIssues.multiple.push(node.id)
      }
      const params: Record<string, any> = {}
      if (probeInfo.kind !== 'time') {
        const raw = node.data.params || {}
        if (raw.window) params.window = raw.window
        if (raw.ref !== undefined) params.ref = raw.ref
        if (raw.include_power !== undefined) params.include_power = raw.include_power
      }
      return {
        node: node.id,
        port: probeInfo.inputPort,
        kind: probeInfo.kind,
        ...(Object.keys(params).length ? { params } : {})
      }
    })
    const useProbes = probeOutputs.length > 0

    const fsValue =
      fsMode === 'auto' ? 'auto' : Number.isFinite(fsCustom) && fsCustom > 0 ? fsCustom : 'auto'
    const sim: any = {
      ...simConfig,
      fs: fsValue
    }
    const nSamplesValue = parseInt(nSamples, 10)
    if (Number.isFinite(nSamplesValue) && nSamplesValue >= 2) {
      sim.n_samples = nSamplesValue
    }

    const graph = {
      version: '0.1',
      sim,
      nodes: graphNodes,
      edges: graphEdges,
      outputs: { extra: probeOutputs }
    }
    return { graph, useProbes, probeIssues }
  }

  const runValidate = async () => {
    const { graph, useProbes, probeIssues } = buildGraph()
    if (!useProbes) {
      setStatus(msg('Add probe nodes (OSA/ESA/Scope) before validating.', '请先添加观测仪器节点（光谱仪/电谱仪/示波器）。'))
      return
    }
    if (probeIssues.missing.length || probeIssues.multiple.length) {
      const missing = probeIssues.missing.length ? `Missing inputs: ${probeIssues.missing.join(', ')}` : ''
      const multiple = probeIssues.multiple.length ? `Multiple inputs: ${probeIssues.multiple.join(', ')}` : ''
      const enMsg = [missing, multiple].filter(Boolean).join('. ')
      const zhMissing = probeIssues.missing.length ? `缺少输入：${probeIssues.missing.join('、')}` : ''
      const zhMultiple = probeIssues.multiple.length ? `多输入冲突：${probeIssues.multiple.join('、')}` : ''
      const zhMsg = [zhMissing, zhMultiple].filter(Boolean).join('；')
      setStatus(msg(enMsg || 'Probe input error.', zhMsg || '观测仪器输入异常。'))
      return
    }
    setStatus(msg('Validating...', '正在校验...'))
    try {
      const res = await api.post('/graph/validate', { graph, validate: true })
      if (res.data.status === 'ok') {
        setStatus(msg('Graph OK', '图校验通过'))
      } else {
        setStatus(msg(`Validate error: ${res.data.error}`, `校验失败：${res.data.error}`))
      }
    } catch (err: any) {
      setStatus(msg(`Validate error: ${err}`, `校验失败：${err}`))
    }
  }

  const runExpand = async () => {
    if (expanded) {
      setShowExpanded((v) => !v)
      return
    }

    const { graph, useProbes, probeIssues } = buildGraph()
    if (!useProbes) {
      setStatus(msg('Add probe nodes (OSA/ESA/Scope) before expanding.', '请先添加观测仪器节点（光谱仪/电谱仪/示波器）。'))
      return
    }
    if (probeIssues.missing.length || probeIssues.multiple.length) {
      const missing = probeIssues.missing.length ? `Missing inputs: ${probeIssues.missing.join(', ')}` : ''
      const multiple = probeIssues.multiple.length ? `Multiple inputs: ${probeIssues.multiple.join(', ')}` : ''
      const enMsg = [missing, multiple].filter(Boolean).join('. ')
      const zhMissing = probeIssues.missing.length ? `缺少输入：${probeIssues.missing.join('、')}` : ''
      const zhMultiple = probeIssues.multiple.length ? `多输入冲突：${probeIssues.multiple.join('、')}` : ''
      const zhMsg = [zhMissing, zhMultiple].filter(Boolean).join('；')
      setStatus(msg(enMsg || 'Probe input error.', zhMsg || '观测仪器输入异常。'))
      return
    }
    setStatus(msg('Expanding...', '正在展开...'))
    try {
      const res = await api.post('/graph/expand', { graph, validate: true, annotate: true })
      setExpanded(res.data.graph)
      setShowExpanded(true)
      setStatus(msg('Expanded', '展开完成'))
    } catch (err: any) {
      setStatus(msg(`Expand error: ${err}`, `展开失败：${err}`))
    }
  }

  const runJob = async () => {
    const { graph, useProbes, probeIssues } = buildGraph()
    if (!useProbes) {
      setStatus(msg('Add probe nodes (OSA/ESA/Scope) before running.', '请先添加观测仪器节点（光谱仪/电谱仪/示波器）。'))
      return
    }
    if (probeIssues.missing.length || probeIssues.multiple.length) {
      const missing = probeIssues.missing.length ? `Missing inputs: ${probeIssues.missing.join(', ')}` : ''
      const multiple = probeIssues.multiple.length ? `Multiple inputs: ${probeIssues.multiple.join(', ')}` : ''
      const enMsg = [missing, multiple].filter(Boolean).join('. ')
      const zhMissing = probeIssues.missing.length ? `缺少输入：${probeIssues.missing.join('、')}` : ''
      const zhMultiple = probeIssues.multiple.length ? `多输入冲突：${probeIssues.multiple.join('、')}` : ''
      const zhMsg = [zhMissing, zhMultiple].filter(Boolean).join('；')
      setStatus(msg(enMsg || 'Probe input error.', zhMsg || '观测仪器输入异常。'))
      return
    }
    setStatus(msg('Submitting job...', '提交任务中...'))
    try {
      const submit = await api.post('/jobs/submit', { graph, validate: true })
      const jobId = submit.data.job_id
      let jobStatus = 'queued'
      while (jobStatus === 'queued' || jobStatus === 'running') {
        const result = await api.get(`/jobs/${jobId}/result`)
        jobStatus = result.data.status
        if (jobStatus === 'done') {
          setResult(result.data.result)
          setStatus(msg('Job done', '任务完成'))
          return
        }
        if (jobStatus === 'error') {
          setStatus(msg(`Job error: ${result.data.error}`, `任务失败：${result.data.error}`))
          return
        }
        await new Promise((r) => setTimeout(r, 500))
      }
    } catch (err: any) {
      setStatus(msg(`Job error: ${err}`, `任务失败：${err}`))
    }
  }

  const view = showExpanded && expanded ? toFlowGraph(expanded) : { flowNodes: nodes, flowEdges: edges }

  const selectedNode = useMemo(() => view.flowNodes.find((n) => n.id === selectedId) || null, [view.flowNodes, selectedId])

  const updateNodeParam = (section: string, key: string, value: any) => {
    if (!selectedNode || showExpanded) return
    setNodes((nds) =>
      nds.map((n) => {
        if (n.id !== selectedNode.id) return n
        return {
          ...n,
          data: {
            ...n.data,
            [section]: {
              ...n.data[section],
              [key]: value
            }
          }
        }
      })
    )
  }
  const toggleExpanded = () => {
    if (!expanded) {
      setStatus(msg('No expanded graph. Click Expand first.', '没有展开图，请先点击展开。'))
      return
    }
    setShowExpanded((v) => !v)
  }

  const clearGraph = () => {
    setNodes([])
    setEdges([])
    setSelectedId(null)
    setSelectedEdgeId(null)
    setExpanded(null)
    setShowExpanded(false)
    setResult(null)
    setStatus(msg('Cleared.', '已清空。'))
  }

  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, label: labelForType(node.data.type) }
      }))
    )
  }, [labelForType])


  const [activePage, setActivePage] = useState<PageId>('editor')

  const renderPage = () => {
    switch (activePage) {
      case 'home':
        return <HomePage onNavigate={setActivePage} />
      case 'editor':
        return (
          <EditorPage
            nodes={nodes}
            edges={edges}
            setNodes={setNodes}
            setEdges={setEdges}
            selectedId={selectedId}
            setSelectedId={setSelectedId}
            selectedEdgeId={selectedEdgeId}
            setSelectedEdgeId={setSelectedEdgeId}
            expanded={expanded}
            showExpanded={showExpanded}
            view={view}
            onNodesChange={(changes) => {
              if (!showExpanded) setNodes((nds) => applyNodeChanges(changes, nds))
            }}
            onEdgesChange={(changes) => {
              if (!showExpanded) setEdges((eds) => applyEdgeChanges(changes, eds))
            }}
            onConnect={onConnect}
            isValidConnection={isValidConnection}
            addNode={addNode}
            deleteSelected={deleteSelected}
            clearGraph={clearGraph}
            autoLayout={autoLayout}
            runValidate={runValidate}
            runExpand={runExpand}
            runJob={runJob}
            loadExample={loadExample}
            layoutGap={layoutGap}
            setLayoutGap={setLayoutGap}
            specs={specs}
            selectedNode={selectedNode}
            updateNodeParam={updateNodeParam}
            t={t}
            msg={msg}
            status={status}
            labelForType={labelForType}
            labels={{
              inspector: t('inspector'),
              selectNode: t('selectNode'),
              title: t('inspector'),
              params: t('params'),
              nonideal: t('nonideal')
            }}
          />
        )
      case 'results':
        return (
          <ResultsPage
            result={result}
            probeOutputs={probeOutputs}
            labels={{
              osaPlotSettings: t('osaPlotSettings'),
              esaPlotSettings: t('esaPlotSettings'),
              showPeak: t('showPeak'),
              showMinMax: t('showMinMax'),
              viewRange: t('viewRange'),
              rangeAuto: t('rangeAuto'),
              rangeCustom: t('rangeCustom'),
              rangeMin: t('rangeMin'),
              rangeMax: t('rangeMax'),
              saveCsv: t('saveCsv'),
              exportSettings: t('exportSettings'),
              exportScale: t('exportScale'),
              exportFormat: t('exportFormat'),
              exportBackground: t('exportBackground'),
              exportPng: t('exportPng'),
              exportSvg: t('exportSvg'),
              exportBgSolid: t('exportBgSolid'),
              exportBgTransparent: t('exportBgTransparent'),
              noResults: msg('No results available. Run a simulation first.', '暂无结果，请先运行仿真。')
            }}
          />
        )
      case 'settings':
        return (
          <SettingsPage
            lang={lang}
            setLang={setLang}
            simConfig={simConfig}
            setSimConfig={setSimConfig}
            fsMode={fsMode}
            setFsMode={setFsMode}
            fsCustom={fsCustom}
            setFsCustom={setFsCustom}
            nSamples={nSamples}
            setNSamples={setNSamples}
            t={t}
          />
        )
      default:
        return null
    }
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'background.default' }}>
      <NavRail activePage={activePage} onNavigate={setActivePage} />
      <Box sx={{ flex: 1, overflow: 'hidden', height: '100%' }}>
        {renderPage()}
      </Box>
    </Box>
  )
}

