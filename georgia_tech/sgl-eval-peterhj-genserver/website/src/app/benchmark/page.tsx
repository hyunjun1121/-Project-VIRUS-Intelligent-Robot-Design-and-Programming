import BenchmarkTable from "@/components/BenchmarkTable";
import BenchmarkDropdown from "@/components/BenchmarkDropdown";

export default function BenchmarkPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-start bg-white py-16 px-4">
      <div className="w-full max-w-7xl">
        <div className="mb-12 flex items-center justify-center">
          <h1 className="text-3xl font-semibold tracking-tight text-gray-900">Benchmark Details</h1>
        </div>
        <div className="mb-8 max-w-md">
          <BenchmarkDropdown />
        </div>
        <BenchmarkTable />
      </div>
    </div>
  );
} 