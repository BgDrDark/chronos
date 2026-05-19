import { gql } from '@apollo/client';

export const ME_QUERY = gql`
  query Me {
    me {
      id
      email
      username
      firstName
      lastName
      companyId
      isSmtpConfigured
      passwordForceChange
      role {
        name
      }
    }
  }
`;

export const MODULES_QUERY = gql`
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

export const INVENTORY_SESSIONS_QUERY = gql`
  query GetInventorySessions($status: String) {
    inventorySessions(status: $status) {
      id
      startedAt
      completedAt
      status
      protocolNumber
    }
  }
`;

export const INVENTORY_SESSION_ITEMS_QUERY = gql`
  query GetInventorySessionItems($sessionId: Int!) {
    inventorySessionItems(sessionId: $sessionId) {
      id
      ingredientId
      ingredientName
      ingredientUnit
      foundQuantity
      systemQuantity
      difference
      adjusted
    }
  }
`;

export const INVENTORY_BY_BARCODE_QUERY = gql`
  query GetInventoryByBarcode($barcode: String!) {
    inventoryByBarcode(barcode: $barcode) {
      ingredientId
      ingredientName
      ingredientUnit
      systemQuantity
    }
  }
`;

export const INGREDIENTS_QUERY = gql`
  query GetIngredients {
    ingredients {
      id
      name
      unit
      currentPrice
      productType
    }
  }
`;

export const GATEWAYS_QUERY = gql`
  query GetGateways($isActive: Boolean) {
    gateways(isActive: $isActive) {
      id
      name
      hardwareUuid
      alias
      ipAddress
      localHostname
      terminalPort
      webPort
      isActive
      lastHeartbeat
      registeredAt
      companyId
    }
  }
`;

export const GATEWAY_QUERY = gql`
  query GetGateway($id: Int!) {
    gateway(id: $id) {
      id
      name
      hardwareUuid
      alias
      ipAddress
      localHostname
      terminalPort
      webPort
      isActive
      lastHeartbeat
      registeredAt
      companyId
    }
  }
`;

export const COMPANIES_QUERY = gql`
  query GetCompanies {
    companies {
      id
      name
    }
  }
`;

export const TERMINALS_QUERY = gql`
  query GetTerminals($gatewayId: Int, $isActive: Boolean) {
    terminals(gatewayId: $gatewayId, isActive: $isActive) {
      id
      hardwareUuid
      deviceName
      deviceType
      deviceModel
      osVersion
      gatewayId
      isActive
      lastSeen
      totalScans
      alias
      mode
    }
  }
`;

export const PRINTERS_QUERY = gql`
  query GetPrinters($gatewayId: Int!) {
    printers(gatewayId: $gatewayId) {
      id
      name
      printerType
      ipAddress
      port
      protocol
      windowsShareName
      manufacturer
      model
      gatewayId
      isActive
      isDefault
      lastTest
      lastError
    }
  }
`;

export const ACCESS_ZONES_QUERY = gql`
  query GetAccessZones {
    accessZones {
      id
      zoneId
      name
      level
      dependsOn
      requiredHoursStart
      requiredHours_end: requiredHoursEnd
      antiPassbackEnabled
      antiPassbackType
      antiPassbackTimeout
      description
      isActive
      authorizedUsers {
        id
        firstName
        lastName
        email
      }
    }
  }
`;

export const USERS_QUERY = gql`
  query GetUsers {
    users {
      users {
        id
        firstName
        lastName
        email
      }
    }
  }
`;

export const ACCESS_DOORS_QUERY = gql`
  query GetAccessDoors($gatewayId: Int) {
    accessDoors(gatewayId: $gatewayId) {
      id
      doorId
      name
      zoneDbId
      gatewayId
      deviceId
      relayNumber
      terminalId
      terminalMode
      description
      isActive
      isOnline
      lastCheck
      zone {
        id
        name
      }
      gateway {
        id
        name
      }
    }
  }
`;

export const ACCESS_CODES_QUERY = gql`
  query GetAccessCodes($gatewayId: Int) {
    accessCodes(gatewayId: $gatewayId) {
      id
      code
      codeType
      zones
      usesRemaining
      expiresAt
      createdAt
      lastUsedAt
      isActive
      gatewayId
    }
  }
`;

export const ACCESS_LOGS_QUERY = gql`
  query GetAccessLogs($gatewayId: Int, $limit: Int) {
    accessLogs(gatewayId: $gatewayId, limit: $limit) {
      id
      timestamp
      userId
      userName
      zoneId
      zoneName
      doorId
      doorName
      action
      result
      reason
      method
      terminalId
      gatewayId
    }
  }
`;

export const GATEWAY_STATS_QUERY = gql`
  query GetGatewayStats {
    gatewayStats {
      totalGateways
      activeGateways
      inactiveGateways
      totalTerminals
      activeTerminals
      totalPrinters
      activePrinters
    }
  }
`;

export const MAINTENANCE_STATUS_QUERY = gql`
  query GetMaintenanceStatus {
    maintenanceStatus {
      enabled
      scheduledAt
      reason
      minutesUntil
      updatedBy {
        id
        firstName
        lastName
      }
    }
  }
`;

export const SCHEDULE_MAINTENANCE_MUTATION = gql`
  mutation ScheduleMaintenance($input: MaintenanceInput!) {
    scheduleMaintenance(input: $input)
  }
`;

export const CANCEL_MAINTENANCE_MUTATION = gql`
  mutation CancelMaintenance {
    cancelMaintenance
  }
`;

export const UPDATE_SCHEDULE_QUERY = gql`
  query UpdateSchedule {
    updateSchedule {
      id
      enabled
      scheduleType
      scheduledAt
      dayOfWeek
      hour
      minute
      notifyEmail
      lastRunAt
      lastRunStatus
      lastRunOutput
      createdAt
      updatedAt
    }
  }
`;

export const SET_UPDATE_SCHEDULE_MUTATION = gql`
  mutation SetUpdateSchedule($input: UpdateScheduleInput!) {
    setUpdateSchedule(input: $input) {
      id
      enabled
      scheduleType
      scheduledAt
      dayOfWeek
      hour
      minute
      notifyEmail
      lastRunAt
      lastRunStatus
      lastRunOutput
      createdAt
      updatedAt
    }
  }
`;

export const RUN_UPDATE_NOW_MUTATION = gql`
  mutation RunUpdateNow {
    runUpdateNow
  }
`;

export const DEPLOY_STATUS_QUERY = gql`
  query DeployStatus {
    deployStatus {
      isDeploying
      status
      progress
      version
      output
    }
  }
`;

export const GET_SHIFTS_FOR_GRID = gql`
  query GetShiftsForGrid {
    shifts { id name startTime endTime shiftType }
  }
`;

export const GET_SCHEDULES_FOR_GRID = gql`
  query GetSchedulesForGrid($startDate: Date!, $endDate: Date!) {
    workSchedules(startDate: $startDate, endDate: $endDate) {
      id date user { id } shift { id name shiftType startTime endTime }
    }
  }
`;

export const GET_SCHEDULE_STATS = gql`
  query GetScheduleStats($month: Int!, $year: Int!) {
    scheduleStats(month: $month, year: $year) {
      userId userName assignedDays workDaysNorm isComplete
    }
  }
`;

export const GET_TEMPLATES_FOR_PREVIEW = gql`
  query GetTemplatesForPreview {
    scheduleTemplates { id name }
  }
`;

export const GET_TEMPLATE_PREVIEW = gql`
  query TemplatePreview($templateId: Int!, $startDate: Date!, $endDate: Date!) {
    templatePreview(templateId: $templateId, startDate: $startDate, endDate: $endDate) {
      date shiftId shiftName dayIndex
    }
  }
`;

export const SET_WORK_SCHEDULE = gql`
  mutation SetWorkSchedule($userId: Int!, $shiftId: Int!, $date: Date!) {
    setWorkSchedule(userId: $userId, shiftId: $shiftId, date: $date) { id date }
  }
`;

export const COPY_SCHEDULES_FROM_MONTH = gql`
  mutation CopySchedulesFromMonth($userId: Int!, $sourceMonth: Int!, $sourceYear: Int!, $targetMonth: Int!, $targetYear: Int!) {
    copySchedulesFromMonth(userId: $userId, sourceMonth: $sourceMonth, sourceYear: $sourceYear, targetMonth: $targetMonth, targetYear: $targetYear)
  }
`;

export const APPLY_SCHEDULE_TEMPLATE = gql`
  mutation ApplyScheduleTemplate($templateId: Int!, $userId: Int!, $startDate: Date!, $endDate: Date!) {
    applyScheduleTemplate(templateId: $templateId, userId: $userId, startDate: $startDate, endDate: $endDate)
  }
`;

export const GET_USERS_QUERY = gql`
  query GetUsers($limit: Int) {
    users(limit: $limit) {
      users { id email firstName lastName }
      totalCount
    }
  }
`;

export const GET_PUBLIC_HOLIDAYS_QUERY = gql`
  query GetPublicHolidays($year: Int) {
    publicHolidays(year: $year) { id date name localName }
  }
`;

export const GET_ORTHODOX_HOLIDAYS_QUERY = gql`
  query GetOrthodoxHolidays($year: Int) {
    orthodoxHolidays(year: $year) { id date name localName }
  }
`;

export const GET_SHIFTS_QUERY = gql`
  query GetShifts {
    shifts { id name startTime endTime toleranceMinutes breakDurationMinutes payMultiplier shiftType }
  }
`;

export const GET_SCHEDULES_QUERY = gql`
  query GetSchedules($startDate: Date!, $endDate: Date!) {
    workSchedules(startDate: $startDate, endDate: $endDate) {
      id date user { id email firstName lastName } shift { id name startTime endTime shiftType }
    }
  }
`;

export const GET_TIME_LOGS_QUERY = gql`
  query GetTimeLogs($startDate: DateTime!, $endDate: DateTime!) {
    timeLogs(startDate: $startDate, endDate: $endDate) {
      id startTime endTime isManual user { id email firstName lastName }
    }
  }
`;

export const CREATE_SHIFT_MUTATION = gql`
  mutation CreateShift($name: String!, $startTime: String!, $endTime: String!, $tolerance: Int, $breakDuration: Int, $payMultiplier: Decimal) {
    createShift(name: $name, startTime: $startTime, endTime: $endTime, toleranceMinutes: $tolerance, breakDurationMinutes: $breakDuration, payMultiplier: $payMultiplier) { id name }
  }
`;

export const DELETE_SHIFT_MUTATION = gql`
  mutation DeleteShift($id: Int!) { deleteShift(id: $id) }
`;

export const SET_SCHEDULE_MUTATION = gql`
  mutation SetSchedule($userId: Int!, $shiftId: Int!, $date: Date!) {
    setWorkSchedule(userId: $userId, shiftId: $shiftId, date: $date) { id date }
  }
`;

export const DELETE_SCHEDULE_MUTATION = gql`
  mutation DeleteSchedule($id: Int!) { deleteWorkSchedule(id: $id) }
`;

export const DELETE_TIME_LOG_MUTATION = gql`
  mutation DeleteTimeLog($id: Int!) { deleteTimeLog(id: $id) }
`;

export const BULK_SET_SCHEDULE_MUTATION = gql`
  mutation BulkSetSchedule($userIds: [Int!]!, $shiftId: Int!, $startDate: Date!, $endDate: Date!, $daysOfWeek: [Int!]!) {
    bulkSetSchedule(userIds: $userIds, shiftId: $shiftId, startDate: $startDate, endDate: $endDate, daysOfWeek: $daysOfWeek)
  }
`;

export const GET_MONTHLY_WORK_DAYS = gql`
  query GetMonthlyWorkDays($year: Int!, $month: Int!) {
    monthlyWorkDays(year: $year, month: $month) { id daysCount }
  }
`;
