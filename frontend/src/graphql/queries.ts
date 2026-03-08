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
