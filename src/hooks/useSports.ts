"use client";

import { useState, useEffect } from 'react';
import { fetchSports } from '@/lib/api';
import type { Sport } from '@/lib/types';

interface UseSportsResult {
  sports: Sport[];
  isLoading: boolean;
  error: string | null;
  remainingCredits: string | null;
  refetch: () => Promise<void>;
}

export function useSports(): UseSportsResult {
  const [sports, setSports] = useState<Sport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [remainingCredits, setRemainingCredits] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetchSports();
      setSports(response.sports);
      setRemainingCredits(response.remaining_credits);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sports');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return {
    sports,
    isLoading,
    error,
    remainingCredits,
    refetch: fetchData,
  };
}
