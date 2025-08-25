export type Message = {
  role: "assistant" | "user";
  content: string;
};

export type QuestionAttemptAnswer = {
  index: number;
  score: number;
  messages: Message[];
};

export type QuestionLlmAnswer = {
  llm_id: string;
  llm_name: string;
  attempts: QuestionAttemptAnswer[];
};

export interface QuestionResponse {
  id: string;
  difficulty: number;
  benchmark_category: string;
  question: string;
  llm_answers: QuestionLlmAnswer[];
} 