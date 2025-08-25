import { atomWithQuery } from 'jotai-tanstack-query';
import { apiClient } from '../lib/api';
import type { LeaderboardResponse } from '../api_types/leaderboard';

// Use atomWithQuery for automatic loading/error state management
export const leaderboardAtom = atomWithQuery(() => ({
  queryKey: ['leaderboard'],
  queryFn: () => apiClient.getLeaderboard(),
})); 