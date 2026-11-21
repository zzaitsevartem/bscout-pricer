import { api } from '@/shared/api/axios';
import { createContractChecker } from '@/shared/lib/check-contract';
import {
  priceHistoryListResponseSchema,
  productListResponseSchema,
  productResponseSchema,
} from './schema';
import type {
  PriceHistoryResponse,
  ProductListResponse,
  ProductResponse,
  ProductSearchParams,
} from './schema';

const checkContract = createContractChecker('models/product');

export const productApi = {
  search: (params: ProductSearchParams) =>
    api.get<ProductListResponse>('/products', { params }).then((response) => {
      checkContract(productListResponseSchema, response.data, 'GET /products');
      return response;
    }),

  getById: (id: number) =>
    api.get<ProductResponse>(`/products/${id}`).then((response) => {
      checkContract(productResponseSchema, response.data, `GET /products/${id}`);
      return response;
    }),

  getPriceHistory: (id: number) =>
    api.get<PriceHistoryResponse[]>(`/products/${id}/price-history`).then((response) => {
      checkContract(
        priceHistoryListResponseSchema,
        response.data,
        `GET /products/${id}/price-history`,
      );
      return response;
    }),
};
