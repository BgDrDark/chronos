import React, { useMemo, useState } from 'react';
import {
  Box, Typography, IconButton, Chip, Collapse,
  List, ListItem, ListItemButton, ListItemText, ListItemIcon
} from '@mui/material';
import {
  ExpandMore, ChevronRight, Edit as EditIcon,
  Delete as DeleteIcon, Add as AddIcon,
  Folder, FolderOpen
} from '@mui/icons-material';
import { AccessZone } from '../../types';

interface ZoneNode {
  zone: AccessZone;
  children: ZoneNode[];
  depth: number;
}

function buildTree(zones: AccessZone[]): ZoneNode[] {
  const map = new Map<number, ZoneNode>();
  const roots: ZoneNode[] = [];

  for (const z of zones) {
    map.set(z.id, { zone: z, children: [], depth: 0 });
  }

  for (const node of map.values()) {
    const parentId = node.zone.parentZoneId;
    if (parentId && map.has(parentId)) {
      node.depth = (map.get(parentId)?.depth ?? 0) + 1;
      map.get(parentId)!.children.push(node);
    } else {
      roots.push(node);
    }
  }

  const sortNodes = (nodes: ZoneNode[]) => {
    nodes.sort((a, b) => (a.zone.traversalOrder ?? 0) - (b.zone.traversalOrder ?? 0));
    for (const n of nodes) sortNodes(n.children);
  };
  sortNodes(roots);

  return roots;
}

interface ZoneTreeViewProps {
  zones: AccessZone[];
  onEdit: (zone: AccessZone) => void;
  onDelete: (id: number) => void;
  onAddChild: (parent: AccessZone) => void;
}

const ZoneTreeView: React.FC<ZoneTreeViewProps> = ({ zones, onEdit, onDelete, onAddChild }) => {
  const tree = useMemo(() => buildTree(zones), [zones]);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const toggle = (id: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const renderNode = (node: ZoneNode) => {
    const hasChildren = node.children.length > 0;
    const isExpanded = expanded.has(node.zone.id);

    return (
      <React.Fragment key={node.zone.id}>
        <ListItem
          sx={{
            pl: 2 + node.depth * 3,
            borderLeft: node.depth > 0 ? '2px solid' : 'none',
            borderColor: 'divider',
            ml: node.depth > 0 ? 3 : 0,
          }}
          secondaryAction={
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <IconButton size="small" title="Добави подзона" onClick={() => onAddChild(node.zone)}>
                <AddIcon fontSize="inherit" />
              </IconButton>
              <IconButton size="small" title="Редактирай" onClick={() => onEdit(node.zone)}>
                <EditIcon fontSize="inherit" />
              </IconButton>
              <IconButton size="small" color="error" title="Изтрий" onClick={() => onDelete(node.zone.id)}>
                <DeleteIcon fontSize="inherit" />
              </IconButton>
            </Box>
          }
          disablePadding
        >
          <ListItemButton onClick={() => hasChildren && toggle(node.zone.id)} dense>
            <ListItemIcon sx={{ minWidth: 28 }}>
              {hasChildren ? (
                isExpanded ? <ExpandMore fontSize="small" /> : <ChevronRight fontSize="small" />
              ) : (
                <Box sx={{ width: 24 }} />
              )}
            </ListItemIcon>
            <ListItemIcon sx={{ minWidth: 28 }}>
              {hasChildren && isExpanded ? <FolderOpen fontSize="small" color="primary" /> : <Folder fontSize="small" color={node.depth === 0 ? 'primary' : 'inherit'} />}
            </ListItemIcon>
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: node.depth === 0 ? 600 : 400 }}>
                    {node.zone.name}
                  </Typography>
                  <Chip label={`Ниво ${node.zone.level ?? 1}`} size="small" variant="outlined" sx={{ height: 20, fontSize: 11 }} />
                  {node.zone.inheritPermissions && (
                    <Chip label="насл." size="small" color="info" variant="outlined" sx={{ height: 20, fontSize: 11 }} />
                  )}
                </Box>
              }
              secondary={`ID: ${node.zone.zoneId ?? ''} | ${node.zone.requiredHoursStart ?? '00:00'} - ${node.zone.requiredHours_end ?? '23:59'}`}
            />
          </ListItemButton>
        </ListItem>
        {hasChildren && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List dense disablePadding>
              {node.children.map(renderNode)}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    );
  };

  return (
    <List dense disablePadding>
      {tree.map(renderNode)}
    </List>
  );
};

export default ZoneTreeView;
