"use client";
import * as React from "react";
import { useAtom } from "jotai";
import { selectedBenchmarkAtom, benchmarkMetadataAtom } from "@/store/benchmark";
import { HiChevronDown, HiCheck } from "react-icons/hi";

export default function BenchmarkDropdown() {
  const [selectedBenchmark, setSelectedBenchmark] = useAtom(selectedBenchmarkAtom);
  const [metadata] = useAtom(benchmarkMetadataAtom);
  const [isOpen, setIsOpen] = React.useState(false);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  const selectedOption = metadata.data?.benchmarks?.find(option => option.id === selectedBenchmark);

  useClickOutside(dropdownRef, () => setIsOpen(false));

  if (metadata.isLoading) return <PendingDropdown message="Loading benchmarks..." />;
  if (metadata.error) return <ErrorDropdown message="Error loading benchmarks" />;

  return (
    <div className="relative" ref={dropdownRef}>
      <div className="relative">
        <DropdownButton
          isOpen={isOpen}
          selectedOption={selectedOption}
          onClick={() => setIsOpen(!isOpen)}
        />
        {isOpen && (
          <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
            {metadata.data?.benchmarks?.map(option => (
              <DropdownOption
                key={option.id}
                option={option}
                selected={selectedBenchmark === option.id}
                onSelect={() => {
                  setSelectedBenchmark(option.id);
                  setIsOpen(false);
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function DropdownButton({ isOpen, selectedOption, onClick }: {
  isOpen: boolean;
  selectedOption: any;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className="relative w-full bg-white border border-gray-300 rounded-md shadow-sm pl-3 pr-10 py-2 text-left cursor-default focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm hover:border-gray-400 transition-colors"
      onClick={onClick}
      aria-haspopup="listbox"
      aria-expanded={isOpen}
    >
      <span className="block truncate">
        {selectedOption ? selectedOption.name : "Select a benchmark..."}
      </span>
      <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
        <HiChevronDown
          className={`h-5 w-5 text-gray-400 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
          aria-hidden="true"
        />
      </span>
    </button>
  );
}

function DropdownOption({ option, selected, onSelect }: {
  option: any;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      className={`${selected ? "text-gray-900 bg-blue-100" : "text-gray-900 hover:bg-gray-100"} cursor-default select-none relative py-2 pl-3 pr-9 w-full text-left`}
      onClick={onSelect}
    >
      <div className="flex flex-col">
        <span className="block truncate font-medium">{option.name}</span>
        <span className={`block truncate text-sm ${selected ? "text-gray-500" : "text-gray-500"}`}>{option.description}</span>
      </div>
      {selected && (
        <span className="absolute inset-y-0 right-0 flex items-center pr-4">
          <HiCheck className="h-5 w-5" aria-hidden="true" />
        </span>
      )}
    </button>
  );
}

function useClickOutside(ref: React.RefObject<HTMLElement | null>, handler: (event: MouseEvent) => void) {
  React.useEffect(() => {
    const listener = (event: MouseEvent) => {
      if (!ref.current || ref.current.contains(event.target as Node)) return;
      handler(event);
    };
    document.addEventListener("mousedown", listener);
    return () => {
      document.removeEventListener("mousedown", listener);
    };
  }, [ref, handler]);
}

export function PendingDropdown({ message = "Loading..." }: { message?: string }) {
  return (
    <div className="relative">
      <div className="w-full bg-gray-100 border border-gray-300 rounded-md shadow-sm pl-3 pr-10 py-2 text-left sm:text-sm">
        <span className="text-gray-500">{message}</span>
      </div>
    </div>
  );
}

export function ErrorDropdown({ message = "Error loading data" }: { message?: string }) {
  return (
    <div className="relative">
      <div className="w-full bg-red-50 border border-red-300 rounded-md shadow-sm pl-3 pr-10 py-2 text-left sm:text-sm">
        <span className="text-red-500">{message}</span>
      </div>
    </div>
  );
} 