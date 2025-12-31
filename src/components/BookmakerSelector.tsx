"use client";

import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import type { Bookmaker } from '@/lib/types';

interface BookmakerSelectorProps {
  bookmakers: Bookmaker[];
  selectedBookmakers: string[];
  onToggle: (key: string) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export function BookmakerSelector({
  bookmakers,
  selectedBookmakers,
  onToggle,
  onSelectAll,
  onDeselectAll,
  isLoading,
  disabled,
}: BookmakerSelectorProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-4 w-24" />
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-10" />
          ))}
        </div>
      </div>
    );
  }

  const allSelected = selectedBookmakers.length === bookmakers.length;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">
          Bookmakers <span className="text-muted-foreground">({selectedBookmakers.length} selected, min 2)</span>
        </label>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onSelectAll}
            disabled={disabled || allSelected}
          >
            Select All
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onDeselectAll}
            disabled={disabled || selectedBookmakers.length === 0}
          >
            Clear
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {bookmakers.map((bookmaker) => {
          const isSelected = selectedBookmakers.includes(bookmaker.key);
          return (
            <button
              key={bookmaker.key}
              onClick={() => onToggle(bookmaker.key)}
              disabled={disabled}
              className={`
                p-3 rounded-lg border text-sm font-medium transition-all
                ${isSelected
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-card hover:bg-accent border-border'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              {bookmaker.name}
            </button>
          );
        })}
      </div>

      {selectedBookmakers.length < 2 && selectedBookmakers.length > 0 && (
        <p className="text-sm text-destructive">Please select at least 2 bookmakers</p>
      )}
    </div>
  );
}
