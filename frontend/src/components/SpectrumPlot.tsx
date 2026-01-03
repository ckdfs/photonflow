import React, { useMemo, useEffect, useRef, useState } from 'react'

interface SpectrumPlotProps {
  title: string
  data: { freq: number[]; power_db: number[]; freq_rel?: number[]; center_freq_hz?: number } | null
  isOptical?: boolean
  carrierAutoHz?: number
  labels?: {
    range: string
    peak: string
    markers: string
    markerInput: string
    addMarker: string
    clearMarkers: string
    removeMarker: string
    unit: string
    unitHz: string
    unitNm: string
    unitOffset: string
    offset: string
    carrierCenter: string
    carrierAuto: string
    carrierManual: string
    carrierValue: string
    wavelengthNm: string
    frequencyHz: string
    saveImage: string
    saveCsv: string
    exportSettings: string
    exportScale: string
    exportFormat: string
    exportBackground: string
    exportPng: string
    exportSvg: string
    exportBgSolid: string
    exportBgTransparent: string
    showPeak: string
    showMinMax: string
    viewRange: string
    rangeAuto: string
    rangeCustom: string
    rangeMin: string
    rangeMax: string
  }
}

export default function SpectrumPlot({ title, data, labels, isOptical = false, carrierAutoHz }: SpectrumPlotProps) {
  const width = 260
  const height = 140
  const padding = 24
  const [markers, setMarkers] = useState<Array<{ freq: number; value: number; index: number }>>([])
  const [markerInput, setMarkerInput] = useState<string>('')
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [editingValue, setEditingValue] = useState<string>('')
  const [unitMode, setUnitMode] = useState<'freq' | 'wavelength' | 'offset'>(isOptical ? 'offset' : 'freq')
  const [exportScale, setExportScale] = useState<number>(4)
  const [exportFormat, setExportFormat] = useState<'png' | 'svg'>('png')
  const [exportBackground, setExportBackground] = useState<'solid' | 'transparent'>('solid')
  const [showExportSettings, setShowExportSettings] = useState(false)
  const [showPeak, setShowPeak] = useState(false)
  const [showMinMax, setShowMinMax] = useState(false)
  const [rangeMode, setRangeMode] = useState<'auto' | 'custom'>('auto')
  const [rangeMinHz, setRangeMinHz] = useState<number | null>(null)
  const [rangeMaxHz, setRangeMaxHz] = useState<number | null>(null)
  const [rangeMinInput, setRangeMinInput] = useState('')
  const [rangeMaxInput, setRangeMaxInput] = useState('')
  const [carrierMode, setCarrierMode] = useState<'auto' | 'manual'>('auto')
  const [manualCarrierInput, setManualCarrierInput] = useState('')
  const [manualCarrierHz, setManualCarrierHz] = useState<number | null>(null)
  const svgRef = useRef<SVGSVGElement | null>(null)
  const plotActionsRef = useRef<HTMLDivElement | null>(null)

  const peakCarrierHz = useMemo(() => {
    if (!data || data.freq.length === 0) return 0
    const peakIdx = data.power_db.reduce(
      (best, val, idx) => (val > data.power_db[best] ? idx : best),
      0
    )
    return data.freq[peakIdx]
  }, [data])

  const autoCarrierHz = useMemo(() => {
    if (!isOptical) return peakCarrierHz
    if (carrierAutoHz !== undefined && Number.isFinite(carrierAutoHz)) return carrierAutoHz
    return peakCarrierHz
  }, [carrierAutoHz, isOptical, peakCarrierHz])

  const carrierRefHz = useMemo(() => {
    if (!isOptical) return peakCarrierHz
    if (carrierMode === 'manual' && manualCarrierHz !== null) return manualCarrierHz
    return autoCarrierHz
  }, [autoCarrierHz, carrierMode, isOptical, manualCarrierHz, peakCarrierHz])

  const centerFreqHz = useMemo(() => {
    if (!data) return null
    return Number.isFinite(data.center_freq_hz) ? (data.center_freq_hz as number) : null
  }, [data])

  const hasFreqRel = useMemo(() => {
    if (!data?.freq_rel) return false
    return data.freq_rel.length === data.freq.length
  }, [data])

  const {
    points,
    minX,
    maxX,
    minY,
    maxY,
    peakX,
    peakY,
    peakVal,
    peakFreq,
    peakDisplayX,
    dataMinX,
    dataMaxX,
    displayMinX,
    displayMaxX
  } = useMemo(() => {
    if (!data || data.freq.length === 0) {
      return {
        points: '',
        minX: 0,
        maxX: 0,
        minY: 0,
        maxY: 0,
        peakX: 0,
        peakY: 0,
        peakVal: 0,
        peakFreq: 0,
        dataMinX: 0,
        dataMaxX: 0,
        displayMinX: 0,
        displayMaxX: 0,
        carrierFreq: 0
      }
    }
    let sourceFreq = data.freq
    let sourcePower = data.power_db
    let sourceRel = data.freq_rel ?? []
    if (!isOptical) {
      const filteredFreq: number[] = []
      const filteredPower: number[] = []
      data.freq.forEach((f, i) => {
        if (f >= 0) {
          filteredFreq.push(f)
          filteredPower.push(data.power_db[i])
        }
      })
      if (filteredFreq.length >= 2) {
        sourceFreq = filteredFreq
        sourcePower = filteredPower
        sourceRel = []
      }
    }
    const dataMinX = Math.min(...sourceFreq)
    const dataMaxX = Math.max(...sourceFreq)
    const carrierFreq = carrierRefHz
    let viewMinX = dataMinX
    let viewMaxX = dataMaxX
    if (rangeMode === 'custom') {
      let minCandidate = rangeMinHz
      let maxCandidate = rangeMaxHz
      if (minCandidate !== null && maxCandidate !== null && minCandidate > maxCandidate) {
        const temp = minCandidate
        minCandidate = maxCandidate
        maxCandidate = temp
      }
      if (minCandidate !== null && Number.isFinite(minCandidate)) {
        viewMinX = minCandidate
      }
      if (maxCandidate !== null && Number.isFinite(maxCandidate)) {
        viewMaxX = maxCandidate
      }
      viewMinX = Math.max(dataMinX, Math.min(viewMinX, dataMaxX))
      viewMaxX = Math.max(dataMinX, Math.min(viewMaxX, dataMaxX))
      if (viewMaxX <= viewMinX) {
        viewMinX = dataMinX
        viewMaxX = dataMaxX
      }
    }
    const filteredFreq: number[] = []
    const filteredPower: number[] = []
    const filteredRel: number[] = []
    sourceFreq.forEach((f, i) => {
      if (f >= viewMinX && f <= viewMaxX) {
        filteredFreq.push(f)
        filteredPower.push(sourcePower[i])
        if (hasFreqRel && sourceRel.length) {
          filteredRel.push(sourceRel[i])
        }
      }
    })
    let usedFreq = filteredFreq
    let usedPower = filteredPower
    let usedFreqRel = hasFreqRel && sourceRel.length ? filteredRel : []
    let usedMinX = viewMinX
    let usedMaxX = viewMaxX
    if (usedFreq.length < 2) {
      usedFreq = sourceFreq
      usedPower = sourcePower
      usedFreqRel = hasFreqRel && sourceRel.length ? sourceRel : []
      usedMinX = dataMinX
      usedMaxX = dataMaxX
    }
    const displayValues = usedFreq.map((f, i) => {
      if (unitMode !== 'offset') return f
      if (hasFreqRel && centerFreqHz !== null) {
        const delta = centerFreqHz - carrierRefHz
        return (usedFreqRel[i] ?? 0) + delta
      }
      return f - carrierFreq
    })
    const displayMinX = Math.min(...displayValues)
    const displayMaxX = Math.max(...displayValues)
    const minY = Math.min(...usedPower)
    const maxY = Math.max(...usedPower)
    const peakIdx = usedPower.reduce((best, val, idx) => (val > usedPower[best] ? idx : best), 0)
    const rangeX = displayMaxX - displayMinX || 1
    const rangeY = maxY - minY || 1
    const pts = displayValues.map((f, i) => {
      const x = padding + ((f - displayMinX) / rangeX) * (width - padding * 2)
      const y = padding + (1 - (usedPower[i] - minY) / rangeY) * (height - padding * 2)
      return `${x.toFixed(2)},${y.toFixed(2)}`
    })
    const peakX = padding + ((displayValues[peakIdx] - displayMinX) / rangeX) * (width - padding * 2)
    const peakY = padding + (1 - (usedPower[peakIdx] - minY) / rangeY) * (height - padding * 2)
    return {
      points: pts.join(' '),
      minX: usedMinX,
      maxX: usedMaxX,
      minY,
      maxY,
      peakX,
      peakY,
      peakVal: usedPower[peakIdx],
      peakFreq: usedFreq[peakIdx],
      peakDisplayX: displayValues[peakIdx],
      dataMinX,
      dataMaxX,
      displayMinX,
      displayMaxX
    }
  }, [data, rangeMode, rangeMinHz, rangeMaxHz, unitMode, carrierRefHz, hasFreqRel, centerFreqHz])

  const formatHz = (value: number) => {
    const abs = Math.abs(value)
    if (abs >= 1e12) return `${(value / 1e12).toFixed(3)} THz`
    if (abs >= 1e9) return `${(value / 1e9).toFixed(3)} GHz`
    if (abs >= 1e6) return `${(value / 1e6).toFixed(3)} MHz`
    if (abs >= 1e3) return `${(value / 1e3).toFixed(3)} kHz`
    return `${value.toFixed(2)} Hz`
  }

  const formatDb = (value: number) => `${value.toFixed(1)} dB`
  const speedOfLight = 299792458
  const freqToNm = (value: number) => (value > 0 ? (speedOfLight / value) * 1e9 : 0)
  const nmToFreq = (value: number) => (value > 0 ? speedOfLight / (value * 1e-9) : NaN)

  const freqScale = useMemo(() => {
    if (!isOptical) return { scale: 1, label: 'Hz' }
    const maxAbs = Math.max(Math.abs(dataMinX), Math.abs(dataMaxX))
    if (maxAbs >= 1e12) return { scale: 1e12, label: 'THz' }
    if (maxAbs >= 1e9) return { scale: 1e9, label: 'GHz' }
    if (maxAbs >= 1e6) return { scale: 1e6, label: 'MHz' }
    if (maxAbs >= 1e3) return { scale: 1e3, label: 'kHz' }
    return { scale: 1, label: 'Hz' }
  }, [dataMinX, dataMaxX, isOptical])

  const offsetScale = useMemo(() => {
    if (!isOptical) return { scale: 1, label: 'Hz' }
    const span = Math.abs(dataMaxX - dataMinX)
    if (span >= 1e12) return { scale: 1e12, label: 'THz' }
    if (span >= 1e9) return { scale: 1e9, label: 'GHz' }
    if (span >= 1e6) return { scale: 1e6, label: 'MHz' }
    if (span >= 1e3) return { scale: 1e3, label: 'kHz' }
    return { scale: 1, label: 'Hz' }
  }, [dataMinX, dataMaxX, isOptical])

  const rangeUnitLabel = unitMode === 'wavelength'
    ? (labels?.unitNm ?? 'nm')
    : (unitMode === 'offset' ? offsetScale.label : (isOptical ? freqScale.label : (labels?.unitHz ?? 'Hz')))

  const carrierUnitLabel = unitMode === 'wavelength'
    ? (labels?.unitNm ?? 'nm')
    : (labels?.unitHz ?? 'Hz')

  useEffect(() => {
    if (!isOptical) {
      setUnitMode('freq')
    }
  }, [isOptical])

  useEffect(() => {
    if (carrierMode !== 'manual') return
    if (manualCarrierHz === null) return
    const nextValue = unitMode === 'wavelength'
      ? freqToNm(manualCarrierHz).toString()
      : manualCarrierHz.toString()
    setManualCarrierInput(nextValue)
  }, [carrierMode, manualCarrierHz, unitMode])

  const closestIndex = (values: number[], target: number) => {
    let lo = 0
    let hi = values.length - 1
    while (lo <= hi) {
      const mid = Math.floor((lo + hi) / 2)
      if (values[mid] === target) return mid
      if (values[mid] < target) {
        lo = mid + 1
      } else {
        hi = mid - 1
      }
    }
    if (lo <= 0) return 0
    if (lo >= values.length) return values.length - 1
    return Math.abs(values[lo] - target) < Math.abs(values[lo - 1] - target) ? lo : lo - 1
  }

  useEffect(() => {
    setEditingIndex(null)
    setEditingValue('')
    if (!data || data.freq.length === 0) return
    setMarkers((prev) => prev.map((marker) => {
      const clamped = Math.min(Math.max(marker.freq, dataMinX), dataMaxX)
      const resolved = resolveMarker(clamped)
      return resolved ?? marker
    }))
  }, [data, dataMinX, dataMaxX])

  useEffect(() => {
    if (!showExportSettings) return
    const handleClick = (event: MouseEvent) => {
      if (!plotActionsRef.current) return
      if (!plotActionsRef.current.contains(event.target as Node)) {
        setShowExportSettings(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [showExportSettings])

  const formatOffsetValue = (value: number) => {
    const scaled = value / offsetScale.scale
    const sign = scaled > 0 ? '+' : ''
    return `${sign}${scaled.toFixed(3)} ${offsetScale.label}`
  }

  const formatX = (value: number) => {
    if (unitMode === 'wavelength') return `${freqToNm(value).toFixed(2)} nm`
    if (unitMode === 'offset') return formatOffsetValue(value - carrierRefHz)
    return formatHz(value)
  }

  const parseInputValue = (value: string) => {
    const num = Number(value)
    if (!Number.isFinite(num)) return NaN
    if (unitMode === 'offset') {
      if (!isOptical) return num
      return carrierRefHz + num * offsetScale.scale
    }
    return unitMode === 'wavelength' ? nmToFreq(num) : num
  }

  const parseRangeInput = (value: string) => {
    if (!value.trim()) return null
    const num = Number(value)
    if (!Number.isFinite(num)) return null
    if (unitMode === 'offset') {
      if (!isOptical) return num
      return carrierRefHz + num * offsetScale.scale
    }
    if (unitMode === 'wavelength') {
      const parsed = nmToFreq(num)
      return Number.isFinite(parsed) ? parsed : null
    }
    if (!isOptical) return num
    return num * freqScale.scale
  }

  const resolveMarker = (targetAbs: number) => {
    if (!data || data.freq.length === 0) return null
    let idx = 0
    if (!isOptical) {
      const start = data.freq.findIndex((f) => f >= 0)
      if (start >= 0) {
        const freqSlice = data.freq.slice(start)
        idx = start + closestIndex(freqSlice, targetAbs)
      } else {
        idx = closestIndex(data.freq, targetAbs)
      }
    } else if (hasFreqRel && centerFreqHz !== null && data.freq_rel) {
      const targetRel = targetAbs - centerFreqHz
      idx = closestIndex(data.freq_rel, targetRel)
    } else {
      idx = closestIndex(data.freq, targetAbs)
    }
    const freq = data.freq[idx]
    const value = data.power_db[idx]
    return { freq, value, index: idx }
  }

  const markerOffsetValue = (marker: { freq: number; index: number }) => {
    if (unitMode !== 'offset') return marker.freq - carrierRefHz
    if (hasFreqRel && centerFreqHz !== null && data?.freq_rel) {
      const delta = centerFreqHz - carrierRefHz
      return data.freq_rel[marker.index] + delta
    }
    return marker.freq - carrierRefHz
  }

  const parseCarrierInput = (value: string) => {
    if (!value.trim()) return null
    const num = Number(value)
    if (!Number.isFinite(num)) return null
    if (unitMode === 'wavelength') {
      const parsed = nmToFreq(num)
      return Number.isFinite(parsed) ? parsed : null
    }
    return num
  }

  const formatRangeValue = (value: number) => {
    if (unitMode === 'offset') {
      const offset = value - carrierRefHz
      const scaled = offset / offsetScale.scale
      return Number.isFinite(scaled) ? scaled.toString() : ''
    }
    if (unitMode === 'wavelength') return freqToNm(value).toFixed(2)
    if (!isOptical) return value.toString()
    const scaled = value / freqScale.scale
    return Number.isFinite(scaled) ? scaled.toString() : ''
  }

  useEffect(() => {
    if (rangeMode !== 'custom') return
    if (!data || data.freq.length === 0) return
    if (rangeMinHz === null && rangeMaxHz === null) {
      const minVal = Math.min(...data.freq)
      const maxVal = Math.max(...data.freq)
      setRangeMinHz(minVal)
      setRangeMaxHz(maxVal)
      setRangeMinInput(formatRangeValue(minVal))
      setRangeMaxInput(formatRangeValue(maxVal))
    }
  }, [rangeMode, data, rangeMinHz, rangeMaxHz, unitMode, freqScale, offsetScale, carrierRefHz])

  useEffect(() => {
    if (rangeMode !== 'custom') return
    if (rangeMinHz !== null) {
      setRangeMinInput(formatRangeValue(rangeMinHz))
    } else {
      setRangeMinInput('')
    }
    if (rangeMaxHz !== null) {
      setRangeMaxInput(formatRangeValue(rangeMaxHz))
    } else {
      setRangeMaxInput('')
    }
  }, [unitMode, rangeMode, freqScale, offsetScale, carrierRefHz])

  const addMarker = (freq: number) => {
    if (!Number.isFinite(freq) || !data || data.freq.length === 0) return
    if (data && data.freq.length) {
      const clamped = Math.min(Math.max(freq, dataMinX), dataMaxX)
      const resolved = resolveMarker(clamped)
      if (!resolved) return
      setMarkers((prev) => {
        const next = [...prev, resolved]
        next.sort((a, b) => a.freq - b.freq)
        return next
      })
    }
  }

  const handleClick = (event: React.MouseEvent<SVGSVGElement>) => {
    if (!data || data.freq.length === 0) return
    const rect = event.currentTarget.getBoundingClientRect()
    const x = event.clientX - rect.left
    const xView = (x / rect.width) * width
    const clamped = Math.min(Math.max(xView, padding), width - padding)
    const rangeX = displayMaxX - displayMinX || 1
    const displayValue = displayMinX + ((clamped - padding) / (width - padding * 2)) * rangeX
    const freq = unitMode === 'offset' ? carrierRefHz + displayValue : displayValue
    addMarker(freq)
  }

  const handleManualAdd = () => {
    if (!markerInput.trim()) return
    const value = parseInputValue(markerInput)
    if (Number.isFinite(value)) {
      addMarker(value)
      setMarkerInput('')
    }
  }

  const handleRangeMinChange = (value: string) => {
    setRangeMinInput(value)
    if (!value.trim()) {
      setRangeMinHz(null)
      return
    }
    const parsed = parseRangeInput(value)
    if (parsed !== null) {
      setRangeMinHz(parsed)
    }
  }

  const handleRangeMaxChange = (value: string) => {
    setRangeMaxInput(value)
    if (!value.trim()) {
      setRangeMaxHz(null)
      return
    }
    const parsed = parseRangeInput(value)
    if (parsed !== null) {
      setRangeMaxHz(parsed)
    }
  }

  const handleCarrierModeChange = (mode: 'auto' | 'manual') => {
    setCarrierMode(mode)
    if (mode === 'manual') {
      const base = Number.isFinite(carrierRefHz) ? carrierRefHz : 0
      setManualCarrierHz(base)
      const nextValue = unitMode === 'wavelength'
        ? freqToNm(base).toString()
        : base.toString()
      setManualCarrierInput(nextValue)
    }
  }

  const handleCarrierInputChange = (value: string) => {
    setManualCarrierInput(value)
    if (!value.trim()) {
      setManualCarrierHz(null)
      return
    }
    const parsed = parseCarrierInput(value)
    if (parsed !== null) {
      setManualCarrierHz(parsed)
    }
  }

  const startEdit = (index: number) => {
    const marker = markers[index]
    if (!marker) return
    setEditingIndex(index)
    if (unitMode === 'wavelength') {
      setEditingValue(freqToNm(marker.freq).toString())
      return
    }
    if (unitMode === 'offset') {
      setEditingValue((markerOffsetValue(marker) / offsetScale.scale).toString())
      return
    }
    setEditingValue(marker.freq.toString())
  }

  const commitEdit = () => {
    if (editingIndex === null) return
    const value = parseInputValue(editingValue)
    if (Number.isFinite(value) && data && data.freq.length) {
      const clamped = Math.min(Math.max(value, dataMinX), dataMaxX)
      const resolved = resolveMarker(clamped)
      const updated = markers.map((marker, idx) => (idx === editingIndex && resolved ? resolved : marker))
      updated.sort((a, b) => a.freq - b.freq)
      setMarkers(updated)
    }
    setEditingIndex(null)
    setEditingValue('')
  }

  const cancelEdit = () => {
    setEditingIndex(null)
    setEditingValue('')
  }

  const rangeText = () => {
    if (unitMode === 'offset') {
      return `${formatOffsetValue(displayMinX)} - ${formatOffsetValue(displayMaxX)}`
    }
    if (unitMode === 'wavelength') {
      const minW = freqToNm(maxX)
      const maxW = freqToNm(minX)
      const lo = Math.min(minW, maxW)
      const hi = Math.max(minW, maxW)
      return `${lo.toFixed(2)} nm - ${hi.toFixed(2)} nm`
    }
    return `${formatHz(minX)} - ${formatHz(maxX)}`
  }

  const download = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
  }

  const handleSaveCsv = () => {
    if (!data || data.freq.length === 0) return
    const rows: string[] = []
    const n = data.freq.length
    const m = markers.length
    const total = Math.max(n, m)
    if (isOptical) {
      rows.push('freq_hz,wavelength_nm,power_db,marker_freq_hz,marker_wavelength_nm,marker_power_db')
      for (let i = 0; i < total; i += 1) {
        const f = i < n ? data.freq[i] : ''
        const wl = i < n && f > 0 ? freqToNm(f) : ''
        const p = i < n ? data.power_db[i] : ''
        const mf = i < m ? markers[i].freq : ''
        const mwl = i < m && markers[i].freq > 0 ? freqToNm(markers[i].freq) : ''
        const mp = i < m ? markers[i].value : ''
        rows.push(`${f},${wl},${p},${mf},${mwl},${mp}`)
      }
    } else {
      rows.push('freq_hz,power_db,marker_freq_hz,marker_power_db')
      for (let i = 0; i < total; i += 1) {
        const f = i < n ? data.freq[i] : ''
        const p = i < n ? data.power_db[i] : ''
        const mf = i < m ? markers[i].freq : ''
        const mp = i < m ? markers[i].value : ''
        rows.push(`${f},${p},${mf},${mp}`)
      }
    }
    download(new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8' }), `${title}.csv`)
  }

  const handleSaveImage = () => {
    const svg = svgRef.current
    if (!svg) return
    const scale = Number.isFinite(exportScale) && exportScale > 0 ? exportScale : 4
    const fontFamily = window.getComputedStyle(document.documentElement).fontFamily || 'serif'
    const svgClone = svg.cloneNode(true) as SVGSVGElement
    svgClone.setAttribute('width', `${width}`)
    svgClone.setAttribute('height', `${height}`)
    svgClone.setAttribute('font-family', fontFamily)
    const rect = svgClone.querySelector('rect')
    if (rect && exportBackground === 'transparent') {
      rect.setAttribute('fill', 'transparent')
    }
    const serializer = new XMLSerializer()
    const svgString = serializer.serializeToString(svgClone)
    const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' })
    if (exportFormat === 'svg') {
      download(svgBlob, `${title}.svg`)
      return
    }
    const url = URL.createObjectURL(svgBlob)
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = width * scale
      canvas.height = height * scale
      const ctx = canvas.getContext('2d')
      if (ctx) {
        if (exportBackground === 'solid') {
          ctx.fillStyle = '#fdf8ef'
          ctx.fillRect(0, 0, canvas.width, canvas.height)
        }
        ctx.scale(scale, scale)
        ctx.drawImage(img, 0, 0)
        canvas.toBlob((blob) => {
          if (blob) download(blob, `${title}.png`)
          URL.revokeObjectURL(url)
        }, 'image/png')
      } else {
        URL.revokeObjectURL(url)
      }
    }
    img.src = url
  }

  return (
    <div className="plot-card">
      <div className="plot-header">
        <div className="plot-title">{title}</div>
        <div className="plot-actions" ref={plotActionsRef}>
          <button
            className="plot-icon-button"
            type="button"
            onClick={handleSaveImage}
            title={labels?.saveImage ?? 'Save Image'}
          >
            ⭳
          </button>
          <button
            className="plot-icon-button"
            type="button"
            onClick={handleSaveCsv}
            title={labels?.saveCsv ?? 'Save CSV'}
          >
            ⓒ
          </button>
          <button
            className="plot-icon-button"
            type="button"
            onClick={() => setShowExportSettings((v) => !v)}
            title={labels?.exportSettings ?? 'Export Settings'}
          >
            ⚙
          </button>
          {showExportSettings && (
            <div className="plot-options">
              {isOptical && (
                <>
                  <div className="plot-options-row">
                    <span>{labels?.carrierCenter ?? 'Carrier'}</span>
                    <select
                      value={carrierMode}
                      onChange={(e) => handleCarrierModeChange(e.target.value as 'auto' | 'manual')}
                    >
                      <option value="auto">{labels?.carrierAuto ?? 'Auto'}</option>
                      <option value="manual">{labels?.carrierManual ?? 'Manual'}</option>
                    </select>
                  </div>
                  {carrierMode === 'manual' && (
                    <div className="plot-options-row">
                      <span>{labels?.carrierValue ?? 'Carrier'} ({carrierUnitLabel})</span>
                      <input
                        type="number"
                        step="any"
                        value={manualCarrierInput}
                        onChange={(e) => handleCarrierInputChange(e.target.value)}
                        onBlur={(e) => handleCarrierInputChange(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleCarrierInputChange((e.target as HTMLInputElement).value)
                        }}
                      />
                    </div>
                  )}
                </>
              )}
              <div className="plot-options-row">
                <span>{labels?.viewRange ?? 'View Range'}</span>
                <select
                  value={rangeMode}
                  onChange={(e) => setRangeMode(e.target.value as 'auto' | 'custom')}
                >
                  <option value="auto">{labels?.rangeAuto ?? 'Auto'}</option>
                  <option value="custom">{labels?.rangeCustom ?? 'Custom'}</option>
                </select>
              </div>
              {rangeMode === 'custom' && (
                <>
                  <div className="plot-options-row">
                    <span>{labels?.rangeMin ?? 'Min'} ({rangeUnitLabel})</span>
                    <input
                      type="number"
                      step="any"
                      value={rangeMinInput}
                      onChange={(e) => handleRangeMinChange(e.target.value)}
                      onBlur={(e) => handleRangeMinChange(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleRangeMinChange((e.target as HTMLInputElement).value)
                      }}
                    />
                  </div>
                  <div className="plot-options-row">
                    <span>{labels?.rangeMax ?? 'Max'} ({rangeUnitLabel})</span>
                    <input
                      type="number"
                      step="any"
                      value={rangeMaxInput}
                      onChange={(e) => handleRangeMaxChange(e.target.value)}
                      onBlur={(e) => handleRangeMaxChange(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleRangeMaxChange((e.target as HTMLInputElement).value)
                      }}
                    />
                  </div>
                </>
              )}
              <div className="plot-options-toggle">
                <label>
                  <input
                    type="checkbox"
                    checked={showPeak}
                    onChange={(e) => setShowPeak(e.target.checked)}
                  />
                  <span>{labels?.showPeak ?? 'Show Peak'}</span>
                </label>
              </div>
              <div className="plot-options-toggle">
                <label>
                  <input
                    type="checkbox"
                    checked={showMinMax}
                    onChange={(e) => setShowMinMax(e.target.checked)}
                  />
                  <span>{labels?.showMinMax ?? 'Show Min/Max'}</span>
                </label>
              </div>
              <div className="plot-options-divider" />
              <div className="plot-options-row">
                <span>{labels?.exportScale ?? 'Scale'}</span>
                <input
                  type="number"
                  min={1}
                  step={1}
                  value={exportScale}
                  onChange={(e) => setExportScale(Number(e.target.value))}
                />
              </div>
              <div className="plot-options-row">
                <span>{labels?.exportFormat ?? 'Format'}</span>
                <select
                  value={exportFormat}
                  onChange={(e) => setExportFormat(e.target.value as 'png' | 'svg')}
                >
                  <option value="png">{labels?.exportPng ?? 'PNG'}</option>
                  <option value="svg">{labels?.exportSvg ?? 'SVG'}</option>
                </select>
              </div>
              <div className="plot-options-row">
                <span>{labels?.exportBackground ?? 'Background'}</span>
                <select
                  value={exportBackground}
                  onChange={(e) => setExportBackground(e.target.value as 'solid' | 'transparent')}
                >
                  <option value="solid">{labels?.exportBgSolid ?? 'Solid'}</option>
                  <option value="transparent">{labels?.exportBgTransparent ?? 'Transparent'}</option>
                </select>
              </div>
            </div>
          )}
        </div>
      </div>
      {data && data.freq.length ? (
        <>
          <svg
            ref={svgRef}
            viewBox={`0 0 ${width} ${height}`}
            className="plot-svg plot-clickable"
            onClick={handleClick}
          >
            <rect x="0" y="0" width={width} height={height} fill="#fdf8ef" rx="10" />
            <polyline points={points} fill="none" stroke="#b4512a" strokeWidth="1.4" />
            {showPeak && <circle cx={peakX} cy={peakY} r="2.6" fill="#6f2c14" />}
            {markers.map((marker, idx) => {
              if (marker.freq < minX || marker.freq > maxX) return null
              const rangeX = displayMaxX - displayMinX || 1
              const displayValue = unitMode === 'offset' ? marker.freq - carrierRefHz : marker.freq
              const x = padding + ((displayValue - displayMinX) / rangeX) * (width - padding * 2)
              return (
                <g key={`${marker.freq}-${idx}`} onDoubleClick={() => startEdit(idx)}>
                  <line
                    x1={x}
                    y1={padding}
                    x2={x}
                    y2={height - padding}
                    stroke="#2c6fb8"
                    strokeWidth="1"
                    strokeDasharray="4 3"
                  />
                </g>
              )
            })}
            {showMinMax && (
              <text x={padding} y={padding - 8} className="plot-axis">
                {maxY.toFixed(1)} dB
              </text>
            )}
            {showMinMax && (
              <text x={padding} y={height - 6} className="plot-axis">
                {minY.toFixed(1)} dB
              </text>
            )}
          </svg>
          <div className="plot-legend">
            <span>{labels?.range ?? 'Range'}: {rangeText()}</span>
            {showPeak && (
              <span>
                {labels?.peak ?? 'Peak'}:{' '}
                {unitMode === 'offset' ? formatOffsetValue(peakDisplayX) : formatX(peakFreq)} @{' '}
                {peakVal.toFixed(1)} dB
              </span>
            )}
            {isOptical && (
              <label className="plot-unit">
                <span>{labels?.unit ?? 'Unit'}</span>
                <select
                  value={unitMode}
                  onChange={(e) => setUnitMode(e.target.value as 'freq' | 'wavelength' | 'offset')}
                >
                  <option value="wavelength">{labels?.unitNm ?? 'nm'}</option>
                  <option value="freq">{labels?.unitHz ?? 'Hz'}</option>
                  <option value="offset">{labels?.unitOffset ?? 'Offset'}</option>
                </select>
              </label>
            )}
          </div>
          <div className="plot-markers">
            <div className="plot-markers-title">{labels?.markers ?? 'Markers'}</div>
            <div className="plot-marker-controls">
              <input
                type="number"
                className="plot-marker-input"
                placeholder={
                  unitMode === 'wavelength'
                    ? labels?.wavelengthNm ?? 'Wavelength (nm)'
                    : unitMode === 'offset'
                    ? `${labels?.offset ?? 'Offset'} (${rangeUnitLabel})`
                    : labels?.frequencyHz ?? 'Frequency (Hz)'
                }
                value={markerInput}
                onChange={(e) => setMarkerInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleManualAdd()
                }}
              />
              <button className="plot-marker-button" type="button" onClick={handleManualAdd}>
                {labels?.addMarker ?? 'Add'}
              </button>
              <button
                className="plot-marker-button ghost"
                type="button"
                onClick={() => setMarkers([])}
                disabled={markers.length === 0}
              >
                {labels?.clearMarkers ?? 'Clear'}
              </button>
            </div>
            {markers.length === 0 ? (
              <div className="plot-marker-empty">-</div>
            ) : (
              <div className="plot-marker-list">
                {markers.map((marker, idx) => (
                  <div
                    key={`${marker.freq}-${idx}`}
                    className="plot-marker-row"
                    onDoubleClick={() => startEdit(idx)}
                  >
                    {editingIndex === idx ? (
                      <input
                        className="plot-marker-edit"
                        type="number"
                        value={editingValue}
                        onChange={(e) => setEditingValue(e.target.value)}
                        onBlur={commitEdit}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') commitEdit()
                          if (e.key === 'Escape') cancelEdit()
                        }}
                        autoFocus
                      />
                    ) : (
                      <span>
                        {unitMode === 'offset' ? formatOffsetValue(markerOffsetValue(marker)) : formatX(marker.freq)} ·{' '}
                        {formatDb(marker.value)}
                      </span>
                    )}
                    <button
                      className="plot-marker-button ghost"
                      type="button"
                      onClick={() => setMarkers((prev) => prev.filter((_, i) => i !== idx))}
                    >
                      {labels?.removeMarker ?? 'Remove'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="plot-empty">No data</div>
      )}
    </div>
  )
}
