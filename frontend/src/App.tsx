import React, { useCallback, useEffect, useMemo, useState } from 'react'
import ReactFlow, {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  Background,
  Connection,
  Controls,
  Edge,
  Node,
  ReactFlowProvider
} from 'reactflow'
import { api } from './api'
import BlockLibrary from './components/BlockLibrary'
import Inspector from './components/Inspector'
import Outputs from './components/Outputs'
import BlockNode from './components/BlockNode'
import ExpandToggle from './components/ExpandToggle'
import { blockLabel, buildLabels, Lang } from './i18n'

const nodeTypes = { block: BlockNode }

type OsaMode = 'auto' | 'manual'
type EsaMode = 'auto' | 'esa' | 'time'

type OutputConfig = {
  osaMode: OsaMode
  osaNode: string
  osaPort: string
  esaMode: EsaMode
  esaNode: string
  esaPort: string
  includePower: boolean
}

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

const defaultOutputConfig: OutputConfig = {
  osaMode: 'auto',
  osaNode: '',
  osaPort: '',
  esaMode: 'auto',
  esaNode: '',
  esaPort: '',
  includePower: false
}

export default function App() {
  const [lang, setLang] = useState<Lang>('zh')
  const [specs, setSpecs] = useState<Record<string, any>>({})
  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)
  const [expanded, setExpanded] = useState<any>(null)
  const [showExpanded, setShowExpanded] = useState(false)
  const [status, setStatus] = useState<string>('')
  const [simConfig, setSimConfig] = useState(defaultSim)
  const [fsMode, setFsMode] = useState<'auto' | 'custom'>('auto')
  const [fsCustom, setFsCustom] = useState<number>(1e10)
  const [nSamples, setNSamples] = useState<string>('')
  const [showAdvancedSim, setShowAdvancedSim] = useState(false)
  const [outputConfig, setOutputConfig] = useState<OutputConfig>(defaultOutputConfig)

  const { t } = useMemo(() => buildLabels(lang), [lang])
  const msg = useCallback(
    (en: string, zh: string) => (lang === 'zh' ? zh : en),
    [lang]
  )

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
    api.get('/blocks/specs').then((res) => setSpecs(res.data))
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

  const outputPorts = useMemo(() => {
    const optical: { nodeId: string; port: string; label: string }[] = []
    const electrical: { nodeId: string; port: string; label: string }[] = []
    const any: { nodeId: string; port: string; label: string; type: string }[] = []
    nodes.forEach((node) => {
      const ports = node.data?.ports || {}
      const displayName = node.data?.label ? `${node.data.label} (${node.id})` : node.id
      Object.entries(ports).forEach(([port, type]) => {
        if (!port.startsWith('opt_out') && !port.startsWith('elec_out')) return
        const entry = { nodeId: node.id, port, label: `${displayName} · ${port}`, type: String(type) }
        if (type === 'optical' && port.startsWith('opt_out')) {
          optical.push({ nodeId: node.id, port, label: entry.label })
        }
        if (type === 'electrical' && port.startsWith('elec_out')) {
          electrical.push({ nodeId: node.id, port, label: entry.label })
        }
        any.push(entry)
      })
    })
    return { optical, electrical, any }
  }, [nodes])

  useEffect(() => {
    const pickLast = (list: { nodeId: string; port: string }[]) =>
      list.length > 0
        ? { nodeId: list[list.length - 1].nodeId, port: list[list.length - 1].port }
        : { nodeId: '', port: '' }
    const hasPort = (list: { nodeId: string; port: string }[], nodeId: string, port: string) =>
      list.some((item) => item.nodeId === nodeId && item.port === port)

    setOutputConfig((prev) => {
      let next = prev
      if (prev.osaMode === 'manual') {
        if (!hasPort(outputPorts.optical, prev.osaNode, prev.osaPort)) {
          const last = pickLast(outputPorts.optical)
          next = { ...next, osaNode: last.nodeId, osaPort: last.port }
        }
      }
      if (prev.esaMode === 'esa') {
        if (!hasPort(outputPorts.electrical, prev.esaNode, prev.esaPort)) {
          const last = pickLast(outputPorts.electrical)
          next = { ...next, esaNode: last.nodeId, esaPort: last.port }
        }
      }
      if (prev.esaMode === 'time') {
        if (!hasPort(outputPorts.any, prev.esaNode, prev.esaPort)) {
          const last = pickLast(outputPorts.any)
          next = { ...next, esaNode: last.nodeId, esaPort: last.port }
        }
      }
      return next
    })
  }, [outputPorts, outputConfig.esaMode, outputConfig.osaMode])

  const toFlowGraph = useCallback((graph: any) => {
    const flowNodes: Node[] = (graph.nodes || []).map((node: any, index: number) => {
      const spec = specs[node.type] || {}
      const parent = node.meta?.composite_parent
      return {
        id: node.id,
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
      source: edge.src,
      target: edge.dst,
      sourceHandle: edge.src_port,
      targetHandle: edge.dst_port
    }))
    return { flowNodes, flowEdges }
  }, [labelForType, lang, specs])

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
    const pd = makeNode('PD', 'pd1', { x: 420, y: 160 }, { responsivity: 1.0 })
    if (!laser || !rf || !pd) return

    if (kind === 'pm') {
      const pm = makeNode('PM', 'pm1', { x: 240, y: 140 }, { Vpi: 4.0, phi_bias: 0.0 })
      if (!pm) return
      baseNodes.push(laser, rf, pm, pd)
      baseEdges.push(
        { id: 'e1', source: 'laser1', target: 'pm1', sourceHandle: 'opt_out', targetHandle: 'opt_in' },
        { id: 'e2', source: 'rf1', target: 'pm1', sourceHandle: 'elec_out', targetHandle: 'elec_in' },
        { id: 'e3', source: 'pm1', target: 'pd1', sourceHandle: 'opt_out', targetHandle: 'opt_in' }
      )
    } else if (kind === 'mzm') {
      const mzm = makeNode('MZMComposite', 'mzm1', { x: 240, y: 140 }, { Vpi: 4.0, phi_bias: 0.1 })
      if (!mzm) return
      baseNodes.push(laser, rf, mzm, pd)
      baseEdges.push(
        { id: 'e1', source: 'laser1', target: 'mzm1', sourceHandle: 'opt_out', targetHandle: 'opt_in' },
        { id: 'e2', source: 'rf1', target: 'mzm1', sourceHandle: 'elec_out', targetHandle: 'elec_in' },
        { id: 'e3', source: 'mzm1', target: 'pd1', sourceHandle: 'opt_out', targetHandle: 'opt_in' }
      )
    } else {
      const rfQ = makeNode('RFSource', 'rf2', { x: 60, y: 300 }, { freq_hz: 1e9, amplitude: 1.0, phase: Math.PI / 2 })
      const dpmzm = makeNode('DPMZMComposite', 'dpmzm1', { x: 240, y: 140 }, { Vpi: 4.0, phi_bias_i: 0.0, phi_bias_q: 0.0 })
      if (!rfQ || !dpmzm) return
      baseNodes.push(laser, rf, rfQ, dpmzm, pd)
      baseEdges.push(
        { id: 'e1', source: 'laser1', target: 'dpmzm1', sourceHandle: 'opt_out', targetHandle: 'opt_in' },
        { id: 'e2', source: 'rf1', target: 'dpmzm1', sourceHandle: 'elec_out', targetHandle: 'elec_i' },
        { id: 'e3', source: 'rf2', target: 'dpmzm1', sourceHandle: 'elec_out', targetHandle: 'elec_q' },
        { id: 'e4', source: 'dpmzm1', target: 'pd1', sourceHandle: 'opt_out', targetHandle: 'opt_in' }
      )
    }
    setNodes(baseNodes)
    setEdges(baseEdges)
    setSelectedId(null)
    setResult(null)
    setExpanded(null)
    setShowExpanded(false)
    setStatus(msg('Example loaded', '示例已加载'))
  }, [makeNode, msg])

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
    if (!selectedId) {
      setStatus(msg('No node selected', '未选择节点'))
      return
    }
    setNodes((nds) => nds.filter((node) => node.id !== selectedId))
    setEdges((eds) => eds.filter((edge) => edge.source !== selectedId && edge.target !== selectedId))
    setSelectedId(null)
    setStatus(msg('Node deleted', '节点已删除'))
  }, [msg, selectedId])

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Delete' && !showExpanded) {
        deleteSelected()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [deleteSelected, showExpanded])

  const selectedNode = useMemo(() => nodes.find((n) => n.id === selectedId) || null, [nodes, selectedId])

  const updateNodeParam = (section: string, key: string, value: any) => {
    if (!selectedNode) return
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

  const buildGraph = () => {
    const graphNodes = nodes.map((node) => ({
      id: node.id,
      type: node.data.type,
      params: node.data.params,
      nonideal: node.data.nonideal
    }))
    const graphEdges = edges.map((edge) => ({
      src: edge.source,
      src_port: edge.sourceHandle || 'opt_out',
      dst: edge.target,
      dst_port: edge.targetHandle || 'opt_in'
    }))
    const warnings = { en: [] as string[], zh: [] as string[] }
    const isValidOutput = (nodeId: string, port: string, kind: 'optical' | 'electrical' | 'any') => {
      const node = nodes.find((n) => n.id === nodeId)
      const portType = node?.data?.ports?.[port]
      if (!portType) return false
      if (!port.startsWith('opt_out') && !port.startsWith('elec_out')) return false
      if (kind === 'optical') return portType === 'optical'
      if (kind === 'electrical') return portType === 'electrical'
      return portType === 'optical' || portType === 'electrical'
    }

    const fallbackNode = nodes[nodes.length - 1] || null
    const autoOsa = outputPorts.optical[outputPorts.optical.length - 1] || (fallbackNode ? { nodeId: fallbackNode.id, port: 'opt_out' } : null)
    const autoElec = outputPorts.electrical[outputPorts.electrical.length - 1] || null

    let osaRef = autoOsa
    if (outputConfig.osaMode === 'manual') {
      if (outputConfig.osaNode && outputConfig.osaPort && isValidOutput(outputConfig.osaNode, outputConfig.osaPort, 'optical')) {
        osaRef = { nodeId: outputConfig.osaNode, port: outputConfig.osaPort }
      } else {
        warnings.en.push('OSA source invalid, using auto.')
        warnings.zh.push('OSA 来源无效，已使用自动。')
      }
    }

    const osaNodeId = osaRef?.nodeId || ''
    const osaPort = osaRef?.port || 'opt_out'
    const spectrumParams = outputConfig.includePower ? { include_power: true } : undefined

    let esaSpec: { node: string; port: string; kind: 'esa' | 'time'; params?: any }
    let usesElecOut = false
    if (outputConfig.esaMode === 'auto') {
      if (autoElec) {
        usesElecOut = true
        esaSpec = { node: autoElec.nodeId, port: autoElec.port, kind: 'esa', ...(spectrumParams ? { params: spectrumParams } : {}) }
      } else {
        esaSpec = { node: osaNodeId, port: osaPort, kind: 'time' }
      }
    } else if (outputConfig.esaMode === 'esa') {
      if (outputConfig.esaNode && outputConfig.esaPort && isValidOutput(outputConfig.esaNode, outputConfig.esaPort, 'electrical')) {
        usesElecOut = true
        esaSpec = { node: outputConfig.esaNode, port: outputConfig.esaPort, kind: 'esa', ...(spectrumParams ? { params: spectrumParams } : {}) }
      } else {
        warnings.en.push('ESA source invalid, using auto.')
        warnings.zh.push('ESA 来源无效，已使用自动。')
        if (autoElec) {
          usesElecOut = true
          esaSpec = { node: autoElec.nodeId, port: autoElec.port, kind: 'esa', ...(spectrumParams ? { params: spectrumParams } : {}) }
        } else {
          esaSpec = { node: osaNodeId, port: osaPort, kind: 'time' }
        }
      }
    } else {
      if (outputConfig.esaNode && outputConfig.esaPort && isValidOutput(outputConfig.esaNode, outputConfig.esaPort, 'any')) {
        esaSpec = { node: outputConfig.esaNode, port: outputConfig.esaPort, kind: 'time' }
      } else {
        warnings.en.push('Time preview source invalid, using auto.')
        warnings.zh.push('时域预览来源无效，已使用自动。')
        esaSpec = { node: osaNodeId, port: osaPort, kind: 'time' }
      }
    }

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
      outputs: {
        osa: {
          node: osaNodeId,
          port: osaPort,
          kind: 'osa',
          ...(spectrumParams ? { params: spectrumParams } : {})
        },
        esa: esaSpec
      }
    }
    return { graph, hasElecOut: usesElecOut, warnings }
  }

  const formatWarnings = (warnings: { en: string[]; zh: string[] }) => {
    if (warnings.en.length === 0) {
      return { en: '', zh: '' }
    }
    return {
      en: ` Warnings: ${warnings.en.join(' ')}`,
      zh: ` 警告：${warnings.zh.join('；')}`
    }
  }

  const runValidate = async () => {
    const { graph, hasElecOut, warnings } = buildGraph()
    const warn = formatWarnings(warnings)
    if (!hasElecOut) {
      setStatus(msg(`No electrical output; ESA uses time preview.${warn.en}`, `未找到电输出端口，ESA 改为时域预览。${warn.zh}`))
    } else {
      setStatus(msg(`Validating...${warn.en}`, `正在校验...${warn.zh}`))
    }
    try {
      const res = await api.post('/graph/validate', { graph, validate: true })
      if (res.data.status === 'ok') {
        setStatus(msg(`Graph OK${warn.en}`, `图校验通过${warn.zh}`))
      } else {
        setStatus(msg(`Validate error: ${res.data.error}`, `校验失败：${res.data.error}`))
      }
    } catch (err: any) {
      setStatus(msg(`Validate error: ${err}`, `校验失败：${err}`))
    }
  }

  const runExpand = async () => {
    const { graph, hasElecOut, warnings } = buildGraph()
    const warn = formatWarnings(warnings)
    if (!hasElecOut) {
      setStatus(msg(`No electrical output; ESA uses time preview.${warn.en}`, `未找到电输出端口，ESA 改为时域预览。${warn.zh}`))
    } else {
      setStatus(msg(`Expanding...${warn.en}`, `正在展开...${warn.zh}`))
    }
    try {
      const res = await api.post('/graph/expand', { graph, validate: true, annotate: true })
      setExpanded(res.data.graph)
      setShowExpanded(true)
      setStatus(msg(`Expanded${warn.en}`, `展开完成${warn.zh}`))
    } catch (err: any) {
      setStatus(msg(`Expand error: ${err}`, `展开失败：${err}`))
    }
  }

  const runJob = async () => {
    const { graph, hasElecOut, warnings } = buildGraph()
    const warn = formatWarnings(warnings)
    if (!hasElecOut) {
      setStatus(msg(`No electrical output; ESA uses time preview.${warn.en}`, `未找到电输出端口，ESA 改为时域预览。${warn.zh}`))
    } else {
      setStatus(msg(`Submitting job...${warn.en}`, `提交任务中...${warn.zh}`))
    }
    try {
      const submit = await api.post('/jobs/submit', { graph, validate: true })
      const jobId = submit.data.job_id
      let jobStatus = 'queued'
      while (jobStatus === 'queued' || jobStatus === 'running') {
        const result = await api.get(`/jobs/${jobId}/result`)
        jobStatus = result.data.status
        if (jobStatus === 'done') {
          setResult(result.data.result)
          setStatus(msg(`Job done${warn.en}`, `任务完成${warn.zh}`))
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
  const toggleExpanded = () => {
    if (!expanded) {
      setStatus(msg('No expanded graph. Click Expand first.', '没有展开图，请先点击展开。'))
      return
    }
    setShowExpanded((v) => !v)
  }

  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, label: labelForType(node.data.type) }
      }))
    )
  }, [labelForType])

  return (
    <div className="layout">
      <div className="sidebar">
        <div className="panel">
          <div className="panel-title">{t('settings')}</div>
          <div className="panel-body">
            <label className="field">
              <span>{t('language')}</span>
              <select value={lang} onChange={(e) => setLang(e.target.value as Lang)}>
                <option value="zh">{lang === 'zh' ? '中文' : 'Chinese'}</option>
                <option value="en">{lang === 'zh' ? '英文' : 'English'}</option>
              </select>
            </label>
          </div>
        </div>
        <div className="panel">
          <div className="panel-title">{t('simSettings')}</div>
          <div className="panel-body">
            <label className="field">
              <span>{t('backend')}</span>
              <select
                value={simConfig.backend}
                onChange={(e) => setSimConfig((cfg) => ({ ...cfg, backend: e.target.value }))}
              >
                <option value="torch">torch</option>
              </select>
            </label>
            <label className="field">
              <span>{t('device')}</span>
              <select
                value={simConfig.device}
                onChange={(e) => setSimConfig((cfg) => ({ ...cfg, device: e.target.value }))}
              >
                <option value="cpu">cpu</option>
                <option value="cuda">cuda</option>
              </select>
            </label>
            <label className="field">
              <span>{t('fsMode')}</span>
              <select
                value={fsMode}
                onChange={(e) => setFsMode(e.target.value as 'auto' | 'custom')}
              >
                <option value="auto">{t('fsAuto')}</option>
                <option value="custom">{t('fsCustom')}</option>
              </select>
            </label>
            <label className="field">
              <span>{t('fsValue')}</span>
              <input
                type="number"
                value={fsCustom}
                disabled={fsMode === 'auto'}
                onChange={(e) => setFsCustom(Number(e.target.value))}
              />
            </label>
            <label className="field">
              <span>{t('oversample')}</span>
              <input
                type="number"
                value={simConfig.oversample}
                onChange={(e) => setSimConfig((cfg) => ({ ...cfg, oversample: Number(e.target.value) }))}
              />
            </label>
            <label className="field">
              <span>{t('window')}</span>
              <select
                value={simConfig.window}
                onChange={(e) => setSimConfig((cfg) => ({ ...cfg, window: e.target.value }))}
              >
                <option value="hann">hann</option>
                <option value="hamming">hamming</option>
                <option value="blackman">blackman</option>
                <option value="rect">rect</option>
                <option value="kaiser">kaiser</option>
              </select>
            </label>
            <label className="field">
              <span>{t('duration')}</span>
              <input
                type="number"
                value={simConfig.duration_s}
                onChange={(e) => setSimConfig((cfg) => ({ ...cfg, duration_s: Number(e.target.value) }))}
              />
            </label>
            <label className="field">
              <span>{t('nSamples')}</span>
              <input
                type="number"
                value={nSamples}
                onChange={(e) => setNSamples(e.target.value)}
              />
            </label>
            <button
              className="link-button"
              onClick={() => setShowAdvancedSim((v) => !v)}
              type="button"
            >
              {showAdvancedSim ? t('hideAdvanced') : t('showAdvanced')}
            </button>
            {showAdvancedSim && (
              <div className="advanced-group">
                <div className="section-title">{t('advancedSettings')}</div>
                <label className="field">
                  <span>{t('seed')}</span>
                  <input
                    type="number"
                    value={simConfig.seed}
                    onChange={(e) => setSimConfig((cfg) => ({ ...cfg, seed: Number(e.target.value) }))}
                  />
                </label>
                <label className="field">
                  <span>{t('fsMin')}</span>
                  <input
                    type="number"
                    value={simConfig.fs_min}
                    onChange={(e) => setSimConfig((cfg) => ({ ...cfg, fs_min: Number(e.target.value) }))}
                  />
                </label>
                <label className="field">
                  <span>{t('fsMax')}</span>
                  <input
                    type="number"
                    value={simConfig.fs_max}
                    onChange={(e) => setSimConfig((cfg) => ({ ...cfg, fs_max: Number(e.target.value) }))}
                  />
                </label>
                <label className="field">
                  <span>{t('chunk')}</span>
                  <input
                    type="number"
                    value={simConfig.chunk}
                    onChange={(e) => setSimConfig((cfg) => ({ ...cfg, chunk: Number(e.target.value) }))}
                  />
                </label>
                <label className="field">
                  <span>{t('minSamples')}</span>
                  <input
                    type="number"
                    value={simConfig.min_samples}
                    onChange={(e) => setSimConfig((cfg) => ({ ...cfg, min_samples: Number(e.target.value) }))}
                  />
                </label>
                <label className="field">
                  <span>{t('maxSamples')}</span>
                  <input
                    type="number"
                    value={simConfig.max_samples}
                    onChange={(e) => setSimConfig((cfg) => ({ ...cfg, max_samples: Number(e.target.value) }))}
                  />
                </label>
              </div>
            )}
          </div>
        </div>
        <div className="panel">
          <div className="panel-title">{t('examples')}</div>
          <div className="panel-body">
            <button className="block-button" onClick={() => loadExample('pm')}>
              {t('examplePm')}
            </button>
            <button className="block-button" onClick={() => loadExample('mzm')}>
              {t('exampleMzm')}
            </button>
            <button className="block-button" onClick={() => loadExample('dpmzm')}>
              {t('exampleDpmzm')}
            </button>
          </div>
        </div>
        <BlockLibrary
          types={Object.keys(specs)}
          onAdd={addNode}
          title={t('blocks')}
          labelForType={labelForType}
          searchPlaceholder={t('searchBlocks')}
          noMatchText={t('noMatch')}
        />
      </div>
      <div className="canvas">
        <ReactFlowProvider>
          <ReactFlow
            nodes={view.flowNodes}
            edges={view.flowEdges}
            nodeTypes={nodeTypes}
            onNodesChange={(changes) => {
              if (!showExpanded) setNodes((nds) => applyNodeChanges(changes, nds))
            }}
            onEdgesChange={(changes) => {
              if (!showExpanded) setEdges((eds) => applyEdgeChanges(changes, eds))
            }}
            onConnect={(connection) => {
              if (!showExpanded) onConnect(connection)
            }}
            isValidConnection={isValidConnection}
            onNodeClick={(_, node) => {
              if (!showExpanded) setSelectedId(node.id)
            }}
            nodesDraggable={!showExpanded}
            nodesConnectable={!showExpanded}
            elementsSelectable={!showExpanded}
            fitView
          >
            <Controls />
            <Background />
          </ReactFlow>
        </ReactFlowProvider>
        <div className="toolbar">
          <button onClick={runValidate}>{t('validate')}</button>
          <button onClick={runExpand}>{t('expand')}</button>
          <button onClick={runJob}>{t('run')}</button>
          <button onClick={deleteSelected} disabled={showExpanded}>{t('delete')}</button>
          <ExpandToggle
            showExpanded={showExpanded}
            onToggle={toggleExpanded}
            labels={{ showExpanded: t('showExpanded'), collapse: t('collapse') }}
          />
          <div className="graph-stats">
            {t('nodes')}: {nodes.length} · {t('edges')}: {edges.length}
          </div>
          <div className="status-line" title={status || '-'}>
            {t('status')}: {status || '-'}
          </div>
        </div>
      </div>
      <div className="sidebar">
        <Inspector
          node={selectedNode}
          spec={selectedNode ? specs[selectedNode.data.type]?.spec : null}
          onChange={updateNodeParam}
          labels={{
            title: t('inspector'),
            selectNode: t('selectNode'),
            params: t('params'),
            nonideal: t('nonideal')
          }}
        />
        <Outputs
          result={result}
          expanded={expanded}
          carrierAutoHz={lastLaserCenterHz ?? undefined}
          outputConfig={outputConfig}
          outputPorts={outputPorts}
          onOutputConfigChange={(patch) => setOutputConfig((cfg) => ({ ...cfg, ...patch }))}
          labels={{
            title: t('outputs'),
            jobResult: t('jobResult'),
            expandedGraph: t('expandedGraph'),
            noResult: t('noResult'),
            notExpanded: t('notExpanded'),
            outputsConfig: t('outputsConfig'),
            osaMode: t('osaMode'),
            esaMode: t('esaMode'),
            auto: t('auto'),
            manual: t('manual'),
            spectrum: t('spectrum'),
            timePreview: t('timePreview'),
            includePower: t('includePower'),
            noOutputs: t('noOutputs'),
            osa: t('osa'),
            esa: t('esa'),
            time: t('time'),
            meta: t('meta'),
            range: t('range'),
            peak: t('peak'),
            markers: t('markers'),
            markerInput: t('markerInput'),
            addMarker: t('addMarker'),
            clearMarkers: t('clearMarkers'),
            removeMarker: t('removeMarker'),
            unit: t('unit'),
            unitHz: t('unitHz'),
            unitNm: t('unitNm'),
            unitOffset: t('unitOffset'),
            offset: t('offset'),
            carrierCenter: t('carrierCenter'),
            carrierAuto: t('carrierAuto'),
            carrierManual: t('carrierManual'),
            carrierValue: t('carrierValue'),
            wavelengthNm: t('wavelengthNm'),
            frequencyHz: t('frequencyHz'),
            saveImage: t('saveImage'),
            saveCsv: t('saveCsv'),
            exportSettings: t('exportSettings'),
            exportScale: t('exportScale'),
            exportFormat: t('exportFormat'),
            exportBackground: t('exportBackground'),
            exportPng: t('exportPng'),
            exportSvg: t('exportSvg'),
            exportBgSolid: t('exportBgSolid'),
            exportBgTransparent: t('exportBgTransparent'),
            osaPlotSettings: t('osaPlotSettings'),
            esaPlotSettings: t('esaPlotSettings'),
            showPeak: t('showPeak'),
            showMinMax: t('showMinMax'),
            viewRange: t('viewRange'),
            rangeAuto: t('rangeAuto'),
            rangeCustom: t('rangeCustom'),
            rangeMin: t('rangeMin'),
            rangeMax: t('rangeMax')
          }}
        />
      </div>
    </div>
  )
}
