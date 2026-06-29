import { gql } from '@apollo/client';

export const CREATE_ELEVATOR_GROUP = gql`
  mutation CreateElevatorGroup($input: ElevatorGroupInput!) {
    createElevatorGroup(input: $input) {
      id
      name
      gatewayId
      terminalId
      controllerType
    }
  }
`;

export const UPDATE_ELEVATOR_GROUP = gql`
  mutation UpdateElevatorGroup($id: Int!, $input: ElevatorGroupUpdateInput!) {
    updateElevatorGroup(id: $id, input: $input) {
      id
      name
      gatewayId
      terminalId
      controllerType
      isActive
    }
  }
`;

export const DELETE_ELEVATOR_GROUP = gql`
  mutation DeleteElevatorGroup($id: Int!) {
    deleteElevatorGroup(id: $id)
  }
`;

export const CREATE_ELEVATOR_FLOOR = gql`
  mutation CreateElevatorFloor($input: ElevatorFloorInput!) {
    createElevatorFloor(input: $input) {
      id
      floorNumber
      name
      zoneId
      relayDeviceId
      relayNumber
      order
    }
  }
`;

export const UPDATE_ELEVATOR_FLOOR = gql`
  mutation UpdateElevatorFloor($id: Int!, $input: ElevatorFloorUpdateInput!) {
    updateElevatorFloor(id: $id, input: $input) {
      id
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

export const DELETE_ELEVATOR_FLOOR = gql`
  mutation DeleteElevatorFloor($id: Int!) {
    deleteElevatorFloor(id: $id)
  }
`;
