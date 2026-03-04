import React, { useState, useEffect } from 'react';
import { 
  Card, CardContent, Typography, Switch, 
  CircularProgress, Alert, Divider, List, ListItem, ListItemText
} from '@mui/material';
import ViewModuleIcon from '@mui/icons-material/ViewModule';
import { useQuery, gql } from '@apollo/client';
import axios from 'axios';

interface ModuleData {
  id: number;
  code: string;
  isEnabled: boolean;
  name: string;
  description: string;
}

const MODULES_QUERY = gql`
  query GetModules {
    modules {
      id
      code
      isEnabled
      name
      description
    }
  }
`;

const ModuleManager: React.FC = () => {
  const { data, loading, error, refetch } = useQuery(MODULES_QUERY);
  const [updating, setUpdating] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [modules, setModules] = useState<ModuleData[]>([]);

  useEffect(() => {
    if (data?.modules) {
      setModules(data.modules);
    }
  }, [data]);

  const handleToggle = async (code: string, currentStatus: boolean) => {
    if (code === 'shifts' && currentStatus) {
        setMsg({ type: 'error', text: "Основният модул 'Работно време' не може да бъде деактивиран." });
        setTimeout(() => setMsg(null), 3000);
        return;
    }

    setUpdating(code);
    try {
      const token = localStorage.getItem('token');
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:14240';
      const newStatus = !currentStatus;
      
      await axios.patch(`${apiUrl}/system/modules/${code}`, 
        { is_enabled: newStatus },
        { 
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          } 
        }
      );
      
      // Update local state immediately
      const updatedModules = modules.map(m => 
        m.code === code ? { ...m, isEnabled: newStatus } : m
      );
      setModules(updatedModules);
      
      setMsg({ type: 'success', text: `Модулът '${code}' е актуализиран.` });
      await refetch();
      setTimeout(() => setMsg(null), 3000);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail;
      setMsg({ 
        type: 'error', 
        text: typeof errorMsg === 'string' ? errorMsg : (errorMsg?.message || err.message) 
      });
    } finally {
      setUpdating(null);
    }
  };

  if (loading) return <CircularProgress size={24} />;
  if (error) return <Alert severity="error">Грешка при зареждане на модулите: {error.message}</Alert>;

  const displayModules = modules.length > 0 ? modules : data?.modules || [];

  return (
    <Card sx={{ mb: 4, border: '1px solid #4caf50' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom color="success.main" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ViewModuleIcon /> Управление на модули
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Активирайте или деактивирайте системни функционалности. Деактивирането на модул скрива неговите менюта и блокира достъпа до API ендпоинтите му.
        </Typography>

        {msg && <Alert severity={msg.type} sx={{ mb: 2 }}>{msg.text}</Alert>}

        <List>
          {displayModules.map((mod: any) => (
            <React.Fragment key={mod.id}>
              <ListItem
                secondaryAction={
                  <Switch
                    edge="end"
                    onChange={() => handleToggle(mod.code, mod.isEnabled)}
                    checked={mod.isEnabled}
                    disabled={updating === mod.code}
                  />
                }
              >
                <ListItemText
                  primary={mod.name}
                  secondary={mod.description}
                  primaryTypographyProps={{ fontWeight: 'bold' }}
                />
                {updating === mod.code && <CircularProgress size={20} sx={{ ml: 2 }} />}
              </ListItem>
              <Divider component="li" />
            </React.Fragment>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default ModuleManager;
