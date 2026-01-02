import React from 'react'

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
  onChange: (section: string, key: string, value: any) => void
) => {
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

  return (
    <div className="panel">
      <div className="panel-title">{labels.title}</div>
      <div className="panel-body">
        <div className="section-title">{labels.params}</div>
        {Object.entries(params).map(([name, entry]) =>
          renderField('params', name, entry, node.data.params?.[name], onChange)
        )}
        <div className="section-title">{labels.nonideal}</div>
        {Object.entries(nonideal).map(([name, entry]) =>
          renderField('nonideal', name, entry, node.data.nonideal?.[name], onChange)
        )}
      </div>
    </div>
  )
}
