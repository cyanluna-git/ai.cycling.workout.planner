/**
 * React Query configuration
 * Provides caching and automatic refetching for API data
 */

import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Cache data for 2 hours (matches backend cache)
      staleTime: 2 * 60 * 60 * 1000,
      // Keep unused data in cache for 5 minutes
      gcTime: 5 * 60 * 1000,
      // Retry failed requests 1 time
      retry: 1,
      // Refetch on window focus for fresh data
      refetchOnWindowFocus: true,
      // Don't refetch on mount if data is fresh
      refetchOnMount: false,
    },
  },
});

// Query keys for type safety and consistency
export const queryKeys = {
  fitness: () => ['fitness'] as const,
  weeklyCalendar: () => ['weeklyCalendar'] as const,
  weeklyPlan: (weekStartDate?: string) =>
    weekStartDate ? ['weeklyPlan', weekStartDate] : ['weeklyPlan'] as const,
  todayWorkout: (date?: string) =>
    date ? ['todayWorkout', date] : ['todayWorkout'] as const,
  apiConfigured: () => ['apiConfigured'] as const,
};
