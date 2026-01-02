import React from 'react'

interface ExpandToggleProps {
  showExpanded: boolean
  onToggle: () => void
  labels: { showExpanded: string; collapse: string }
}

export default function ExpandToggle({ showExpanded, onToggle, labels }: ExpandToggleProps) {
  return (
    <button onClick={onToggle}>
      {showExpanded ? labels.collapse : labels.showExpanded}
    </button>
  )
}
