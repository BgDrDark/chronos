"""
Seed script за попълване на документацията с реални данни
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from backend.database.database import AsyncSessionLocal
from backend.database.models import DocumentationCategory, DocumentationArticle, User, sofia_now


DOCUMENTATION_DATA = [
    {
        "title": "Персонал",
        "icon": "people",
        "order": 0,
        "articles": [
            {
                "title": "Създаване на нов служител",
                "content": """
<h2>Стъпки за създаване на служител</h2>
<ol>
<li>Отидете в меню <strong>Потребители</strong> → <strong>Списък служители</strong></li>
<li>Натиснете бутон <strong>Нов потребител</strong></li>
<li>Попълнете задължителните полета:
  <ul>
    <li>Име и фамилия</li>
    <li>Email адрес</li>
    <li>Телефон (опционално)</li>
    <li>ЕГН (за трудови договори)</li>
  </ul>
</li>
<li>Изберете роля:
  <ul>
    <li><strong>Служител</strong> - базов достъп</li>
    <li><strong>Мениджър</strong> - може да одобрява отпуски</li>
    <li><strong>Админ</strong> - пълен достъп</li>
  </ul>
</li>
<li>Задайте отдел и позиция</li>
<li>Натиснете <strong>Запази</strong></li>
</ol>
<h3>Резултат</h3>
<p>Служителят е създаден и получава email с инструкции за първоначална парола.</p>
""",
                "order": 0
            },
            {
                "title": "Организационна структура",
                "content": """
<h2>Управление на организационната структура</h2>
<p>Организационната структура показва йерархията в компанията.</p>
<h3>Създаване на отдел</h3>
<ol>
<li>Отидете в <strong>Потребители</strong> → <strong>Организационна структура</strong></li>
<li>Натиснете <strong>Нов отдел</strong></li>
<li>Попълнете име на отдела и изберете мениджър</li>
<li>Запазете</li>
</ol>
<h3>Преместване на служител</h3>
<ol>
<li>Намерете служителя в списъка</li>
<li>Натиснете <strong>Редактирай</strong></li>
<li>Променете отдела и/или позицията</li>
<li>Запазете промените</li>
</ol>
""",
                "order": 1
            }
        ]
    },
    {
        "title": "Присъствие и Графици",
        "icon": "time",
        "order": 1,
        "articles": [
            {
                "title": "Clock in / Clock out",
                "content": """
<h2>Отчитане на работно време</h2>
<h3>Чрез мобилен телефон</h3>
<ol>
<li>Отворете <strong>Моята карта</strong> от менюто</li>
<li>Сканирайте QR кода на терминала</li>
<li>Системата автоматично отбелязва вход/изход</li>
</ol>
<h3>Чрез киоск терминал</h3>
<ol>
<li>Приближете картата до четеца</li>
<li>ИЛИ въведете вашия PIN код</li>
<li>Терминалът показва потвърждение</li>
</ol>
<h3>Ръчно отбелязване (от админ)</h3>
<ol>
<li>Отидете в <strong>Табло присъствие</strong> → <strong>Присъствие</strong></li>
<li>Намерете служителя и датата</li>
<li>Натиснете <strong>Ръчно добавяне</strong></li>
<li>Въведете час на вход/изход</li>
<li>Добавете причина за ръчната корекция</li>
</ol>
""",
                "order": 0
            },
            {
                "title": "Създаване на график",
                "content": """
<h2>Управление на графици</h2>
<h3>Създаване на шаблон</h3>
<ol>
<li>Отидете в <strong>Графици</strong> → <strong>Настройки</strong></li>
<li>Натиснете <strong>Нов шаблон</strong></li>
<li>Задайте име на шаблона</li>
<li>Конфигурирайте работните дни и часове</li>
<li>Запазете шаблона</li>
</ol>
<h3>Прилагане на шаблон</h3>
<ol>
<li>Отидете в <strong>Графици</strong> → <strong>График</strong></li>
<li>Изберете период (седмица/месец)</li>
<li>Маркирайте служителите</li>
<li>Натиснете <strong>Приложи шаблон</strong></li>
<li>Изберете желания шаблон</li>
</ol>
<h3>Размяна на смени</h3>
<ol>
<li>Служител А иска размяна със служител Б</li>
<li>Служител Б получава известие и потвърждава</li>
<li>Администратор одобрява размяната</li>
<li>Графикът се обновява автоматично</li>
</ol>
""",
                "order": 1
            },
            {
                "title": "Анализи и KPI",
                "content": """
<h2>Анализи на присъствието</h2>
<h3>Основни KPI показатели</h3>
<ul>
<li><strong>Общо отработени часове</strong> - сума от всички часове за периода</li>
<li><strong>Закъснения</strong> - брой и продължителност</li>
<li><strong>Извънреден труд</strong> - часове над нормата</li>
<li><strong>Отсъствия</strong> - неплатени и платени</li>
</ul>
<h3>Генериране на отчет</h3>
<ol>
<li>Отидете в <strong>Табло присъствие</strong> → <strong>Анализи и KPI</strong></li>
<li>Изберете период</li>
<li>Филтрирайте по отдел или служител</li>
<li>Прегледайте графиките и таблиците</li>
<li>Експортирайте в Excel/PDF при нужда</li>
</ol>
""",
                "order": 2
            }
        ]
    },
    {
        "title": "Отпуски",
        "icon": "leave",
        "order": 2,
        "articles": [
            {
                "title": "Заявка за отпуск",
                "content": """
<h2>Подаване на заявка за отпуск</h2>
<ol>
<li>Отидете в <strong>Отпуски</strong> → <strong>Моите заявки</strong></li>
<li>Натиснете <strong>+ Нова заявка</strong></li>
<li>Изберете вид отпуск:
  <ul>
    <li><strong>Платен годишен отпуск</strong></li>
    <li><strong>Неплатен отпуск</strong></li>
    <li><strong>Болничен</strong></li>
    <li><strong>Майчинство/Бащинство</strong></li>
  </ul>
</li>
<li>Задайте начална и крайна дата</li>
<li>Добавете причина (опционално)</li>
<li>Натиснете <strong>Изпрати</strong></li>
</ol>
<h3>Статус на заявката</h3>
<ul>
<li><strong>Чакаща</strong> - изпратена за одобрение</li>
<li><strong>Одобрена</strong> - одобрена от мениджър</li>
<li><strong>Отхвърлена</strong> - отхвърлена с причина</li>
</ul>
""",
                "order": 0
            },
            {
                "title": "Одобряване на заявки",
                "content": """
<h2>Одобряване на отпуски (за мениджъри)</h2>
<ol>
<li>Отидете в <strong>Отпуски</strong> → <strong>Одобрения</strong></li>
<li>Прегледайте чакащите заявки</li>
<li>За всяка заявка можете да:
  <ul>
    <li>Видите детайли (период, причина, наличен баланс)</li>
    <li>Одобрите с бутон <strong>Одобри</strong></li>
    <li>Отхвърлите с бутон <strong>Отхвърли</strong> и причина</li>
  </ul>
</li>
</ol>
<h3>Баланс на отпуските</h3>
<p>Всеки служител може да види оставащите дни отпуск в <strong>Моите заявки</strong>.</p>
<p>Администраторите виждат баланса на всички служители в <strong>Всички заявки</strong>.</p>
""",
                "order": 1
            }
        ]
    },
    {
        "title": "Отдел ТРЗ",
        "icon": "payroll",
        "order": 3,
        "articles": [
            {
                "title": "Изчисляване на заплати",
                "content": """
<h2>Процес на изчисляване на заплати</h2>
<ol>
<li>Отидете в <strong>Отдел ТРЗ</strong> → <strong>Плащания</strong></li>
<li>Изберете месец и година</li>
<li>Натиснете <strong>Изчисли заплати</strong></li>
<li>Системата автоматично изчислява:
  <ul>
    <li>Брутна заплата (основна + бонуси)</li>
    <li>Осигуровки (ДОО, ЗО)</li>
    <li>Данъци (ДДФЛ)</li>
    <li>Нетна заплата</li>
  </ul>
</li>
<li>Прегледайте фишовете</li>
<li>Коригирайте при нужда</li>
<li>Финализирайте с <strong>Утвърди</strong></li>
</ol>
""",
                "order": 0
            },
            {
                "title": "Трудови договори",
                "content": """
<h2>Управление на трудови договори</h2>
<h3>Създаване на нов договор</h3>
<ol>
<li>Отидете в <strong>Отдел ТРЗ</strong> → <strong>Трудови договори</strong></li>
<li>Натиснете <strong>Нов договор</strong></li>
<li>Изберете служител</li>
<li>Изберете шаблон (или създайте нов)</li>
<li>Попълнете данните:
  <ul>
    <li>Начална дата</li>
    <li>Длъжност</li>
    <li>Основна заплата</li>
    <li>Работно време</li>
  </ul>
</li>
<li>Генерирайте PDF</li>
<li>Разпечатайте и подпишете</li>
</ol>
""",
                "order": 1
            },
            {
                "title": "SEPA плащания",
                "content": """
<h2>Генериране на SEPA XML за банкови плащания</h2>
<ol>
<li>Отидете в <strong>Отдел ТРЗ</strong> → <strong>Плащания</strong></li>
<li>Изберете утвърден период</li>
<li>Натиснете <strong>Генерирай XML</strong></li>
<li>Изтеглете XML файла</li>
<li>Качете го в онлайн банкирането</li>
<li>Банката обработва плащанията</li>
</ol>
<h3>Важно</h3>
<p>Уверете се, че IBAN-ите на служителите са попълнени в профилите им.</p>
""",
                "order": 2
            }
        ]
    },
    {
        "title": "Счетоводство",
        "icon": "accounting",
        "order": 4,
        "articles": [
            {
                "title": "Входящи фактури",
                "content": """
<h2>Управление на входящи фактури</h2>
<h3>Добавяне на фактура</h3>
<ol>
<li>Отидете в <strong>Счетоводство</strong> → <strong>Входящи фактури</strong></li>
<li>Натиснете <strong>Нова фактура</strong></li>
<li>Попълнете:
  <ul>
    <li>Доставчик</li>
    <li>Номер и дата на фактурата</li>
    <li>Суми (без ДДС, ДДС, общо)</li>
    <li>Срок на плащане</li>
  </ul>
</li>
<li>Качете сканирано копие (PDF/снимка)</li>
<li>Запазете</li>
</ol>
<h3>OCR разпознаване</h3>
<p>Системата автоматично разпознава данни от качените фактури и предлага попълване на полетата.</p>
""",
                "order": 0
            },
            {
                "title": "Изходящи фактури",
                "content": """
<h2>Създаване на изходящи фактури</h2>
<ol>
<li>Отидете в <strong>Счетоводство</strong> → <strong>Изходящи фактури</strong></li>
<li>Натиснете <strong>Нова фактура</strong></li>
<li>Изберете клиент</li>
<li>Добавете артикули/услуги</li>
<li>Системата автоматично изчислява сумите</li>
<li>Генерирайте PDF</li>
<li>Изпратете по email или разпечатайте</li>
</ol>
""",
                "order": 1
            },
            {
                "title": "ДДС регистри",
                "content": """
<h2>ДДС регистри и декларации</h2>
<h3>Генериране на ДНС</h3>
<ol>
<li>Отидете в <strong>Счетоводство</strong> → <strong>ДДС регистри</strong></li>
<li>Изберете месец</li>
<li>Прегледайте дневниците:
  <ul>
    <li>Дневник покупки</li>
    <li>Дневник продажби</li>
  </ul>
</li>
<li>Експортирайте в XML за НАП</li>
</ol>
""",
                "order": 2
            }
        ]
    },
    {
        "title": "Склад и Производство",
        "icon": "warehouse",
        "order": 5,
        "articles": [
            {
                "title": "Управление на склад",
                "content": """
<h2>Складово стопанство</h2>
<h3>Добавяне на продукт</h3>
<ol>
<li>Отидете в <strong>Склад</strong></li>
<li>Натиснете <strong>Нов продукт</strong></li>
<li>Попълнете:
  <ul>
    <li>Име и код</li>
    <li>Мерна единица</li>
    <li>Категория</li>
    <li>Начално количество</li>
  </ul>
</li>
<li>Запазете</li>
</ol>
<h3>Инвентаризация</h3>
<ol>
<li>Отидете в <strong>Склад</strong> → <strong>Инвентаризация</strong></li>
<li>Натиснете <strong>Нова сесия</strong></li>
<li>Сканирайте или въведете продуктите</li>
<li>Системата показва разликите</li>
<li>Потвърдете и приключете</li>
</ol>
""",
                "order": 0
            },
            {
                "title": "Рецепти и производство",
                "content": """
<h2>Управление на рецепти</h2>
<h3>Създаване на рецепта</h3>
<ol>
<li>Отидете в <strong>Рецепти</strong></li>
<li>Натиснете <strong>Нова рецепта</strong></li>
<li>Задайте име на продукта</li>
<li>Добавете съставки и количества</li>
<li>Запазете рецептата</li>
</ol>
<h3>Производствена поръчка</h3>
<ol>
<li>Отидете в <strong>Поръчки</strong></li>
<li>Натиснете <strong>Нова поръчка</strong></li>
<li>Изберете рецепта</li>
<li>Задайте количество</li>
<li>Стартирайте производството</li>
<li>Следете прогреса в <strong>Контрол</strong></li>
</ol>
""",
                "order": 1
            }
        ]
    },
    {
        "title": "Автопарк и Логистика",
        "icon": "fleet",
        "order": 6,
        "articles": [
            {
                "title": "Управление на автомобили",
                "content": """
<h2>Автопарк</h2>
<h3>Добавяне на автомобил</h3>
<ol>
<li>Отидете в <strong>Автомобили</strong></li>
<li>Натиснете <strong>Нов автомобил</strong></li>
<li>Попълнете:
  <ul>
    <li>Регистрационен номер</li>
    <li>Марка и модел</li>
    <li>Година на производство</li>
    <li>VIN номер</li>
    <li>Тип гориво</li>
  </ul>
</li>
<li>Запазете</li>
</ol>
<h3>Зареждане с гориво</h3>
<ol>
<li>Изберете автомобил</li>
<li>Отидете в таб <strong>Гориво</strong></li>
<li>Натиснете <strong>Ново зареждане</strong></li>
<li>Попълнете литри, цена, километраж</li>
</ol>
""",
                "order": 0
            },
            {
                "title": "Логистика и маршрути",
                "content": """
<h2>Управление на логистиката</h2>
<h3>Създаване на маршрут</h3>
<ol>
<li>Отидете в <strong>Логистика</strong></li>
<li>Натиснете <strong>Нов маршрут</strong></li>
<li>Изберете автомобил и шофьор</li>
<li>Задавете начална и крайна точка</li>
<li>Добавете междинни спирки</li>
<li>Запазете маршрута</li>
</ol>
<h3>Проследяване</h3>
<p>Активните маршрути се проследяват в реално време в таблото за логистика.</p>
""",
                "order": 1
            }
        ]
    },
    {
        "title": "Контрол на достъпа",
        "icon": "access",
        "order": 7,
        "articles": [
            {
                "title": "Зони и врати",
                "content": """
<h2>Управление на достъпа</h2>
<h3>Създаване на зона</h3>
<ol>
<li>Отидете в <strong>Отдел КД</strong> → <strong>Зони за достъп</strong></li>
<li>Натиснете <strong>Нова зона</strong></li>
<li>Задайте име (напр. "Офис", "Склад", "Сървърна")</li>
<li>Запазете</li>
</ol>
<h3>Добавяне на врата</h3>
<ol>
<li>Отидете в <strong>Отдел КД</strong> → <strong>Врати</strong></li>
<li>Натиснете <strong>Нова врата</strong></li>
<li>Задайте име и номер</li>
<li>Свържете със зона</li>
<li>Конфигурирайте терминал (ако има)</li>
</ol>
""",
                "order": 0
            },
            {
                "title": "Права за достъп",
                "content": """
<h2>Задаване на права</h2>
<ol>
<li>Отидете в <strong>Отдел КД</strong> → <strong>Потребители</strong></li>
<li>Изберете служител</li>
<li>Натиснете <strong>Редактирай права</strong></li>
<li>Маркирайте зоните, до които има достъп</li>
<li>Зададете времеви ограничения (ако има)</li>
<li>Запазете</li>
</ol>
<h3>Използване</h3>
<ul>
<li>Приближете картата до четеца</li>
<li>ИЛИ въведете PIN код</li>
<li>Ако имате права - вратата се отваря</li>
<li>Всички събития се записват в <strong>Логове</strong></li>
</ul>
""",
                "order": 1
            }
        ]
    },
    {
        "title": "Уведомления",
        "icon": "notifications",
        "order": 8,
        "articles": [
            {
                "title": "Конфигуриране на уведомления",
                "content": """
<h2>Система за уведомления</h2>
<h3>Видове събития</h3>
<ul>
<li><strong>Заявка за отпуск</strong> - при нова заявка</li>
<li><strong>Одобрение на отпуск</strong> - при одобрение/отхвърляне</li>
<li><strong>Размяна на смени</strong> - при заявка за размяна</li>
<li><strong>Изтичащ договор</strong> - 30 дни преди изтичане</li>
<li><strong>Изтичаща застраховка</strong> - за автомобили</li>
</ul>
<h3>SMTP настройки</h3>
<ol>
<li>Отидете в <strong>Уведомления</strong> → <strong>SMTP Настройки</strong></li>
<li>Попълнете:
  <ul>
    <li>SMTP сървър</li>
    <li>Порт</li>
    <li>Потребител и парола</li>
    <li>From адрес</li>
  </ul>
</li>
<li>Тествайте с бутон <strong>Изпрати тестов email</strong></li>
</ol>
""",
                "order": 0
            }
        ]
    },
    {
        "title": "Поведенчески анализ",
        "icon": "folder",
        "order": 9,
        "articles": [
            {
                "title": "Какво представлява модулът",
                "content": """
<h2>Поведенчески анализ — Behavioral Analysis Module</h2>
<p>Модулът за поведенчески анализ е AI-базирана система за оценка на работното поведение,
ангажираността и риска от burnout на служителите. Използва комбинация от обективни данни
(отработени часове, закъснения, болнични, продуктивност) и субективни самооценки
(UWES-9 анкети, pulse surveys) за изграждане на цялостен профил на всеки служител.</p>

<h3>Четирислойна архитектура</h3>
<ol>
  <li><strong>Data Collection Layer</strong> — събира данни от TimeLog, ProductionTask, WorkSchedule, LeaveRequest и други модули</li>
  <li><strong>Analysis Engine</strong> — изчислява 7 ключови метрики (attendance, engagement, burnout, punctuality, overtime, sick_leave, efficiency) с Mann-Kendall trend и Z-score anomaly detection</li>
  <li><strong>Rule Engine</strong> — прилага дефинирани от HR правила и генерира препоръки</li>
  <li><strong>Feedback Loop</strong> — проследява резултатите от препоръките и подобрява точността</li>
</ol>

<h3>Ключови възможности</h3>
<ul>
  <li><strong>Автоматично изчисляване</strong> на 7 метрики всеки ден за всеки активен служител</li>
  <li><strong>Trend detection</strong> — проследяване на посоката (подобрение/влошаване) с Mann-Kendall статистическа значимост (p-value)</li>
  <li><strong>Anomaly detection</strong> — откриване на необичайно поведение с Z-score нормализация и severity оценка</li>
  <li><strong>Личностен профил (IPIP-50)</strong> — Big Five психо-портрет за корекция на метриките според типа личност</li>
  <li><strong>Triangulation</strong> — комбиниране на обективни данни със self-report за по-висока точност (формула: objective × 0.6 + pulse × 0.4)</li>
  <li><strong>HR препоръки</strong> — конкретни действия при идентифицирани проблеми (preventive, corrective, escalation)</li>
  <li><strong>Organizational Health</strong> — агрегиран изглед на здравето на цялата компания или отдел</li>
  <li><strong>Bias Detection</strong> — откриване на систематични отклонения между отдели (напр. единият отдел има постоянно по-висок burnout)</li>
  <li><strong>Manager Effectiveness</strong> — оценка на мениджърите на база резултатите на техните екипи</li>
  <li><strong>Explainable AI (XAI)</strong> — показва кои фактори влияят най-много на профила на всеки служител</li>
</ul>

<h3>За кого е предназначен</h3>
<ul>
  <li><strong>HR специалисти</strong> — за превенция на burnout, задържане на таланти, управление на организационното здраве</li>
  <li><strong>Мениджъри</strong> — за разбиране на екипната динамика и ранно откриване на проблеми</li>
  <li><strong>Служители</strong> — за обратна връзка за собственото им представяне, IPIP-50 тест и pulse survey</li>
  <li><strong>Ръководство</strong> — за стратегически решения на база организационно здраве и manager effectiveness</li>
</ul>

<h3>Откъде идват данните</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#e3f2fd"><th>Метрика</th><th>Източник на данни</th><th>Честота на обновяване</th></tr>
  <tr><td>Attendance (присъствие)</td><td>TimeLog (часовници) + LeaveRequest (отпуски)</td><td>Ежедневно</td></tr>
  <tr><td>Punctuality (точност)</td><td>TimeLog + WorkSchedule (график)</td><td>Ежедневно</td></tr>
  <tr><td>Overtime (извънреден труд)</td><td>TimeLog</td><td>Ежедневно</td></tr>
  <tr><td>Efficiency (ефективност)</td><td>ProductionTask (производствени задачи)</td><td>Ежедневно</td></tr>
  <tr><td>Burnout (прегаряне)</td><td>Overtime + SickLeave + Pulse Survey + IPIP-50</td><td>Ежедневно (след pulse — моментално)</td></tr>
  <tr><td>Engagement (ангажираност)</td><td>UWES-9 / Pulse survey</td><td>Месечно/тримесечно</td></tr>
  <tr><td>Sick Leave (болнични)</td><td>LeaveRequest (болнични)</td><td>Ежедневно</td></tr>
</table>

<h3>Екранни форми и навигация</h3>
<ul>
  <li><strong>/my-behavioral-profile</strong> — личен профил на служителя: метрики, IPIP-50 тест, pulse survey, manager effectiveness (ако е мениджър)</li>
  <li><strong>/admin/behavioral-analysis/dashboard</strong> — обзорно табло за HR: брой профили, критични/рискови служители, последни аномалии и препоръки</li>
  <li><strong>/admin/behavioral-analysis/rules</strong> — създаване и управление на правила за автоматични препоръки</li>
  <li><strong>/admin/behavioral-analysis/settings</strong> — глобални настройки на модула (периоди на профилиране, cleanup, etc.)</li>
  <li><strong>/admin/behavioral-analysis/health</strong> — organizational health dashboard за компанията/отделите</li>
  <li><strong>/admin/behavioral-analysis/bias</strong> — bias detection report</li>
  <li><strong>/admin/behavioral-analysis/system</strong> — system health (статус на изчисленията, circuit breaker, alerts)</li>
  <li><strong>/admin/behavioral-analysis/templates</strong> — управление на шаблони за IPIP-50 теста (избор на 50 от 200 въпроса)</li>
  <li><strong>/admin/behavioral-analysis/employee/:id</strong> — детайлен профил на конкретен служител</li>
</ul>
""",
                "order": 0
            },
            {
                "title": "Ползи от използването на модула",
                "content": """
<h2>Ползи за организацията</h2>

<h3>🔍 Ранно откриване на проблеми</h3>
<p>Модулът идентифицира служители в риск от burnout или дезингийджмънт
<strong>седмици преди</strong> те да доведат до напускане или болничен.
Системата следи 7 метрики едновременно и сигнализира при комбинация от рискови фактори.</p>

<h3>📉 Намаляване на текучеството</h3>
<p>Според проучвания, 70% от team engagement се дължи на manager quality (Gallup, 2024).
Чрез manager effectiveness scoring идентифицираме кои мениджъри създават стойност и кои се нуждаят от подкрепа.
Ранната намеса може да намали текучеството с до 25%.</p>

<h3>🎯 Персонализиран подход</h3>
<ul>
  <li><strong>IPIP-50 психо-портрет</strong> — коригира метриките според личността (напр. интроверт ≠ слаба комуникация)</li>
  <li><strong>Triangulation</strong> — не взимаме решение само на база числа; слушаме и служителя</li>
  <li><strong>Pulse surveys</strong> — кратки анкети (5 въпроса) на месец за собствената оценка на служителя</li>
</ul>

<h3>📊 Data-driven решения за HR</h3>
<ul>
  <li>Отговори на въпроси като:
    <ul>
      <li>"Кои екипи са най-рискови?"</li>
      <li>"Кои мениджъри губят хора?"</li>
      <li>"Пушат ли новите служители по-бързо?"</li>
      <li>"Има ли систематично отклонение между отдели?" (bias detection)</li>
    </ul>
  </li>
  <li>Trend анализ с Mann-Kendall тест (p-value) — сигурни ли сме, че трендът е реален?</li>
  <li>Anomaly severity (Z-score) — 60h OT е по-тежко от 42h OT</li>
</ul>

<h3>🛡️ Превенция на burnout</h3>
<p>Burnout струва скъпо — болнични, ниска продуктивност, напускания.
Модулът следи комбинация от фактори:</p>
<ul>
  <li>Извънреден труд > 48h/седмица</li>
  <li>Чести болнични (3+ за 3 месеца)</li>
  <li>Липса на отпуск (6+ месеца без почивка)</li>
  <li>Влошаващ се trend в attendance_score</li>
  <li>Pulse survey самооценка (burnout_feeling, stress_level)</li>
</ul>

<h3>📈 Дългосрочни ползи</h3>
<ul>
  <li>По-здравословна работна среда</li>
  <li>По-висока задържаемост на таланти</li>
  <li>Оптимизация на мениджърския състав</li>
  <li>Намаляване на отсъствията</li>
  <li>По-добро планиране на workforce</li>
</ul>
""",
                "order": 1
            },
            {
                "title": "Показатели за наблюдение (KPI)",
                "content": """
<h2>Основни показатели за мониторинг</h2>

<h3>1. 🔵 Attendance Score (0-100)</h3>
<p><strong>Какво измерва:</strong> Колко от работните дни служителят е присъствал.</p>
<p><strong>Формула:</strong> <code>presence_days / workdays × 100</code></p>
<p><strong>Източник:</strong> TimeLog (часовници) + LeaveRequest</p>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#e3f2fd"><th>Скала</th><th>Интерпретация</th><th>Действие</th></tr>
  <tr><td>90-100</td><td>✅ Отлично присъствие</td><td>Няма нужда от действие</td></tr>
  <tr><td>75-89</td><td>⚠️ Добро, но има отсъствия</td><td>Проверете причината</td></tr>
  <tr><td>50-74</td><td>🔴 Тревожно</td><td>Разговор с мениджър</td></tr>
  <tr><td>Под 50</td><td>⛔ Критично</td><td>HR интервенция</td></tr>
</table>

<h3>2. 🟢 Engagement Score (UWES-9, 0-100)</h3>
<p><strong>Какво измерва:</strong> Истинската психологическа ангажираност чрез 9-те въпроса на UWES-9.</p>
<p><strong>Трите измерения на UWES-9:</strong></p>
<ul>
  <li><strong>Vigor</strong> (енергия, 3 въпроса) — висока енергия и устойчивост на работа</li>
  <li><strong>Dedication</strong> (отдаденост, 3 въпроса) — ентусиазъм, гордост от работата</li>
  <li><strong>Absorption</strong> (потопеност, 3 въпроса) — пълна концентрация и удоволствие от работата</li>
</ul>
<p><strong>Честота:</strong> Тримесечно (1× на 3 месеца)</p>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#e8f5e9"><th>Скала</th><th>Интерпретация</th><th>Риск от напускане</th></tr>
  <tr><td>75-100</td><td>✅ Високо ангажиран</td><td>Много нисък</td></tr>
  <tr><td>50-74</td><td>⚠️ Умерено ангажиран</td><td>Среден</td></tr>
  <tr><td>25-49</td><td>🔴 Ниско ангажиран</td><td>Висок</td></tr>
  <tr><td>Под 25</td><td>⛔ Критично дезингийджмънт</td><td>Много висок</td></tr>
</table>

<h3>3. 🟠 Burnout Risk (0.0-1.0)</h3>
<p><strong>Какво измерва:</strong> Риск от професионално изчерпване.</p>
<p><strong>Фактори:</strong> Извънреден труд + болнични + Self-report (pulse survey) с triangulation + IPIP-50 корекция.</p>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#fff3e0"><th>Скала</th><th>Статус</th><th>Интерпретация</th></tr>
  <tr><td>0.0-0.3</td><td>✅ normal</td><td>Нисък риск, нормално натоварване</td></tr>
  <tr><td>0.3-0.5</td><td>⚠️ watch</td><td>Повишено внимание, следете trend-а</td></tr>
  <tr><td>0.5-0.7</td><td>🔴 at_risk</td><td>Нужна е намеса, намалете натоварването</td></tr>
  <tr><td>0.7-1.0</td><td>⛔ critical</td><td>Незабавна HR интервенция</td></tr>
</table>

<h3>4. 🟣 Punctuality Score (0-100)</h3>
<p><strong>Какво измерва:</strong> Колко често служителят започва работа навреме според графика.</p>
<p><strong>Формула:</strong> <code>on_time_days / total_days × 100</code> — закъснение до tolerance (15 мин) се брои за навреме</p>
<p><strong>Източник:</strong> TimeLog + WorkSchedule.start_time + tolerance_minutes от shift-а</p>

<h3>5. ⚪ Overtime Factor (0.0-1.0)</h3>
<p><strong>Какво измерва:</strong> Отклонение от нормалното работно време.</p>
<ul>
  <li>40h/седм = 0.0 (норма)</li>
  <li>48h/седм = 0.3 (праг на внимание)</li>
  <li>56h/седм = 0.7 (рисково)</li>
  <li>60h+ /седм = 1.0 (критично)</li>
</ul>

<h3>6. 🟤 Sick Leave Factor (0.0-1.0)</h3>
<p><strong>Какво измерва:</strong> Честота на болнични спрямо нормите.</p>
<ul>
  <li>0 дни = 0.0</li>
  <li>3-5 дни (1x) = 0.2</li>
  <li>10+ дни (2+ пъти) = 0.7+</li>
  <li>Подозрителна честота = 1.0</li>
</ul>

<h3>7. 🔵 Efficiency Score (0-100)</h3>
<p><strong>Какво измерва:</strong> Продуктивност спрямо очакванията (за production потребители).</p>
<p><strong>Формула:</strong> Базирана на <code>ProductionTask</code> и <code>RecipeStep.estimated_duration_minutes</code> — колко от планираните задачи са изпълнени в рамките на очакваното време.</p>

<h3>8. 📊 Organizational Health (0-100)</h3>
<p>Агрегиран показател за цялата компания или отдел:</p>
<ul>
  <li><strong>health_index</strong> (0-100) — общо здраве на организацията</li>
  <li><strong>avg_burnout_risk</strong> — среден burnout риск за отдела</li>
  <li><strong>avg_attendance</strong> — средно присъствие</li>
  <li><strong>avg_efficiency</strong> — средна ефективност</li>
  <li><strong>avg_punctuality</strong> — средна точност</li>
  <li><strong>risk_distribution</strong> — какъв % от служителите са във всяка категория</li>
  <li><strong>trend_direction</strong> — подобрение/влошаване</li>
  <li><strong>top_risk_factors</strong> — топ 3 рискови фактора в момента</li>
  <li><strong>turnover_rate</strong> — процент на текучество</li>
</ul>
""",
                "order": 2
            },
            {
                "title": "Критерии и статуси",
                "content": """
<h2>Критерии за оценка и статуси</h2>

<h3>Статуси на служител</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#e3f2fd"><th>Статус</th><th>Условия</th><th>Цвят</th></tr>
  <tr>
    <td><strong>active</strong></td>
    <td>Всички метрики в нормални граници, няма аномалии</td>
    <td style="color:green">🟢 Зелен</td>
  </tr>
  <tr>
    <td><strong>watch</strong></td>
    <td>Една или две метрики в предупредителна зона; или влошаващ се trend</td>
    <td style="color:orange">🟡 Жълт</td>
  </tr>
  <tr>
    <td><strong>at_risk</strong></td>
    <td>Burnout > 0.5; или комбинация от 3+ влошени метрики; или аномалия с notable severity</td>
    <td style="color:red">🔴 Червен</td>
  </tr>
  <tr>
    <td><strong>critical</strong></td>
    <td>Burnout > 0.7; или множество аномалии; или статистически значимо влошаване (p < 0.01)</td>
    <td style="color:darkred">⛔ Тъмночервен</td>
  </tr>
</table>

<h3>Trend направление</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#e8f5e9"><th>Посока</th><th>p-value</th><th>Интерпретация</th></tr>
  <tr><td><strong>improving ↑</strong></td><td>p < 0.05</td><td>Статистически значимо подобрение (напр. намаляване на OT)</td></tr>
  <tr><td><strong>stable →</strong></td><td>p ≥ 0.05</td><td>Без статистически значима промяна</td></tr>
  <tr><td><strong>declining ↓</strong></td><td>p < 0.05</td><td>Статистически значимо влошаване</td></tr>
</table>

<h3>Anomaly severity</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#fff3e0"><th>Severity</th><th>Z-score</th><th>Пример</th></tr>
  <tr><td><strong>normal</strong></td><td>z < 1</td><td>42h OT при средно 40h</td></tr>
  <tr><td><strong>mild</strong></td><td>1 ≤ z < 2</td><td>50h OT при средно 40h (SD=5)</td></tr>
  <tr><td><strong>notable</strong></td><td>2 ≤ z < 3</td><td>55h OT при средно 40h (SD=5)</td></tr>
  <tr><td><strong>severe</strong></td><td>z ≥ 3</td><td>60h+ OT при средно 40h (SD=5)</td></tr>
</table>

<h3>Confidence score (след Triangulation)</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#f3e5f5"><th>Confidence</th><th>Сценарий</th></tr>
  <tr><td><strong>0.9-1.0</strong></td><td>Обективни данни + pulse survey съвпадат (diff < 0.2)</td></tr>
  <tr><td><strong>0.7-0.8</strong></td><td>Само обективни данни (без pulse)</td></tr>
  <tr><td><strong>0.5-0.6</strong></td><td>Pulse е стар > 30 дни</td></tr>
  <tr><td><strong>0.3</strong></td><td>Няма никакви данни за служителя</td></tr>
</table>

<h3>Manager Effectiveness (0-100)</h3>
<p>Оценка на мениджъра на база резултатите на неговия екип. Изчислява се от мутацията <code>computeManagerEffectiveness</code>.</p>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#e3f2fd"><th>Компонент</th><th>Тежест</th></tr>
  <tr><td>Team attendance</td><td>15%</td></tr>
  <tr><td>Team engagement (UWES-9)</td><td>25%</td></tr>
  <tr><td>Burnout penalty (по-нисък = по-добре)</td><td>20%</td></tr>
  <tr><td>Turnover rate (по-нисък = по-добре)</td><td>25%</td></tr>
  <tr><td>Anomaly penalty (по-нисък = по-добре)</td><td>15%</td></tr>
</table>
<p><strong>Скала:</strong></p>
<ul>
  <li><strong>80-100</strong> — Отличен мениджър</li>
  <li><strong>60-79</strong> — Добър мениджър, има място за подобрение</li>
  <li><strong>40-59</strong> — Нуждае се от подкрепа</li>
  <li><strong>Под 40</strong> — Критично, нужна е HR намеса</li>
</ul>

<h3>Правила за аномалии</h3>
<p>Системата автоматично създава аномалия при:</p>
<ul>
  <li>Отсъствие 3+ последователни дни без одобрен отпуск</li>
  <li>Извънреден труд > 48h за седмица</li>
  <li>Болнични > 10 дни в рамките на 3 месеца</li>
  <li>Спад на punctuality с > 20% за месец</li>
  <li>Комбинация от 3+ метрики в watch зона</li>
  <li>Статистически значим declining trend (p < 0.05)</li>
</ul>

<h3>Препоръки и действия</h3>
<p>Всяка препоръка има тип, приоритет и статус. Служителят или HR могат да обжалват препоръка (dispute).</p>
<ul>
  <li><strong>preventive</strong> — служителят е в норма, но trend-ът се влошава; препоръка за разговор</li>
  <li><strong>corrective</strong> — служителят е в риск; конкретни стъпки за подобрение</li>
  <li><strong>escalation</strong> — критична ситуация; незабавно уведомяване на HR директор</li>
</ul>
<p><strong>Статуси на препоръка:</strong> pending (нова) → applied (приложена)/ dismissed (отхвърлена)/ disputed (обжалвана)</p>
""",
                "order": 3
            },
            {
                "title": "IPIP-50 Личностен тест (Big Five)",
                "content": """
<h2>IPIP-50 — Психологически профил (Big Five)</h2>

<p>IPIP-50 е 50-въпросен тест, който измерва петте големи личностни фактора (Big Five).
Служителите могат да го попълнят от страницата <strong>Моят поведенчески профил</strong>.</p>

<h3>Петте фактора</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#e3f2fd"><th>Фактор</th><th>Степен 1-10</th><th>Висок резултат (8-10)</th><th>Нисък резултат (1-3)</th></tr>
  <tr>
    <td><strong>Отвореност (Openness)</strong></td>
    <td>Креативност, любопитство</td>
    <td>Изобретателен, артистичен, търси нови преживявания</td>
    <td>Практичен, конвенционален, предпочита рутина</td>
  </tr>
  <tr>
    <td><strong>Съзнателност (Conscientiousness)</strong></td>
    <td>Организираност, надеждност</td>
    <td>Организиран, отговорен, спазва срокове</td>
    <td>Спонтанен, небрежен, мързелив</td>
  </tr>
  <tr>
    <td><strong>Екстраверсия (Extraversion)</strong></td>
    <td>Общителност, енергичност</td>
    <td>Дружелюбен, енергичен, търси социални контакти</td>
    <td>Срамежлив, резервиран, предпочита самота</td>
  </tr>
  <tr>
    <td><strong>Дружелюбност (Agreeableness)</strong></td>
    <td>Сътрудничество, емпатия</td>
    <td>Състрадателен, доверчив, кооперативен</td>
    <td>Критичен, конкурентен, скептичен</td>
  </tr>
  <tr>
    <td><strong>Невротизъм (Neuroticism)</strong></td>
    <td>Емоционална стабилност</td>
    <td>Тревожен, чувствителен на стрес, емоционален</td>
    <td>Спокоен, емоционално стабилен, устойчив на стрес</td>
  </tr>
</table>

<h3>Как работи</h3>
<ol>
  <li><strong>Избор на шаблон:</strong> HR избира/създава шаблон с 50 въпроса от общо 200 (IPIP-200) през <code>/admin/behavioral-analysis/templates</code></li>
  <li><strong>Попълване:</strong> Служителят попълва теста от <code>/my-behavioral-profile</code> — Likert скала 1-5, 5 страници (по 10 въпроса на фактор)</li>
  <li><strong>Scoring:</strong> Всеки отговор се трансформира според посоката (positive = нормално, reverse = 6 - отговор). Суровите резултати се нормализират към Sten скала (1-10)</li>
  <li><strong>Интерпретация:</strong> Генерира се текстово описание за всеки фактор според нивото (нисък/среден/висок/много висок)</li>
  <li><strong>Корекция на метрики:</strong> Личностният профил се използва за коригиране на burnout и engagement метриките (напр. човек с висок невротизъм може да има burnout надценка, която се коригира)</li>
</ol>

<h3>Как HR създава шаблон</h3>
<ol>
  <li>Отидете на <strong>Поведенчески анализ → Шаблони тестове</strong></li>
  <li>Натиснете <strong>"Нов шаблон"</strong></li>
  <li>Въведете име (напр. "IPIP-50 стандартен")</li>
  <li>Изберете <strong>точно 50 въпроса</strong> от таблицата (препоръчително: по 10 от всеки Big Five фактор)</li>
  <li>Кликнете <strong>"Запази"</strong></li>
  <li>Ако е активен, служителите ще видят шаблона в профила си</li>
</ol>
<p>Може да създадете няколко шаблона, но само <strong>един активен</strong> се показва на служителите.</p>
""",
                "order": 4
            },
            {
                "title": "Pulse Survey и Triangulation",
                "content": """
<h2>Pulse Survey и Triangulation</h2>

<h3>Pulse Survey — месечна анкета</h3>
<p>Кратка анонимна анкета (5 въпроса), която служителят попълва от <strong>Моят поведенчески профил</strong>.</p>

<h4>Въпроси</h4>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#e3f2fd"><th>Въпрос</th><th>Скала</th><th>Какво измерва</th></tr>
  <tr><td>Чувство на burnout</td><td>1-5</td><td>Ниво на изчерпване според служителя</td></tr>
  <tr><td>Ангажираност</td><td>1-5</td><td>Колко ангажиран се чувства</td></tr>
  <tr><td>Ниво на стрес</td><td>1-5</td><td>Субективен стрес</td></tr>
  <tr><td>Енергия</td><td>1-5</td><td>Ниво на енергия напоследък</td></tr>
  <tr><td>Удовлетвореност от работата</td><td>1-5</td><td>Обща удовлетвореност</td></tr>
</table>

<h3>Triangulation — триангулация на данни</h3>
<p>Комбинира обективни данни (OT часове, болнични) със субективна самооценка (pulse survey).</p>

<p><strong>Формула:</strong></p>
<p><code>adjusted_score = objective_score × 0.6 + pulse_score × 0.4</code></p>

<p><strong>Пример:</strong></p>
<ul>
  <li>Обективен burnout = 0.7 (много OT + чести болнични)</li>
  <li>Pulse survey burnout = 0.3 (служителят казва, че се чувства добре)</li>
  <li>Adjusted = 0.7 × 0.6 + 0.3 × 0.4 = <strong>0.54</strong> (at_risk, но не critical)</li>
  <li>Confidence = 0.6 (разминаване между обективно и субективно)</li>
</ul>

<p><strong>Кога confidence е висок:</strong></p>
<ul>
  <li>Обективните данни и pulse survey съвпадат → confidence 0.9-1.0</li>
  <li>Няма pulse survey → confidence 0.7-0.8 (разчитаме само на обективни данни)</li>
  <li>Pulse е стар > 30 дни → confidence спада с 0.1 на месец</li>
  <li>Няма никакви данни → confidence 0.3 (insufficient_data статус)</li>
</ul>
""",
                "order": 5
            },
            {
                "title": "Organizational Health и Bias Detection",
                "content": """
<h2>Организационно здраве и Bias монитор</h2>

<h3>Organizational Health Dashboard</h3>
<p>Страницата <strong>/admin/behavioral-analysis/health</strong> показва агрегирани данни за цялата компания,
разделени по отдели. Полезно за:</p>
<ul>
  <li>Сравнение между отдели — кой отдел е най-здрав и кой е най-рисков</li>
  <li>Проследяване на trend-ове на ниво отдел</li>
  <li>Идентифициране на системни проблеми (is_systemic_issue = true)</li>
</ul>

<h4>Ключови показатели</h4>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#e3f2fd"><th>Показател</th><th>Описание</th></tr>
  <tr><td>avg_burnout_risk</td><td>Среден burnout риск за отдела</td></tr>
  <tr><td>avg_attendance</td><td>Средно присъствие</td></tr>
  <tr><td>avg_efficiency</td><td>Средна ефективност</td></tr>
  <tr><td>avg_punctuality</td><td>Средна точност</td></tr>
  <tr><td>anomaly_count</td><td>Брой активни аномалии в отдела</td></tr>
  <tr><td>turnover_rate</td><td>Текучество в отдела</td></tr>
  <tr><td>trend</td><td>Обща посока (improving/stable/declining)</td></tr>
  <tr><td>is_systemic_issue</td><td>Отделът има системен проблем (burnout > 0.7 или аномалии > 5)</td></tr>
</table>

<h3>Bias Detection — откриване на отклонения</h3>
<p>Страницата <strong>/admin/behavioral-analysis/bias</strong> (или мутация <code>computeBiasReport</code>)
сравнява отдели по двойки и търси статистически значими разлики в burnout_risk.</p>

<p><strong>Как работи:</strong></p>
<ul>
  <li>Взима всички отдели с поне 1 служител</li>
  <li>Сравнява средния burnout_risk между всяка двойка отдели</li>
  <li>Ако разликата > 0.2 — създава bias находка (finding)</li>
  <li>Генерира препоръка (напр. "Review workload distribution between Отдел А and Отдел Б")</li>
</ul>

<p><strong>Кога да използвате:</strong></p>
<ul>
  <li>При съмнение за неравномерно разпределение на натоварването</li>
  <li>Преди реорганизация на отдели</li>
  <li>Месечен преглед на здравето на отделите</li>
</ul>

<p><strong>Ограничения:</strong> Нужни са поне 2 отдела с данни; малките отдели (1-2 човека) дават по-слабо статистически значими резултати.</p>
""",
                "order": 6
            },
            {
                "title": "Правила за препоръки (Rule Engine)",
                "content": """
<h2>Правила за препоръки — Rule Engine</h2>

<p>Модулът позволява на HR да създава персонализирани правила за генериране на препоръки.
Правилата се управляват от <strong>/admin/behavioral-analysis/rules</strong>.</p>

<h3>Типове условия (condition_type)</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#e3f2fd"><th>Тип</th><th>Описание</th><th>Пример</th></tr>
  <tr>
    <td><strong>threshold</strong></td>
    <td>Проверка на конкретна метрика спрямо праг</td>
    <td><code>burnout_risk > 0.5</code></td>
  </tr>
  <tr>
    <td><strong>composite</strong></td>
    <td>Комбинация от няколко метрики</td>
    <td><code>burnout_risk > 0.3 AND attendance < 70</code></td>
  </tr>
  <tr>
    <td><strong>trend</strong></td>
    <td>Проверка на trend направлението</td>
    <td><code>trend_direction == "declining" AND p < 0.05</code></td>
  </tr>
  <tr>
    <td><strong>custom_expression</strong></td>
    <td>Сложна логика с multiple условия</td>
    <td>Комбинация от всички горе</td>
  </tr>
</table>

<h3>Как се създава правило</h3>
<ol>
  <li>Отидете на <strong>Поведенчески анализ → Правила</strong></li>
  <li>Въведете <strong>име</strong> и описание на правилото</li>
  <li>Изберете <strong>тип условие</strong> и метрика (threshold)</li>
  <li>Задайте <strong>праг</strong> (threshold value) и посока (above/below)</li>
  <li>Попълнете <strong>текст на препоръката</strong> (може със заместители като {employee_name})</li>
  <li>Изберете <strong>автоматично изпълнение</strong> (auto_execute) или само recommendation</li>
  <li>Включете <strong>shadow mode</strong> ако искате да тествате без да създавате реални препоръки</li>
</ol>

<h3>Вградени (system) правила</h3>
<p>Системата идва с няколко вградени правила, които не могат да бъдат изтрити:</p>
<ul>
  <li>Burnout > 0.5 → препоръка за намаляване на натоварването</li>
  <li>Отсъствие 3+ дни без отпуск → аномалия</li>
  <li>Извънреден труд > 48h → аномалия</li>
  <li>Статистически значим declining trend → preventive препоръка</li>
</ul>
""",
                "order": 7
            },
            {
                "title": "System Health и мониторинг",
                "content": """
<h2>System Health — Здраве на системата</h2>
<p>Страницата <strong>/admin/behavioral-analysis/system</strong> показва техническия статус на модула.</p>

<h3>Показатели</h3>
<ul>
  <li><strong>last_computation_at</strong> — последно успешно изчисляване на профили</li>
  <li><strong>last_computation_status</strong> — успех/грешка от последното изчисляване</li>
  <li><strong>employees_processed</strong> — колко служители са обработени</li>
  <li><strong>employees_failed</strong> — колко са пропуснати поради грешки</li>
  <li><strong>circuit_breaker_open</strong> — дали circuit breaker е активиран (предпазва от претоварване)</li>
  <li><strong>circuit_breaker_failure_count</strong> — брой последователни грешки</li>
  <li><strong>triggered_alerts_today</strong> — брой аларми за деня</li>
  <li><strong>last_bias_check</strong> — последен bias report</li>
</ul>

<h3>Circuit Breaker</h3>
<p>Ако системата detect-не 5+ последователни грешки при изчисляване, circuit breaker се отваря
и спира автоматичните изчисления. Това предпазва базата данни от претоварване.
След като проблемът бъде отстранен, circuit breaker-ът се затваря автоматично на следващия цикъл.</p>

<h3>Какво да направите при грешки</h3>
<ol>
  <li>Проверете <strong>System Health</strong> страницата</li>
  <li>Ако circuit breaker е open — изчакайте следващия цикъл или рестартирайте модула</li>
  <li>Ако employees_failed > 0 — проверете логовете за конкретни грешки</li>
  <li>Аномалии с много високо severity може да блокират изчисляването</li>
</ol>
""",
                "order": 8
            },
            {
                "title": "Стъпки за начало работа",
                "content": """
<h2>Как да започнете с модула</h2>

<h3>За HR администратор</h3>
<ol>
  <li><strong>Активирайте модула</strong> — уверете се, че <code>behavioral_analysis</code> е включен в Настройки → Модули</li>
  <li><strong>Създайте IPIP-50 шаблон</strong> — отидете на <strong>Шаблони тестове</strong> и създайте шаблон с 50 въпроса</li>
  <li><strong>Проверете настройките</strong> — <strong>Поведенчески анализ → Настройки</strong>:
    <ul>
      <li>Период за raw профилиране (по подразбиране 90 дни)</li>
      <li>Период за агрегирани профили (12 месеца)</li>
      <li>Auto cleanup на стари данни</li>
    </ul>
  </li>
  <li><strong>Изчакайте нощното изчисляване</strong> — профилите се създават автоматично в 02:00</li>
  <li><strong>Разгледайте dashboard-а</strong> — <strong>Поведенчески анализ → Обзор</strong> за преглед на профилите</li>
  <li><strong>Насърчете служителите</strong> да попълнят IPIP-50 теста от <strong>Моят поведенчески профил</strong></li>
  <li><strong>Създайте правила</strong> за автоматични препоръки (<strong>Правила</strong>)</li>
</ol>

<h3>За служител</h3>
<ol>
  <li>Отидете на <strong>Моят поведенчески профил</strong> (от sidebar менюто)</li>
  <li>Попълнете <strong>IPIP-50 теста</strong> (50 въпроса, ~10 минути)</li>
  <li>Всеки месец попълвайте <strong>Pulse survey</strong> (5 въпроса, ~1 минута)</li>
  <li>Преглеждайте препоръките и обжалвайте ако не сте съгласни</li>
</ol>

<h3>Важни изисквания за данни</h3>
<ul>
  <li>Служителят трябва да има <strong>активен трудов договор</strong> и позиция</li>
  <li>Трябва да има поне <strong>5 работни дни</strong> с данни в TimeLog</li>
  <li>За efficiency метриката — трябва да има <strong>производствени задачи</strong></li>
  <li>За punctuality — трябва да има <strong>график (WorkSchedule)</strong> със start_time</li>
  <li>Pulse survey може да се попълва всеки месец (не по-често от 20 дни)</li>
</ul>

<h3>Често срещани проблеми</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#fff3e0"><th>Проблем</th><th>Причина</th><th>Решение</th></tr>
  <tr><td>Профилът показва "insufficient_data"</td><td>Няма достатъчно данни за изчисляване</td><td>Изчакайте 5+ работни дни с данни</td></tr>
  <tr><td>Не виждам IPIP-50 теста</td><td>Няма активен шаблон</td><td>HR да създаде шаблон в Шаблони тестове</td></tr>
  <tr><td>Pulse survey не се записва</td><td>Твърде скоро след последния</td><td>Изчакайте 20 дни от последния pulse</td></tr>
  <tr><td>Не виждам модула в менюто</td><td>Модулът е изключен</td><td>Включете го в Настройки → Модули</td></tr>
</table>
""",
                "order": 9
            },
            {
                "title": "Често задавани въпроси (FAQ)",
                "content": """
<h2>Често задавани въпроси за поведенческия анализ</h2>

<h3>❓ Как се различава attendance_score от engagement_score?</h3>
<p><strong>Attendance score</strong> (присъствие) измерва колко дни служителят идва на работа — чисто обективен показател.
<strong>Engagement score</strong> (ангажираност) измерва психологическата връзка на служителя с работата чрез UWES-9.
Може да имате служител, който идва всеки ден (attendance = 100), но е напълно дезингийджмънтнат (engagement = 20).</p>

<h3>❓ Какво е UWES-9?</h3>
<p>Utrecht Work Engagement Scale — 9 въпроса, измерващи 3 измерения:</p>
<ul>
  <li><strong>Vigor</strong> (енергия) — "На работа се чувствам пълен/на с енергия"</li>
  <li><strong>Dedication</strong> (отдаденост) — "Работата ми вдъхва ентусиазъм"</li>
  <li><strong>Absorption</strong> (потопеност) — "Когато работя, забравям за всичко около мен"</li>
</ul>

<h3>❓ Как се изчислява burnout рискът?</h3>
<p>Burnout = комбинация от извънреден труд (overtime_factor) и честота на болнични (leave_factor),
след което се коригира спрямо личностния профил (IPIP-50) и pulse survey самооценка (triangulation).</p>

<h3>❓ Какво е Triangulation?</h3>
<p>Сравняване на обективни данни (OT часове, болнични) със субективна самооценка (pulse survey).
Ако и двата източника сочат едно и също — confidence е висок. Ако се разминават — търсим обяснение.
Формула: <code>adjusted = objective × 0.6 + pulse × 0.4</code></p>

<h3>❓ Какво е IPIP-50?</h3>
<p>50-въпросен тест за измерване на Big Five (Големите 5) личностни фактори:</p>
<ul>
  <li><strong>Openness</strong> — отвореност към нови преживявания</li>
  <li><strong>Conscientiousness</strong> — съзнателност, организираност</li>
  <li><strong>Extraversion</strong> — екстравертност, общителност</li>
  <li><strong>Agreeableness</strong> — съгласие, сътрудничество</li>
  <li><strong>Neuroticism</strong> — невротизъм, емоционална нестабилност</li>
</ul>
<p>Резултатът се използва за корекция на метриките (напр. невротизъм = по-висок burnout при същите условия).</p>

<h3>❓ Може ли модулът да се използва за уволнения?</h3>
<p><strong>Не.</strong> Модулът е създаден за <strong>превенция и подкрепа</strong>, не за наказателни мерки.
Целта е да идентифицира служители, които се нуждаят от помощ, и да предложи конкретни стъпки
за подобрение. Вземането на кадрови решения само на база поведенчески анализ е лоша практика.</p>

<h3>❓ Какви данни се съхраняват?</h3>
<ul>
  <li>Обективни данни: TimeLog, ProductionTask, LeaveRequest (вече съществуващи)</li>
  <li>Self-report: UWES-9 (9 въпроса, тримесечно), Pulse survey (5 въпроса, месечно)</li>
  <li>IPIP-50 psycho-portrait (50 въпроса, еднократно с опция за повторение)</li>
  <li>Manager feedback (опционално, при обжалване на препоръка)</li>
</ul>

<h3>❓ Колко често се обновяват данните?</h3>
<p>Основните метрики се изчисляват дневно (в 02:00 през нощта).
Pulse survey е месечен (не по-често от 20 дни), UWES-9 е тримесечен, IPIP-50 е по желание.</p>

<h3>❓ Какъв е минималният период за trend анализ?</h3>
<p>Mann-Kendall тестът изисква минимум 3 точки от данни (<code>n ≥ 3</code>), но препоръчителният
минимум е 14 дни (2 седмици) за статистически значими резултати. P-value под 0.05 се счита за значим.</p>

<h3>❓ Какво е разликата между органично здраве и bias detection?</h3>
<p><strong>Organizational Health</strong> показва абсолютните стойности на метриките за всеки отдел.
<strong>Bias Detection</strong> търси <em>разлики</em> между отдели — дори и двата отдела да са "здрави",
единият може да е систематично по-натоварен.</p>

<h3>❓ Може ли служителят да обжалва препоръка?</h3>
<p>Да. Всяка препоръка може да бъде обжалвана (disputed) от служителя или от HR.
При обжалване се изисква причина и опционални бележки. Обжалваните препоръки се преглеждат от HR.</p>

<h3>❓ Какъв е смисълът на XAI contribution factors?</h3>
<p>Показва на служителя <strong>кое конкретно</strong> влияе на профила му.
Например: "Извънредният труд допринася 60% за burnout риска, а болничните 40%".
Това прави модела прозрачен и разбираем.</p>
""",
                "order": 10
            }
        ]
    },
    {
        "title": "Настройки",
        "icon": "settings",
        "order": 10,
        "articles": [
            {
                "title": "Общи настройки",
                "content": """
<h2>Конфигурация на системата</h2>
<h3>Компания</h3>
<ul>
<li>Име и адрес</li>
<li>ЕИК/БУЛСТАТ</li>
<li>МОЛ</li>
<li>Данни за фактури</li>
</ul>
<h3>Работно време</h3>
<ul>
<li>Стандартно работно време</li>
<li>Почивни дни</li>
<li>Официални празници</li>
</ul>
<h3>Модули</h3>
<p>Активирайте/деактивирайте модули според нуждите:</p>
<ul>
<li>Присъствие и графици</li>
<li>Отпуски</li>
<li>ТРЗ</li>
<li>Счетоводство</li>
<li>Склад</li>
<li>Автопарк</li>
<li>Контрол на достъпа</li>
</ul>
""",
                "order": 0
            },
            {
                "title": "Сигурност",
                "content": """
<h2>Настройки за сигурност</h2>
<h3>Пароли</h3>
<ul>
<li>Минимална дължина: 8 символа</li>
<li>Изискване за сложност (главни, малки, цифри, специални)</li>
<li>Периодична смяна (90 дни)</li>
</ul>
<h3>Сесии</h3>
<ul>
<li>Автоматично изтичане: 8 часа</li>
<li>Предупреждение преди изтичане: 5 минути</li>
</ul>
<h3>Двуфакторна автентикация (2FA)</h3>
<p>Препоръчва се за администратори и мениджъри.</p>
""",
                "order": 1
            }
        ]
    }
]


async def seed_documentation():
    """Попълва документацията с реални данни"""
    async with AsyncSessionLocal() as session:
        # Изтриваме старата документация
        await session.execute(DocumentationArticle.__table__.delete())
        await session.execute(DocumentationCategory.__table__.delete())
        await session.commit()
        
        # Намираме admin потребител
        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            print("Грешка: admin@example.com не е намерен")
            return
        
        # Създаваме категориите и статиите
        for cat_data in DOCUMENTATION_DATA:
            category = DocumentationCategory(
                title=cat_data["title"],
                icon=cat_data["icon"],
                order=cat_data["order"],
                is_active=True,
                created_at=sofia_now(),
                updated_at=sofia_now()
            )
            session.add(category)
            await session.flush()
            
            for article_data in cat_data["articles"]:
                article = DocumentationArticle(
                    category_id=category.id,
                    title=article_data["title"],
                    content=article_data["content"],
                    order=article_data["order"],
                    is_active=True,
                    created_by=admin_user.id,
                    created_at=sofia_now(),
                    updated_at=sofia_now()
                )
                session.add(article)
            
            await session.commit()
            print(f"✓ Създадена категория: {cat_data['title']} ({len(cat_data['articles'])} статии)")
        
        print(f"\n✅ Документацията е попълнена успешно!")
        print(f"   Категории: {len(DOCUMENTATION_DATA)}")
        print(f"   Статии: {sum(len(c['articles']) for c in DOCUMENTATION_DATA)}")


if __name__ == "__main__":
    asyncio.run(seed_documentation())
