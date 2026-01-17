import React, { useMemo } from 'react'
import { Paper, Typography, Box } from '@mui/material'

interface TimePlotProps {
  title: string
  data: { t: number[]; real: number[]; imag?: number[] } | null
}

export default function TimePlot({ title, data }: TimePlotProps) {
  const width = 260
  const height = 140
  const padding = 24

  const { lineReal, lineImag } = useMemo(() => {
    if (!data || data.t.length === 0) return { lineReal: '', lineImag: '' }
    const minX = Math.min(...data.t)
    const maxX = Math.max(...data.t)
    const allY = data.imag ? data.real.concat(data.imag) : data.real
    const minY = Math.min(...allY)
    const maxY = Math.max(...allY)
    const rangeX = maxX - minX || 1
    const rangeY = maxY - minY || 1

    const toPoint = (x: number, y: number) => {
      const px = padding + ((x - minX) / rangeX) * (width - padding * 2)
      const py = padding + (1 - (y - minY) / rangeY) * (height - padding * 2)
      return `${px.toFixed(2)},${py.toFixed(2)}`
    }

    const realLine = data.t.map((x, i) => toPoint(x, data.real[i])).join(' ')
    const imagLine = data.imag ? data.t.map((x, i) => toPoint(x, data.imag![i])).join(' ') : ''
    return { lineReal: realLine, lineImag: imagLine }
  }, [data])

  return (
    <Paper variant="outlined" sx={{ p: 1.5, minWidth: 280 }}>
      <Typography variant="subtitle2" gutterBottom align="center">{title}</Typography>
      {data && data.t.length ? (
        <Box sx={{ display: 'flex', justifyContent: 'center' }}>
          <svg viewBox={`0 0 ${width} ${height}`} width={width} height={height} style={{ overflow: 'visible' }}>
            <rect x="0" y="0" width={width} height={height} fill="none" stroke="#e0e0e0" rx="4" />
            <polyline points={lineReal} fill="none" stroke="#2c6fb8" strokeWidth="1.4" />
            {lineImag ? <polyline points={lineImag} fill="none" stroke="#b4512a" strokeWidth="1.1" strokeDasharray="4 3" /> : null}
          </svg>
        </Box>
      ) : (
        <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 4 }}>
          No data
        </Typography>
      )}
    </Paper>
  )
}
