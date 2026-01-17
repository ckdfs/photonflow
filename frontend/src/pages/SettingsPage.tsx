import React, { useState } from 'react'
import { Box, Typography, Paper, Stack, FormControl, InputLabel, Select, MenuItem, TextField, Button, Divider } from '@mui/material'
import { Lang } from '../i18n'

interface SettingsPageProps {
    lang: Lang
    setLang: (lang: Lang) => void
    simConfig: any
    setSimConfig: (config: any) => void
    fsMode: 'auto' | 'custom'
    setFsMode: (mode: 'auto' | 'custom') => void
    fsCustom: number
    setFsCustom: (val: number) => void
    nSamples: string
    setNSamples: (val: string) => void
    t: (key: string) => string
}

export default function SettingsPage({
    lang,
    setLang,
    simConfig,
    setSimConfig,
    fsMode,
    setFsMode,
    fsCustom,
    setFsCustom,
    nSamples,
    setNSamples,
    t
}: SettingsPageProps) {
    const [showAdvancedSim, setShowAdvancedSim] = useState(false)

    return (
        <Box sx={{ height: '100%', p: 3, overflow: 'auto' }}>
            <Typography variant="h5" gutterBottom>
                {t('simSettings')}
            </Typography>

            <Paper variant="outlined" sx={{ p: 3, maxWidth: 600 }}>
                <Stack spacing={3}>
                    <Box>
                        <Typography variant="subtitle1" gutterBottom sx={{ color: 'text.secondary' }}>
                            General
                        </Typography>
                        <FormControl fullWidth size="small">
                            <InputLabel>{t('language')}</InputLabel>
                            <Select
                                value={lang}
                                label={t('language')}
                                onChange={(e) => setLang(e.target.value as Lang)}
                            >
                                <MenuItem value="zh">{lang === 'zh' ? '中文' : 'Chinese'}</MenuItem>
                                <MenuItem value="en">{lang === 'zh' ? '英文' : 'English'}</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>

                    <Divider />

                    <Box>
                        <Typography variant="subtitle1" gutterBottom sx={{ color: 'text.secondary' }}>
                            Simulation Engine
                        </Typography>
                        <Stack spacing={2}>
                            <FormControl fullWidth size="small">
                                <InputLabel>{t('backend')}</InputLabel>
                                <Select
                                    value={simConfig.backend}
                                    label={t('backend')}
                                    onChange={(e) => setSimConfig((cfg: any) => ({ ...cfg, backend: e.target.value }))}
                                >
                                    <MenuItem value="torch">torch</MenuItem>
                                </Select>
                            </FormControl>

                            <FormControl fullWidth size="small">
                                <InputLabel>{t('device')}</InputLabel>
                                <Select
                                    value={simConfig.device}
                                    label={t('device')}
                                    onChange={(e) => setSimConfig((cfg: any) => ({ ...cfg, device: e.target.value }))}
                                >
                                    <MenuItem value="cpu">cpu</MenuItem>
                                    <MenuItem value="cuda">cuda</MenuItem>
                                </Select>
                            </FormControl>
                        </Stack>
                    </Box>

                    <Divider />

                    <Box>
                        <Typography variant="subtitle1" gutterBottom sx={{ color: 'text.secondary' }}>
                            Sampling & Duration
                        </Typography>
                        <Stack spacing={2}>
                            <FormControl fullWidth size="small">
                                <InputLabel>{t('fsMode')}</InputLabel>
                                <Select
                                    value={fsMode}
                                    label={t('fsMode')}
                                    onChange={(e) => setFsMode(e.target.value as 'auto' | 'custom')}
                                >
                                    <MenuItem value="auto">{t('fsAuto')}</MenuItem>
                                    <MenuItem value="custom">{t('fsCustom')}</MenuItem>
                                </Select>
                            </FormControl>

                            <TextField
                                label={t('fsValue')}
                                type="number"
                                size="small"
                                value={fsCustom}
                                disabled={fsMode === 'auto'}
                                onChange={(e) => setFsCustom(Number(e.target.value))}
                                fullWidth
                            />

                            <TextField
                                label={t('oversample')}
                                type="number"
                                size="small"
                                value={simConfig.oversample}
                                onChange={(e) => setSimConfig((cfg: any) => ({ ...cfg, oversample: Number(e.target.value) }))}
                                fullWidth
                            />

                            <FormControl fullWidth size="small">
                                <InputLabel>{t('window')}</InputLabel>
                                <Select
                                    value={simConfig.window}
                                    label={t('window')}
                                    onChange={(e) => setSimConfig((cfg: any) => ({ ...cfg, window: e.target.value }))}
                                >
                                    <MenuItem value="hann">hann</MenuItem>
                                    <MenuItem value="hamming">hamming</MenuItem>
                                    <MenuItem value="blackman">blackman</MenuItem>
                                    <MenuItem value="rect">rect</MenuItem>
                                    <MenuItem value="kaiser">kaiser</MenuItem>
                                </Select>
                            </FormControl>

                            <TextField
                                label={t('duration')}
                                type="number"
                                size="small"
                                value={simConfig.duration_s}
                                onChange={(e) => setSimConfig((cfg: any) => ({ ...cfg, duration_s: Number(e.target.value) }))}
                                fullWidth
                            />

                            <TextField
                                label={t('nSamples')}
                                type="number"
                                size="small"
                                value={nSamples}
                                onChange={(e) => setNSamples(e.target.value)}
                                fullWidth
                            />
                        </Stack>
                    </Box>

                    <Button onClick={() => setShowAdvancedSim((v) => !v)}>
                        {showAdvancedSim ? t('hideAdvanced') : t('showAdvanced')}
                    </Button>

                    {showAdvancedSim && (
                        <Stack spacing={1.5} sx={{ pt: 1, borderTop: '1px dashed #e0e0e0' }}>
                            <Typography variant="subtitle2">{t('advancedSettings')}</Typography>
                            <TextField
                                label={t('seed')}
                                type="number"
                                size="small"
                                value={simConfig.seed}
                                onChange={(e) => setSimConfig((cfg: any) => ({ ...cfg, seed: Number(e.target.value) }))}
                            />
                            <TextField
                                label={t('fsMin')}
                                type="number"
                                size="small"
                                value={simConfig.fs_min}
                                onChange={(e) => setSimConfig((cfg: any) => ({ ...cfg, fs_min: Number(e.target.value) }))}
                            />
                            <TextField
                                label={t('fsMax')}
                                type="number"
                                size="small"
                                value={simConfig.fs_max}
                                onChange={(e) => setSimConfig((cfg: any) => ({ ...cfg, fs_max: Number(e.target.value) }))}
                            />
                            <TextField
                                label={t('chunk')}
                                type="number"
                                size="small"
                                value={simConfig.chunk}
                                onChange={(e) => setSimConfig((cfg: any) => ({ ...cfg, chunk: Number(e.target.value) }))}
                            />
                            <TextField
                                label={t('minSamples')}
                                type="number"
                                size="small"
                                value={simConfig.min_samples}
                                onChange={(e) => setSimConfig((cfg: any) => ({ ...cfg, min_samples: Number(e.target.value) }))}
                            />
                            <TextField
                                label={t('maxSamples')}
                                type="number"
                                size="small"
                                value={simConfig.max_samples}
                                onChange={(e) => setSimConfig((cfg: any) => ({ ...cfg, max_samples: Number(e.target.value) }))}
                            />
                        </Stack>
                    )}
                </Stack>
            </Paper>
        </Box>
    )
}
