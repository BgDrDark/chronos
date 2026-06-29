import { gql } from '@apollo/client';

export const EMERGENCY_EVENTS_QUERY = gql`
  query GetEmergencyEvents($isActive: Boolean) {
    emergencyEvents(isActive: $isActive) {
      id
      eventType
      scope
      gatewayId
      zoneId
      triggeredBy
      triggeredAt
      resolvedAt
      resolvedBy
      isActive
      notes
      zone {
        id
        name
        zoneId
      }
    }
  }
`;
