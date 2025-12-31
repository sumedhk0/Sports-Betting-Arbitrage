"use client";

import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import type { Sport } from '@/lib/types';

interface SportSelectorProps {
  sports: Sport[];
  selectedSport: string;
  onSelect: (value: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export function SportSelector({
  sports,
  selectedSport,
  onSelect,
  isLoading,
  disabled,
}: SportSelectorProps) {
  if (isLoading) {
    return <Skeleton className="h-10 w-full" />;
  }

  // Group sports by category
  const groupedSports = sports.reduce((acc, sport) => {
    const group = sport.group || 'Other';
    if (!acc[group]) {
      acc[group] = [];
    }
    acc[group].push(sport);
    return acc;
  }, {} as Record<string, Sport[]>);

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Sport</label>
      <Select
        value={selectedSport}
        onValueChange={onSelect}
        disabled={disabled}
      >
        <option value="">Select a sport...</option>
        <option value="all">All Sports (Scan Everything)</option>
        {Object.entries(groupedSports).map(([group, groupSports]) => (
          <optgroup key={group} label={group}>
            {groupSports.map((sport) => (
              <option key={sport.key} value={sport.key}>
                {sport.title}
              </option>
            ))}
          </optgroup>
        ))}
      </Select>
    </div>
  );
}
