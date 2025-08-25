import { atomWithInfiniteQuery, atomWithQuery } from 'jotai-tanstack-query';
import { atom } from 'jotai';
import { apiClient } from '../lib/api';
import type { 
  BenchmarkId, 
  BenchmarkResponse, 
  BenchmarkTableRow, 
  BenchmarkMetadataResponse 
} from '../api_types/benchmarks';

export const selectedBenchmarkAtom = atom<BenchmarkId>("1");

export const benchmarkAtom = atomWithInfiniteQuery((get) => {
  const selectedBenchmark = get(selectedBenchmarkAtom);
  const LIMIT = 20;
  
  return {
    queryKey: ['benchmark', selectedBenchmark],
    queryFn: ({ pageParam = 0 }) => apiClient.getBenchmarkData(selectedBenchmark, pageParam, LIMIT),
    getNextPageParam: (lastPage: BenchmarkResponse, allPages: BenchmarkResponse[]) => {
      if (lastPage.table_rows.length < LIMIT) {
        return undefined;
      }
      return allPages.length * LIMIT;
    },
    initialPageParam: 0,
  };
});

export const benchmarkMetadataAtom = atomWithQuery(() => ({
  queryKey: ['benchmark-metadata'],
  queryFn: () => apiClient.getBenchmarkMetadata(),
})); 