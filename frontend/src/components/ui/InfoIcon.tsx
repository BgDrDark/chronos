import { Info as InfoIconMUI } from '@mui/icons-material';
import { Popover, Typography, Box, IconButton } from '@mui/material';
import { useState, MouseEvent } from 'react';

interface InfoIconProps {
  helpText: string;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  size?: 'default' | 'smaller';
}

export const InfoIcon: React.FC<InfoIconProps> = ({ helpText, placement = 'right', size = 'default' }) => {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  const handleClick = (event: MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };

  const handleClose = (event: MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);

  const getAnchorOrigin = () => {
    switch (placement) {
      case 'top':
        return { vertical: 'bottom' as const, horizontal: 'center' as const };
      case 'bottom':
        return { vertical: 'top' as const, horizontal: 'center' as const };
      case 'left':
        return { vertical: 'center' as const, horizontal: 'right' as const };
      case 'right':
        return { vertical: 'bottom' as const, horizontal: 'left' as const };
      default:
        return { vertical: 'bottom' as const, horizontal: 'left' as const };
    }
  };

  const getTransformOrigin = () => {
    switch (placement) {
      case 'top':
        return { vertical: 'top' as const, horizontal: 'center' as const };
      case 'bottom':
        return { vertical: 'bottom' as const, horizontal: 'center' as const };
      case 'left':
        return { vertical: 'center' as const, horizontal: 'left' as const };
      case 'right':
        return { vertical: 'top' as const, horizontal: 'right' as const };
      default:
        return { vertical: 'top' as const, horizontal: 'right' as const };
    }
  };

  return (
    <>
      <IconButton
        size="small"
        onClick={handleClick}
        sx={{ p: 0.25, color: 'info.main', cursor: 'pointer', '& .MuiSvgIcon-root': { fontSize: size === 'smaller' ? '0.75rem' : '1rem' } }}
        aria-label="Помощна информация"
      >
        <InfoIconMUI />
      </IconButton>
      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={getAnchorOrigin()}
        transformOrigin={getTransformOrigin()}
        slotProps={{
          paper: {
            sx: {
              bgcolor: 'info.main',
              color: 'info.contrastText',
              maxWidth: 280,
              boxShadow: 2,
            }
          }
        }}
        disableRestoreFocus
      >
        <Box sx={{ p: 1 }}>
          <Typography variant="caption" sx={{ fontSize: '0.75rem', lineHeight: 1.3 }}>{helpText}</Typography>
        </Box>
      </Popover>
    </>
  );
};

export default InfoIcon;
