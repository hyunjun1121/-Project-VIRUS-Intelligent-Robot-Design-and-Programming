import { atom } from 'jotai';
import { atomWithQuery } from 'jotai-tanstack-query';
import { apiClient } from '../lib/api';

export const questionIdAtom = atom<string | null>(null);

export const questionAtom = atomWithQuery((get) => {
  const id = get(questionIdAtom);
  if (!id) {
    return {
      queryKey: ['question', 'null'],
      queryFn: () => Promise.reject(new Error('No question ID provided')),
      enabled: false,
    };
  }
  return {
    queryKey: ['question', id],
    queryFn: () => apiClient.getQuestion(id),
  };
}); 