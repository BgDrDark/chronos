import React from 'react';
import { Box, Chip, Tooltip } from '@mui/material';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import SlowMotionVideoIcon from '@mui/icons-material/SlowMotionVideo';
import { useNetworkStatus } from '../hooks/useNetworkStatus';
import { useBackgroundSync } from '../hooks/useBackgroundSync';

export const OfflineIndicator: React.FC = () => {
  const { isOnline, connectionType, isSlowConnection } = useNetworkStatus();
  const { pendingCount } = useBackgroundSync();

  if (isOnline && !isSlowConnection && pendingCount === 0) return null;

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      {!isOnline && (
        <Tooltip title="Няма интернет връзка. Данните се записват локално.">
          <Chip
            icon={<WifiOffIcon />}
            label="Офлайн"
            size="small"
            color="error"
            variant="filled"
          />
        </Tooltip>
      )}
      {isSlowConnection && isOnline && (
        <Tooltip title={`Бавен интернет (${connectionType}). Олекотен режим.`}>
          <Chip
            icon={<SlowMotionVideoIcon />}
            label={`2G`}
            size="small"
            color="warning"
            variant="filled"
          />
        </Tooltip>
      )}
      {pendingCount > 0 && (
        <Tooltip title={`${pendingCount} записа чакат синхронизация`}>
          <Chip
            label={`${pendingCount} за синхр.`}
            size="small"
            color="info"
            variant="outlined"
          />
        </Tooltip>
      )}
    </Box>
  );
};
