import React, { useState, useMemo } from 'react';
import { Container, Typography, Paper, Box, Divider, List, ListItem, ListItemText, Tabs, Tab, CircularProgress, TextField, InputAdornment, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import SearchIcon from '@mui/icons-material/Search';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PeopleIcon from '@mui/icons-material/People';
import QrCodeScannerIcon from '@mui/icons-material/QrCodeScanner';
import PaymentsIcon from '@mui/icons-material/Payments';
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff';
import WarehouseIcon from '@mui/icons-material/Warehouse';
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar';
import SecurityIcon from '@mui/icons-material/Security';
import FolderIcon from '@mui/icons-material/Folder';
import { useQuery } from '@apollo/client';
import { ME_QUERY } from '../graphql/queries';
import { GET_DOCUMENTATION_CATEGORIES } from '../graphql/documentation';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const getIconComponent = (iconName: string) => {
  const icons: Record<string, React.ReactElement> = {
    people: <PeopleIcon />,
    time: <QrCodeScannerIcon />,
    leave: <FlightTakeoffIcon />,
    payroll: <PaymentsIcon />,
    warehouse: <WarehouseIcon />,
    fleet: <DirectionsCarIcon />,
    access: <SecurityIcon />,
    help: <HelpOutlineIcon />,
    folder: <FolderIcon />,
  };
  return icons[iconName] || <FolderIcon />;
};

const DocumentationPage: React.FC = () => {
  const { loading: meLoading } = useQuery(ME_QUERY);
  const { data: docData, loading: docLoading } = useQuery(GET_DOCUMENTATION_CATEGORIES);
  const [tabValue, setTabValue] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');

  const categories = docData?.documentationCategories?.filter((c: any) => c.isActive) || [];
  
  const filteredCategories = useMemo(() => {
    if (!searchQuery.trim()) return categories;
    
    const query = searchQuery.toLowerCase();
    return categories.map((category: any) => ({
      ...category,
      articles: category.articles?.filter((article: any) => 
        article.isActive && (
          article.title.toLowerCase().includes(query) ||
          article.content.toLowerCase().includes(query)
        )
      ) || []
    })).filter((category: any) => category.articles.length > 0);
  }, [categories, searchQuery]);
  
  if (meLoading || docLoading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 4, gap: 2 }}>
        <HelpOutlineIcon color="primary" sx={{ fontSize: 40 }} />
        <Typography variant="h4" fontWeight="bold">Документация</Typography>
      </Box>

      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Търсене в документацията..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Paper>

      <Paper sx={{ borderRadius: 3 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}
        >
          {filteredCategories.map((category: any, index: number) => (
            <Tab 
              key={category.id}
              icon={getIconComponent(category.icon)} 
              label={category.title} 
              iconPosition="start" 
            />
          ))}
        </Tabs>

        <Box sx={{ p: 3 }}>
          {filteredCategories.map((category: any, index: number) => (
            <TabPanel key={category.id} value={tabValue} index={index}>
              <Typography variant="h5" gutterBottom color="primary" fontWeight="bold">
                {category.title}
              </Typography>
              
              {category.articles?.map((article: any) => (
                <Accordion key={article.id} sx={{ mb: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6" fontWeight="bold">{article.title}</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box 
                      sx={{ 
                        '& h1, & h2, & h3': { mt: 2, mb: 1 },
                        '& ul, & ol': { pl: 3 },
                        '& blockquote': { borderLeft: 3, borderColor: 'divider', pl: 2, ml: 0, fontStyle: 'italic' },
                        '& code': { bgcolor: 'grey.100', px: 0.5, borderRadius: 1, fontFamily: 'monospace' },
                        '& pre': { bgcolor: 'grey.100', p: 2, borderRadius: 1, overflow: 'auto' },
                        '& pre code': { bgcolor: 'transparent', p: 0 },
                        '& img': { maxWidth: '100%', height: 'auto', my: 2 },
                        '& a': { color: 'primary.main' },
                      }}
                      dangerouslySetInnerHTML={{ __html: article.content }}
                    />
                  </AccordionDetails>
                </Accordion>
              ))}

              {(!category.articles || category.articles.length === 0) && (
                <Typography color="text.secondary" sx={{ mt: 2 }}>
                  Няма налични статии в тази категория.
                </Typography>
              )}
            </TabPanel>
          ))}

          {filteredCategories.length === 0 && (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">
                {searchQuery ? 'Няма намерени резултати за вашето търсене.' : 'Няма налична документация.'}
              </Typography>
            </Box>
          )}
        </Box>
      </Paper>

      <Box sx={{ mt: 4, p: 3, bgcolor: 'primary.light', color: 'primary.contrastText', borderRadius: 2 }}>
        <Typography variant="h6" gutterBottom>📞 Нужда от помощ?</Typography>
        <Typography variant="body1">
          Ако имате проблеми или въпроси, свържете се с:
        </Typography>
        <Typography variant="body1" sx={{ mt: 1 }}>
          • Вашия ръководител<br />
          • Системния администратор<br />
          • Имейл: admin@example.com
        </Typography>
      </Box>

      <Box sx={{ mt: 4, p: 2, bgcolor: 'action.hover', borderRadius: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" align="center">
            © {new Date().getFullYear()} Chronos - Работно Време. Всички права запазени.
        </Typography>
      </Box>
    </Container>
  );
};

export default DocumentationPage;
