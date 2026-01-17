import React, { useMemo, useState } from 'react'
import { Paper, Typography, TextField, Button, Stack, Box, Tooltip } from '@mui/material'

interface BlockLibraryProps {
  types: string[]
  onAdd: (type: string) => void
  title: string
  labelForType: (type: string) => string
  groups?: { id: string; title: string; types: string[] }[]
  typeStyles?: Record<string, string>
  searchPlaceholder: string
  noMatchText: string
  getDescription?: (type: string) => string
}

export default function BlockLibrary({
  types,
  onAdd,
  title,
  labelForType,
  groups,
  typeStyles,
  searchPlaceholder,
  noMatchText,
  getDescription
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

  const renderButton = (type: string) => {
    const label = labelForType(type)
    const description = getDescription ? getDescription(type) : ''
    // Use whitespace-pre-wrap to handle newlines if user wants full name + description in separate lines?
    // User asked for "Full Name" and "Description". labelForType is likely the full name (or close to it).
    // Let's assume label is the name.

    return (
      <Tooltip
        key={type}
        title={
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>{label}</Typography>
            {description && <Typography variant="body2">{description}</Typography>}
          </Box>
        }
        arrow
        placement="right"
      >
        <Button
          variant="outlined"
          size="small"
          onClick={() => onAdd(type)}
          sx={{
            justifyContent: 'flex-start',
            textTransform: 'none',
            textAlign: 'left',
            height: 'auto',
            py: 0.5,
            px: 1,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: 'block'
          }}
          color={typeStyles?.[type]?.includes('measure') ? 'secondary' : 'primary'}
        >
          {label}
        </Button>
      </Tooltip>
    )
  }

  return (
    <Paper variant="outlined" sx={{ p: 1.5, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
      <Typography variant="h6">{title}</Typography>
      <TextField
        size="small"
        fullWidth
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={searchPlaceholder}
      />
      <Box sx={{ pr: 0.5 }}>
        {filtered.length === 0 ? (
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
            {noMatchText}
          </Typography>
        ) : grouped ? (
          <Stack spacing={2}>
            {grouped.map((group) => (
              <Box key={group.id}>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  {group.title}
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', gap: 1 }}>
                  {group.types.map((type) => renderButton(type))}
                </Box>
              </Box>
            ))}
          </Stack>
        ) : (
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', gap: 1 }}>
            {filtered.map((type) => renderButton(type))}
          </Box>
        )}
      </Box>
    </Paper>
  )
}
