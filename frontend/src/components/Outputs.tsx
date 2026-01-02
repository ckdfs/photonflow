import React from 'react'
import SpectrumPlot from './SpectrumPlot'
import TimePlot from './TimePlot'

interface OutputsProps {
  result: any
  expanded: any
  labels: {
    title: string
    jobResult: string
    expandedGraph: string
    noResult: string
    notExpanded: string
    osa: string
    esa: string
    time: string
    meta: string
  }
}

export default function Outputs({ result, expanded, labels }: OutputsProps) {
  const osa = result?.osa || null
  const esa = result?.esa || null
  const meta = result?.meta || null
  const esaIsTime = esa?.kind === 'time'
  return (
    <div className="panel">
      <div className="panel-title">{labels.title}</div>
      <div className="panel-body outputs">
        <SpectrumPlot title={labels.osa} data={osa?.kind === 'osa' ? osa : null} />
        {esaIsTime ? (
          <TimePlot title={labels.time} data={esa} />
        ) : (
          <SpectrumPlot title={labels.esa} data={esa?.kind === 'esa' ? esa : null} />
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
