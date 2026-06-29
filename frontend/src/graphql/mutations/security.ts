import { gql } from '@apollo/client';

export const TRIGGER_EMERGENCY = gql`
  mutation TriggerEmergency($input: EmergencyTriggerInput!) {
    triggerEmergency(input: $input) {
      id
      eventType
      scope
      zoneId
      isActive
      triggeredAt
    }
  }
`;

export const RESOLVE_EMERGENCY = gql`
  mutation ResolveEmergency($id: Int!) {
    resolveEmergency(id: $id) {
      id
      isActive
      resolvedAt
    }
  }
`;

export const UPDATE_ZONE_EMERGENCY_SETTINGS = gql`
  mutation UpdateZoneEmergencySettings($id: Int!, $isSafeZone: Boolean, $lockdownBehavior: String, $emergencyContact: String) {
    updateZoneEmergencySettings(id: $id, isSafeZone: $isSafeZone, lockdownBehavior: $lockdownBehavior, emergencyContact: $emergencyContact) {
      id
      isSafeZone
      lockdownBehavior
      emergencyContact
    }
  }
`;
