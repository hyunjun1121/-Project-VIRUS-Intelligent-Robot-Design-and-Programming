import LeaderboardTable from "@/components/LeaderboardTable";

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-start bg-white py-16 px-4">
      <div className="w-full max-w-5xl">
        <div className="mb-12 flex items-center justify-between">
          <h1 className="text-3xl font-semibold tracking-tight text-gray-900 w-full text-center">Leaderboard</h1>
        </div>
        <LeaderboardTable />
      </div>
    </div>
  );
}
