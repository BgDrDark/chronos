import { gql } from '@apollo/client';

export const GET_MY_NOTIFICATIONS = gql`
  query GetMyNotifications($unreadOnly: Boolean = false, $offset: Int = 0, $limit: Int = 50) {
    myNotifications(unreadOnly: $unreadOnly, offset: $offset, limit: $limit) {
      id
      message
      isRead
      createdAt
    }
  }
`;

export const GET_MY_NOTIFICATIONS_COUNT = gql`
  query GetMyNotificationsCount($unreadOnly: Boolean = false) {
    myNotificationsCount(unreadOnly: $unreadOnly)
  }
`;

export const MARK_NOTIFICATION_READ = gql`
  mutation MarkNotificationRead($id: Int!) {
    markNotificationRead(id: $id)
  }
`;

export const MARK_ALL_NOTIFICATIONS_READ = gql`
  mutation MarkAllNotificationsRead {
    markAllNotificationsRead
  }
`;

export const DELETE_NOTIFICATION = gql`
  mutation DeleteNotification($id: Int!) {
    deleteNotification(id: $id)
  }
`;
