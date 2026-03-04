import React from 'react';
import { Box, Typography } from '@mui/material';
import { getShiftIcon } from '../utils/shiftUtils';

interface ShiftEventContentProps {
  eventInfo: any;
  minimal?: boolean;
}

const ShiftEventContent: React.FC<ShiftEventContentProps> = ({ eventInfo, minimal = false }) => {
  const props = eventInfo.event.extendedProps;
  const isHoliday = props.isHoliday;
  const isLog = props.isLog;
  const isManual = props.isManual;
  
  // Determine Type for Icon
  let type = 'regular';
  if (isHoliday) type = 'public_holiday';
  else if (isLog) type = isManual ? 'manual_log' : 'auto_log';
  else if (props.shiftType) type = props.shiftType;

  // Custom styling for holidays
  if (isHoliday) {
    return (
      <Box sx={{ 
        p: 0.5, 
        height: '100%', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        textAlign: 'center',
        gap: 0.5,
        color: '#c62828',
        backgroundColor: '#fff5f5',
        borderRadius: 1,
        border: '1px solid #ffcdd2'
      }}>
        {getShiftIcon('public_holiday', { style: { fontSize: '0.9rem', color: '#c62828' } })}
        {!minimal && (
          <Typography variant="caption" sx={{ fontWeight: 'bold', fontSize: '0.75rem', lineHeight: 1.1 }}>
            {eventInfo.event.title}
          </Typography>
        )}
      </Box>
    );
  }

  return (
    <Box sx={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: 0.5, 
      overflow: 'hidden', 
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
      px: 0.5,
      width: '100%',
      color: 'white', // Text is usually on colored background
      justifyContent: minimal ? 'center' : 'flex-start'
    }}>
      {/* Icon */}
      <Box component="span" sx={{ display: 'flex', alignItems: 'center' }}>
        {getShiftIcon(type, { style: { fontSize: '0.85rem', color: 'inherit' } })}
      </Box>

      {/* Time Range (if available and NOT a log, or if it is a log show times too) */}
      {!minimal && (props.startTime || isLog) && (
         <Typography variant="caption" sx={{ fontSize: '0.7rem', opacity: 0.9, minWidth: 'fit-content' }}>
            {isLog 
                ? `${eventInfo.timeText}` // FullCalendar handles time text for logs usually
                : `${props.startTime.substring(0, 5)}-${props.endTime.substring(0, 5)}`
            }
         </Typography>
      )}

      {/* Title / User Name */}
      {!minimal && (
        <Typography variant="caption" sx={{ fontWeight: 'bold', fontSize: '0.75rem', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {eventInfo.event.title}
        </Typography>
      )}
    </Box>
  );
};

export default ShiftEventContent;
