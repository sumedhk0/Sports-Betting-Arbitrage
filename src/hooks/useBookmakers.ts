"use client";

import { useState, useEffect } from 'react';
import { fetchBookmakers } from '@/lib/api';
import type { Bookmaker } from '@/lib/types';

interface UseBookmakersResult {
  bookmakers: Bookmaker[];
  isLoading: boolean;
  error: string | null;
}

export function useBookmakers(): UseBookmakersResult {
  const [bookmakers, setBookmakers] = useState<Bookmaker[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetchBookmakers();
        setBookmakers(response.bookmakers);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch bookmakers');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  return {
    bookmakers,
    isLoading,
    error,
  };
}
