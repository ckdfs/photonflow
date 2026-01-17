import React, { useMemo, useEffect, useRef, useCallback } from 'react'
import ReactFlow, { Background, Controls, Node, Edge, ReactFlowProvider, Connection } from 'reactflow'
import { Box, Paper, Stack, Button, Slider, Typography, IconButton } from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import OpenInFullIcon from '@mui/icons-material/OpenInFull'
import DeleteIcon from '@mui/icons-material/Delete'
import ClearAllIcon from '@mui/icons-material/ClearAll'
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh'

import BlockLibrary from '../components/BlockLibrary'
import Inspector from '../components/Inspector'
import BlockNode from '../components/BlockNode'

const nodeTypes = { block: BlockNode }

interface EditorPageProps {
    nodes: Node[]
    edges: Edge[]
    setNodes: React.Dispatch<React.SetStateAction<Node[]>>
    setEdges: React.Dispatch<React.SetStateAction<Edge[]>>
    selectedId: string | null
    setSelectedId: (id: string | null) => void
    selectedEdgeId: string | null
    setSelectedEdgeId: (id: string | null) => void
    expanded: any
    showExpanded: boolean
    view: { flowNodes: Node[]; flowEdges: Edge[] }
    onNodesChange: (changes: any) => void
    onEdgesChange: (changes: any) => void
    onConnect: (connection: Connection) => void
    isValidConnection: (connection: Connection) => boolean
    addNode: (type: string) => void
    deleteSelected: () => void
    clearGraph: () => void
    autoLayout: () => void
    runValidate: () => void
    runExpand: () => void
    runJob: () => void
    layoutGap: number
    setLayoutGap: (gap: number) => void
    specs: any
    selectedNode: Node | null
    updateNodeParam: (section: string, key: string, value: any) => void
    t: (key: string) => string
    msg: (en: string, zh: string) => string
    status: string
    labels: {
        title: string
        selectNode: string
        params: string
        nonideal: string
        [key: string]: string
    }
    loadExample: (kind: 'pm' | 'mzm' | 'dpmzm') => void
    labelForType: (type: string) => string
}

export default function EditorPage({
    nodes,
    edges,
    selectedId,
    setSelectedId,
    selectedEdgeId,
    setSelectedEdgeId,
    expanded,
    showExpanded,
    view,
    onNodesChange,
    onEdgesChange,
    onConnect,
    isValidConnection,
    addNode,
    deleteSelected,
    clearGraph,
    autoLayout,
    runValidate,
    runExpand,
    runJob,
    loadExample,
    layoutGap,
    setLayoutGap,
    specs,
    selectedNode,
    updateNodeParam,
    t,
    msg,
    status,
    labels,
    labelForType
}: EditorPageProps) {

    // Force resize on mount or visibility change
    // Note: Parent container handles the actual sizing

    // Block grouping logic
    const blockGroups = useMemo(() => {
        const allTypes = Object.keys(specs)
        const typeSet = new Set(allTypes)
        const pick = (list: string[]) => list.filter((type) => typeSet.has(type))
        const groups = [
            { id: 'measurement', title: t('blocksMeasurement') || 'Measurement', types: pick(['OSAProbe', 'ESAProbe', 'ScopeProbe']) },
            {
                id: 'optical', title: t('blocksOptical') || 'Optical', types: pick([
                    'Laser',
                    'Coupler',
                    'PhaseShifter',
                    'Attenuator',
                    'OpticalFiber',
                    'OpticalFilter',
                    'PolarizationRotator',
                    'PolarizationPDL',
                    'PolarizationWaveplate',
                    'PolarizationController'
                ])
            },
            { id: 'eo', title: t('blocksEO') || 'Electro-Optic', types: pick(['PM', 'MZMComposite', 'DPMZMComposite']) },
            { id: 'oe', title: t('blocksOE') || 'Opto-Electric', types: pick(['PD']) },
            { id: 'electrical', title: t('blocksElectrical') || 'Electrical', types: pick(['RFSource', 'DCSource', 'ElecSplitter', 'ElecGain']) }
        ]
        const used = new Set(groups.flatMap((group) => group.types))
        const other = allTypes.filter((type) => !used.has(type))
        if (other.length) {
            groups.push({ id: 'other', title: t('blocksOther') || 'Other', types: other })
        }
        return groups.filter((group) => group.types.length > 0)
    }, [specs, t])

    const typeStyles = useMemo(() => ({
        OSAProbe: 'block-button--measure',
        ESAProbe: 'block-button--measure',
        ScopeProbe: 'block-button--measure'
    }), [])

    const getDescription = useCallback((type: string) => {
        const spec = specs[type]
        return spec?.doc || spec?.description || spec?.info || ''
    }, [specs])

    return (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '260px 1fr 320px' }, gap: 1.5, height: '100%', overflow: 'hidden' }}>

            {/* Left Column: Library */}
            <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto' }}>
                <Paper variant="outlined" sx={{ p: 1.5, flexShrink: 0, mb: 1.5 }}>
                    <Typography variant="h6" gutterBottom>{t('examples')}</Typography>
                    <Stack spacing={1}>
                        <Button variant="outlined" onClick={() => loadExample('pm')}>{t('examplePm')}</Button>
                        <Button variant="outlined" onClick={() => loadExample('mzm')}>{t('exampleMzm')}</Button>
                        <Button variant="outlined" onClick={() => loadExample('dpmzm')}>{t('exampleDpmzm')}</Button>
                    </Stack>
                </Paper>
                <BlockLibrary
                    types={Object.keys(specs)}
                    onAdd={addNode}
                    title={t('library')}
                    labelForType={labelForType}
                    searchPlaceholder={t('searchBlocks')}
                    noMatchText={t('noBlocksMatch')}
                    groups={blockGroups}
                    typeStyles={typeStyles}
                    getDescription={getDescription}
                />
            </Box>

            {/* Center Column: Canvas */}
            <Paper variant="outlined" sx={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', position: 'relative' }}>
                <Box sx={{ flex: 1, position: 'relative', height: '100%' }}>
                    <ReactFlowProvider>
                        <ReactFlow
                            nodes={view.flowNodes}
                            edges={view.flowEdges}
                            nodeTypes={nodeTypes}
                            onNodesChange={onNodesChange}
                            onEdgesChange={onEdgesChange}
                            onConnect={onConnect}
                            isValidConnection={isValidConnection}
                            onNodeClick={(_, node) => {
                                console.log('Node clicked:', node.id)
                                setSelectedId(node.id)
                                setSelectedEdgeId(null)
                            }}
                            onEdgeClick={(_, edge) => {
                                console.log('Edge clicked:', edge.id)
                                setSelectedEdgeId(edge.id)
                                setSelectedId(null)
                            }}
                            onPaneClick={() => {
                                if (!showExpanded) {
                                    setSelectedId(null)
                                    setSelectedEdgeId(null)
                                }
                            }}
                            fitView
                            minZoom={0.1}
                        >
                            <Controls position="bottom-right" />
                            <Background />
                        </ReactFlow>
                    </ReactFlowProvider>

                    {/* Toolbar */}
                    <Paper
                        elevation={3}
                        sx={{
                            position: 'absolute',
                            bottom: 16,
                            left: 16,
                            zIndex: 10,
                            p: 1,
                            display: 'flex',
                            gap: 1,
                            alignItems: 'center',
                            flexWrap: 'wrap'
                        }}
                    >
                        <Button size="small" variant="outlined" startIcon={<AutoFixHighIcon />} onClick={autoLayout} disabled={showExpanded || nodes.length === 0 || edges.length === 0}>
                            {msg('Auto layout', '自动排布')}
                        </Button>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, border: '1px solid #e0e0e0', borderRadius: 1, px: 1, height: 32 }}>
                            <Typography variant="caption">{msg('Spacing', '间距')}</Typography>
                            <Slider
                                size="small"
                                min={0}
                                max={200}
                                step={10}
                                value={layoutGap}
                                onChange={(_, v) => setLayoutGap(v as number)}
                                disabled={nodes.length === 0 || edges.length === 0}
                                sx={{ width: 100 }}
                            />
                            <Typography variant="caption" sx={{ minWidth: 24, textAlign: 'right' }}>{layoutGap}</Typography>
                        </Box>
                        <Button size="small" variant="contained" color="primary" startIcon={<CheckCircleIcon />} onClick={runValidate}>{t('validate')}</Button>
                        <Button size="small" variant="contained" color="secondary" startIcon={<OpenInFullIcon sx={{ transform: showExpanded ? 'rotate(180deg)' : 'none' }} />} onClick={runExpand}>
                            {showExpanded ? msg('Collapse', '收起') : (expanded ? msg('Expand', '展开') : t('expand'))}
                        </Button>
                        <Button size="small" variant="contained" color="success" startIcon={<PlayArrowIcon />} onClick={runJob}>{t('run')}</Button>
                        <IconButton size="small" color="error" onClick={deleteSelected} disabled={showExpanded} title={t('delete')}>
                            <DeleteIcon />
                        </IconButton>
                        <IconButton size="small" color="warning" onClick={clearGraph} disabled={showExpanded} title={t('clearGraph')}>
                            <ClearAllIcon />
                        </IconButton>
                    </Paper>

                    {/* Stats & Status */}
                    <Box sx={{ position: 'absolute', top: 12, left: 12, zIndex: 10, display: 'flex', gap: 1 }}>
                        <Paper variant="outlined" sx={{ px: 1, py: 0.5, bgcolor: 'background.paper', display: 'flex', alignItems: 'center' }}>
                            <Typography variant="caption">
                                {t('nodes')}: {nodes.length} · {t('edges')}: {edges.length}
                            </Typography>
                        </Paper>
                        <Paper variant="outlined" sx={{ px: 1, py: 0.5, bgcolor: 'background.paper', maxWidth: 300, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', display: 'flex', alignItems: 'center' }}>
                            <Typography variant="caption">
                                {t('status')}: {status || '-'}
                            </Typography>
                        </Paper>
                    </Box>
                </Box>
            </Paper>

            {/* Right Column: Inspector */}
            <Stack spacing={1.5} sx={{ minHeight: 0, overflow: 'auto' }}>
                <Inspector
                    node={selectedNode}
                    spec={selectedNode ? specs[selectedNode.data.type]?.spec : null}
                    onChange={updateNodeParam}
                    labels={labels}
                />
            </Stack>
        </Box>
    )
}
