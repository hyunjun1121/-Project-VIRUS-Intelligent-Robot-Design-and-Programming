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
import {
  benchmarkAtom,
  selectedBenchmarkAtom,
  benchmarkMetadataAtom,
} from "@/store/benchmark";
import type { BenchmarkTableRow, BenchmarkMetadataResponse } from "@/api_types/benchmarks";
import { useRouter } from "next/navigation";
import BaseTable from "./BaseTable";
import { StatusCard, InfoMessage} from "./CommonUI";

export default function BenchmarkTable() {
  const [
    {
      data,
      isPending,
      isError,
      error,
      fetchNextPage,
      hasNextPage,
      isFetchingNextPage,
    },
  ] = useAtom(benchmarkAtom);
  const [selectedBenchmark] = useAtom(selectedBenchmarkAtom);
  const [metadata] = useAtom(benchmarkMetadataAtom);
  const [sorting, setSorting] = React.useState<SortingState>([
    { id: "id", desc: false },
  ]);

  const currentBenchmarkName = React.useMemo(() => {
    return (
      metadata.data?.benchmarks?.find((option: any) => option.id === selectedBenchmark)?.name ||
      "Unknown"
    );
  }, [metadata.data, selectedBenchmark]);

  const allData = React.useMemo(() => {
    if (!data?.pages) return [];
    return data.pages.flatMap((page: any) => page.table_rows);
  }, [data?.pages]);

  const columns = useBenchmarkColumns(metadata);
  const table = useReactTable({
    data: allData,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    debugTable: false,
  });

  useFetchWhenScrolledToBottom(hasNextPage, isFetchingNextPage, fetchNextPage);

  const router = useRouter();

  if (isPending || metadata.isLoading) return <StatusCard message={`Loading data...`} color="text-gray-400" />;
  if (isError || metadata.error) return <StatusCard message={error?.message} color="text-red-500" />;

  return (
    <div>
      <BaseTable
        table={table}
        onRowClick={row => router.push(`/question?id=${row.original.id}`)}
      />
      {isFetchingNextPage &&  <InfoMessage message="Loading more data..." />}
      {!hasNextPage && allData.length > 0 &&  <InfoMessage message="No more data to load" />}
    </div>
  );
}

function useBenchmarkColumns(metadata: any) {
  const router = useRouter();
  return React.useMemo(() => {
    const baseColumns = [
      {
        accessorKey: "id",
        header: ({ column }: { column: any }) => (
          <ColumnHeader column={column}>Id</ColumnHeader>
        ),
      },
      {
        accessorKey: "question",
        header: "Question",
      },
      {
        accessorKey: "difficulty",
        header: ({ column }: { column: any }) => (
          <ColumnHeader column={column}>Difficulty</ColumnHeader>
        ),
      },
    ];
    const metadataData = metadata.data;
    const modelColumns =
      metadataData?.llms?.map((model: { id: string; name: string }) => ({
        accessorKey: `model_metas.${model.id}.score`,
        header: ({ column }: { column: any }) => (
          <ColumnHeader column={column}>{model.name}</ColumnHeader>
        ),
        cell: (info: any) => {
          const row = info.row.original;
          return (
            <button
              className="w-full h-full hover:underline focus:outline-none"
              onClick={e => {
                e.stopPropagation();
                router.push(`/question?question_id=${row.id}&llm_id=${model.id}`);
              }}
            >
              {info.getValue()}
            </button>
          );
        },
      })) || [];
    return [...baseColumns, ...modelColumns];
  }, [metadata.data, router]);
}

function useFetchWhenScrolledToBottom(hasNextPage: boolean, isFetchingNextPage: boolean, fetchNextPage: () => void) {
  React.useEffect(() => {
    const handleScroll = () => {
      if (
        window.innerHeight + document.documentElement.scrollTop >=
        document.documentElement.offsetHeight - 100
      ) {
        if (hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      }
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);
}

function ColumnHeader({ column, children }: { column: any; children: React.ReactNode }) {
  const sorted = column.getIsSorted();
  return (
    <button
      className="w-full text-left"
      onClick={() => column.toggleSorting(sorted === "asc")}
    >
      {children} {sorted === "asc" ? "↑" : sorted === "desc" ? "↓" : ""}
    </button>
  );
} 