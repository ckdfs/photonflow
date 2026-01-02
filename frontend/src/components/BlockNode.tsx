import { Handle, NodeProps, Position } from 'reactflow'

const portStyle = (portType: string) => {
  if (portType === 'optical') return 'port port-optical'
  if (portType === 'electrical') return 'port port-electrical'
  return 'port port-control'
}

const isOutputPort = (name: string) => name.includes('out')

export default function BlockNode({ data }: NodeProps) {
  const ports: Record<string, string> = data.ports || {}
  const entries = Object.entries(ports)
  const inputs = entries.filter(([name]) => !isOutputPort(name))
  const outputs = entries.filter(([name]) => isOutputPort(name))

  return (
    <div className="block-node">
      <div className="block-title">{data.label}</div>
      {data.subtitle ? <div className="block-subtitle">{data.subtitle}</div> : null}
      <div className="block-ports">
        <div className="block-col">
          {inputs.map(([name, type], idx) => (
            <div key={name} className="port-row">
              <Handle
                type="target"
                position={Position.Left}
                id={name}
                className={portStyle(type)}
              />
              <span>{name}</span>
            </div>
          ))}
        </div>
        <div className="block-col">
          {outputs.map(([name, type], idx) => (
            <div key={name} className="port-row">
              <span>{name}</span>
              <Handle
                type="source"
                position={Position.Right}
                id={name}
                className={portStyle(type)}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
