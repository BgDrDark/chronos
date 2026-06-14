import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemButton,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  DragIndicator as DragIcon,
  Article as ArticleIcon,
  Folder as FolderIcon,
  People as PeopleIcon,
  AccessTime as TimeIcon,
  FlightTakeoff as LeaveIcon,
  Payments as PayrollIcon,
  Inventory as WarehouseIcon,
  DirectionsCar as FleetIcon,
  Security as AccessIcon,
  Help as HelpIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@apollo/client';
import RichTextEditor from '../components/RichTextEditor';
import {
  GET_DOCUMENTATION_CATEGORIES,
  CREATE_DOCUMENTATION_CATEGORY,
  UPDATE_DOCUMENTATION_CATEGORY,
  DELETE_DOCUMENTATION_CATEGORY,
  CREATE_DOCUMENTATION_ARTICLE,
  UPDATE_DOCUMENTATION_ARTICLE,
  DELETE_DOCUMENTATION_ARTICLE,
} from '../graphql/documentation';

const ICON_OPTIONS = [
  { value: 'people', label: 'Персонал', icon: <PeopleIcon /> },
  { value: 'time', label: 'Часове', icon: <TimeIcon /> },
  { value: 'leave', label: 'Отпуски', icon: <LeaveIcon /> },
  { value: 'payroll', label: 'Заплати', icon: <PayrollIcon /> },
  { value: 'warehouse', label: 'Склад', icon: <WarehouseIcon /> },
  { value: 'fleet', label: 'Автопарк', icon: <FleetIcon /> },
  { value: 'access', label: 'Достъп', icon: <AccessIcon /> },
  { value: 'help', label: 'Помощ', icon: <HelpIcon /> },
  { value: 'folder', label: 'Папка', icon: <FolderIcon /> },
];

const getIconComponent = (iconName: string) => {
  const found = ICON_OPTIONS.find((opt) => opt.value === iconName);
  return found ? found.icon : <FolderIcon />;
};

const AdminDocumentationPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [selectedArticle, setSelectedArticle] = useState<number | null>(null);
  const [categoryDialogOpen, setCategoryDialogOpen] = useState(false);
  const [articleDialogOpen, setArticleDialogOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<any>(null);
  const [editingArticle, setEditingArticle] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const [categoryForm, setCategoryForm] = useState({
    title: '',
    icon: 'folder',
    order: 0,
    isActive: true,
  });

  const [articleForm, setArticleForm] = useState({
    title: '',
    content: '',
    order: 0,
    isActive: true,
  });

  const { data, loading, refetch } = useQuery(GET_DOCUMENTATION_CATEGORIES);

  const [createCategory] = useMutation(CREATE_DOCUMENTATION_CATEGORY);
  const [updateCategory] = useMutation(UPDATE_DOCUMENTATION_CATEGORY);
  const [deleteCategory] = useMutation(DELETE_DOCUMENTATION_CATEGORY);
  const [createArticle] = useMutation(CREATE_DOCUMENTATION_ARTICLE);
  const [updateArticle] = useMutation(UPDATE_DOCUMENTATION_ARTICLE);
  const [deleteArticle] = useMutation(DELETE_DOCUMENTATION_ARTICLE);

  const categories = data?.documentationCategories || [];
  const currentCategory = categories.find((c: any) => c.id === selectedCategory);
  const articles = currentCategory?.articles || [];
  const currentArticle = articles.find((a: any) => a.id === selectedArticle);

  const handleCategoryClick = (categoryId: number) => {
    setSelectedCategory(categoryId);
    setSelectedArticle(null);
  };

  const handleArticleClick = (articleId: number) => {
    setSelectedArticle(articleId);
    const article = articles.find((a: any) => a.id === articleId);
    if (article) {
      setArticleForm({
        title: article.title,
        content: article.content,
        order: article.order,
        isActive: article.isActive,
      });
    }
  };

  const handleCreateCategory = () => {
    setEditingCategory(null);
    setCategoryForm({ title: '', icon: 'folder', order: categories.length, isActive: true });
    setCategoryDialogOpen(true);
  };

  const handleEditCategory = (category: any) => {
    setEditingCategory(category);
    setCategoryForm({
      title: category.title,
      icon: category.icon,
      order: category.order,
      isActive: category.isActive,
    });
    setCategoryDialogOpen(true);
  };

  const handleSaveCategory = async () => {
    try {
      setError(null);
      if (editingCategory) {
        await updateCategory({
          variables: { id: editingCategory.id, input: categoryForm },
        });
      } else {
        await createCategory({ variables: { input: categoryForm } });
      }
      setCategoryDialogOpen(false);
      refetch();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteCategory = async (id: number) => {
    if (window.confirm('Сигурни ли сте, че искате да изтриете тази категория?')) {
      try {
        setError(null);
        await deleteCategory({ variables: { id } });
        if (selectedCategory === id) {
          setSelectedCategory(null);
          setSelectedArticle(null);
        }
        refetch();
      } catch (err: any) {
        setError(err.message);
      }
    }
  };

  const handleCreateArticle = () => {
    if (!selectedCategory) {
      setError('Моля, изберете категория първо');
      return;
    }
    setEditingArticle(null);
    setArticleForm({ title: '', content: '', order: articles.length, isActive: true });
    setArticleDialogOpen(true);
  };

  const handleSaveArticle = async () => {
    try {
      setError(null);
      if (editingArticle) {
        await updateArticle({
          variables: { id: editingArticle.id, input: { ...articleForm, categoryId: selectedCategory } },
        });
      } else {
        await createArticle({
          variables: { input: { ...articleForm, categoryId: selectedCategory } },
        });
      }
      setArticleDialogOpen(false);
      refetch();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteArticle = async (id: number) => {
    if (window.confirm('Сигурни ли сте, че искате да изтриете тази статия?')) {
      try {
        setError(null);
        await deleteArticle({ variables: { id } });
        if (selectedArticle === id) {
          setSelectedArticle(null);
        }
        refetch();
      } catch (err: any) {
        setError(err.message);
      }
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Управление на документацията
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'flex', gap: 2, height: 'calc(100vh - 200px)' }}>
        {/* Categories Panel */}
        <Paper sx={{ width: 300, display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: 1, borderColor: 'divider' }}>
            <Typography variant="h6">Категории</Typography>
            <IconButton onClick={handleCreateCategory} color="primary">
              <AddIcon />
            </IconButton>
          </Box>
          <List sx={{ flex: 1, overflow: 'auto' }}>
            {categories.map((category: any) => (
              <ListItem
                key={category.id}
                disablePadding
                secondaryAction={
                  <Box>
                    <IconButton edge="end" size="small" onClick={() => handleEditCategory(category)}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton edge="end" size="small" onClick={() => handleDeleteCategory(category.id)}>
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                }
              >
                <ListItemButton selected={selectedCategory === category.id} onClick={() => handleCategoryClick(category.id)}>
                  <ListItemIcon>{getIconComponent(category.icon)}</ListItemIcon>
                  <ListItemText primary={category.title} secondary={`${category.articles?.length || 0} статии`} />
                </ListItemButton>
              </ListItem>
            ))}
            {categories.length === 0 && (
              <ListItem>
                <ListItemText secondary="Няма категории" />
              </ListItem>
            )}
          </List>
        </Paper>

        {/* Articles Panel */}
        <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {selectedCategory ? (
            <>
              <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: 1, borderColor: 'divider' }}>
                <Typography variant="h6">{currentCategory?.title} - Статии</Typography>
                <Button startIcon={<AddIcon />} onClick={handleCreateArticle} variant="contained" size="small">
                  Нова статия
                </Button>
              </Box>
              <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
                {articles.length === 0 ? (
                  <Typography color="text.secondary">Няма статии в тази категория</Typography>
                ) : (
                  <List>
                    {articles.map((article: any) => (
                      <ListItem
                        key={article.id}
                        disablePadding
                        secondaryAction={
                          <IconButton edge="end" onClick={() => handleDeleteArticle(article.id)}>
                            <DeleteIcon />
                          </IconButton>
                        }
                      >
                        <ListItemButton selected={selectedArticle === article.id} onClick={() => handleArticleClick(article.id)}>
                          <ListItemIcon>
                            <DragIcon />
                          </ListItemIcon>
                          <ListItemIcon>
                            <ArticleIcon />
                          </ListItemIcon>
                          <ListItemText
                            primary={article.title}
                            secondary={`Поредност: ${article.order} | ${article.isActive ? 'Активна' : 'Неактивна'}`}
                          />
                        </ListItemButton>
                      </ListItem>
                    ))}
                  </List>
                )}
              </Box>
            </>
          ) : (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
              <Typography color="text.secondary">Изберете категория, за да видите статиите</Typography>
            </Box>
          )}
        </Paper>

        {/* Article Editor Panel */}
        {selectedArticle && currentArticle && (
          <Paper sx={{ width: 500, display: 'flex', flexDirection: 'column', p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Редактиране на статия
            </Typography>
            <TextField
              label="Заглавие"
              value={articleForm.title}
              onChange={(e) => setArticleForm({ ...articleForm, title: e.target.value })}
              fullWidth
              sx={{ mb: 2 }}
            />
            <TextField
              label="Поредност"
              type="number"
              value={articleForm.order}
              onChange={(e) => setArticleForm({ ...articleForm, order: parseInt(e.target.value) })}
              fullWidth
              sx={{ mb: 2 }}
            />
            <FormControlLabel
              control={<Switch checked={articleForm.isActive} onChange={(e) => setArticleForm({ ...articleForm, isActive: e.target.checked })} />}
              label="Активна"
              sx={{ mb: 2 }}
            />
            <Typography variant="subtitle2" gutterBottom>
              Съдържание
            </Typography>
            <RichTextEditor
              content={articleForm.content}
              onChange={(html) => setArticleForm({ ...articleForm, content: html })}
              placeholder="Напишете съдържанието на статията..."
            />
            <Box sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <Button onClick={() => setSelectedArticle(null)}>Отказ</Button>
              <Button variant="contained" onClick={handleSaveArticle}>
                Запази
              </Button>
            </Box>
          </Paper>
        )}
      </Box>

      {/* Category Dialog */}
      <Dialog open={categoryDialogOpen} onClose={() => setCategoryDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingCategory ? 'Редактиране на категория' : 'Нова категория'}</DialogTitle>
        <DialogContent>
          <TextField
            label="Заглавие"
            value={categoryForm.title}
            onChange={(e) => setCategoryForm({ ...categoryForm, title: e.target.value })}
            fullWidth
            sx={{ mt: 2, mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Икона</InputLabel>
            <Select
              value={categoryForm.icon}
              label="Икона"
              onChange={(e) => setCategoryForm({ ...categoryForm, icon: e.target.value })}
            >
              {ICON_OPTIONS.map((opt) => (
                <MenuItem key={opt.value} value={opt.value}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {opt.icon}
                    {opt.label}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            label="Поредност"
            type="number"
            value={categoryForm.order}
            onChange={(e) => setCategoryForm({ ...categoryForm, order: parseInt(e.target.value) })}
            fullWidth
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={<Switch checked={categoryForm.isActive} onChange={(e) => setCategoryForm({ ...categoryForm, isActive: e.target.checked })} />}
            label="Активна"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCategoryDialogOpen(false)}>Отказ</Button>
          <Button onClick={handleSaveCategory} variant="contained">
            Запази
          </Button>
        </DialogActions>
      </Dialog>

      {/* Article Dialog */}
      <Dialog open={articleDialogOpen} onClose={() => setArticleDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Нова статия</DialogTitle>
        <DialogContent>
          <TextField
            label="Заглавие"
            value={articleForm.title}
            onChange={(e) => setArticleForm({ ...articleForm, title: e.target.value })}
            fullWidth
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            label="Поредност"
            type="number"
            value={articleForm.order}
            onChange={(e) => setArticleForm({ ...articleForm, order: parseInt(e.target.value) })}
            fullWidth
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={<Switch checked={articleForm.isActive} onChange={(e) => setArticleForm({ ...articleForm, isActive: e.target.checked })} />}
            label="Активна"
            sx={{ mb: 2 }}
          />
          <Typography variant="subtitle2" gutterBottom>
            Съдържание
          </Typography>
          <RichTextEditor
            content={articleForm.content}
            onChange={(html) => setArticleForm({ ...articleForm, content: html })}
            placeholder="Напишете съдържанието на статията..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setArticleDialogOpen(false)}>Отказ</Button>
          <Button onClick={handleSaveArticle} variant="contained">
            Запази
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdminDocumentationPage;
