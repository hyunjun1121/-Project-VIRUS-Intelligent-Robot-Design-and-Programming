import Link from "next/link";
import Image from "next/image";

export default function Navbar() {
  return (
    <nav className="w-full flex items-center justify-between px-6 py-3 border-b border-gray-200 bg-white">
      <Link href="/" className="flex items-center gap-2">
        <Image src="/favicon.ico" alt="Logo" width={28} height={28} />
        <span className="font-bold text-lg tracking-tight">sgl-eval</span>
      </Link>
      <div className="flex items-center gap-6">
        <Link href="/" className="text-gray-700 hover:text-black font-medium transition-colors">Leaderboard</Link>
        <Link href="/benchmark" className="text-gray-700 hover:text-black font-medium transition-colors">Details</Link>
      </div>
    </nav>
  );
} 