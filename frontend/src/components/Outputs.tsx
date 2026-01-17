import React from 'react'
import { Paper, Typography, Box, Stack } from '@mui/material'
import SpectrumPlot from './SpectrumPlot'
import TimePlot from './TimePlot'

interface OutputsProps {
  result: any
  expanded: any
  carrierAutoHz?: number
  probeOutputs: { id: string; kind: 'osa' | 'esa' | 'time'; isOptical: boolean; title: string }[]
  labels: {
    title: string
    jobResult: string
    expandedGraph: string
    noResult: string
    notExpanded: string
    noProbes: string
    osa: string
    esa: string
    time: string
    meta: string
    range: string
    peak: string
    markers: string
    markerInput: string
    addMarker: string
    clearMarkers: string
    removeMarker: string
    unit: string
    unitHz: string
    unitNm: string
    unitOffset: string
    offset: string
    carrierCenter: string
    carrierAuto: string
    carrierManual: string
    carrierValue: string
    wavelengthNm: string
    frequencyHz: string
    saveImage: string
    saveCsv: string
    exportSettings: string
    exportScale: string
    exportFormat: string
    exportBackground: string
    exportPng: string
    exportSvg: string
    exportBgSolid: string
    exportBgTransparent: string
    osaPlotSettings: string
    esaPlotSettings: string
    showPeak: string
    showMinMax: string
    viewRange: string
    rangeAuto: string
    rangeCustom: string
    rangeMin: string
    rangeMax: string
  }
}

export default function Outputs({
  result,
  expanded,
  labels,
  carrierAutoHz,
  probeOutputs
}: OutputsProps) {
  const extra = Array.isArray(result?.extra) ? result.extra : []
  const meta = result?.meta || null
  const hasProbes = probeOutputs.length > 0

  return (
    <Paper variant="outlined" sx={{ p: 1.5 }}>
      <Typography variant="h6" gutterBottom>{labels.title}</Typography>
      <Stack spacing={2}>
        {!hasProbes ? (
          <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 2 }}>
            {labels.noProbes}
          </Typography>
        ) : (
          probeOutputs.map((probe, index) => {
            const item = extra[index] || null
            const title =
              probe.kind === 'osa'
                ? `${labels.osa} · ${probe.title}`
                : probe.kind === 'esa'
                  ? `${labels.esa} · ${probe.title}`
                  : `${labels.time} · ${probe.title}`
            if (probe.kind === 'time') {
              return <TimePlot key={probe.id} title={title} data={item?.kind === 'time' ? item : null} />
            }
            return (
              <SpectrumPlot
                key={probe.id}
                title={title}
                data={item?.kind === probe.kind ? item : null}
                isOptical={probe.isOptical}
                carrierAutoHz={carrierAutoHz}
                labels={{
                  range: labels.range,
                  peak: labels.peak,
                  markers: labels.markers,
                  markerInput: labels.markerInput,
                  addMarker: labels.addMarker,
                  clearMarkers: labels.clearMarkers,
                  removeMarker: labels.removeMarker,
                  unit: labels.unit,
                  unitHz: labels.unitHz,
                  unitNm: labels.unitNm,
                  unitOffset: labels.unitOffset,
                  offset: labels.offset,
                  carrierCenter: labels.carrierCenter,
                  carrierAuto: labels.carrierAuto,
                  carrierManual: labels.carrierManual,
                  carrierValue: labels.carrierValue,
                  wavelengthNm: labels.wavelengthNm,
                  frequencyHz: labels.frequencyHz,
                  saveImage: labels.saveImage,
                  saveCsv: labels.saveCsv,
                  exportSettings: probe.kind === 'osa' ? labels.exportSettings : labels.exportSettings,
                  osaPlotSettings: labels.osaPlotSettings,
                  esaPlotSettings: labels.esaPlotSettings,
                  exportScale: labels.exportScale,
                  exportFormat: labels.exportFormat,
                  exportBackground: labels.exportBackground,
                  exportPng: labels.exportPng,
                  exportSvg: labels.exportSvg,
                  exportBgSolid: labels.exportBgSolid,
                  exportBgTransparent: labels.exportBgTransparent,
                  showPeak: labels.showPeak,
                  showMinMax: labels.showMinMax,
                  viewRange: labels.viewRange,
                  rangeAuto: labels.rangeAuto,
                  rangeCustom: labels.rangeCustom,
                  rangeMin: labels.rangeMin,
                  rangeMax: labels.rangeMax
                }}
              />
            )
          })
        )}

        <Box>
          <Typography variant="subtitle2" color="primary" gutterBottom>{labels.meta}</Typography>
          {meta ? (
            <Paper variant="outlined" sx={{ p: 1, bgcolor: 'action.hover' }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, fontSize: '0.875rem' }}>
                <div>fs: {meta.fs}</div>
                <div>duration: {meta.duration_s}</div>
                <div>samples: {meta.n_samples ?? '-'}</div>
                <div>device: {meta.device}</div>
              </Box>
            </Paper>
          ) : (
            <Typography variant="body2" color="text.secondary">{labels.noResult}</Typography>
          )}
        </Box>

        <Box>
          <Typography variant="subtitle2" color="primary" gutterBottom>{labels.jobResult}</Typography>
          <Paper variant="outlined" sx={{ p: 1, bgcolor: 'action.hover', overflow: 'auto', maxHeight: 200 }}>
            <pre style={{ margin: 0, fontSize: '0.75rem', fontFamily: 'monospace' }}>
              {result ? JSON.stringify(result, null, 2) : labels.noResult}
            </pre>
          </Paper>
        </Box>

        <Box>
          <Typography variant="subtitle2" color="primary" gutterBottom>{labels.expandedGraph}</Typography>
          <Paper variant="outlined" sx={{ p: 1, bgcolor: 'action.hover', overflow: 'auto', maxHeight: 200 }}>
            <pre style={{ margin: 0, fontSize: '0.75rem', fontFamily: 'monospace' }}>
              {expanded ? JSON.stringify(expanded, null, 2) : labels.notExpanded}
            </pre>
          </Paper>
        </Box>
      </Stack>
    </Paper>
  )
}
