import React, { useState } from 'react'
import { Box, IconButton, Tooltip, Divider, Stack, Typography, Button } from '@mui/material'
import HomeIcon from '@mui/icons-material/Home'
import EditIcon from '@mui/icons-material/Edit'
import AssessmentIcon from '@mui/icons-material/Assessment'
import SettingsIcon from '@mui/icons-material/Settings'
import MenuIcon from '@mui/icons-material/Menu'
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import { useTheme } from '@mui/material/styles'

export type PageId = 'home' | 'editor' | 'results' | 'settings'

interface NavRailProps {
    activePage: PageId
    onNavigate: (page: PageId) => void
}

export default function NavRail({ activePage, onNavigate }: NavRailProps) {
    const theme = useTheme()
    const [expanded, setExpanded] = useState(false)

    const NavItem = ({ id, icon, label }: { id: PageId; icon: React.ReactNode; label: string }) => {
        const active = activePage === id

        if (expanded) {
            return (
                <Button
                    onClick={() => onNavigate(id)}
                    startIcon={icon}
                    fullWidth
                    sx={{
                        justifyContent: 'flex-start',
                        px: 2,
                        py: 1.5,
                        borderRadius: 2,
                        bgcolor: active ? theme.palette.primary.main : 'transparent',
                        color: active ? theme.palette.primary.contrastText : theme.palette.text.secondary,
                        '&:hover': {
                            bgcolor: active ? theme.palette.primary.dark : theme.palette.action.hover,
                        },
                        textTransform: 'none',
                        fontWeight: active ? 'bold' : 'normal',
                        minHeight: 48
                    }}
                >
                    {label}
                </Button>
            )
        }

        return (
            <Tooltip title={label} placement="right">
                <IconButton
                    onClick={() => onNavigate(id)}
                    sx={{
                        borderRadius: 2,
                        bgcolor: active ? theme.palette.primary.main : 'transparent',
                        color: active ? theme.palette.primary.contrastText : theme.palette.text.secondary,
                        '&:hover': {
                            bgcolor: active ? theme.palette.primary.dark : theme.palette.action.hover,
                        },
                        width: 48,
                        height: 48,
                    }}
                >
                    {icon}
                </IconButton>
            </Tooltip>
        )
    }

    return (
        <Box
            sx={{
                width: expanded ? 200 : 72,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: expanded ? 'stretch' : 'center',
                py: 2,
                px: expanded ? 1.5 : 0,
                borderRight: `1px solid ${theme.palette.divider}`,
                bgcolor: 'background.paper',
                flexShrink: 0,
                transition: 'width 0.2s ease, padding 0.2s ease'
            }}
        >
            <Box sx={{ display: 'flex', justifyContent: expanded ? 'flex-start' : 'center', mb: 2, px: expanded ? 0 : 0 }}>
                <IconButton onClick={() => setExpanded(!expanded)} sx={{ ml: expanded ? 1 : 0 }}>
                    <MenuIcon />
                </IconButton>
            </Box>

            <Stack spacing={2} alignItems={expanded ? 'stretch' : 'center'}>
                <NavItem id="home" icon={<HomeIcon />} label="Home" />
                <Divider flexItem sx={{ width: expanded ? '100%' : '60%', alignSelf: 'center' }} />
                <NavItem id="editor" icon={<EditIcon />} label="Editor" />
                <NavItem id="results" icon={<AssessmentIcon />} label="Results" />
                <NavItem id="settings" icon={<SettingsIcon />} label="Settings" />
            </Stack>
        </Box>
    )
}
