import React, { useMemo, useState } from 'react'

interface BlockLibraryProps {
  types: string[]
  onAdd: (type: string) => void
  title: string
  labelForType: (type: string) => string
  searchPlaceholder: string
  noMatchText: string
}

export default function BlockLibrary({
  types,
  onAdd,
  title,
  labelForType,
  searchPlaceholder,
  noMatchText
}: BlockLibraryProps) {
  const [query, setQuery] = useState('')
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return types
    return types.filter((type) => {
      const label = labelForType(type).toLowerCase()
      return label.includes(q) || type.toLowerCase().includes(q)
    })
  }, [labelForType, query, types])

  return (
    <div className="panel">
      <div className="panel-title">{title}</div>
      <div className="panel-body">
        <input
          className="field-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={searchPlaceholder}
        />
        {filtered.length === 0 ? (
          <div className="hint">{noMatchText}</div>
        ) : (
          filtered.map((type) => (
            <button key={type} className="block-button" onClick={() => onAdd(type)}>
              {labelForType(type)}
            </button>
          ))
        )}
      </div>
    </div>
  )
}
