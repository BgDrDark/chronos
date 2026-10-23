import { gql } from '@apollo/client';

export const UPDATE_GATEWAY = gql`
  mutation UpdateGateway($id: Int!, $alias: String, $companyId: Int) {
    updateGateway(id: $id, alias: $alias, companyId: $companyId) {
      id
      alias
      companyId
    }
  }
`;

export const SYNC_GATEWAY_CONFIG = gql`
  mutation SyncGatewayConfig($id: Int!, $direction: String!) {
    syncGatewayConfig(id: $id, direction: $direction)
  }
`;

export const UPDATE_TERMINAL = gql`
  mutation UpdateTerminal($id: Int!, $alias: String, $mode: String, $isActive: Boolean, $config: JSON) {
    updateTerminal(id: $id, alias: $alias, mode: $mode, isActive: $isActive, config: $config) {
      id
      alias
      mode
      isActive
      config
    }
  }
`;

export const DELETE_TERMINAL = gql`
  mutation DeleteTerminal($id: Int!) {
    deleteTerminal(id: $id)
  }
`;

export const BULK_EMERGENCY_ACTION = gql`
  mutation BulkEmergencyAction($action: String!) {
    bulkEmergencyAction(action: $action)
  }
`;
