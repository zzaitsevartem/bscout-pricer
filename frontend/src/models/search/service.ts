import { api } from '@/shared/api/axios';
import { createContractChecker } from '@/shared/lib/check-contract';
import { searchHistoryListResponseSchema } from './schema';
import type { SearchHistoryResponse } from './schema';

const checkContract = createContractChecker('models/search');

export const searchApi = {
  clearHistory: () => api.delete<void>('/search/history'),
  getHistory: () =>
    api.get<SearchHistoryResponse[]>('/search/history').then((response) => {
      checkContract(searchHistoryListResponseSchema, response.data, 'GET /search/history');
      return response;
    }),
};
