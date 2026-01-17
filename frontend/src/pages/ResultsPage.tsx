import React from 'react'
import { Box, Typography, Paper } from '@mui/material'
import Outputs from '../components/Outputs'

interface ResultsPageProps {
    result: any
    probeOutputs: any[]
    labels: any // For i18n
}

export default function ResultsPage({ result, probeOutputs, labels }: ResultsPageProps) {
    if (!result) {
        return (
            <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary' }}>
                <Typography>{labels.noResults || 'No results available. Run a simulation first.'}</Typography>
            </Box>
        )
    }

    return (
        <Box sx={{ height: '100%', p: 2, overflow: 'hidden' }}>
            <Typography variant="h5" gutterBottom>
                Simulation Results
            </Typography>
            <Paper variant="outlined" sx={{ height: 'calc(100% - 48px)', overflowY: 'auto' }}>
                <Outputs
                    result={result}
                    probeOutputs={probeOutputs}
                    labels={labels}
                    carrierAutoHz={undefined}
                    expanded={null}
                />
            </Paper>
        </Box>
    )
}
