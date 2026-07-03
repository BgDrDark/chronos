import { gql } from '@apollo/client';

export const CREATE_FLOOR_PLAN = gql`
  mutation CreateFloorPlan($input: FloorPlanInput!) {
    createFloorPlan(input: $input) {
      id
      name
      imagePath
      svgContent
      backgroundImage
      width
      height
      isActive
    }
  }
`;

export const UPDATE_FLOOR_PLAN = gql`
  mutation UpdateFloorPlan($input: UpdateFloorPlanInput!) {
    updateFloorPlan(input: $input) {
      id
      name
      imagePath
      svgContent
      backgroundImage
      width
      height
      isActive
    }
  }
`;

export const DELETE_FLOOR_PLAN = gql`
  mutation DeleteFloorPlan($id: Int!) {
    deleteFloorPlan(id: $id)
  }
`;

export const ADD_DOOR_TO_FLOOR_PLAN = gql`
  mutation AddDoorToFloorPlan($input: FloorPlanDoorInput!) {
    addDoorToFloorPlan(input: $input) {
      id
      floorPlanId
      doorId
      x
      y
      width
      height
      rotation
      label
    }
  }
`;

export const UPDATE_DOOR_ON_FLOOR_PLAN = gql`
  mutation UpdateDoorOnFloorPlan($input: UpdateFloorPlanDoorInput!) {
    updateDoorOnFloorPlan(input: $input) {
      id
      x
      y
      width
      height
      rotation
      label
    }
  }
`;

export const REMOVE_DOOR_FROM_FLOOR_PLAN = gql`
  mutation RemoveDoorFromFloorPlan($id: Int!) {
    removeDoorFromFloorPlan(id: $id)
  }
`;
