import React from 'react'
import { Box, Typography, Button, Paper, Container } from '@mui/material'
import AddIcon from '@mui/icons-material/Add'

interface HomePageProps {
    onNavigate: (page: any) => void
}

export default function HomePage({ onNavigate }: HomePageProps) {
    return (
        <Container maxWidth="md" sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Stack spacing={4} alignItems="center" sx={{ textAlign: 'center' }}>
                <Typography variant="h3" fontWeight="bold" color="primary">
                    PhotonFlow
                </Typography>
                <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600 }}>
                    Advanced Photonic Simulation Platform
                </Typography>

                <Stack direction="row" spacing={2}>
                    <Button
                        variant="contained"
                        size="large"
                        startIcon={<AddIcon />}
                        onClick={() => onNavigate('editor')}
                    >
                        New Project
                    </Button>
                    <Button
                        variant="outlined"
                        size="large"
                        onClick={() => onNavigate('editor')}
                    >
                        Open Example
                    </Button>
                </Stack>

                <Paper variant="outlined" sx={{ p: 4, width: '100%', bgcolor: 'background.default' }}>
                    <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                        Recent Activity
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        No recent projects found.
                    </Typography>
                </Paper>
            </Stack>
        </Container>
    )
}

// Helper to avoid import error if Stack is missing
import { Stack } from '@mui/material'
