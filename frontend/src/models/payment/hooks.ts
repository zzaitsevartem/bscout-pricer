import { useEffect, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { paymentApi } from './service';
import type { PaymentCreateRequest } from './schema';

export function usePlans() {
  return useQuery({
    queryKey: ['payment', 'plans'],
    queryFn: () => paymentApi.getPlans(),
    staleTime: 5 * 60 * 1000,
  });
}

export function usePaymentHistory(options?: { enabled?: boolean }) {
  const queryClient = useQueryClient();
  const previousPending = useRef<number[]>([]);
  const query = useQuery({
    queryKey: ['payment', 'history'],
    queryFn: () => paymentApi.getHistory(),
    enabled: options?.enabled ?? true,
    retry: false,
    refetchInterval: (query) => query.state.data?.some((payment) => payment.status === 'pending') ? 3000 : false,
  });
  useEffect(() => {
    if (!query.data) return;
    const completed = query.data.some((payment) =>
      previousPending.current.includes(payment.id) && payment.status !== 'pending');
    previousPending.current = query.data.filter((payment) => payment.status === 'pending')
      .map((payment) => payment.id);
    if (completed) {
      queryClient.invalidateQueries({ queryKey: ['user', 'subscription'] });
      queryClient.invalidateQueries({ queryKey: ['tracking'] });
    }
  }, [query.data, queryClient]);
  return query;
}

export function useSubscribe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PaymentCreateRequest) => paymentApi.subscribe(data),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['payment', 'history'] });
      queryClient.invalidateQueries({ queryKey: ['user', 'subscription'] });
    },
  });
}

export function useCancelSubscription() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => paymentApi.cancel(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'subscription'] });
      queryClient.invalidateQueries({ queryKey: ['payment', 'history'] });
    },
  });
}
