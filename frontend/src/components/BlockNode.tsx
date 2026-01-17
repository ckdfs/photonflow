import React from 'react'
import { Handle, NodeProps, Position } from 'reactflow'

const isOutputPort = (name: string) => name.includes('out')

export default function BlockNode({ data }: NodeProps) {
  const safeData = data || {}
  const ports: Record<string, string> = safeData.ports || {}
  const entries = Object.entries(ports)
  const inputs = entries.filter(([name]) => !isOutputPort(name))
  const outputs = entries.filter(([name]) => isOutputPort(name))

  const getPortColor = (type: string) => {
    if (type === 'optical') return '#2979ff' // Blue
    if (type === 'electrical') return '#ff9100' // Orange
    return '#bdbdbd' // Grey
  }

  return (
    <div
      style={{
        minWidth: 150,
        padding: 8,
        borderRadius: 8,
        backgroundColor: '#fff',
        border: '1px solid #e0e0e0',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        fontFamily: 'sans-serif',
        fontSize: '12px'
      }}
    >
      <div>
        <div style={{ textAlign: 'center', fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={safeData.label || ''}>
          {safeData.label || 'Unknown'}
        </div>
        {safeData.subtitle && (
          <div style={{ textAlign: 'center', color: '#666', fontSize: '10px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {safeData.subtitle}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
        {/* Inputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-start', minWidth: 20 }}>
          {inputs.map(([name, type]) => (
            <div key={name} style={{ position: 'relative', display: 'flex', alignItems: 'center', height: 24 }}>
              <Handle
                type="target"
                position={Position.Left}
                id={name}
                style={{
                  background: getPortColor(type),
                  width: 10,
                  height: 10,
                  left: -14,
                  border: '1px solid #fff'
                }}
              />
              <span style={{ fontSize: '11px', color: '#333' }}>{name}</span>
            </div>
          ))}
        </div>

        {/* Outputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-end', minWidth: 20 }}>
          {outputs.map(([name, type]) => (
            <div key={name} style={{ position: 'relative', display: 'flex', alignItems: 'center', height: 24 }}>
              <span style={{ fontSize: '11px', color: '#333' }}>{name}</span>
              <Handle
                type="source"
                position={Position.Right}
                id={name}
                style={{
                  background: getPortColor(type),
                  width: 10,
                  height: 10,
                  right: -14,
                  border: '1px solid #fff'
                }}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
