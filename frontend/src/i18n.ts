export type Lang = 'zh' | 'en'

type Entry = { en: string; zh: string }

type Dict = Record<string, Entry>

const dict: Dict = {
  blocks: { en: 'Blocks', zh: '组件' },
  inspector: { en: 'Inspector', zh: '参数面板' },
  outputs: { en: 'Outputs', zh: '输出' },
  validate: { en: 'Validate', zh: '校验' },
  expand: { en: 'Expand', zh: '展开' },
  run: { en: 'Run', zh: '运行' },
  showExpanded: { en: 'Show Expanded', zh: '显示展开' },
  collapse: { en: 'Collapse', zh: '折叠' },
  delete: { en: 'Delete', zh: '删除' },
  settings: { en: 'Settings', zh: '设置' },
  language: { en: 'Language', zh: '语言' },
  selectNode: { en: 'Select a node.', zh: '请选择一个节点。' },
  params: { en: 'params', zh: '参数' },
  nonideal: { en: 'nonideal', zh: '非理想' },
  jobResult: { en: 'Job Result', zh: '任务结果' },
  expandedGraph: { en: 'Expanded Graph', zh: '展开图' },
  noResult: { en: 'No result yet.', zh: '暂无结果。' },
  notExpanded: { en: 'Not expanded.', zh: '尚未展开。' },
  status: { en: 'Status', zh: '状态' },
  osa: { en: 'OSA', zh: '光谱' },
  esa: { en: 'ESA', zh: '电谱' },
  time: { en: 'Time', zh: '时域' },
  examples: { en: 'Examples', zh: '示例' },
  examplePm: { en: 'PM Test', zh: 'PM 基本测试' },
  exampleMzm: { en: 'MZM Test', zh: 'MZM 基本测试' },
  exampleDpmzm: { en: 'DPMZM Test', zh: 'DPMZM 基本测试' },
  searchBlocks: { en: 'Search blocks', zh: '搜索组件' },
  noMatch: { en: 'No matching blocks.', zh: '没有匹配的组件。' },
  noOutputs: { en: 'No output ports.', zh: '没有可用的输出端口。' },
  simSettings: { en: 'Simulation', zh: '仿真设置' },
  backend: { en: 'Backend', zh: '后端' },
  device: { en: 'Device', zh: '设备' },
  fsMode: { en: 'Sample Rate', zh: '采样率' },
  fsAuto: { en: 'Auto', zh: '自动' },
  fsCustom: { en: 'Custom', zh: '自定义' },
  fsValue: { en: 'Fs (Hz)', zh: 'Fs (Hz)' },
  oversample: { en: 'Oversample', zh: '过采样' },
  seed: { en: 'Seed', zh: '随机种子' },
  window: { en: 'Window', zh: '窗函数' },
  duration: { en: 'Duration (s)', zh: '时长 (s)' },
  nSamples: { en: 'Samples', zh: '采样点数' },
  outputsConfig: { en: 'Outputs', zh: '输出设置' },
  osaMode: { en: 'OSA Source', zh: 'OSA 来源' },
  esaMode: { en: 'ESA Mode', zh: 'ESA 模式' },
  auto: { en: 'Auto', zh: '自动' },
  manual: { en: 'Manual', zh: '手动' },
  spectrum: { en: 'Spectrum', zh: '频谱' },
  timePreview: { en: 'Time Preview', zh: '时域预览' },
  includePower: { en: 'Include Power', zh: '包含线性功率' },
  graphStats: { en: 'Graph', zh: '图统计' },
  nodes: { en: 'Nodes', zh: '节点' },
  edges: { en: 'Edges', zh: '连线' },
  meta: { en: 'Meta', zh: '元信息' }
}

export function buildLabels(lang: Lang) {
  const t = (key: keyof typeof dict) => {
    const entry = dict[key]
    if (!entry) return key
    return lang === 'zh' ? entry.zh : entry.en
  }
  return { t }
}

const blockDict: Dict = {
  Laser: { en: 'Laser', zh: '激光器' },
  RFSource: { en: 'RF Source', zh: '射频源' },
  DCSource: { en: 'DC Source', zh: '直流源' },
  PM: { en: 'Phase Modulator', zh: '相位调制器' },
  MZM: { en: 'MZM', zh: '马赫-曾德尔调制器' },
  DPMZM: { en: 'DPMZM', zh: '双并行调制器' },
  MZMComposite: { en: 'MZM Composite', zh: 'MZM 复合器件' },
  DPMZMComposite: { en: 'DPMZM Composite', zh: 'DPMZM 复合器件' },
  Coupler: { en: 'Coupler', zh: '耦合器' },
  PhaseShifter: { en: 'Phase Shifter', zh: '相移器' },
  Attenuator: { en: 'Attenuator', zh: '光衰减器' },
  PD: { en: 'Photodiode', zh: '光电探测器' },
  ElecSplitter: { en: 'Electrical Splitter', zh: '电分路器' },
  ElecGain: { en: 'Electrical Gain', zh: '电增益' }
}

export function blockLabel(type: string, lang: Lang) {
  const entry = blockDict[type]
  if (!entry) return type
  return lang === 'zh' ? entry.zh : entry.en
}
