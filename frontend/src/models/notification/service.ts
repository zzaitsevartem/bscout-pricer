import { api } from '@/shared/api/axios';
import { createContractChecker } from '@/shared/lib/check-contract';
import {
  notificationListResponseSchema,
  notificationResponseSchema,
  unreadCountResponseSchema,
} from './schema';
import type {
  NotificationListParams,
  NotificationListResponse,
  NotificationResponse,
  UnreadCountResponse,
} from './schema';

const checkContract = createContractChecker('models/notification');

export const notificationApi = {
  list: (params?: NotificationListParams) =>
    api.get<NotificationListResponse>('/notifications', { params }).then((response) => {
      checkContract(notificationListResponseSchema, response.data, 'GET /notifications');
      return response;
    }),

  unreadCount: () =>
    api.get<UnreadCountResponse>('/notifications/unread-count').then((response) => {
      checkContract(unreadCountResponseSchema, response.data, 'GET /notifications/unread-count');
      return response;
    }),

  markRead: (notificationId: number) =>
    api.post<NotificationResponse>(`/notifications/${notificationId}/read`).then((response) => {
      checkContract(
        notificationResponseSchema,
        response.data,
        `POST /notifications/${notificationId}/read`,
      );
      return response;
    }),
};
