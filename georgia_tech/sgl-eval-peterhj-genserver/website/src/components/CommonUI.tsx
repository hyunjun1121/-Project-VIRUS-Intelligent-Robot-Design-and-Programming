"use client";
import React from "react";

function InfoMessage({ message, className = "", color = "text-gray-500" }: { message: string; className?: string; color?: string }) {
  return (
    <div className={`text-center py-4 ${className}`}>
      <div className={color}>{message}</div>
    </div>
  );
}

function StatusCard({ message, className = "", color = "text-gray-500" }: { message?: string; className?: string; color?: string }) {
  return (
    <div className={`rounded-2xl shadow bg-white p-8 flex items-center justify-center min-h-[120px] ${className}`}>
      <div className={`${color} text-base`}>{message}</div>
    </div>
  );
}

export { StatusCard, InfoMessage };
