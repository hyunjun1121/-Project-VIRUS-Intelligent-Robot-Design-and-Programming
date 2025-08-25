"use client";

import React from "react";
import type { Message } from "@/api_types/questions";

export type ChatConversationUIProps = {
  messages: Message[];
  className?: string;
};

export default function ChatConversationUI({ messages, className = "" }: ChatConversationUIProps) {
  return (
    <div className={`space-y-4 ${className}`}>
      {messages.map((message, index) => (
        <ChatMessage key={index} message={message} />
      ))}
    </div>
  );
}

function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <div className="flex">
      <div
        className={`rounded-2xl px-5 py-3 shadow-sm transition-all
          ${isUser ? "bg-gray-100 text-gray-900" : "bg-white text-gray-900"}
        `}
      >
        <div className={`text-xs font-medium mb-1 ${isUser ? "text-gray-400" : "text-gray-400"}`}>
          {isUser ? "You" : "Assistant"}
        </div>
        <div className="whitespace-pre-line text-base leading-relaxed">{message.content}</div>
      </div>
    </div>
  );
} 