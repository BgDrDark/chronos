import { gql } from '@apollo/client';

export const CREATE_ACCESS_ZONE = gql`
  mutation CreateAccessZone($input: AccessZoneInput!) {
    createAccessZone(input: $input) {
      id
      zoneId
      name
      parentZoneId
      requiredAuthFactors
      interlockEnabled
      interlockTimeout
      dualAuthEnabled
      dualAuthTimeout
    }
  }
`;

export const UPDATE_ACCESS_ZONE = gql`
  mutation UpdateAccessZone($id: Int!, $input: AccessZoneInput!) {
    updateAccessZone(id: $id, input: $input) {
      id
      zoneId
      name
      parentZoneId
      requiredAuthFactors
      interlockEnabled
      interlockTimeout
      dualAuthEnabled
      dualAuthTimeout
    }
  }
`;

export const DELETE_ACCESS_ZONE = gql`
  mutation DeleteAccessZone($id: Int!) {
    deleteAccessZone(id: $id)
  }
`;

export const CREATE_ACCESS_DOOR = gql`
  mutation CreateAccessDoor($input: AccessDoorInput!) {
    createAccessDoor(input: $input) {
      id
      doorId
      name
    }
  }
`;

export const DELETE_ACCESS_DOOR = gql`
  mutation DeleteAccessDoor($id: Int!) {
    deleteAccessDoor(id: $id)
  }
`;

export const OPEN_DOOR = gql`
  mutation OpenDoor($id: Int!) {
    openDoor(id: $id)
  }
`;

export const UPDATE_DOOR_TERMINAL = gql`
  mutation UpdateDoorTerminal($id: Int!, $terminalId: String, $terminalMode: String) {
    updateDoorTerminal(id: $id, terminalId: $terminalId, terminalMode: $terminalMode) {
      id
      doorId
      terminalId
      terminalMode
    }
  }
`;

export const CREATE_ACCESS_CODE = gql`
  mutation CreateAccessCode($input: AccessCodeInput!) {
    createAccessCode(input: $input) {
      id
      code
      codeType
    }
  }
`;

export const REVOKE_ACCESS_CODE = gql`
  mutation RevokeAccessCode($id: Int!) {
    revokeAccessCode(id: $id)
  }
`;

export const DELETE_ACCESS_CODE = gql`
  mutation DeleteAccessCode($id: Int!) {
    deleteAccessCode(id: $id)
  }
`;

export const ASSIGN_ZONE_TO_USER = gql`
  mutation AssignZoneToUser($userId: Int!, $zoneId: Int!) {
    assignZoneToUser(userId: $userId, zoneId: $zoneId)
  }
`;

export const REMOVE_ZONE_FROM_USER = gql`
  mutation RemoveZoneFromUser($userId: Int!, $zoneId: Int!) {
    removeZoneFromUser(userId: $userId, zoneId: $zoneId)
  }
`;

export const BULK_UPDATE_USER_ACCESS = gql`
  mutation BulkUpdateUserAccess($userIds: [Int!]!, $zoneIds: [Int!]!, $action: String!) {
    bulkUpdateUserAccess(userIds: $userIds, zoneIds: $zoneIds, action: $action)
  }
`;
