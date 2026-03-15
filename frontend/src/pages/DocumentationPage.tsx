import React, { useState } from 'react';
import { Container, Typography, Paper, Box, Divider, List, ListItem, ListItemText, Tabs, Tab, CircularProgress } from '@mui/material';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import QrCodeScannerIcon from '@mui/icons-material/QrCodeScanner';
import PaymentsIcon from '@mui/icons-material/Payments';
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff';
import WarehouseIcon from '@mui/icons-material/Warehouse';
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar';
import SecurityIcon from '@mui/icons-material/Security';
import PeopleIcon from '@mui/icons-material/People';
import { useQuery } from '@apollo/client';
import { ME_QUERY } from '../graphql/queries';

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

const DocumentationPage: React.FC = () => {
  const { loading } = useQuery(ME_QUERY);
  const [tabValue, setTabValue] = useState(0);
  
  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 4, gap: 2 }}>
        <HelpOutlineIcon color="primary" sx={{ fontSize: 40 }} />
        <Typography variant="h4" fontWeight="bold">Документация</Typography>
      </Box>

      <Paper sx={{ borderRadius: 3 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}
        >
          <Tab icon={<PeopleIcon />} label="Персонал" iconPosition="start" />
          <Tab icon={<QrCodeScannerIcon />} label="Часове" iconPosition="start" />
          <Tab icon={<FlightTakeoffIcon />} label="Отпуски" iconPosition="start" />
          <Tab icon={<PaymentsIcon />} label="Заплати" iconPosition="start" />
          <Tab icon={<WarehouseIcon />} label="Склад" iconPosition="start" />
          <Tab icon={<DirectionsCarIcon />} label="Автопарк" iconPosition="start" />
          <Tab icon={<SecurityIcon />} label="Достъп" iconPosition="start" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {/* TAB 1: ПЕРСОНАЛ */}
          <TabPanel value={tabValue} index={0}>
            <Typography variant="h5" gutterBottom color="primary" fontWeight="bold">Управление на персонала</Typography>
            
            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Създаване на нов служител</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в меню 'Служители'" /></ListItem>
              <ListItem><ListItemText primary="2. Натискате бутон 'Нов потребител'" /></ListItem>
              <ListItem><ListItemText primary="3. Попълвате данните: име, фамилия, email, телефон" /></ListItem>
              <ListItem><ListItemText primary="4. Задавате роля и отдел" /></ListItem>
              <ListItem><ListItemText primary="5. Запазвате" /></ListItem>
            </List>
            <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
              Резултат: Служителят е създаден и може да влиза в системата
            </Typography>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Създаване на трудов договор</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Отдел ТРЗ' → 'Шаблони'" /></ListItem>
              <ListItem><ListItemText primary="2. Избирате шаблон за договор" /></ListItem>
              <ListItem><ListItemText primary="3. Отивате в 'Допълнителни споразумения'" /></ListItem>
              <ListItem><ListItemText primary="4. Натискате 'Нов договор'" /></ListItem>
              <ListItem><ListItemText primary="5. Избирате служител и шаблон" /></ListItem>
              <ListItem><ListItemText primary="6. Попълвате данните за договора" /></ListItem>
              <ListItem><ListItemText primary="7. Запазвате" /></ListItem>
            </List>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Задаване на график</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Графици'" /></ListItem>
              <ListItem><ListItemText primary="2. Създавате или избирате шаблон" /></ListItem>
              <ListItem><ListItemText primary="3. Прилагате шаблона към служител/служители" /></ListItem>
              <ListItem><ListItemText primary="4. Задавате период" /></ListItem>
            </List>

            <Divider sx={{ my: 4 }} />
            <Typography variant="h6" gutterBottom>Често задавани въпроси</Typography>
            <List>
              <ListItem><ListItemText primary="❓ Как да добавя нов служител?" /></ListItem>
              <ListItem><ListItemText primary="💡 Отидете в 'Служители' и натиснете 'Нов потребител'" /></ListItem>
              <ListItem><ListItemText primary="❓ Как да създам договор?" /></ListItem>
              <ListItem><ListItemText primary="💡 Отидете в 'Отдел ТРЗ' → 'Допълнителни споразумения' → 'Нов договор'" /></ListItem>
              <ListItem><ListItemText primary="❓ Как да задам график?" /></ListItem>
              <ListItem><ListItemText primary="💡 Отидете в 'Графици', създайте шаблон и го приложете" /></ListItem>
            </List>
          </TabPanel>

          {/* TAB 2: ЧАСОВЕ */}
          <TabPanel value={tabValue} index={1}>
            <Typography variant="h5" gutterBottom color="primary" fontWeight="bold">Отчитане на часовете</Typography>
            
            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Clock in / Clock out</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отворете 'Моята карта' на телефона" /></ListItem>
              <ListItem><ListItemText primary="2. Сканирате QR кода на терминала" /></ListItem>
              <ListItem><ListItemText primary="3. ИЛИ: Въведете кода си в киоска" /></ListItem>
            </List>
            <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
              Резултат: Часовете са отбелязани
            </Typography>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Ръчно отбелязване (от админ)</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Часове'" /></ListItem>
              <ListItem><ListItemText primary="2. Натискате 'Ръчно добавяне'" /></ListItem>
              <ListItem><ListItemText primary="3. Избирате служител и дата/час" /></ListItem>
              <ListItem><ListItemText primary="4. Натискате 'Вход' или 'Изход'" /></ListItem>
            </List>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Размяна на смени</Typography>
            <List>
              <ListItem><ListItemText primary="1. Служител А иска размяна с Б" /></ListItem>
              <ListItem><ListItemText primary="2. Служител Б потвърждава" /></ListItem>
              <ListItem><ListItemText primary="3. Админ одобрява" /></ListItem>
            </List>

            <Divider sx={{ my: 4 }} />
            <Typography variant="h6" gutterBottom>Често задавани въпроси</Typography>
            <List>
              <ListItem><ListItemText primary="❓ Как да си отбележа часовете?" /></ListItem>
              <ListItem><ListItemText primary="💡 Сканирайте QR кода или въведете кода на киоска" /></ListItem>
              <ListItem><ListItemText primary="❓ Забравих си кода" /></ListItem>
              <ListItem><ListItemText primary="💡 Питайте администратора да ви го покаже" /></ListItem>
              <ListItem><ListItemText primary="❓ Защо не мога да се чекирам?" /></ListItem>
              <ListItem><ListItemText primary="💡 Проверете дали имате активна смяна за днес" /></ListItem>
            </List>
          </TabPanel>

          {/* TAB 3: ОТПУСКИ */}
          <TabPanel value={tabValue} index={2}>
            <Typography variant="h5" gutterBottom color="primary" fontWeight="bold">Управление на отпуските</Typography>
            
            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Заявка за отпуск</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Отпуски'" /></ListItem>
              <ListItem><ListItemText primary="2. Натискате '+ Нова заявка'" /></ListItem>
              <ListItem><ListItemText primary="3. Избирате вид отпуск (платен, неплатен, болничен)" /></ListItem>
              <ListItem><ListItemText primary="4. Задавате начална и крайна дата" /></ListItem>
              <ListItem><ListItemText primary="5. Натискате 'Изпрати'" /></ListItem>
            </List>
            <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
              Резултат: Заявката е изпратена за одобрение
            </Typography>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Одобряване на заявка (от ръководител)</Typography>
            <List>
              <ListItem><ListItemText primary="1. Получавате известие за нова заявка" /></ListItem>
              <ListItem><ListItemText primary="2. Отивате в 'Отпуски'" /></ListItem>
              <ListItem><ListItemText primary="3. Преглеждате заявката" /></ListItem>
              <ListItem><ListItemText primary="4. Натискате 'Одобря' или 'Отхвърля'" /></ListItem>
            </List>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Баланс на отпуските</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Моят профил' или 'Отпуски'" /></ListItem>
              <ListItem><ListItemText primary="2. Виждате оставащите дни" /></ListItem>
            </List>

            <Divider sx={{ my: 4 }} />
            <Typography variant="h6" gutterBottom>Често задавани въпроси</Typography>
            <List>
              <ListItem><ListItemText primary="❓ Колко отпуск ми остава?" /></ListItem>
              <ListItem><ListItemText primary="💡 Отидете в 'Отпуски' → 'Моите заявки'" /></ListItem>
              <ListItem><ListItemText primary="❓ Защо ми отхвърлиха заявката?" /></ListItem>
              <ListItem><ListItemText primary="💡 Проверете причината в детайлите на заявката" /></ListItem>
              <ListItem><ListItemText primary="❓ Мога ли да кандидатствам за отпуск без график?" /></ListItem>
              <ListItem><ListItemText primary="💡 Не, трябва да имате задан график" /></ListItem>
            </List>
          </TabPanel>

          {/* TAB 4: ЗАПЛАТИ */}
          <TabPanel value={tabValue} index={3}>
            <Typography variant="h5" gutterBottom color="primary" fontWeight="bold">Заплати и TRZ</Typography>
            
            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Изчисляване на заплата</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Заплати'" /></ListItem>
              <ListItem><ListItemText primary="2. Избирате период (месец)" /></ListItem>
              <ListItem><ListItemText primary="3. Натискате 'Изчисли'" /></ListItem>
              <ListItem><ListItemText primary="4. Преглеждате фишовете" /></ListItem>
            </List>
            <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
              Резултат: Изчислени заплати за периода
            </Typography>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Допълнително споразумение (анекс)</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Отдел ТРЗ' → 'Допълнителни споразумения'" /></ListItem>
              <ListItem><ListItemText primary="2. Натискате 'Нов анекс'" /></ListItem>
              <ListItem><ListItemText primary="3. Избирате служител и шаблон" /></ListItem>
              <ListItem><ListItemText primary="4. Попълвате новите условия" /></ListItem>
              <ListItem><ListItemText primary="5. Натискате 'Подпиши'" /></ListItem>
            </List>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Плащане на заплати (SEPA)</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Плащания'" /></ListItem>
              <ListItem><ListItemText primary="2. Избирате периода" /></ListItem>
              <ListItem><ListItemText primary="3. Натискате 'Генерирай XML'" /></ListItem>
              <ListItem><ListItemText primary="4. Качвате XML-то в банката" /></ListItem>
            </List>

            <Divider sx={{ my: 4 }} />
            <Typography variant="h6" gutterBottom>Често задавани въпроси</Typography>
            <List>
              <ListItem><ListItemText primary="❓ Кога ще ми дойде заплатата?" /></ListItem>
              <ListItem><ListItemText primary="💡 Проверете в 'Плащания' - там е датата на плащане" /></ListItem>
              <ListItem><ListItemText primary="❓ Как да видя фиша си?" /></ListItem>
              <ListItem><ListItemText primary="💡 Отидете в 'Заплати' и качете конкретния служител" /></ListItem>
              <ListItem><ListItemText primary="❓ Какво е TRZ?" /></ListItem>
              <ListItem><ListItemText primary="💡 Трудово-правни отношения - управление на заплати, данъци, осигуровки" /></ListItem>
            </List>
          </TabPanel>

          {/* TAB 5: СКЛАД */}
          <TabPanel value={tabValue} index={4}>
            <Typography variant="h5" gutterBottom color="primary" fontWeight="bold">Склад и производство</Typography>
            
            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Управление на продукти</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Склад' → 'Продукти'" /></ListItem>
              <ListItem><ListItemText primary="2. Натискате 'Нов продукт'" /></ListItem>
              <ListItem><ListItemText primary="3. Попълвате име, количество, мярка" /></ListItem>
              <ListItem><ListItemText primary="4. Задавате склад" /></ListItem>
            </List>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Поръчка за производство</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Поръчки'" /></ListItem>
              <ListItem><ListItemText primary="2. Натискате 'Нова поръчка'" /></ListItem>
              <ListItem><ListItemText primary="3. Избирате рецепта" /></ListItem>
              <ListItem><ListItemText primary="4. Задавате количество" /></ListItem>
              <ListItem><ListItemText primary="5. Стартирате производството" /></ListItem>
            </List>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Инвентаризация</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Склад' → 'Инвентаризация'" /></ListItem>
              <ListItem><ListItemText primary="2. Натискате 'Нова сесия'" /></ListItem>
              <ListItem><ListItemText primary="3. Сканирате продуктите" /></ListItem>
              <ListItem><ListItemText primary="4. Приключвате" /></ListItem>
            </List>

            <Divider sx={{ my: 4 }} />
            <Typography variant="h6" gutterBottom>Често задавани въпроси</Typography>
            <List>
              <ListItem><ListItemText primary="❓ Как да добавя продукт?" /></ListItem>
              <ListItem><ListItemText primary="💡 Отидете в 'Склад' → 'Продукти' → 'Нов продукт'" /></ListItem>
              <ListItem><ListItemText primary="❓ Как да направя поръчка?" /></ListItem>
              <ListItem><ListItemText primary="💡 Отидете в 'Поръчки' → 'Нова поръчка'" /></ListItem>
              <ListItem><ListItemText primary="❓ Приключи ли ми се поръчката?" /></ListItem>
              <ListItem><ListItemText primary="💡 Проверете статуса в 'Поръчки'" /></ListItem>
            </List>
          </TabPanel>

          {/* TAB 6: АВТОПАРК */}
          <TabPanel value={tabValue} index={5}>
            <Typography variant="h5" gutterBottom color="primary" fontWeight="bold">Автопарк</Typography>
            
            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Добавяне на автомобил</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Автопарк'" /></ListItem>
              <ListItem><ListItemText primary="2. Натискате 'Нова кола'" /></ListItem>
              <ListItem><ListItemText primary="3. Попълвате данните (номер, марка, модел)" /></ListItem>
              <ListItem><ListItemText primary="4. Качвате документи" /></ListItem>
            </List>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Зареждане с гориво</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Автопарк' → 'Гориво'" /></ListItem>
              <ListItem><ListItemText primary="2. Натискате 'Ново зареждане'" /></ListItem>
              <ListItem><ListItemText primary="3. Избирате кола, литри, цена" /></ListItem>
            </List>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Ремонт</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Автопарк' → 'Ремонти'" /></ListItem>
              <ListItem><ListItemText primary="2. Натискате 'Нов ремонт'" /></ListItem>
              <ListItem><ListItemText primary="3. Описвате проблема" /></ListItem>
              <ListItem><ListItemText primary="4. Приключвате след ремонта" /></ListItem>
            </List>

            <Divider sx={{ my: 4 }} />
            <Typography variant="h6" gutterBottom>Често задавани въпроси</Typography>
            <List>
              <ListItem><ListItemText primary="❓ Как да добавя нова кола?" /></ListItem>
              <ListItem><ListItemText primary="💡 Отидете в 'Автопарк' → 'Нова кола'" /></ListItem>
              <ListItem><ListItemText primary="❓ Кога ми е прегледът?" /></ListItem>
              <ListItem><ListItemText primary="💡 Виждате го в детайлите на колата" /></ListItem>
              <ListItem><ListItemText primary="❓ Как да отчета гориво?" /></ListItem>
              <ListItem><ListItemText primary="💡 Отидете в 'Гориво' → 'Ново зареждане'" /></ListItem>
            </List>
          </TabPanel>

          {/* TAB 7: ДОСТЪП */}
          <TabPanel value={tabValue} index={6}>
            <Typography variant="h5" gutterBottom color="primary" fontWeight="bold">Контрол на достъпа</Typography>
            
            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Добавяне на врата</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Достъп' → 'Врати'" /></ListItem>
              <ListItem><ListItemText primary="2. Натискате 'Нова врата'" /></ListItem>
              <ListItem><ListItemText primary="3. Задавате име и номер" /></ListItem>
              <ListItem><ListItemText primary="4. Свързвате със зона" /></ListItem>
            </List>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Създаване на зона</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Достъп' → 'Зони'" /></ListItem>
              <ListItem><ListItemText primary="2. Натискате 'Нова зона'" /></ListItem>
              <ListItem><ListItemText primary="3. Задавате име" /></ListItem>
              <ListItem><ListItemText primary="4. Добавете врати" /></ListItem>
            </List>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Задаване на права</Typography>
            <List>
              <ListItem><ListItemText primary="1. Отивате в 'Достъп' → 'Права'" /></ListItem>
              <ListItem><ListItemText primary="2. Избирате потребител" /></ListItem>
              <ListItem><ListItemText primary="3. Добавете зоните с достъп" /></ListItem>
            </List>

            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Използване на достъп</Typography>
            <List>
              <ListItem><ListItemText primary="1. Приближавате картата до четеца" /></ListItem>
              <ListItem><ListItemText primary="2. ИЛИ: Въведете кода на клавиатурата" /></ListItem>
              <ListItem><ListItemText primary="3. Ако имате права - вратата се отваря" /></ListItem>
            </List>

            <Divider sx={{ my: 4 }} />
            <Typography variant="h6" gutterBottom>Често задавани въпроси</Typography>
            <List>
              <ListItem><ListItemText primary="❓ Защо не мога да вляза?" /></ListItem>
              <ListItem><ListItemText primary="💡 Проверете дали имате права за тази зона" /></ListItem>
              <ListItem><ListItemText primary="❓ Как да добавя права?" /></ListItem>
              <ListItem><ListItemText primary="💡 Отидете в 'Достъп' → 'Права' и добавете зона" /></ListItem>
              <ListItem><ListItemText primary="❓ Кой е влизал?" /></ListItem>
              <ListItem><ListItemText primary="💡 Прегледайте логовете в 'Достъп' → 'Логове'" /></ListItem>
            </List>
          </TabPanel>
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
