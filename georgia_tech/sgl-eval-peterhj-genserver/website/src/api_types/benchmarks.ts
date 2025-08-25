export type BenchmarkId = string;

export type BenchmarkMeta = {
  id: BenchmarkId;
  name: string;
  description: string;
};

export type LlmMeta = {
  id: string;
  name: string;
};

export type BenchmarkMetadataResponse = {
  benchmarks: BenchmarkMeta[];
  llms: LlmMeta[];
};

export type BenchmarkModelMeta = {
  score: number;
};

export type BenchmarkTableRow = {
  id: number;
  question: string;
  difficulty: number;
  model_metas: Record<string, BenchmarkModelMeta>;
};

export type BenchmarkResponse = {
  table_rows: BenchmarkTableRow[];
}; 