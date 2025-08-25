"use client";
import * as React from "react";
import { useAtom } from "jotai";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  SortingState,
  ColumnDef,
} from "@tanstack/react-table";
import { leaderboardAtom } from "@/store/leaderboard";
import type { LeaderboardTableRow } from "@/api_types/leaderboard";
import BaseTable from "./BaseTable";
import { StatusCard } from "./CommonUI";

export default function LeaderboardTable() {
  const [{ data, isPending, isError, error }] = useAtom(leaderboardAtom);
  const [sorting, setSorting] = React.useState<SortingState>([
    { id: "overall_score", desc: true },
  ]);
  const categoryNames = data?.category_names || [];
  const tableRows = data?.table_rows || [];

  const columns = useLeaderboardColumns(categoryNames);

  const table = useReactTable({
    data: tableRows,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    debugTable: false,
  });

  if (isPending) return <StatusCard message="Loading leaderboard data..." color="text-gray-400" />;
  if (isError) return <StatusCard message={error?.message} color="text-red-500" />;

  const colGroup = (
    <colgroup>
      <col />
      <col />
      <col />
      {categoryNames.map(key => (
        <col key={key} className="w-28" />
      ))}
    </colgroup>
  );

  return (
    <BaseTable table={table} colGroup={colGroup} columnAlign={{ llm_name: 'text-right' }} />
  );
}

function useLeaderboardColumns(categoryNames: string[]): ColumnDef<LeaderboardTableRow>[] {
  return React.useMemo(() => {
    const baseColumns: ColumnDef<LeaderboardTableRow>[] = [
      { accessorKey: "rank", header: "Rank" },
      {
        accessorKey: "llm_name",
        header: "Model",
        cell: (info: any) => (
          <span className="text-right block pl-2">{info.getValue() as string}</span>
        ),
      },
      {
        accessorKey: "overall_score",
        header: ({ column }: { column: any }) => (
          <ColumnHeader column={column}>Overall Score</ColumnHeader>
        ),
      },
    ];
    const categoryColumns = categoryNames.map(key => ({
      accessorFn: (row: LeaderboardTableRow) => row.category_scores[key] || 0,
      id: key,
      header: ({ column }: { column: any }) => (
        <ColumnHeader column={column}>
          {key.charAt(0).toUpperCase() + key.slice(1)}
        </ColumnHeader>
      ),
      cell: (info: any) => (
        <span className={info.column.id === 'llm_name' ? 'text-right block pl-2' : 'text-center block w-full text-center'}>{info.getValue() as string | number}</span>
      ),
    }));
    return [...baseColumns, ...categoryColumns];
  }, [categoryNames]);
}

function ColumnHeader({ column, children }: { column: any; children: React.ReactNode }) {
  const sorted = column.getIsSorted();
  const isModel = column.id === 'llm_name';
  return (
    <button
      className={`w-full font-semibold text-gray-700 focus:outline-none focus:underline ${isModel ? 'text-right' : 'text-center'}`}
      onClick={() => column.toggleSorting(sorted === "asc")}
    >
      {children} {sorted === "asc" ? "↑" : sorted === "desc" ? "↓" : ""}
    </button>
  );
} 