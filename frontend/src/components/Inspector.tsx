import React, { useEffect, useState } from 'react'

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
      <label key={name} className="field">
        <span>{name}</span>
        {custom}
      </label>
    )
  }
  const type = entry?.type || 'float'
  if (type === 'bool') {
    return (
      <label key={name} className="field">
        <span>{name}</span>
        <input
          type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => onChange(section, name, e.target.checked)}
        />
      </label>
    )
  }
  if (type === 'enum') {
    return (
      <label key={name} className="field">
        <span>{name}</span>
        <select value={value ?? entry.default} onChange={(e) => onChange(section, name, e.target.value)}>
          {entry.options?.map((opt: string) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </label>
    )
  }
  return (
    <label key={name} className="field">
      <span>{name}</span>
      <input
        type="number"
        value={value ?? entry.default ?? ''}
        onChange={(e) => onChange(section, name, Number(e.target.value))}
      />
    </label>
  )
}

export default function Inspector({ node, spec, onChange, labels }: InspectorProps) {
  if (!node || !spec) {
    return (
      <div className="panel">
        <div className="panel-title">{labels.title}</div>
        <div className="panel-body">{labels.selectNode}</div>
      </div>
    )
  }

  const params = spec.params || {}
  const nonideal = spec.nonideal || {}
  const [laserFreqMode, setLaserFreqMode] = useState<'hz' | 'nm'>('hz')
  const speedOfLight = 299792458

  useEffect(() => {
    setLaserFreqMode('hz')
  }, [node?.id])

  const toNm = (hz: number) => (hz > 0 ? (speedOfLight / hz) * 1e9 : 0)
  const toHz = (nm: number) => (nm > 0 ? speedOfLight / (nm * 1e-9) : 0)

  return (
    <div className="panel">
      <div className="panel-title">{labels.title}</div>
      <div className="panel-body">
        <div className="section-title">{labels.params}</div>
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
              <div className="field-inline">
                <input
                  type="number"
                  value={Number.isFinite(value) ? value : 0}
                  onChange={(e) => {
                    const num = Number(e.target.value)
                    if (!Number.isFinite(num)) return
                    const hz = laserFreqMode === 'nm' ? toHz(num) : num
                    onChange('params', name, hz)
                  }}
                />
                <select
                  value={laserFreqMode}
                  onChange={(e) => setLaserFreqMode(e.target.value as 'hz' | 'nm')}
                >
                  <option value="hz">Hz</option>
                  <option value="nm">nm</option>
                </select>
              </div>
            )
          }
          return renderField('params', name, entry, node.data.params?.[name], onChange)
        })}
        <div className="section-title">{labels.nonideal}</div>
        {Object.entries(nonideal).map(([name, entry]) =>
          renderField('nonideal', name, entry, node.data.nonideal?.[name], onChange)
        )}
      </div>
    </div>
  )
}
