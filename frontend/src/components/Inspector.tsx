import React, { useEffect, useState } from 'react'
import { Paper, Typography, TextField, Select, MenuItem, Checkbox, FormControlLabel, FormControl, InputLabel, Box, Stack } from '@mui/material'

interface InspectorProps {
  node: any | null
  spec: any | null
  onChange: (section: string, key: string, value: any) => void
  labels: {
    title: string
    selectNode: string
    params: string
    nonideal: string
  }
}

const renderField = (
  section: string,
  name: string,
  entry: any,
  value: any,
  onChange: (section: string, key: string, value: any) => void,
  custom?: React.ReactNode
) => {
  if (custom) {
    return (
      <Box key={name} sx={{ mb: 1.5 }}>
        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>{name}</Typography>
        {custom}
      </Box>
    )
  }
  const type = entry?.type || 'float'
  if (type === 'bool') {
    return (
      <Box key={name} sx={{ mb: 1 }}>
        <FormControlLabel
          control={
            <Checkbox
              checked={Boolean(value)}
              onChange={(e) => onChange(section, name, e.target.checked)}
              size="small"
            />
          }
          label={<Typography variant="body2">{name}</Typography>}
        />
      </Box>
    )
  }
  if (type === 'enum') {
    return (
      <FormControl key={name} fullWidth size="small" sx={{ mb: 1.5 }}>
        <InputLabel>{name}</InputLabel>
        <Select
          value={value ?? entry.default}
          label={name}
          onChange={(e) => onChange(section, name, e.target.value)}
        >
          {entry.options?.map((opt: string) => (
            <MenuItem key={opt} value={opt}>{opt}</MenuItem>
          ))}
        </Select>
      </FormControl>
    )
  }
  return (
    <TextField
      key={name}
      label={name}
      type="number"
      size="small"
      fullWidth
      value={value ?? entry.default ?? ''}
      onChange={(e) => onChange(section, name, Number(e.target.value))}
      sx={{ mb: 1.5 }}
    />
  )
}

export default function Inspector({ node, spec, onChange, labels }: InspectorProps) {
  const [laserFreqMode, setLaserFreqMode] = useState<'hz' | 'nm'>('hz')
  const speedOfLight = 299792458

  useEffect(() => {
    setLaserFreqMode('hz')
  }, [node?.id])

  if (!node) {
    return (
      <Paper variant="outlined" sx={{ p: 1.5 }}>
        <Typography variant="h6" gutterBottom>{labels.title}</Typography>
        <Typography variant="body2" color="text.secondary">{labels.selectNode}</Typography>
      </Paper>
    )
  }

  if (!spec) {
    return (
      <Paper variant="outlined" sx={{ p: 1.5 }}>
        <Typography variant="h6" gutterBottom>{labels.title}</Typography>
        <Typography variant="body2" color="error">
          {labels.selectNode} (Unknown Type: {node.data?.type})
        </Typography>
      </Paper>
    )
  }

  const params = spec.params || {}
  const nonideal = spec.nonideal || {}

  const toNm = (hz: number) => (hz > 0 ? (speedOfLight / hz) * 1e9 : 0)
  const toHz = (nm: number) => (nm > 0 ? speedOfLight / (nm * 1e-9) : 0)

  return (
    <Paper variant="outlined" sx={{ p: 1.5 }}>
      <Typography variant="h6" gutterBottom>{labels.title}</Typography>
      <Stack spacing={1}>
        <Box>
          <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 1 }}>{labels.params}</Typography>
          {Object.entries(params).map(([name, entry]) => {
            if (node.data.type === 'Laser' && name === 'center_freq_hz') {
              const raw = Number(node.data.params?.[name] ?? entry.default ?? 0)
              const value = laserFreqMode === 'nm' ? toNm(raw) : raw
              return renderField(
                'params',
                name,
                entry,
                raw,
                onChange,
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <TextField
                    type="number"
                    size="small"
                    fullWidth
                    value={Number.isFinite(value) ? value : 0}
                    onChange={(e) => {
                      const num = Number(e.target.value)
                      if (!Number.isFinite(num)) return
                      const hz = laserFreqMode === 'nm' ? toHz(num) : num
                      onChange('params', name, hz)
                    }}
                  />
                  <Select
                    size="small"
                    value={laserFreqMode}
                    onChange={(e) => setLaserFreqMode(e.target.value as 'hz' | 'nm')}
                    sx={{ minWidth: 70 }}
                  >
                    <MenuItem value="hz">Hz</MenuItem>
                    <MenuItem value="nm">nm</MenuItem>
                  </Select>
                </Box>
              )
            }
            return renderField('params', name, entry, node.data.params?.[name], onChange)
          })}
        </Box>
        <Box>
          <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 1 }}>{labels.nonideal}</Typography>
          {Object.entries(nonideal).map(([name, entry]) =>
            renderField('nonideal', name, entry, node.data.nonideal?.[name], onChange)
          )}
        </Box>
      </Stack>
    </Paper>
  )
}
