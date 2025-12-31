"use client";

import { useState, useCallback } from 'react';
import { scanSport } from '@/lib/api';
import type { Opportunity, Sport } from '@/lib/types';

interface UseScanResult {
  opportunities: Opportunity[];
  isScanning: boolean;
  progress: number;
  currentSport: string;
  error: string | null;
  totalFound: number;
  remainingCredits: string | null;
  scanSingleSport: (sportKey: string, bookmakers: string[], includeProps?: boolean) => Promise<void>;
  scanMultipleSports: (sports: Sport[], bookmakers: string[], includeProps?: boolean) => Promise<void>;
  clearResults: () => void;
}

export function useScan(): UseScanResult {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentSport, setCurrentSport] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [totalFound, setTotalFound] = useState(0);
  const [remainingCredits, setRemainingCredits] = useState<string | null>(null);

  const scanSingleSport = useCallback(async (
    sportKey: string,
    bookmakers: string[],
    includeProps: boolean = true
  ) => {
    setIsScanning(true);
    setProgress(0);
    setCurrentSport(sportKey);
    setError(null);

    try {
      const result = await scanSport({
        sport_key: sportKey,
        bookmakers,
        include_props: includeProps,
      });

      setOpportunities(result.opportunities);
      setTotalFound(result.total_found);
      setRemainingCredits(result.remaining_credits);
      setProgress(100);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setIsScanning(false);
      setCurrentSport('');
    }
  }, []);

  const scanMultipleSports = useCallback(async (
    sports: Sport[],
    bookmakers: string[],
    includeProps: boolean = true
  ) => {
    setIsScanning(true);
    setProgress(0);
    setError(null);
    setOpportunities([]);

    const allOpportunities: Opportunity[] = [];
    let totalCount = 0;
    let credits = '';

    for (let i = 0; i < sports.length; i++) {
      const sport = sports[i];
      setCurrentSport(sport.title);

      try {
        const result = await scanSport({
          sport_key: sport.key,
          bookmakers,
          include_props: includeProps,
        });

        allOpportunities.push(...result.opportunities);
        totalCount += result.total_found;
        credits = result.remaining_credits;

        // Update progress
        setProgress(Math.round(((i + 1) / sports.length) * 100));

        // Update opportunities in real-time
        const sorted = [...allOpportunities].sort((a, b) => b.roi - a.roi);
        setOpportunities(sorted);

      } catch (err) {
        console.error(`Failed to scan ${sport.key}:`, err);
        // Continue with other sports
      }
    }

    setTotalFound(totalCount);
    setRemainingCredits(credits);
    setIsScanning(false);
    setCurrentSport('');
  }, []);

  const clearResults = useCallback(() => {
    setOpportunities([]);
    setTotalFound(0);
    setProgress(0);
    setError(null);
  }, []);

  return {
    opportunities,
    isScanning,
    progress,
    currentSport,
    error,
    totalFound,
    remainingCredits,
    scanSingleSport,
    scanMultipleSports,
    clearResults,
  };
}
