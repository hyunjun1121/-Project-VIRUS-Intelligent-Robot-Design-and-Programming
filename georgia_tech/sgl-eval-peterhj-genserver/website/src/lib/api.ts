import type { QuestionResponse } from '../api_types/questions';
import type { BenchmarkMetadataResponse, BenchmarkResponse } from '../api_types/benchmarks';
import type { LeaderboardResponse } from '../api_types/leaderboard';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async getQuestion(id: string): Promise<QuestionResponse> {
    return this.request(`/api/questions/${id}`);
  }

  async getBenchmarkMetadata(): Promise<BenchmarkMetadataResponse> {
    return this.request('/api/benchmarks/metadata');
  }

  async getBenchmarkData(benchmarkId: string, offset: number = 0, limit: number = 20): Promise<BenchmarkResponse> {
    const params = new URLSearchParams({
      offset: offset.toString(),
      limit: limit.toString(),
    });
    return this.request(`/api/benchmarks/${benchmarkId}?${params}`);
  }

  async getLeaderboard(): Promise<LeaderboardResponse> {
    return this.request('/api/leaderboard/');
  }
}

export const apiClient = new ApiClient();
