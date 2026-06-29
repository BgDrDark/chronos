import React from 'react';
import { Box, Container, Typography } from '@mui/material';

const KioskAdminLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom fontWeight="bold">Терминали и устройства</Typography>
      <Box sx={{ mb: 3 }}>
        {children}
      </Box>
    </Container>
  );
};

export default KioskAdminLayout;
