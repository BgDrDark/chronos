import { gql } from '@apollo/client';

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
