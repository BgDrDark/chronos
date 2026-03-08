import React from 'react';
import { Container, Typography, Paper, Box, Divider, List, ListItem, ListItemIcon, ListItemText, Accordion, AccordionSummary, AccordionDetails, CircularProgress } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import SecurityIcon from '@mui/icons-material/Security';
import AssignmentIndIcon from '@mui/icons-material/AssignmentInd';
import QrCodeScannerIcon from '@mui/icons-material/QrCodeScanner';
import ViewModuleIcon from '@mui/icons-material/ViewModule';
import BusinessIcon from '@mui/icons-material/Business';
import PaymentsIcon from '@mui/icons-material/Payments';
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff';
import WarehouseIcon from '@mui/icons-material/Warehouse';
import RestaurantMenuIcon from '@mui/icons-material/RestaurantMenu';
import LocalPrintshopIcon from '@mui/icons-material/LocalPrintshop';
import FactoryIcon from '@mui/icons-material/Factory';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import { useQuery } from '@apollo/client';
import { ME_QUERY } from '../graphql/queries';

const DocumentationPage: React.FC = () => {
  const { data, loading } = useQuery(ME_QUERY);
  
  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  
  const user = data?.me;
  const isSuperAdmin = user?.role?.name === 'super_admin';

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 4, gap: 2 }}>
        <HelpOutlineIcon color="primary" sx={{ fontSize: 40 }} />
        <Typography variant="h4" fontWeight="bold">Помощ</Typography>
      </Box>

      <Paper sx={{ p: 4, borderRadius: 3 }}>
        
        {/* --- 1. КАКВО Е CHRONOS --- */}
        <Typography variant="h5" gutterBottom color="primary" fontWeight="bold">1. Какво представлява системата?</Typography>
        <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem', lineHeight: 1.8 }}>
          <strong>Chronos</strong> е програма, която помага на фирмите да управляват:
        </Typography>
        <Box sx={{ pl: 2, mb: 3 }}>
          <Typography variant="body1">✓ Кой кога идва на работа</Typography>
          <Typography variant="body1">✓ Колко часове е работил всеки служител</Typography>
          <Typography variant="body1">✓ Когато служителите ползват отпуск</Typography>
          <Typography variant="body1">✓ Заплатите и данъците</Typography>
          <Typography variant="body1">✓ Фактурите на фирмата</Typography>
          <Typography variant="body1">✓ Кой може да влиза в определени стаи</Typography>
          <Typography variant="body1">✓ Складът и производството (при сладкарници)</Typography>
        </Box>

        <Divider sx={{ my: 4 }} />

        {/* --- 2. КАК ДА ВЛЕЗЕТЕ --- */}
        <Typography variant="h5" gutterBottom color="primary" fontWeight="bold">2. Как да влезете в системата?</Typography>
        <Box sx={{ bgcolor: 'grey.100', p: 3, borderRadius: 2, mb: 3 }}>
          <Typography variant="body1" gutterBottom><strong>Стъпка 1:</strong> Отворете браузъра (Chrome, Firefox, Edge)</Typography>
          <Typography variant="body1" gutterBottom><strong>Стъпка 2:</strong> Въведете адреса на системата</Typography>
          <Typography variant="body1" gutterBottom><strong>Стъпка 3:</strong> Въведете вашия email и парола</Typography>
          <Typography variant="body1" gutterBottom><strong>Стъпка 4:</strong> Натиснете бутона "Вход"</Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Ако забравите паролата си, потърсете администратора на системата.
        </Typography>

        <Divider sx={{ my: 4 }} />

        {/* --- 3. КОЙ КАКВО МОЖЕ ДА ПРАВИ --- */}
        <Typography variant="h5" gutterBottom color="primary" fontWeight="bold">3. Кой какво може да прави?</Typography>
        <Typography variant="body1" paragraph>
          В системата има три вида потребители:
        </Typography>
        
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <AccountCircleIcon color="error" />
            <Typography variant="h6" fontWeight="bold">Главен администратор</Typography>
          </Box>
          <Typography variant="body1" sx={{ pl: 4 }}>
            Този потребител може всичко - да добавя нови фирми, да включва и изключва модули, да вижда всичко.
          </Typography>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <AccountCircleIcon color="primary" />
            <Typography variant="h6" fontWeight="bold">Администратор на фирма</Typography>
          </Box>
          <Typography variant="body1" sx={{ pl: 4 }}>
            Управлява служителите на своята фирма - може да добавя нови хора, да прави графици, да следи кой е на работа.
          </Typography>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <AccountCircleIcon color="success" />
            <Typography variant="h6" fontWeight="bold">Служител</Typography>
          </Box>
          <Typography variant="body1" sx={{ pl: 4 }}>
            Всеки редови служител. Може да вижда своя график, да пуска заявки за отпуск, да си отбелязва часовете.
          </Typography>
        </Box>

        <Divider sx={{ my: 4 }} />

        {/* --- 4. ОТБЕЛЯЗВАНЕ НА ЧАСОВЕ --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #ff5722' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <QrCodeScannerIcon sx={{ color: '#ff5722' }} />
              <Typography variant="h6" fontWeight="bold">4. Как да си отбележа часовете?</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" paragraph>
              Има два начина да си отбележите кога идвате и си тръгвате от работа:
            </Typography>
            
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>Начин 1: QR код (препоръчителен)</Typography>
            <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, mb: 2 }}>
              <Typography variant="body1">1. Отворете <strong>http://localhost:3000/kiosk</strong></Typography>
              <Typography variant="body1">2. Отворете "Моята карта" на телефона си</Typography>
              <Typography variant="body1">3. Покажете QR кода на камерата</Typography>
              <Typography variant="body1">4. Готово! Системата е записала часа ви.</Typography>
            </Box>

            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>Начин 2: Код</Typography>
            <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, mb: 2 }}>
              <Typography variant="body1">1. Въведете вашия код (например 1234)</Typography>
              <Typography variant="body1">2. Натиснете Clock In или Clock Out</Typography>
            </Box>

            <Typography variant="body2" color="text.secondary">
              Ако сте забравили кода си, питайте администратора.
            </Typography>
          </AccordionDetails>
        </Accordion>

        {/* --- 5. ГРАФИЦИ --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #2196f3' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AssignmentIndIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">5. Графици и смени</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" paragraph>
              Графикът показва кога трябва да сте на работа. Ако нещо не разбирате, питайте началника си.
            </Typography>
            
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>Какво можете да правите?</Typography>
            <List>
              <ListItem>
                <ListItemText primary="• Да виждате кога са вашите смени" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Да пускате заявка за размяна на смяна с колега" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Да виждате кой още работи днес" />
              </ListItem>
            </List>

            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              За да ви бъде променен графикът, се обърнете към вашия ръководител или администратор.
            </Typography>
          </AccordionDetails>
        </Accordion>

        {/* --- 6. ОТПУСКИ --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #607d8b' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FlightTakeoffIcon sx={{ color: '#607d8b' }} />
              <Typography variant="h6" fontWeight="bold">6. Отпуски</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" paragraph>
              Ако искате да излезете в отпуск, трябва да пуснете заявка:
            </Typography>

            <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, mb: 2 }}>
              <Typography variant="body1">1. В менюто изберете <strong>Отпуски</strong></Typography>
              <Typography variant="body1">2. Кликнете <strong>+ Нова заявка</strong></Typography>
              <Typography variant="body1">3. Попълнете: вид на отпуската, от коя дата до коя дата</Typography>
              <Typography variant="body1">4. Натиснете <strong>Изпрати</strong></Typography>
            </Box>

            <Typography variant="body2" color="text.secondary">
              Вашата заявка ще бъде прегледана от вашия ръководител. Ще получите имейл или ще видите статуса в системата.
            </Typography>
          </AccordionDetails>
        </Accordion>

        {/* --- 7. КОНТРОЛ НА ДОСТЪПА --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #f44336' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SecurityIcon color="error" />
              <Typography variant="h6" fontWeight="bold">7. Врати и контрол на достъп</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" paragraph>
              Контролът на достъп означава кой може да влиза в определени помещения. 
              Например: не всеки може да влиза в склада или в офиса.
            </Typography>

            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>Какво означава това на практика?</Typography>
            <List>
              <ListItem>
                <ListItemText primary="• Всяка врата има име и номер" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Всяка врата е свързана към определена зона (например Офис, Склад)" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Само хората с права могат да влизат в дадена зона" />
              </ListItem>
              <ListItem>
                <ListItemText primary="• Всяко влизане се записва (кой, кога, коя врата)" />
              </ListItem>
            </List>

            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>Как да влезете?</Typography>
            <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1 }}>
              <Typography variant="body1">1. Отидете на вратата</Typography>
              <Typography variant="body1">2. Сложете картата или въведете кода</Typography>
              <Typography variant="body1">3. Ако имате права - вратата се отваря</Typography>
              <Typography variant="body1">4. Ако нямате права - вратата остава заключена</Typography>
            </Box>

            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Ако ви трябват права за дадена врата, питайте администратора.
            </Typography>
          </AccordionDetails>
        </Accordion>

        {/* --- 8. СКЛАД И ПРОИЗВОДСТВО --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #795548' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarehouseIcon sx={{ color: '#795548' }} />
              <Typography variant="h6" fontWeight="bold">8. Склад и производство</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" paragraph>
              Ако работите в сладкарница или производство, тук е обяснено как работи складът.
            </Typography>

            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>Какво е складът?</Typography>
            <Typography variant="body1" paragraph>
              Складът е мястото където се пазят продуктите. В системата има три вида складове:
            </Typography>
            <List>
              <ListItem><ListItemText primary="🧊 Хладилен (-18°C) - за замразени продукти" /></ListItem>
              <ListItem><ListItemText primary="❄️ Фризер (-18°C) - за замразени храни" /></ListItem>
              <ListItem><ListItemText primary="📦 Сух склад - за сухи продукти (брашно, захар)" /></ListItem>
            </List>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>Какво е рецептурникът?</Typography>
            <Typography variant="body1" paragraph>
              Рецептурникът е списъкът с всички рецепти. Всяка рецепта показва какви продукти и в какво количество са нужни за направата на даден десерт.
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>Какво е поръчка?</Typography>
            <Typography variant="body1" paragraph>
              Поръчката е какво трябва да направите. Когато дойде поръчка от клиент (например 10 торти), тя се появява в системата и вие я изпълнявате стъпка по стъпка.
            </Typography>

            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>Етикетиране</Typography>
            <Typography variant="body1">
              Всеки продукт има етикет с име, съставки, срок на годност и QR код. Това е нужно по закон (HACCP).
            </Typography>
          </AccordionDetails>
        </Accordion>

        {/* --- 9. СЧЕТОВОДСТВО --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #9c27b0' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PaymentsIcon sx={{ color: '#9c27b0' }} />
              <Typography variant="h6" fontWeight="bold">9. Счетоводство и фактури</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body1" paragraph>
              Тук се управляват парите на фирмата - фактурите, които плащаме и фактурите, които получаваме.
            </Typography>

            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>Входящи фактури</Typography>
            <Typography variant="body1" paragraph>
              Това са фактурите, които получаваме от доставчиците (например за ток, вода, продукти).
            </Typography>

            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>Изходящи фактури</Typography>
            <Typography variant="body1" paragraph>
              Това са фактурите, които издаваме на нашите клиенти.
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>Статуси на фактурите</Typography>
            <List>
              <ListItem><ListItemText primary="📝 Чернова - още се редактира" /></ListItem>
              <ListItem><ListItemText primary="📤 Изпратена - изпратена е на клиента/доставчика" /></ListItem>
              <ListItem><ListItemText primary="💰 Платена - парите са получени/платени" /></ListItem>
              <ListItem><ListItemText primary="⚠️ Просрочена - не е платена навреме" /></ListItem>
              <ListItem><ListItemText primary="❌ Анулирана - отменена е" /></ListItem>
            </List>
          </AccordionDetails>
        </Accordion>

        {/* --- 10. ЧЕСТО ЗАДАВАНИ ВЪПРОСИ --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #4caf50' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <HelpOutlineIcon sx={{ color: '#4caf50' }} />
              <Typography variant="h6" fontWeight="bold">10. Често задавани въпроси</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">❓ Забравих паролата си</Typography>
              <Typography variant="body1">Потърсете администратора на системата или използвайте "Забравена парола" (ако е включено).</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">❓ Не мога да вляза</Typography>
              <Typography variant="body1">Проверете дали email-ът е правилен. Ако продължавате да имате проблеми, свържете се с администратора.</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">❓ Забравих кода за Clock In/Out</Typography>
              <Typography variant="body1">Вашият код може да видите в "Моята карта" или питайте администратора.</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">❓ Защо вратата не се отваря?</Typography>
              <Typography variant="body1">Вероятно нямате права за тази зона. Питайте администратора да ви добави.</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">❓ Как да видя колко отпуск ми остава?</Typography>
              <Typography variant="body1">Отидете в "Отпуски" → "Моите заявки". Там ще видите оставащите дни.</Typography>
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" fontWeight="bold">❓ Не виждам определено меню</Typography>
              <Typography variant="body1">Някои менюта са само за администратори. Ако ви трябва достъп, питайте вашия ръководител.</Typography>
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* --- 11. КОНТАКТИ --- */}
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

        <Box sx={{ mt: 6, p: 2, bgcolor: 'action.hover', borderRadius: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" align="center">
              © {new Date().getFullYear()} Chronos - Работно Време. Всички права запазени.
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default DocumentationPage;
