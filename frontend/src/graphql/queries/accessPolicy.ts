import { gql } from '@apollo/client';

export const ACCESS_LEVELS_QUERY = gql`
  query GetAccessLevels($companyId: Int!) {
    accessLevels(companyId: $companyId) {
      id
      name
      description
      companyId
      isActive
      createdAt
      updatedAt
      zoneAssignments {
        id
        accessLevelId
        zoneId
        scheduleId
        outOfHoursBehavior
        priority
      }
      userCount
    }
  }
`;

export const ACCESS_LEVEL_QUERY = gql`
  query GetAccessLevel($id: Int!) {
    accessLevel(id: $id) {
      id
      name
      description
      companyId
      isActive
      createdAt
      updatedAt
      zoneAssignments {
        id
        accessLevelId
        zoneId
        scheduleId
        outOfHoursBehavior
        priority
      }
      userCount
    }
  }
`;

export const ACCESS_SCHEDULES_QUERY = gql`
  query GetAccessSchedules($companyId: Int!) {
    accessSchedules(companyId: $companyId) {
      id
      name
      companyId
      timezone
      config
      holidayOverrideAuto
      isActive
      createdAt
    }
  }
`;
