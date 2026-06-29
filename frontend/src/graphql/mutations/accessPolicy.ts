import { gql } from '@apollo/client';

export const CREATE_ACCESS_LEVEL = gql`
  mutation CreateAccessLevel($input: AccessLevelInput!, $companyId: Int!) {
    createAccessLevel(input: $input, companyId: $companyId) {
      id
      name
      description
      isActive
    }
  }
`;

export const UPDATE_ACCESS_LEVEL = gql`
  mutation UpdateAccessLevel($id: Int!, $input: AccessLevelUpdateInput!) {
    updateAccessLevel(id: $id, input: $input) {
      id
      name
      description
      isActive
    }
  }
`;

export const DELETE_ACCESS_LEVEL = gql`
  mutation DeleteAccessLevel($id: Int!) {
    deleteAccessLevel(id: $id)
  }
`;

export const CREATE_ACCESS_SCHEDULE = gql`
  mutation CreateAccessSchedule($input: AccessScheduleInput!, $companyId: Int!) {
    createAccessSchedule(input: $input, companyId: $companyId) {
      id
      name
      timezone
      config
      holidayOverrideAuto
      isActive
    }
  }
`;

export const UPDATE_ACCESS_SCHEDULE = gql`
  mutation UpdateAccessSchedule($id: Int!, $input: AccessScheduleUpdateInput!) {
    updateAccessSchedule(id: $id, input: $input) {
      id
      name
      timezone
      config
      holidayOverrideAuto
      isActive
    }
  }
`;

export const DELETE_ACCESS_SCHEDULE = gql`
  mutation DeleteAccessSchedule($id: Int!) {
    deleteAccessSchedule(id: $id)
  }
`;

export const ASSIGN_LEVEL_TO_ZONE = gql`
  mutation AssignLevelToZone($input: AssignLevelToZoneInput!) {
    assignLevelToZone(input: $input) {
      id
      accessLevelId
      zoneId
      scheduleId
      outOfHoursBehavior
      priority
    }
  }
`;

export const REMOVE_LEVEL_FROM_ZONE = gql`
  mutation RemoveLevelFromZone($accessLevelId: Int!, $zoneId: Int!) {
    removeLevelFromZone(accessLevelId: $accessLevelId, zoneId: $zoneId)
  }
`;

export const ASSIGN_ACCESS_LEVEL_TO_USER = gql`
  mutation AssignAccessLevelToUser($input: AssignAccessLevelToUserInput!) {
    assignAccessLevelToUser(input: $input)
  }
`;

export const REMOVE_ACCESS_LEVEL_FROM_USER = gql`
  mutation RemoveAccessLevelFromUser($userId: Int!) {
    removeAccessLevelFromUser(userId: $userId)
  }
`;
