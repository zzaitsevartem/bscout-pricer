import { api } from '@/shared/api/axios';
import { createContractChecker } from '@/shared/lib/check-contract';
import {
  trackedProductListResponseSchema,
  trackedProductResponseSchema,
  trackingUsageResponseSchema,
} from './schema';
import type {
  TrackedProductCreateRequest,
  TrackedProductListResponse,
  TrackedProductResponse,
  TrackedProductUpdateRequest,
  TrackingListParams,
  TrackingUsageResponse,
} from './schema';

const checkContract = createContractChecker('models/tracking');

export const trackingApi = {
  devices: () => api.get<import('./schema').TrackedDevice[]>('/tracking/devices'),
  addDevice: (id: number) => api.put(`/tracking/devices/${id}`),
  removeDevice: (id: number) => api.delete(`/tracking/devices/${id}`),
  usage: () =>
    api.get<TrackingUsageResponse>('/tracking/usage').then((response) => {
      checkContract(trackingUsageResponseSchema, response.data, 'GET /tracking/usage');
      return response;
    }),

  list: (params?: TrackingListParams) =>
    api.get<TrackedProductListResponse>('/tracking', { params }).then((response) => {
      checkContract(trackedProductListResponseSchema, response.data, 'GET /tracking');
      return response;
    }),

  create: (payload: TrackedProductCreateRequest) =>
    api.post<TrackedProductResponse>('/tracking', payload).then((response) => {
      checkContract(trackedProductResponseSchema, response.data, 'POST /tracking');
      return response;
    }),

  update: (trackedId: number, payload: TrackedProductUpdateRequest) =>
    api.patch<TrackedProductResponse>(`/tracking/${trackedId}`, payload).then((response) => {
      checkContract(trackedProductResponseSchema, response.data, `PATCH /tracking/${trackedId}`);
      return response;
    }),

  remove: (trackedId: number) => api.delete<void>(`/tracking/${trackedId}`),
};
