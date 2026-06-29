import React from 'react';
import { Box, Container, Typography } from '@mui/material';

const AccessControlLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom fontWeight="bold">Контрол на Достъпа</Typography>
      <Box sx={{ mb: 3 }}>
        {children}
      </Box>
    </Container>
  );
};

export default AccessControlLayout;
