import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import axios from 'axios';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Paper,
  Typography,
  Tooltip,
  ToggleButtonGroup,
  ToggleButton,
  Menu,
  MenuItem,
  ListItemIcon,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  PanTool as PanToolIcon,
  TouchApp as SelectIcon,
  RotateRight as RotateIcon,
  Tune as TuneIcon,
  Wallpaper as WallpaperIcon,
  Code as CodeIcon,
} from '@mui/icons-material';

import { ValidatedTextField } from '../components/ui/ValidatedTextField';
import { InfoIcon } from '../components/ui/InfoIcon';
import { accessControlFieldsHelp } from '../components/ui/fieldsHelpText';
import { useError } from '../context/ErrorContext';
import { getErrorMessage } from '../types';
import { FLOOR_PLANS_QUERY, FLOOR_PLAN_QUERY, FLOOR_PLAN_DOORS_QUERY } from '../graphql/queries/floorPlan';
import { ACCESS_DOORS_QUERY } from '../graphql/queries/accessControl';
import {
  CREATE_FLOOR_PLAN,
  DELETE_FLOOR_PLAN,
  UPDATE_FLOOR_PLAN,
  ADD_DOOR_TO_FLOOR_PLAN,
  UPDATE_DOOR_ON_FLOOR_PLAN,
  REMOVE_DOOR_FROM_FLOOR_PLAN,
} from '../graphql/mutations/floorPlan';

interface FloorPlanType {
  id: number;
  name: string;
  imagePath?: string | null;
  svgContent?: string | null;
  backgroundImage?: string | null;
  width: number;
  height: number;
  isActive: boolean;
}

interface FloorPlanDoorType {
  id: number;
  floorPlanId: number;
  doorId: number;
  x: number;
  y: number;
  width: number;
  height: number;
  rotation: number;
  label?: string | null;
}

type ToolMode = 'select' | 'pan' | 'add' | 'rotate';

const DOOR_COLORS = [
  '#1976d2', '#388e3c', '#d32f2f', '#f57c00', '#7b1fa2',
  '#00838f', '#c2185b', '#455a64', '#558b2f', '#e65100',
];

const FloorPlanPage: React.FC = () => {
  const { showError, showSuccess } = useError();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [toolMode, setToolMode] = useState<ToolMode>('select');
  const [draggingDoor, setDraggingDoor] = useState<number | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [panning, setPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [viewOffset, setViewOffset] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; doorId: number } | null>(null);
  const [propsDoor, setPropsDoor] = useState<FloorPlanDoorType | null>(null);
  const [propsForm, setPropsForm] = useState({ label: '', width: 0, height: 0, rotation: 0 });
  const [uploading, setUploading] = useState(false);
  const [svgEditorOpen, setSvgEditorOpen] = useState(false);
  const [svgEditContent, setSvgEditContent] = useState('');
  const [doorSelectOpen, setDoorSelectOpen] = useState(false);
  const [pendingDoorPos, setPendingDoorPos] = useState<{ x: number; y: number } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const svgRef = useRef<SVGSVGElement>(null);
  const viewerRef = useRef<HTMLDivElement>(null);

  const { data: doorsList } = useQuery(ACCESS_DOORS_QUERY, { skip: !doorSelectOpen });

  const { data: listData, loading: listLoading, refetch: refetchList } = useQuery(FLOOR_PLANS_QUERY);
  const { data: detailData, refetch: refetchPlan } = useQuery(FLOOR_PLAN_QUERY, {
    variables: { id: selectedId! },
    skip: !selectedId,
  });
  const { data: doorsData, refetch: refetchDoors } = useQuery(FLOOR_PLAN_DOORS_QUERY, {
    variables: { floorPlanId: selectedId! },
    skip: !selectedId,
  });

  const [createFloorPlan] = useMutation(CREATE_FLOOR_PLAN);
  const [deleteFloorPlan] = useMutation(DELETE_FLOOR_PLAN);
  const [updateFloorPlan] = useMutation(UPDATE_FLOOR_PLAN);
  const [addDoor] = useMutation(ADD_DOOR_TO_FLOOR_PLAN);
  const [updateDoor] = useMutation(UPDATE_DOOR_ON_FLOOR_PLAN);
  const [removeDoor] = useMutation(REMOVE_DOOR_FROM_FLOOR_PLAN);

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!selectedId) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const ws = new WebSocket(`${protocol}//${host}/ws/floor-plan/${selectedId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'door_moved' || msg.type === 'door_rotated' || msg.type === 'door_added' || msg.type === 'door_removed') {
          refetchDoors();
        }
      } catch {
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [selectedId, refetchDoors]);

  const selectedPlan = detailData?.floorPlan as FloorPlanType | undefined;
  const doors = (doorsData?.floorPlanDoors as FloorPlanDoorType[]) || [];

  const svgViewBox = useMemo(() => {
    if (!selectedPlan) return '0 0 1000 800';
    return `0 0 ${selectedPlan.width} ${selectedPlan.height}`;
  }, [selectedPlan]);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      const result = await createFloorPlan({ variables: { input: { name: newName, companyId: 1 } } });
      showSuccess('Етажът е създаден успешно');
      setCreateOpen(false);
      setNewName('');
      refetchList();
      const newId = result.data?.createFloorPlan?.id;
      if (newId) setSelectedId(newId);
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteFloorPlan({ variables: { id } });
      showSuccess('Етажът е изтрит');
      if (selectedId === id) setSelectedId(null);
      refetchList();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((prev) => Math.max(0.1, Math.min(10, prev * delta)));
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (toolMode === 'pan' || (toolMode === 'select' && e.button === 1)) {
      setPanning(true);
      setPanStart({ x: e.clientX - viewOffset.x, y: e.clientY - viewOffset.y });
      return;
    }
    if (toolMode === 'add') {
      if (!selectedId) return;
      const svg = svgRef.current;
      if (!svg) return;
      const rect = svg.getBoundingClientRect();
      const scaleX = selectedPlan ? selectedPlan.width / rect.width : 1;
      const scaleY = selectedPlan ? selectedPlan.height / rect.height : 1;
      const x = Math.round((e.clientX - rect.left) * scaleX / zoom);
      const y = Math.round((e.clientY - rect.top) * scaleY / zoom);
      setPendingDoorPos({ x, y });
      setDoorSelectOpen(true);
      return;
    }
  }, [toolMode, viewOffset, zoom, selectedId, selectedPlan, addDoor, refetchDoors, showSuccess, showError]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (panning) {
      setViewOffset({ x: e.clientX - panStart.x, y: e.clientY - panStart.y });
      return;
    }
    if (draggingDoor !== null) {
      const svg = svgRef.current;
      if (!svg || !selectedPlan) return;
      const rect = svg.getBoundingClientRect();
      const scaleX = selectedPlan.width / rect.width;
      const scaleY = selectedPlan.height / rect.height;
      const x = Math.round((e.clientX - rect.left) * scaleX / zoom - dragOffset.x);
      const y = Math.round((e.clientY - rect.top) * scaleY / zoom - dragOffset.y);
      setDoorsLocal((prev) =>
        prev.map((d) => (d.id === draggingDoor ? { ...d, x, y } : d))
      );
    }
  }, [panning, draggingDoor, dragOffset, zoom, selectedPlan]);

  const [doorsLocal, setDoorsLocal] = useState<FloorPlanDoorType[]>([]);

  useEffect(() => {
    setDoorsLocal(doors);
  }, [doors]);

  const handleMouseUp = useCallback(async () => {
    if (panning) {
      setPanning(false);
      return;
    }
    if (draggingDoor !== null) {
      const door = doorsLocal.find((d) => d.id === draggingDoor);
      if (door) {
        try {
          await updateDoor({
            variables: {
              input: { id: door.id, x: door.x, y: door.y },
            },
          });
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'door_moved', doorId: door.id, x: door.x, y: door.y }));
          }
          refetchDoors();
        } catch (err) {
          showError(getErrorMessage(err));
        }
      }
      setDraggingDoor(null);
    }
  }, [draggingDoor, doorsLocal, updateDoor, refetchDoors, showError]);

  const handleDoorMouseDown = useCallback((e: React.MouseEvent, door: FloorPlanDoorType) => {
    if (toolMode !== 'select') return;
    e.stopPropagation();
    e.preventDefault();
    const svg = svgRef.current;
    if (!svg || !selectedPlan) return;
    const rect = svg.getBoundingClientRect();
    const scaleX = selectedPlan.width / rect.width;
    const scaleY = selectedPlan.height / rect.height;
    setDraggingDoor(door.id);
    setDragOffset({
      x: (e.clientX - rect.left) * scaleX / zoom - door.x,
      y: (e.clientY - rect.top) * scaleY / zoom - door.y,
    });
  }, [toolMode, zoom, selectedPlan]);

  const handleDoorContext = useCallback((e: React.MouseEvent, door: FloorPlanDoorType) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu({ x: e.clientX, y: e.clientY, doorId: door.id });
  }, []);

  const handleDoorProps = useCallback(() => {
    if (!contextMenu) return;
    const door = doorsLocal.find((d) => d.id === contextMenu.doorId);
    if (!door) return;
    setPropsDoor(door);
    setPropsForm({ label: door.label || '', width: door.width, height: door.height, rotation: door.rotation });
    setContextMenu(null);
  }, [contextMenu, doorsLocal]);

  const handleSaveDoorProps = useCallback(async () => {
    if (!propsDoor) return;
    try {
      await updateDoor({
        variables: {
          input: {
            id: propsDoor.id,
            label: propsForm.label || null,
            width: propsForm.width,
            height: propsForm.height,
            rotation: propsForm.rotation,
          },
        },
      });
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'door_updated', doorId: propsDoor.id }));
      }
      refetchDoors();
      setPropsDoor(null);
      showSuccess('Свойствата са запазени');
    } catch (err) {
      showError(getErrorMessage(err));
    }
  }, [propsDoor, propsForm, updateDoor, refetchDoors, showSuccess, showError]);

  const handleRotateDoor = useCallback(async () => {
    if (!contextMenu) return;
    const door = doorsLocal.find((d) => d.id === contextMenu.doorId);
    if (!door) return;
    const newRotation = (door.rotation + 90) % 360;
    try {
      await updateDoor({ variables: { input: { id: door.id, rotation: newRotation } } });
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'door_rotated', doorId: door.id, rotation: newRotation }));
      }
      refetchDoors();
      showSuccess('Вратата е завъртяна');
    } catch (err) {
      showError(getErrorMessage(err));
    }
    setContextMenu(null);
  }, [contextMenu, doorsLocal, updateDoor, refetchDoors, showSuccess, showError]);

  const handleRemoveDoor = useCallback(async () => {
    if (!contextMenu) return;
    try {
      await removeDoor({ variables: { id: contextMenu.doorId } });
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'door_removed', doorId: contextMenu.doorId }));
      }
      refetchDoors();
      showSuccess('Вратата е премахната');
    } catch (err) {
      showError(getErrorMessage(err));
    }
    setContextMenu(null);
  }, [contextMenu, removeDoor, refetchDoors, showSuccess, showError]);

  const handleResetView = useCallback(() => {
    setZoom(1);
    setViewOffset({ x: 0, y: 0 });
  }, []);

  const handleUploadBackground = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedId) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`/floor-plan/${selectedId}/upload-background`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
      showSuccess('Фоновото изображение е качено');
      refetchPlan();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setUploading(false);
      if (e.target) e.target.value = '';
    }
  }, [selectedId, refetchPlan, showSuccess, showError]);

  const handleOpenSvgEditor = useCallback(() => {
    setSvgEditContent(selectedPlan?.svgContent || '');
    setSvgEditorOpen(true);
  }, [selectedPlan]);

  const handleSaveSvg = useCallback(async () => {
    if (!selectedId) return;
    try {
      await updateFloorPlan({ variables: { input: { id: selectedId, svgContent: svgEditContent } } });
      showSuccess('SVG съдържанието е запазено');
      setSvgEditorOpen(false);
      refetchPlan();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  }, [selectedId, svgEditContent, updateFloorPlan, refetchPlan, showSuccess, showError]);

  return (
    <Box sx={{ display: 'flex', height: '100%', gap: 2, p: 2 }}>
      <Paper sx={{ width: 280, p: 2, overflow: 'auto', flexShrink: 0 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Етажи</Typography>
          <IconButton onClick={() => setCreateOpen(true)} size="small">
            <AddIcon />
          </IconButton>
        </Box>
        {listLoading ? (
          <Typography variant="body2">Зареждане...</Typography>
        ) : (
          <List>
            {(listData?.floorPlans || []).map((fp: FloorPlanType) => (
              <ListItem key={fp.id} disablePadding secondaryAction={
                <IconButton edge="end" size="small" onClick={() => handleDelete(fp.id)}>
                  <DeleteIcon />
                </IconButton>
              }>
                <ListItemButton
                  selected={selectedId === fp.id}
                  onClick={() => setSelectedId(fp.id)}
                >
                  <ListItemText primary={fp.name} secondary={`${fp.width}x${fp.height}`} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </Paper>

      <Paper sx={{ flex: 1, p: 2, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {selectedPlan ? (
          <>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexShrink: 0 }}>
              <Typography variant="h5" sx={{ flex: 1 }}>{selectedPlan.name}</Typography>
              <ToggleButtonGroup
                value={toolMode}
                exclusive
                onChange={(_, v) => v && setToolMode(v)}
                size="small"
              >
                <ToggleButton value="select">
                  <Tooltip title="Избор/Влачене">
                    <SelectIcon />
                  </Tooltip>
                </ToggleButton>
                <ToggleButton value="pan">
                  <Tooltip title="Придвижване">
                    <PanToolIcon />
                  </Tooltip>
                </ToggleButton>
                <ToggleButton value="add">
                  <Tooltip title="Добавяне на врата">
                    <AddIcon />
                  </Tooltip>
                </ToggleButton>
              </ToggleButtonGroup>
              <IconButton size="small" onClick={() => setZoom((z) => Math.min(10, z * 1.2))}>
                <ZoomInIcon />
              </IconButton>
              <Typography variant="body2" sx={{ minWidth: 40, textAlign: 'center' }}>
                {Math.round(zoom * 100)}%
              </Typography>
              <IconButton size="small" onClick={() => setZoom((z) => Math.max(0.1, z / 1.2))}>
                <ZoomOutIcon />
              </IconButton>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={handleUploadBackground}
              />
              <IconButton size="small" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
                <WallpaperIcon />
              </IconButton>
              <IconButton size="small" onClick={handleOpenSvgEditor}>
                <CodeIcon />
              </IconButton>
              <Button size="small" onClick={handleResetView}>Нулирай</Button>
              <InfoIcon helpText={accessControlFieldsHelp.floorPlanToolMode} />
            </Box>

            <Box
              ref={viewerRef}
              sx={{
                flex: 1,
                position: 'relative',
                bgcolor: '#f5f5f5',
                borderRadius: 1,
                overflow: 'hidden',
                cursor: toolMode === 'pan' ? 'grab' : toolMode === 'add' ? 'crosshair' : draggingDoor !== null ? 'grabbing' : 'default',
              }}
              onWheel={handleWheel}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
            >
              <svg
                ref={svgRef}
                viewBox={svgViewBox}
                style={{
                  width: '100%',
                  height: '100%',
                  transform: `translate(${viewOffset.x}px, ${viewOffset.y}px) scale(${zoom})`,
                  transformOrigin: '0 0',
                  display: 'block',
                }}
                preserveAspectRatio="xMidYMid meet"
              >
                {selectedPlan.backgroundImage && (
                  <image
                    href={`/uploads/${selectedPlan.backgroundImage}`}
                    x={0} y={0}
                    width={selectedPlan.width}
                    height={selectedPlan.height}
                    preserveAspectRatio="xMidYMid meet"
                  />
                )}
                {selectedPlan.svgContent && (
                  <foreignObject x={0} y={0} width={selectedPlan.width} height={selectedPlan.height}>
                    <div
                      dangerouslySetInnerHTML={{ __html: selectedPlan.svgContent }}
                      style={{ width: selectedPlan.width, height: selectedPlan.height }}
                    />
                  </foreignObject>
                )}
                {doorsLocal.map((door, idx) => (
                  <g
                    key={door.id}
                    onMouseDown={(e) => handleDoorMouseDown(e, door)}
                    onContextMenu={(e) => handleDoorContext(e, door)}
                    style={{ cursor: toolMode === 'select' ? 'pointer' : 'default' }}
                  >
                    <rect
                      x={door.x}
                      y={door.y}
                      width={door.width}
                      height={door.height}
                      fill={DOOR_COLORS[idx % DOOR_COLORS.length]}
                      opacity={0.8}
                      stroke="#fff"
                      strokeWidth={1}
                      transform={`rotate(${door.rotation}, ${door.x + door.width / 2}, ${door.y + door.height / 2})`}
                    />
                    {door.label && (
                      <text
                        x={door.x + door.width / 2}
                        y={door.y - 5}
                        textAnchor="middle"
                        fontSize={12}
                        fill="#333"
                      >
                        {door.label}
                      </text>
                    )}
                  </g>
                ))}
              </svg>
            </Box>
          </>
        ) : (
          <Typography variant="body1" color="text.secondary" sx={{ m: 'auto' }}>
            Изберете етаж от списъка
          </Typography>
        )}
      </Paper>

      <Menu
        open={!!contextMenu}
        onClose={() => setContextMenu(null)}
        anchorReference="anchorPosition"
        anchorPosition={contextMenu ? { top: contextMenu.y, left: contextMenu.x } : undefined}
      >
        <MenuItem onClick={handleDoorProps}>
          <ListItemIcon><TuneIcon fontSize="small" /></ListItemIcon>
          Свойства
        </MenuItem>
        <MenuItem onClick={handleRotateDoor}>
          <ListItemIcon><RotateIcon fontSize="small" /></ListItemIcon>
          Завърти на 90°
        </MenuItem>
        <MenuItem onClick={handleRemoveDoor}>
          <ListItemIcon><DeleteIcon fontSize="small" /></ListItemIcon>
          Премахни врата
        </MenuItem>
      </Menu>

      <Dialog open={!!propsDoor} onClose={() => setPropsDoor(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Свойства на врата</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <ValidatedTextField
              label="Надпис"
              value={propsForm.label}
              onChange={(v) => setPropsForm((f) => ({ ...f, label: v }))}
              size="medium"
            />
            <Box sx={{ display: 'flex', gap: 2 }}>
              <ValidatedTextField
                label="Ширина"
                value={String(propsForm.width)}
                onChange={(v) => setPropsForm((f) => ({ ...f, width: parseFloat(v) || 0 }))}
                size="medium"
              />
              <ValidatedTextField
                label="Височина"
                value={String(propsForm.height)}
                onChange={(v) => setPropsForm((f) => ({ ...f, height: parseFloat(v) || 0 }))}
                size="medium"
              />
            </Box>
            <ValidatedTextField
              label="Завъртане (градуси)"
              value={String(propsForm.rotation)}
              onChange={(v) => setPropsForm((f) => ({ ...f, rotation: parseFloat(v) || 0 }))}
              size="medium"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPropsDoor(null)}>Отказ</Button>
          <Button onClick={handleSaveDoorProps} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={svgEditorOpen} onClose={() => setSvgEditorOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>SVG редактор</DialogTitle>
        <DialogContent>
          <Box
            component="textarea"
            sx={{
              width: '100%',
              minHeight: 300,
              fontFamily: 'monospace',
              fontSize: 13,
              p: 1,
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
            }}
            value={svgEditContent}
            onChange={(e) => setSvgEditContent(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSvgEditorOpen(false)}>Отказ</Button>
          <Button onClick={handleSaveSvg} variant="contained">Запази</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={doorSelectOpen} onClose={() => setDoorSelectOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Избери врата</DialogTitle>
        <DialogContent dividers sx={{ minHeight: 200 }}>
          {!doorsList?.accessDoors || doorsList.accessDoors.length === 0 ? (
            <Typography color="text.secondary">Няма налични врати за достъп</Typography>
          ) : (
            <List dense>
              {doorsList.accessDoors.map((door: { id: number; name: string; doorId: string; zone?: { name: string } | null }) => (
                <ListItem key={door.id} disablePadding>
                  <ListItemButton
                    onClick={() => {
                      if (!pendingDoorPos || !selectedId) return;
                      addDoor({
                        variables: {
                          input: {
                            floorPlanId: selectedId,
                            doorId: door.id,
                            x: pendingDoorPos.x,
                            y: pendingDoorPos.y,
                            width: 20,
                            height: 5,
                            rotation: 0,
                          },
                        },
                      }).then(() => {
                        refetchDoors();
                        showSuccess('Вратата е добавена');
                      }).catch((err) => showError(getErrorMessage(err)));
                      setDoorSelectOpen(false);
                      setPendingDoorPos(null);
                    }}
                  >
                    <ListItemText primary={door.name} secondary={`ID: ${door.doorId}${door.zone ? ` — ${door.zone.name}` : ''}`} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDoorSelectOpen(false); setPendingDoorPos(null); }}>Отказ</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)}>
        <DialogTitle>Нов етаж</DialogTitle>
        <DialogContent>
          <ValidatedTextField
            autoFocus
            label="Име на етажа"
            value={newName}
            onChange={(v) => setNewName(v)}
            size="medium"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Отказ</Button>
          <Button onClick={handleCreate} variant="contained">Създай</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FloorPlanPage;
