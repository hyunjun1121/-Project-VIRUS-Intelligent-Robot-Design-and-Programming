"use client";
import * as React from "react";
import { flexRender } from "@tanstack/react-table";

interface BaseTableProps {
  table: any;
  className?: string;
  onRowClick?: (row: any) => void;
  colGroup?: React.ReactNode;
  columnAlign?: Record<string, string>;
}

export default function BaseTable({ table, className = "", onRowClick, colGroup, columnAlign = {} }: BaseTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl shadow bg-white">
      <table className={`min-w-full text-center border-separate border-spacing-0 ${className}`}>
        {colGroup}
        <thead>
          {table.getHeaderGroups().map((headerGroup: any) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header: any) => (
                <th
                  key={header.id}
                  className={
                    `px-6 py-4 text-sm font-semibold text-gray-700 bg-gray-100 first:rounded-tl-2xl last:rounded-tr-2xl border-b border-gray-200` +
                    ` ${columnAlign[header.column.id] || 'text-center'}`
                  }
                >
                  {header.isPlaceholder
                    ? null
                    : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row: any) => (
            <tr
              key={row.id}
              className="hover:bg-gray-50 transition-colors cursor-pointer"
              onClick={onRowClick ? () => onRowClick(row) : undefined}
            >
              {row.getVisibleCells().map((cell: any) => (
                <td
                  key={cell.id}
                  className="px-6 py-3 text-gray-900 border-b border-gray-100 last:border-r-0 first:border-l-0"
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
} 