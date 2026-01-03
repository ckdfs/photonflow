import React, { useMemo, useState } from 'react'

interface BlockLibraryProps {
  types: string[]
  onAdd: (type: string) => void
  title: string
  labelForType: (type: string) => string
  groups?: { id: string; title: string; types: string[] }[]
  typeStyles?: Record<string, string>
  searchPlaceholder: string
  noMatchText: string
}

export default function BlockLibrary({
  types,
  onAdd,
  title,
  labelForType,
  groups,
  typeStyles,
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
  const filteredSet = useMemo(() => new Set(filtered), [filtered])
  const grouped = useMemo(() => {
    if (!groups) return null
    return groups
      .map((group) => ({
        ...group,
        types: group.types.filter((type) => filteredSet.has(type))
      }))
      .filter((group) => group.types.length > 0)
  }, [filteredSet, groups])

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
        ) : grouped ? (
          grouped.map((group) => (
            <div key={group.id} className="block-group">
              <div className="block-group-title">{group.title}</div>
              {group.types.map((type) => (
                <button
                  key={type}
                  className={`block-button ${typeStyles?.[type] ?? ''}`.trim()}
                  onClick={() => onAdd(type)}
                >
                  {labelForType(type)}
                </button>
              ))}
            </div>
          ))
        ) : (
          filtered.map((type) => (
            <button key={type} className={`block-button ${typeStyles?.[type] ?? ''}`.trim()} onClick={() => onAdd(type)}>
              {labelForType(type)}
            </button>
          ))
        )}
      </div>
    </div>
  )
}
