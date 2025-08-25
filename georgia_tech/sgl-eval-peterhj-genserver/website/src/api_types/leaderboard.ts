export type LeaderboardTableRow = {
  rank: number;
  llm_name: string;
  overall_score: number;
  category_scores: Record<string, number>;
};

export type LeaderboardResponse = {
  category_names: string[];
  table_rows: LeaderboardTableRow[];
}; 