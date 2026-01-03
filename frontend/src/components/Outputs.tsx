import React from 'react'
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
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">{labels.title}</div>
      </div>
      <div className="panel-body outputs">
        {!hasProbes ? (
          <div className="hint">{labels.noProbes}</div>
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
                  exportSettings: probe.kind === 'osa' ? labels.osaPlotSettings : labels.esaPlotSettings,
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
        <div>
          <div className="section-title">{labels.meta}</div>
          {meta ? (
            <div className="meta-grid">
              <div>fs: {meta.fs}</div>
              <div>duration: {meta.duration_s}</div>
              <div>samples: {meta.n_samples ?? '-'}</div>
              <div>device: {meta.device}</div>
            </div>
          ) : (
            <div className="hint">{labels.noResult}</div>
          )}
        </div>
        <div>
          <div className="section-title">{labels.jobResult}</div>
          <pre>{result ? JSON.stringify(result, null, 2) : labels.noResult}</pre>
        </div>
        <div>
          <div className="section-title">{labels.expandedGraph}</div>
          <pre>{expanded ? JSON.stringify(expanded, null, 2) : labels.notExpanded}</pre>
        </div>
      </div>
    </div>
  )
}
