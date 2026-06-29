import { gql } from '@apollo/client';

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
      parentZoneId
      inheritPermissions
      traversalOrder
      parentZone {
        id
        zoneId
        name
      }
      children {
        id
        zoneId
        name
      }
      authorizedUsers {
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
