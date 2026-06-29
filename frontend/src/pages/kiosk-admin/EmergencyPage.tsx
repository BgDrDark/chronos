import React from 'react';
import {
  Typography, Card, CardContent, Box,
} from '@mui/material';
import { useQuery } from '@apollo/client';
import { GATEWAYS_QUERY } from '../../graphql/queries/kioskAdmin';
import { EmergencyControl } from './dialogs/EmergencyControl';

const EmergencyPage: React.FC = () => {
  const { data: gatewaysData, refetch: refetchGateways } = useQuery(GATEWAYS_QUERY);

  return (
    <Box>
      <EmergencyControl
        currentMode={gatewaysData?.gateways?.[0]?.systemMode || 'normal'}
        onAction={() => refetchGateways()}
      />
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="body2" color="text.secondary">
            Текущият режим на системата се прилага за всички свързани gateways и терминали.
            Използвайте бутоните за аварийно отключване или пълна блокада при необходимост.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default EmergencyPage;
