// Централизиран файл с текстове за help tooltips на всички полета

// ==================== ОБЩИ ПОЛЕТА ====================

export const commonFieldsHelp = {
  name: 'Наименование на обекта',
  description: 'Описание или бележка',
  address: 'Пълен адрес по местоживеене/работа',
  email: 'Електронна поща (валиден имейл адрес)',
  phone: 'Телефонен номер за връзка',
  phoneNumber: 'Телефонен номер за връзка (+359 или 0)',
  notes: 'Допълнителни бележки',
};

// ==================== ПОТРЕБИТЕЛИ ====================

export const userFieldsHelp = {
  firstName: 'Собственото име на служителя',
  surname: 'Бащино име (незадължително)',
  lastName: 'Фамилията на служителя',
  egn: '10-цифрен Единен Граждански Номер',
  birthDate: 'Дата на раждане (ГГГГ-ММ-ДД)',
  iban: 'Номер на банкова сметка (BGXX XXXX XXXX XXXX XXXX)',
  address: 'Пълен адрес по местоживеене',
  phoneNumber: 'Телефонен номер за връзка (+359 или 0)',
  username: 'Уникално име за вход в системата (поне 3 символа)',
  email: 'Електронна поща (задължителна за вход)',
  password: 'Поне 8 символа, главни, малки, цифри',
  passwordConfirm: 'Повтори паролата за потвърждение',
  roleId: 'Ниво на достъп на служителя',
  companyId: 'Фирмата, в която работи служителят',
  departmentId: 'Отделът във фирмата',
  positionId: 'Заеманата длъжност',
  isActive: 'Дали акаунтът е активен',
  passwordForceChange: 'Принудителна смяна при първи вход',
  contractType: 'Вид на трудовия договор',
  contractNumber: 'Уникален номер на договора',
  contractStartDate: 'Начална дата на договора',
  contractEndDate: 'Крайна дата на договора',
  baseSalary: 'Брутна месечна заплата',
  workHoursPerWeek: 'Работни часове на седмица (по подразбиране 40)',
  probationMonths: 'Продължителност в месеци',
  salaryCalculationType: 'Брутно или нето изчисление',
  salaryInstallmentsCount: 'Брой месечни вноски',
  monthlyAdvanceAmount: 'Фиксирана сума за аванс',
  taxResident: 'Дали е данъчен резидент на България',
  hasIncomeTax: 'Удържане на данък върху дохода (10%)',
  insuranceContributor: 'Дали има здравни осигуровки',
  paymentDay: 'Ден от месеца за изплащане',
  nightWorkRate: 'Множител за нощен труд (напр. 0.50 = +50%)',
  overtimeRate: 'Множител за извънреден труд',
  holidayRate: 'Множител за работа на празници',
  workClass: 'Категория на труда (I, II, III)',
  dangerousWork: 'Работа при вредни условия',
};

// ==================== СКЛАД ====================

export const warehouseFieldsHelp = {
  ingredientName: 'Наименование на продукта/съставката',
  barcode: 'Баркод или QR код',
  unit: 'Единица за измерване (kg, l, бр., гр., мл)',
  currentStock: 'Налично количество на склад',
  baselineMinStock: 'Минимално количество за автоматична поръчка',
  isPerishable: 'Дали продуктът е с ограничен срок на годност',
  expiryWarningDays: 'Брой дни преди изтичане за предупреждение',
  storageZone: 'Зона за съхранение в склада',
  price: 'Цена без ДДС',
};

// ==================== ПАРТИДИ ====================

export const batchFieldsHelp = {
  batchNumber: 'Уникален номер на партидата',
  quantity: 'Количество в килограми или литри',
  expiryDate: 'Дата на изтичане на срока на годност',
  receivedAt: 'Дата на получаване на партидата',
  invoiceNumber: 'Номер на съпровождащата фактура',
  priceNoVat: 'Цена без ДДС',
  priceWithVat: 'Цена с включено ДДС',
  supplierId: 'Доставчик на партидата',
};

// ==================== ДОСТАВЧИЦИ ====================

export const supplierFieldsHelp = {
  supplierName: 'Наименование на фирмата доставчик',
  contactPerson: 'Лице за контакт при доставката',
  eik: 'Единен идентификационен код на фирмата',
  vatNumber: 'ДДС номер на фирмата',
  phone: 'Телефон за връзка',
  address: 'Адрес на офиса/склада',
};

// ==================== РЕЦЕПТИ ====================

export const recipeFieldsHelp = {
  name: 'Наименование на рецептата',
  description: 'Описание на рецептата',
  category: 'Категория (торта, кекс, бисквити и т.н.)',
  yieldQuantity: 'Количество на крайния продукт',
  yieldUnit: 'Единица за измерване на крайния продукт',
  shelfLifeDays: 'Срок на годност в дни (преди замразяване)',
  shelfLifeFrozenDays: 'Срок на годност в дни (след замразяване)',
  productionDeadlineDays: 'Срок за производство в дни',
  defaultPieces: 'Брой парчета/броеве по подразбиране',
  standardQuantity: 'Стандартно количество за една партида',
  markupPercentage: 'Процент надценка върху себестойността',
  costPrice: 'Изчислена себестойност на рецептата',
  sellingPrice: 'Продажна цена на рецептата',
  portionPrice: 'Цена за една порция/брой',
};

// ==================== СЪСТАВКИ НА РЕЦЕПТА ====================

export const recipeIngredientFieldsHelp = {
  ingredientId: 'Избери съставка от списъка',
  quantityGross: 'Количество в грамове или милилитри',
  wastePercentage: 'Процент загуба при обработка',
};

// ==================== АВТОПАРК ====================

export const fleetFieldsHelp = {
  registrationNumber: 'Регистрационен номер на МПС',
  brand: 'Марка на превозното средство',
  model: 'Модел на превозното средство',
  year: 'Година на производство',
  vehicleType: 'Тип на превозното средство',
  fuelType: 'Вид гориво',
  status: 'Текущ статус на автомобила',
  mileage: 'Пробег в километри',
  mileageDate: 'Дата на отчитане на километрите',
  fuelLiters: 'Количество гориво в литри',
  pricePerLiter: 'Цена на горивото за литър',
  fuelLocation: 'Место на зареждане',
  repairType: 'Вид ремонт',
  repairDescription: 'Описание на извършения ремонт',
  serviceProvider: 'Сервиз/фирма извършила ремонта',
  repairCost: 'Стойност на ремонта',
  insuranceType: 'Вид застраховка',
  insuranceCompany: 'Застрахователна компания',
  insurancePremium: 'Застрахователна премия',
  insuranceExpiryDate: 'Дата на изтичане на застраховката',
};

// ==================== СЧЕТОВОДСТВО ====================

export const accountingFieldsHelp = {
  date: 'Дата на операцията',
  amount: 'Сума на операцията',
  description: 'Описание на операцията',
  referenceNumber: 'Референтен номер на документа',
  accountNumber: 'Номер на сметката',
  accountName: 'Наименование на сметката',
  accountType: 'Тип на сметката (активна, пасивна)',
  bic: 'БИК код на банката',
  bankName: 'Наименование на банката',
  documentType: 'Вид на документа (фактура, дебитно известие)',
  griff: 'Гриф на документа',
  paymentMethod: 'Начин на плащане',
  paymentStatus: 'Статус на плащането',
  vatRate: 'Процент ДДС',
  discountPercent: 'Процент отстъпка',
  subtotal: 'Междинна сума без ДДС',
  vatAmount: 'Сума на ДДС',
  total: 'Обща сума с ДДС',
  supplierName: 'Име на доставчика',
  clientName: 'Име на клиента',
  clientEik: 'ЕИК на клиента',
  clientAddress: 'Адрес на клиента',
};

// ==================== ТРЗ ====================

export const trzFieldsHelp = {
  nightWorkEnabled: 'Включване на автоматично изчисление за нощен труд',
  nightWorkRate: 'Процент/множител за нощен труд',
  overtimeEnabled: 'Включване на автоматично изчисление за извънреден труд',
  overtimeRate: 'Процент/множител за извънреден труд',
  holidayWorkEnabled: 'Включване на автоматично изчисление за работа на празници',
  holidayWorkRate: 'Процент/множител за празничен труд',
  businessTripsEnabled: 'Включване на командировъчни добавки',
  dailyAllowance: 'Дневна надбавка за командировка',
};

// ==================== ГРАФИК ====================

export const scheduleFieldsHelp = {
  shiftName: 'Наименование на смяната',
  startTime: 'Час на започване',
  endTime: 'Час на приключване',
  toleranceMinutes: 'Толеранс в минути за късно влизане/ранно излизане',
  breakMinutes: 'Продължителност на почивката в минути',
  coefficient: 'Коефициент за изчисление на заплатата',
  scheduleDate: 'Дата на графика',
  rotationPattern: 'Шаблон за ротация на смените',
};

// ==================== ОТПУСКИ ====================

export const leaveFieldsHelp = {
  leaveType: 'Вид на отпуската',
  startDate: 'Начална дата на отпуската',
  endDate: 'Крайна дата на отпуската',
  reason: 'Причина/основание за отпуската',
  approvedBy: 'Одобрил ръководител',
  approvedAt: 'Дата на одобрение',
};

// ==================== ПРОИЗВОДСТВО ====================

export const productionFieldsHelp = {
  orderNumber: 'Номер на производствената поръчка',
  recipeId: 'Избери рецепта за производство',
  plannedQuantity: 'Планирано количество за производство',
  actualQuantity: 'Фактически произведено количество',
  productionDate: 'Дата на производство',
  workstationId: 'Работна станция/машина',
  status: 'Статус на поръчката',
  notes: 'Бележки по производството',
};

// ==================== ПОРЪЧКИ ====================

export const orderFieldsHelp = {
  orderNumber: 'Номер на поръчката',
  clientName: 'Име на клиента',
  clientPhone: 'Телефон за връзка с клиента',
  deliveryAddress: 'Адрес за доставка',
  deliveryDate: 'Дата за доставка',
  orderStatus: 'Статус на поръчката',
  totalAmount: 'Обща сума на поръчката',
  paidAmount: 'Платена сума',
  notes: 'Бележки по поръчката',
};

// ==================== ОРГАНИЗАЦИЯ ====================

export const organizationFieldsHelp = {
  companyName: 'Наименование на фирмата',
  eik: 'Единен идентификационен код',
  bulstat: 'БУЛСТАТ номер',
  vatNumber: 'ДДС номер',
  mol: 'Материално отговорно лице',
  departmentName: 'Наименование на отдела',
  departmentHead: 'Началник на отдела',
  positionTitle: 'Наименование на длъжността',
};

// ==================== НАСТРОЙКИ ====================

export const settingsFieldsHelp = {
  maxLoginAttempts: 'Брой неуспешни опити за вход преди заключване',
  lockoutMinutes: 'Време за заключване в минути след неуспешни опити',
  latitude: 'Географска ширина (напр. 42.6977)',
  longitude: 'Географска дължина (напр. 23.3219)',
  radius: 'Радиус в метри за GPS проверката',
  cutoffDate: 'Дата за архивиране - всичко преди нея ще бъде изтрито',
};

// ==================== ВЕДОМОСТИ ====================

export const payrollFieldsHelp = {
  payrollStartDate: 'Начална дата на периода за ведомостта',
  payrollEndDate: 'Крайна дата на периода за ведомостта',
  selectEmployees: 'Избери конкретни служители или остави празно за всички',
  maxInsuranceBase: 'Максимален осигурителен праг за месец',
  employeeInsuranceRate: 'Процент на осигуровките за служител',
  incomeTaxRate: 'Процент на данък върху дохода (ДОД)',
  noiCompensationPercent: 'Процент обезщетение за НОИ',
  employerPaidSickDays: 'Брой дни платени от работодателя при болнични',
  hourlyRate: 'Часова ставка за изчисление',
  monthlySalary: 'Месечна заплата (бруто)',
  workHoursPerWeek: 'Работни часове на седмица',
  currency: 'Валута за заплатата',
  vacationDays: 'Брой дни платен отпуск годишно',
  overtimeCoefficient: 'Коефициент за извънреден труд',
  taxDeduction: 'Данъчно облекчение (10%)',
  healthInsurance: 'Здравна осигуровка',
  bonusAmount: 'Сума на бонуса',
  bonusDate: 'Дата на бонуса',
  bonusDescription: 'Описание на бонуса (незадължително)',
  templateName: 'Име на шаблона',
  templateDescription: 'Описание на шаблона',
  contractType: 'Вид на договора (пълно/ непълно работно време)',
  workHoursPerWeekTemplate: 'Работни часове на седмица',
  probationMonths: 'Продължителност на пробния период в месеци',
  paymentDay: 'Ден от месеца за изплащане',
  nightWorkRate: 'Процент/множител за нощен труд',
  overtimeRateTemplate: 'Множител за извънреден труд',
  holidayRate: 'Множител за празничен труд',
  salaryCalculationType: 'Начин на изчисляване (бруто/нетно)',
  annexChangeType: 'Вид промяна в анекса',
  newBaseSalary: 'Нова базова заплата',
  newWorkHoursPerWeek: 'Нови работни часове на седмица',
  clauseTitle: 'Заглав на клаузата',
  clauseCategory: 'Категория на клаузата',
  clauseContent: 'Съдържание на клаузата',
};

// ==================== ЕКСПОРТ ====================

// Комбиниран обект за лесен достъп
export const fieldsHelp = {
  ...commonFieldsHelp,
  ...userFieldsHelp,
  ...warehouseFieldsHelp,
  ...batchFieldsHelp,
  ...supplierFieldsHelp,
  ...recipeFieldsHelp,
  ...recipeIngredientFieldsHelp,
  ...fleetFieldsHelp,
  ...accountingFieldsHelp,
  ...trzFieldsHelp,
  ...scheduleFieldsHelp,
  ...leaveFieldsHelp,
  ...productionFieldsHelp,
  ...orderFieldsHelp,
  ...organizationFieldsHelp,
  ...settingsFieldsHelp,
  ...payrollFieldsHelp,
};

export default fieldsHelp;
