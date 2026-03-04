import { gql } from '@apollo/client';

export const CREATE_ACCESS_ZONE = gql`
  mutation CreateAccessZone($input: AccessZoneInput!) {
    createAccessZone(input: $input) {
      id
      zoneId
      name
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

export const UPDATE_GATEWAY_ALIAS = gql`
  mutation UpdateGatewayAlias($id: Int!, $alias: String!) {
    updateGatewayAlias(id: $id, alias: $alias) {
      id
      name
      alias
    }
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

export const BULK_EMERGENCY_ACTION = gql`
  mutation BulkEmergencyAction($action: String!) {
    bulkEmergencyAction(action: $action)
  }
`;
