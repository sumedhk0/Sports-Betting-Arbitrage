"use client";

import { OpportunityCard } from './OpportunityCard';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, AlertCircle } from 'lucide-react';
import type { Opportunity } from '@/lib/types';

interface OpportunityListProps {
  opportunities: Opportunity[];
  isLoading?: boolean;
  error?: string | null;
  totalFound?: number;
}

export function OpportunityList({
  opportunities,
  isLoading,
  error,
  totalFound,
}: OpportunityListProps) {
  if (error) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
        <h3 className="text-lg font-semibold mb-2">Scan Failed</h3>
        <p className="text-muted-foreground">{error}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="rounded-lg border p-4 space-y-3">
            <div className="flex justify-between">
              <Skeleton className="h-6 w-64" />
              <Skeleton className="h-6 w-24" />
            </div>
            <Skeleton className="h-4 w-48" />
            <div className="space-y-2 pt-2">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (opportunities.length === 0) {
    return (
      <div className="text-center py-12 border rounded-lg bg-muted/20">
        <TrendingUp className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">No Opportunities Found</h3>
        <p className="text-muted-foreground max-w-md mx-auto">
          Select a sport and bookmakers, then click scan to find arbitrage opportunities.
          Results depend on current market conditions.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {totalFound !== undefined && totalFound > 0 && (
        <div className="text-sm text-muted-foreground">
          Showing {opportunities.length} of {totalFound} opportunities (sorted by ROI)
        </div>
      )}
      {opportunities.map((opp, index) => (
        <OpportunityCard key={`${opp.event}-${opp.market}-${index}`} opportunity={opp} rank={index + 1} />
      ))}
    </div>
  );
}
