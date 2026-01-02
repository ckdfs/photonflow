import React, { useMemo } from 'react'

interface SpectrumPlotProps {
  title: string
  data: { freq: number[]; power_db: number[] } | null
}

export default function SpectrumPlot({ title, data }: SpectrumPlotProps) {
  const width = 260
  const height = 140
  const padding = 24

  const { points, minY, maxY } = useMemo(() => {
    if (!data || data.freq.length === 0) return { points: '', minY: 0, maxY: 0 }
    const minX = Math.min(...data.freq)
    const maxX = Math.max(...data.freq)
    const minY = Math.min(...data.power_db)
    const maxY = Math.max(...data.power_db)
    const rangeX = maxX - minX || 1
    const rangeY = maxY - minY || 1
    const pts = data.freq.map((f, i) => {
      const x = padding + ((f - minX) / rangeX) * (width - padding * 2)
      const y = padding + (1 - (data.power_db[i] - minY) / rangeY) * (height - padding * 2)
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    return { points: pts.join(' '), minY, maxY }
  }, [data])

  return (
    <div className="plot-card">
      <div className="plot-title">{title}</div>
      {data && data.freq.length ? (
        <svg viewBox={`0 0 ${width} ${height}`} className="plot-svg">
          <rect x="0" y="0" width={width} height={height} fill="#fdf8ef" rx="10" />
          <polyline points={points} fill="none" stroke="#b4512a" strokeWidth="1.4" />
          <text x={padding} y={padding - 8} className="plot-axis">{maxY.toFixed(1)} dB</text>
          <text x={padding} y={height - 6} className="plot-axis">{minY.toFixed(1)} dB</text>
        </svg>
      ) : (
        <div className="plot-empty">No data</div>
      )}
    </div>
  )
}
