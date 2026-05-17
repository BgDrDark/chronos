import React from 'react';
import { Container, Box, Typography } from '@mui/material';
import ScheduleGrid from '../components/ScheduleGrid';
import ScheduleCalendar from '../components/ScheduleCalendar';
import ScheduleSettings from '../components/ScheduleSettings';
import TemplatePreviewModal from '../components/TemplatePreviewModal';

interface Props {
  tab?: string;
}

const SchedulesPage: React.FC<Props> = ({ tab }) => {
  const [previewOpen, setPreviewOpen] = React.useState(false);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight="bold">Работни графици</Typography>
      </Box>
      {tab === 'grid' && <ScheduleGrid onOpenTemplatePreview={() => setPreviewOpen(true)} />}
      {tab === 'calendar' && <ScheduleCalendar />}
      {tab === 'settings' && <ScheduleSettings />}
      <TemplatePreviewModal open={previewOpen} onClose={() => setPreviewOpen(false)} />
    </Container>
  );
};

export default SchedulesPage;
