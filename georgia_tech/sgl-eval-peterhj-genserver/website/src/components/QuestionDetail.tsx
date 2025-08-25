"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useAtom } from "jotai";
import { questionAtom, questionIdAtom } from "@/store/question";
import type { QuestionResponse } from "@/api_types/questions";
import ChatConversationUI from "./ChatConversationUI";
import { StatusCard } from "./CommonUI";

export default function QuestionDetail() {
  const searchParams = useSearchParams();
  const questionId = searchParams.get("question_id");
  const llmId = searchParams.get("llm_id") ?? undefined;
  if (!questionId) return <NoData />;
  return <QuestionDetailContent questionId={questionId} llmId={llmId} />;
}

function QuestionDetailContent({ questionId, llmId }: { questionId: string; llmId?: string }) {
  const [, setQuestionId] = useAtom(questionIdAtom);
  const [{ data, isPending, isError, error }] = useAtom(questionAtom);
  const [selectedItem, setSelectedItem] = useState<{ llm_idx: number; attempt_idx: number }>({ llm_idx: 0, attempt_idx: 0 });

  useEffect(() => {
    setQuestionId(questionId);
  }, [questionId, setQuestionId]);

  useEffect(() => {
    if (!data) return;
    let llm_idx = 0;
    if (llmId && data.llm_answers && data.llm_answers.length > 0) {
      const idx = data.llm_answers.findIndex(ans => ans.llm_id === llmId);
      if (idx !== -1) llm_idx = idx;
    }
    setSelectedItem({ llm_idx, attempt_idx: 0 });
  }, [data, llmId]);

  if (isPending) return <StatusCard message="Loading conversation data..." color="text-gray-400" />;
  if (isError) return <StatusCard message={error?.message} color="text-red-500" />;
  if (!data) return <NoData />;

  const models = data.llm_answers;
  const selectedModel = models[selectedItem.llm_idx];
  const selectedAttempt = selectedModel?.attempts[selectedItem.attempt_idx] || selectedModel?.attempts[0];

  return (
    <div className="space-y-6">
      <QuestionHeader data={data} />
      <ModelAttemptSelectorCard
        models={models}
        selectedItem={selectedItem}
        setSelectedItem={setSelectedItem}
      />
      {selectedModel && selectedAttempt && (
        <ChatConversationUI messages={selectedAttempt.messages} />
      )}
    </div>
  );
}

function QuestionHeader({ data }: { data: QuestionResponse }) {
  return (
    <div className="rounded-2xl shadow bg-white p-6 mb-4">
      <div className="flex flex-wrap items-center text-gray-400 text-sm mb-2 gap-x-6 gap-y-2">
        <span>ID: {data.id}</span>
        <span>Difficulty: {data.difficulty}</span>
        <span>Category: {data.benchmark_category}</span>
        <button
          className="ml-auto px-3 py-1 rounded-md bg-white hover:bg-gray-100 text-xs text-gray-500 transition-colors border border-gray-200"
          onClick={() => window.open('https://github.com/sgl-project/sgl-eval/issues/new', '_blank')}
        >
          Feedback
        </button>
      </div>
      <div className="font-semibold text-lg text-gray-900 mb-2">Question</div>
      <div className="mb-2 whitespace-pre-line text-gray-800 text-base leading-relaxed">{data.question}</div>
    </div>
  );
}

function ModelAttemptSelectorCard({
  models,
  selectedItem,
  setSelectedItem,
}: {
  models: QuestionResponse["llm_answers"];
  selectedItem: { llm_idx: number; attempt_idx: number };
  setSelectedItem: (item: { llm_idx: number; attempt_idx: number }) => void;
}) {
  return (
    <div className="rounded-2xl shadow bg-white p-4 mb-4 flex flex-wrap gap-4 items-center">
      {models.map((model, llm_idx) => (
        <div key={model.llm_name} className="flex items-center gap-2">
          <button
            className={`text-sm px-2 py-1 rounded transition-colors ${selectedItem.llm_idx === llm_idx ? "bg-blue-100 text-blue-700" : "text-gray-700"}`}
            onClick={() => {
              setSelectedItem({ llm_idx, attempt_idx: 0 });
            }}
          >
            {model.llm_name}
          </button>
          <div className="flex gap-1">
            {model.attempts.map((attempt, attempt_idx) => {
              const correct = attempt.score > 0.5;
              const selected = selectedItem.llm_idx === llm_idx && selectedItem.attempt_idx === attempt_idx;
              return (
                <ModelAttemptSelectorItemButton
                  key={attempt_idx}
                  correct={correct}
                  selected={selected}
                  onClick={() => setSelectedItem({ llm_idx, attempt_idx })}
                  title={correct ? "Correct" : "Incorrect"}
                />
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

function ModelAttemptSelectorItemButton({
  correct,
  selected,
  onClick,
  title,
}: {
  correct: boolean;
  selected: boolean;
  onClick: () => void;
  title: string;
}) {
  return (
    <button
      className={`
        w-3 h-3 rounded-full border flex items-center justify-center text-xs transition-colors
        ${correct ? "bg-green-400 border-green-500 text-white" : "bg-red-300 border-red-400 text-white"}
        ${selected ? "ring-1 ring-blue-400 ring-offset-1" : ""}
      `}
      onClick={onClick}
      title={title}
      type="button"
    >
    </button>
  );
}

function NoData() {
  return (
    <div className="rounded-2xl shadow bg-white p-8 flex items-center justify-center min-h-[180px]">
      <div className="text-gray-400 text-base">No data available.</div>
    </div>
  );
}
