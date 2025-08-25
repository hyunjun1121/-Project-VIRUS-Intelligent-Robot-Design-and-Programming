import QuestionDetail from "@/components/QuestionDetail";

export default function QuestionPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-start bg-white py-16 px-4">
      <div className="w-full max-w-4xl">
        <div className="mb-12 flex items-center justify-center">
          <h1 className="text-3xl font-semibold tracking-tight text-gray-900 text-center">Question Details</h1>
        </div>
        <QuestionDetail />
      </div>
    </div>
  );
} 