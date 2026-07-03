import { gql } from '@apollo/client';

export const FLOOR_PLANS_QUERY = gql`
  query GetFloorPlans {
    floorPlans {
      id
      name
      imagePath
      svgContent
      backgroundImage
      width
      height
      isActive
      createdAt
      updatedAt
    }
  }
`;

export const FLOOR_PLAN_QUERY = gql`
  query GetFloorPlan($id: Int!) {
    floorPlan(id: $id) {
      id
      name
      imagePath
      svgContent
      backgroundImage
      width
      height
      isActive
      createdAt
      updatedAt
    }
  }
`;

export const FLOOR_PLAN_DOORS_QUERY = gql`
  query GetFloorPlanDoors($floorPlanId: Int!) {
    floorPlanDoors(floorPlanId: $floorPlanId) {
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
