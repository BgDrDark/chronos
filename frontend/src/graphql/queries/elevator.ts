import { gql } from '@apollo/client';

export const ELEVATOR_GROUPS_QUERY = gql`
  query GetElevatorGroups {
    elevatorGroups {
      id
      name
      gatewayId
      terminalId
      controllerType
      isActive
      createdAt
      updatedAt
      floors {
        id
        elevatorGroupId
        floorNumber
        name
        zoneId
        relayDeviceId
        relayNumber
        order
        isActive
        zone {
          id
          name
        }
      }
    }
  }
`;

export const ELEVATOR_FLOORS_QUERY = gql`
  query GetElevatorFloors($elevatorGroupId: Int!) {
    elevatorFloors(elevatorGroupId: $elevatorGroupId) {
      id
      elevatorGroupId
      floorNumber
      name
      zoneId
      relayDeviceId
      relayNumber
      order
      isActive
    }
  }
`;
