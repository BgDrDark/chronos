import React from 'react';
import { Container, Typography, Paper, Box, Divider, List, ListItem, ListItemIcon, ListItemText, Accordion, AccordionSummary, AccordionDetails, CircularProgress } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import SecurityIcon from '@mui/icons-material/Security';
import AssignmentIndIcon from '@mui/icons-material/AssignmentInd';
import QrCodeScannerIcon from '@mui/icons-material/QrCodeScanner';
import ViewModuleIcon from '@mui/icons-material/ViewModule';
import SpeedIcon from '@mui/icons-material/Speed';
import BusinessIcon from '@mui/icons-material/Business';
import PaymentsIcon from '@mui/icons-material/Payments';
import AssessmentIcon from '@mui/icons-material/Assessment';
import WarehouseIcon from '@mui/icons-material/Warehouse';
import RestaurantMenuIcon from '@mui/icons-material/RestaurantMenu';
import AddShoppingCartIcon from '@mui/icons-material/AddShoppingCart';
import FactoryIcon from '@mui/icons-material/Factory';
import LocalPrintshopIcon from '@mui/icons-material/LocalPrintshop';
import WarningIcon from '@mui/icons-material/Warning';
import DoneIcon from '@mui/icons-material/Done';
import ExitToAppIcon from '@mui/icons-material/ExitToApp';
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
        <Typography variant="h4" fontWeight="bold">Документация на системата Chronos</Typography>
      </Box>

      <Paper sx={{ p: 4, borderRadius: 3 }}>
        <Typography variant="h5" gutterBottom color="primary" fontWeight="bold">1. Общ преглед</Typography>
        <Typography variant="body1" paragraph>
          Chronos v2.2 е комплексна ERP система за управление на човешки ресурси (HR), фокусирана върху автоматизираното отчитане на работното време и финансовата отчетност. Системата е проектирана да обслужва множество компании едновременно, гарантирайки пълна сигурност и изолация на данните.
        </Typography>

        <Divider sx={{ my: 4 }} />

        <Typography variant="h5" gutterBottom color="primary" fontWeight="bold">2. Роли и нива на достъп</Typography>
        <List>
          <ListItem>
            <ListItemText 
              primary="Super Admin (Главен Администратор)" 
              secondary="Притежава пълен контрол над платформата. Единствен може да активира/деактивира модули и да конфигурира глобалните защити." 
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Admin (Администратор на фирма)" 
              secondary="Управлява служителите, техните договори, графици и заплати само в рамките на своята организация." 
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Служител (User)" 
              secondary="Използва системата за отчитане на време, преглед на фишове и подаване на молби за отпуск." 
            />
          </ListItem>
        </List>

        <Divider sx={{ my: 4 }} />

        {/* --- 3. МОДУЛНА СИСТЕМА --- */}
        {isSuperAdmin && (
          <Accordion defaultExpanded sx={{ mb: 2, borderLeft: '4px solid #4caf50', bgcolor: 'rgba(76, 175, 80, 0.05)' }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ViewModuleIcon color="success" />
                <Typography variant="h6" fontWeight="bold">3. Модулна Архитектура (Административна)</Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2" paragraph>
                Системата работи на принципа "Feature Toggling". Всеки модул може да бъде деактивиран, което спира API достъпа и скрива интерфейса:
              </Typography>
              <List dense>
                <ListItem><ListItemText primary="• Смени (shifts): Графици, реално време, размяна на смени." /></ListItem>
                <ListItem><ListItemText primary="• Отдел финанси (salaries): Калкулатор, бонуси, ведомости, аванси и заеми." /></ListItem>
                <ListItem><ListItemText primary="• Kiosk: Софтуерен терминал за вход/изход чрез QR." /></ListItem>
              </List>
            </AccordionDetails>
          </Accordion>
        )}

        {/* --- 4. СИГУРНОСТ --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #2196f3' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SecurityIcon color="primary" />
              <Typography variant="h6" fontWeight="bold">4. Сигурност и Защита (Advanced Security)</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="subtitle2" fontWeight="bold">Криптиране (AES-256):</Typography>
            <Typography variant="body2" paragraph>Чувствителните лични данни като ЕГН, IBAN и адреси се криптират на ниво база данни и се маскират в потребителския интерфейс.</Typography>
            
            <Typography variant="subtitle2" fontWeight="bold">Защита от атаки:</Typography>
            <List dense>
              <ListItem><ListItemText primary="• Rate Limiting: Блокиране на IP адреси при прекомерен брой опити за вход (Brute-force)." /></ListItem>
              <ListItem><ListItemText primary="• Password Complexity: Динамично управление на изискванията за пароли (дължина, знаци) от страна на Super Admin." /></ListItem>
              <ListItem><ListItemText primary="• API Throttling: Ограничаване на скоростта за тежки финансови справки." /></ListItem>
              <ListItem><ListItemText primary="• Input Sanitization: Автоматично изчистване на бележките от злонамерен HTML код." /></ListItem>
            </List>
          </AccordionDetails>
        </Accordion>

        {/* --- 5. ИЗОЛАЦИЯ --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #ff9800' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <BusinessIcon sx={{ color: '#ff9800' }} />
              <Typography variant="h6" fontWeight="bold">5. Мултитенантна Изолация (Multi-tenancy)</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2">
              Системата поддържа пълна софтуерна изолация между фирмите. Администраторът на една фирма не може да вижда или променя данни на друга, благодарение на принудително филтриране по `company_id` на ниво база данни и GraphQL резолвъри.
            </Typography>
          </AccordionDetails>
        </Accordion>

        {/* --- 6. ДОГОВОРИ И ФИНАНСИ --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #9c27b0' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PaymentsIcon color="secondary" />
              <Typography variant="h6" fontWeight="bold">6. Трудови договори и ТРЗ</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              Финансовият модул се базира на параметрите, заложени в **Индивидуалния трудов договор**:
            </Typography>
            <List dense>
              <ListItem><ListItemText primary="• Автоматични Аванси: Поддръжка на месечни аванси и разсрочени служебни заеми." /></ListItem>
              <ListItem><ListItemText primary="• Калкулация: Автоматично изчисляване на бруто/нето, осигуровки и данъци (ДОД)." /></ListItem>
              <ListItem><ListItemText primary="• Експорт: Генериране на ведомости в Excel и индивидуални фишове в PDF." /></ListItem>
            </List>
          </AccordionDetails>
        </Accordion>

        {/* --- 7. РАБОТНО ВРЕМЕ --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #ff5722' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AssignmentIndIcon sx={{ color: '#ff5722' }} />
              <Typography variant="h6" fontWeight="bold">7. Отчитане на време и Графици</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              Интелигентна логика за разпознаване на присъствието:
            </Typography>
            <List dense>
              <ListItem><ListItemText primary="• Толеранс (Tolerance): Възможност за 'прилепване' (snap) на влизането/излизането към началния час на смяната при малки закъснения." /></ListItem>
              <ListItem><ListItemText primary="• Размяна на смени: Система за одобрение на промени в графика между колеги." /></ListItem>
              <ListItem><ListItemText primary="• Geofencing: Възможност за ограничаване на влизането само в рамките на офисната зона (GPS)." /></ListItem>
            </List>
          </AccordionDetails>
        </Accordion>

        {/* --- 8. ОТПУСКИ --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #607d8b' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AssessmentIcon sx={{ color: '#607d8b' }} />
              <Typography variant="h6" fontWeight="bold">8. Управление на отпуски и Болнични</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <List dense>
              <ListItem><ListItemText primary="• Smart Balance: Следене на оставащите дни платен отпуск по години." /></ListItem>
              <ListItem><ListItemText primary="• Болнични (НОЙ): Автоматично изчисляване на дни за сметка на работодателя и на НОЙ." /></ListItem>
              <ListItem><ListItemText primary="• OCR Интеграция: Качване на документ и автоматично разпознаване на текст за бележките към отпуска." /></ListItem>
            </List>
          </AccordionDetails>
        </Accordion>

        {/* --- 9. KIOSK --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #f44336' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <QrCodeScannerIcon color="error" />
              <Typography variant="h6" fontWeight="bold">9. Kiosk Терминал v2.2</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2">
              Използва **Динамични QR кодове (TOTP)**, които се регенерират на всеки 30 секунди. Това гарантира, че служителят не може да изпрати снимка на кода си на колега, за да го "маркира" дистанционно.
            </Typography>
          </AccordionDetails>
        </Accordion>

        {/* --- 10. CONFECTIONERY & WAREHOUSE (v2.3) --- */}
        <Accordion sx={{ mb: 2, borderLeft: '4px solid #795548' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FactoryIcon sx={{ color: '#795548' }} />
              <Typography variant="h6" fontWeight="bold">10. Сладкарско производство и Склад (v2.3)</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              Специализиран модул за управление на производствения цикъл в хранителната индустрия:
            </Typography>
            <List dense>
              <ListItem>
                <ListItemIcon><WarehouseIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Хранителен Склад (FEFO):" secondary="Следене на наличности по зони (Сух, Хладилен, Фризер) и автоматично управление на партиди по срок на годност." />
              </ListItem>
              <ListItem>
                <ListItemIcon><RestaurantMenuIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Рецептурник (MRP):" secondary="Дефиниране на съставки с фира (Бруто/Нето) и разпределение на задачите по работни станции." />
              </ListItem>
              <ListItem>
                <ListItemIcon><AddShoppingCartIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Управление на Поръчки:" secondary="Интелигентно приемане на поръчки с автоматична проверка на наличността в склада." />
              </ListItem>
              <ListItem>
                <ListItemIcon><FactoryIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="MES Терминал:" secondary="Таблетен интерфейс за сладкари с таймери и real-time синхронизация между станциите." />
              </ListItem>
              <ListItem>
                <ListItemIcon><LocalPrintshopIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Етикетиране и HACCP:" secondary="Автоматично генериране на етикети с алергени, QR кодове и пълна проследяемост на партидите." />
              </ListItem>
            </List>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>10.1 Проследяване на производството (Traceability)</Typography>
            <Typography variant="body2" paragraph>
              Пълна проследяемост на всяка поръчка: когато ръководител потвърди поръчката за транспорт, системата записва:
            </Typography>
            <List dense>
              <ListItem><ListItemText primary="• Кой е работил по всяка задача (работници)" /></ListItem>
              <ListItem><ListItemText primary="• Какви съставки са използвани с номера на партидите" /></ListItem>
              <ListItem><ListItemText primary="• Срокове на годност на всяка съставка" /></ListItem>
              <ListItem><ListItemText primary="• Дата и час на потвърждение" /></ListItem>
            </List>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>10.2 Инвентаризация</Typography>
            <Typography variant="body2" paragraph>
              Система за инвентаризация на склада в реално време:
            </Typography>
            <List dense>
              <ListItem><ListItemText primary="• Стартиране на инвентаризационна сесия" /></ListItem>
              <ListItem><ListItemText primary="• Сканиране на баркодове за бързо добавяне на артикули" /></ListItem>
              <ListItem><ListItemText primary="• Автоматично изчисляване на разликите (излишък/недостиг)" /></ListItem>
              <ListItem><ListItemText primary="• Автоматично коригиране на наличностите при приключване" /></ListItem>
            </List>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>10.3 Полуфабрикати</Typography>
            <Typography variant="body2" paragraph>
              При завършване на задача от работна станция, системата автоматично създава заготовка в склада с:
            </Typography>
            <List dense>
              <ListItem><ListItemText primary="• Име: Рецепта + Име на стъпката" /></ListItem>
              <ListItem><ListItemText primary="• Партида с количество от поръчката" /></ListItem>
              <ListItem><ListItemText primary="• Срок на годност според рецептата (по подразбиране 7 дни)" /></ListItem>
            </List>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>10.4 Клавишни комбинации</Typography>
            <Typography variant="body2" paragraph>
              Клавишните комбинации работят глобално в цялото приложение (не само на конкретната страница):
            </Typography>
            <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, mb: 2 }}>
              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Страница "Склад":</Typography>
              <Typography variant="body2" component="div">
                • <strong>Ctrl+F1</strong> - Нов продукт<br />
                • <strong>Ctrl+F2</strong> - Приемане на стока<br />
                • <strong>Ctrl+S</strong> - Отваряне на скенера за баркод<br />
                • <strong>Ctrl+F12</strong> - Стартиране на инвентаризация<br />
                • <strong>Ctrl+F5</strong> - Нов доставчик<br />
                • <strong>Ctrl+F6</strong> - Нова зона
              </Typography>
            </Box>
            <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1 }}>
              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Страница "Рецепти":</Typography>
              <Typography variant="body2" component="div">
                • <strong>Ctrl+F5</strong> - Нова рецепта<br />
                • <strong>Ctrl+F6</strong> - Нова работна станция
              </Typography>
            </Box>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>10.5 Подобрения в създаването на рецепти</Typography>
            <Typography variant="body2" paragraph>
              Нови функционалности за по-бързо и удобно въвеждане на рецепти:
            </Typography>
            <List dense>
              <ListItem><ListItemText primary="• Автоматично изчисляване на фирата: Въведи само Бруто или само Нето, системата изчислява автоматично" /></ListItem>
              <ListItem><ListItemText primary="• Autocomplete търсене: Бързо търсене на съставки и работни станции" /></ListItem>
              <ListItem><ListItemText primary="• Копиране на рецепта: Бутон за копиране на съществуваща рецепта като основа за нова" /></ListItem>
              <ListItem><ListItemText primary="• Масов внос: Импортиране на рецепти от JSON файл" /></ListItem>
              <ListItem><ListItemText primary="• Enter за нов ред: Натисни Enter в последното поле за автоматично добавяне на нов ред" /></ListItem>
              <ListItem><ListItemText primary="• Скенер за баркод: Сканирай продукт и го добави директно в рецептата" /></ListItem>
            </List>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>10.6 Производствен Терминал (MES Terminal)</Typography>
            <Typography variant="body2" paragraph>
              Производственият терминал е специализиран интерфейс за работниците в цеха, който позволява:
            </Typography>
            <List dense>
              <ListItem>
                <ListItemIcon><QrCodeScannerIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Идентификация чрез QR код:" secondary="Служителят сканира личния си QR код за идентификация преди да започне работа." />
              </ListItem>
              <ListItem>
                <ListItemIcon><AssignmentIndIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Избор на работна станция:" secondary="След идентификация, служителят избира станцията на която ще работи." />
              </ListItem>
              <ListItem>
                <ListItemIcon><FactoryIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Работа по поръчки и задачи:" secondary="Преглед на активни поръчки и задачи за избраната станция с инструкции и количество." />
              </ListItem>
              <ListItem>
                <ListItemIcon><WarningIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Брак (БРАК):" secondary="Бутон за маркиране на количество брак със запис на причината." />
              </ListItem>
              <ListItem>
                <ListItemIcon><DoneIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Завършване (ЗАВЪРШИ):" secondary="Бутон за приключване на задачата след като е завършена." />
              </ListItem>
              <ListItem>
                <ListItemIcon><ExitToAppIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Изход (ИЗХОД):" secondary="Бутон за изход от системата, винаги видим в горния десен ъгъл." />
              </ListItem>
            </List>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Поток на работа в терминала:</Typography>
            <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, mb: 2 }}>
              <Typography variant="body2" component="div">
                1. <strong>Идентификация</strong> - Сканиране на QR код на служителя<br />
                2. <strong>Избор на станция</strong> - Избор на работна станция от списъка<br />
                3. <strong>Преглед на поръчки</strong> - Виждат се активните поръчки за станцията<br />
                4. <strong>Старт на задача</strong> - Избор на задача и започване на работа<br />
                5. <strong>Таймер</strong> - Отчитане на времето за изпълнение<br />
                6. <strong>БРАК / ЗАВЪРШИ</strong> - Приключване на задачата<br />
                7. <strong>ИЗХОД</strong> - Излизане от терминала
              </Typography>
            </Box>

            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Gateway услуга:</Typography>
            <Typography variant="body2" paragraph>
              За комуникация с терминалите се използва Gateway услуга (chronos-gateway), която:
            </Typography>
            <List dense>
              <ListItem><ListItemText primary="• Инсталира се като Windows услуга на локална машина в цеха" /></ListItem>
              <ListItem><ListItemText primary="• Управлява връзката между терминалите и централния сървър" /></ListItem>
              <ListItem><ListItemText primary="• Поддържа локални принтери за етикетиране" /></ListItem>
              <ListItem><ListItemText primary="• Генерира уникален HWID базиран на хардуера на машината" /></ListItem>
              <ListItem><ListItemText primary="• Автоматично се регистрира в системата при стартиране" /></ListItem>
            </List>
          </AccordionDetails>
        </Accordion>

        <Accordion sx={{ mb: 2, borderLeft: '4px solid #4caf50' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PaymentsIcon sx={{ color: '#4caf50' }} />
              <Typography variant="h6" fontWeight="bold">11. Счетоводство и Фактури (v2.4)</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              Модул за управление на входящи и изходящи фактури с автоматична интеграция със склада:
            </Typography>
            <List dense>
              <ListItem>
                <ListItemIcon><PaymentsIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Входящи фактури:" secondary="Фактури от доставчици с автоматично заприходяване на стока." />
              </ListItem>
              <ListItem>
                <ListItemIcon><PaymentsIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Изходящи фактури:" secondary="Фактури към клиенти с име, ЕИК и адрес." />
              </ListItem>
              <ListItem>
                <ListItemIcon><PaymentsIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Автоматично създаване:" secondary="При заприходяване на партида в склада, системата пита дали да създаде фактура." />
              </ListItem>
              <ListItem>
                <ListItemIcon><PaymentsIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="Управление на модули:" secondary="Модулът може да се включва/изключва от 'Управление на модули' в Настройки." />
              </ListItem>
            </List>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>11.1 Номерация на фактури</Typography>
            <List dense>
              <ListItem><ListItemText primary="• Входящи: ВХ-2026-0001 (ВХ-Година-Пореден_номер)" /></ListItem>
              <ListItem><ListItemText primary="• Изходящи: ИЗХ-2026-0001 (ИЗХ-Година-Пореден_номер)" /></ListItem>
            </List>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>11.2 Структура на фактурата</Typography>
            <List dense>
              <ListItem><ListItemText primary="• Подсубтова (сума преди отстъпка и ДДС)" /></ListItem>
              <ListItem><ListItemText primary="• Отстъпка % (отстъпка от подсубтовата)" /></ListItem>
              <ListItem><ListItemText primary="• ДДС (данък добавена стойност)" /></ListItem>
              <ListItem><ListItemText primary="• Общо (подсубтова - отстъпка + ДДС)" /></ListItem>
            </List>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>11.3 Статуси на фактура</Typography>
            <List dense>
              <ListItem><ListItemText primary="• Чернова (draft) - В процес на редактиране" /></ListItem>
              <ListItem><ListItemText primary="• Изпратена (sent) - Изпратена на клиента/доставчика" /></ListItem>
              <ListItem><ListItemText primary="• Платена (paid) - Плащането е получено/извършено" /></ListItem>
              <ListItem><ListItemText primary="• Просрочена (overdue) - Не е платена в срок" /></ListItem>
              <ListItem><ListItemText primary="• Анулирана (cancelled) - Анулирана фактура" /></ListItem>
            </List>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>11.4 Интеграция със Склад</Typography>
            <Typography variant="body2" paragraph>
              При създаване на нова партида в Склад (Прием на стока), след успешно заприходяване системата пита:
              "Желаете ли да създадете входяща фактура?". При потвърждение се създава чернова фактура с данните на партидата.
            </Typography>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>11.5 Валидация на форми</Typography>
            <List dense>
              <ListItem><ListItemText primary="• Датата е задължителна" /></ListItem>
              <ListItem><ListItemText primary="• Доставчикът е задължителен за входящи фактури" /></ListItem>
              <ListItem><ListItemText primary="• Име на клиент и ЕИК са задължителни за изходящи фактури" /></ListItem>
              <ListItem><ListItemText primary="• Поне един артикул е задължителен" /></ListItem>
              <ListItem><ListItemText primary="• Количеството трябва да е по-голямо от 0" /></ListItem>
            </List>
            </AccordionDetails>
            </Accordion>

            {/* --- 12. ACCESS CONTROL & GATEWAY (v3.0) --- */}
            <Accordion sx={{ mb: 2, borderLeft: '4px solid #d32f2f', bgcolor: 'rgba(211, 47, 47, 0.02)' }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SecurityIcon color="error" />
              <Typography variant="h6" fontWeight="bold">12. Контрол на Достъпа и Gateway (v3.0)</Typography>
            </Box>
            </AccordionSummary>
            <AccordionDetails>
            <Typography variant="body2" paragraph>
              Интегрирана система за физически контрол на достъпа чрез хардуерни контролери и софтуерни гейтуеи:
            </Typography>

            <Typography variant="subtitle2" fontWeight="bold" color="error.main">12.1 Клъстерна Архитектура (High Availability):</Typography>
            <Typography variant="body2" paragraph>
              Поддържа работа на множество гейтуеи в една локална мрежа чрез Master-Slave модел:
            </Typography>
            <List dense>
              <ListItem><ListItemText primary="• Автоматичен избор на Лидер (Master):" secondary="Най-мощната машина (CPU/RAM) автоматично става Master и управлява синхронизацията с облака." /></ListItem>
              <ListItem><ListItemText primary="• Slave Проксиране:" secondary="Slave устройствата препращат заявките за достъп към Master-а за централизирана Anti-passback проверка." /></ListItem>
              <ListItem><ListItemText primary="• Автоматичен Failover:" secondary="Ако Master устройството отпадне, Slave с най-висок приоритет поема управлението автоматично след 60 секунди." /></ListItem>
            </List>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" fontWeight="bold">12.2 Защита и Персистентност:</Typography>
            <List dense>
              <ListItem><ListItemText primary="• SQLite Persistence:" secondary="Всички логове се записват веднага в локална SQLite база данни, гарантираща оцеляване при рестарт или срив." /></ListItem>
              <ListItem><ListItemText primary="• HMAC-SHA256 Подписи:" secondary="Всяко събитие е защитено с цифров подпис за интегритет, предотвратяващ манипулация на данните по пътя." /></ListItem>
              <ListItem><ListItemText primary="• Transactional Sync:" secondary="Slave устройствата изпращат офлайн логове към Master-а само след изрично потвърждение (ACK)." /></ListItem>
            </List>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" fontWeight="bold" color="error.dark">12.3 Спешни Команди (Emergency Modes):</Typography>
            <List dense>
              <ListItem><ListItemText primary="• АВАРИЙНО ОТКЛЮЧВАНЕ (Evacuation):" secondary="С един клик от таблото всички врати се отварят автоматично за бърза евакуация." /></ListItem>
              <ListItem><ListItemText primary="• ПЪЛНА БЛОКАДА (Lockdown):" secondary="Мигновена забрана на всякакъв достъп до обекта при инцидент или заплаха." /></ListItem>
              <ListItem><ListItemText primary="• Дистанционно управление:" secondary="Възможност за ръчно отваряне на всяка врата директно от интерфейса на администратора." /></ListItem>
            </List>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" fontWeight="bold">12.4 Управление на Потребители:</Typography>
            <Typography variant="body2">
              Централизиран интерфейс за масово управление на правата. Администраторът може да избира групи от служители и да им назначава достъп до конкретни зони с чекбоксове, което оптимизира работата при голям персонал.
            </Typography>
            </AccordionDetails>
            </Accordion>


        {/* --- ТЕХНИЧЕСКА ЧАСТ (ADMIN ONLY) --- */}
        {isSuperAdmin && (
          <Accordion sx={{ mt: 2, border: '1px solid #2196f3', bgcolor: 'rgba(33, 150, 243, 0.05)' }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SpeedIcon color="primary" />
                <Typography variant="h6" fontWeight="bold" color="primary.main">10. Техническа Архитектура</Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <List dense>
                <ListItem><ListItemText primary="• Стек: Python 3.13, FastAPI, PostgreSQL (asyncpg)." /></ListItem>
                <ListItem><ListItemText primary="• Производителност: DataLoaders за избягване на N+1 проблеми в GraphQL." /></ListItem>
                <ListItem><ListItemText primary="• Одит: Пълен Audit Log за административни промени." /></ListItem>
                <ListItem><ListItemText primary="• Инфраструктура: Docker-ready с поддръжка на PWA (Offline Mode)." /></ListItem>
              </List>
            </AccordionDetails>
          </Accordion>
        )}

        <Box sx={{ mt: 6, p: 2, bgcolor: 'action.hover', borderRadius: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" align="center">
              © {new Date().getFullYear()} Chronos WorkTime System. Всички права запазени.
          </Typography>
        </Box>
      </Paper>

      {/* STATUS OVERVIEW SECTION */}
      <Paper sx={{ p: 4, borderRadius: 3, mt: 4 }}>
        <Typography variant="h4" gutterBottom color="primary" fontWeight="bold">
          📊 Статус на Системата
        </Typography>
        
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 2 }}>
          <Box sx={{ p: 2, bgcolor: 'success.light', borderRadius: 2 }}>
            <Typography variant="subtitle2" fontWeight="bold" color="success.dark">✅ Активни Защити</Typography>
            <List dense>
              <ListItem><ListItemText primary="• Rate Limiting (SlowAPI)" /></ListItem>
              <ListItem><ListItemText primary="• API Throttling (GraphQL Middleware)" /></ListItem>
              <ListItem><ListItemText primary="• Multi-tenant Isolation" /></ListItem>
              <ListItem><ListItemText primary="• Modular Guard System" /></ListItem>
            </List>
          </Box>

          <Box sx={{ p: 2, bgcolor: 'info.light', borderRadius: 2 }}>
            <Typography variant="subtitle2" fontWeight="bold" color="info.dark">🚀 Оперативни Показатели</Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              • Модулност: <strong>Активна (v2.2)</strong><br />
              • Изолация: <strong>Фирмена (Active)</strong><br />
              • Key Rotation: <strong>Автоматичен (30 дни)</strong><br />
              • PWA Status: <strong>Инсталиран / Offline Ready</strong>
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default DocumentationPage;