"use client";

import { useState, useCallback } from 'react';
import { Header } from '@/components/Header';
import { SportSelector } from '@/components/SportSelector';
import { BookmakerSelector } from '@/components/BookmakerSelector';
import { OpportunityList } from '@/components/OpportunityList';
import { ScanProgress } from '@/components/ScanProgress';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useSports } from '@/hooks/useSports';
import { useBookmakers } from '@/hooks/useBookmakers';
import { useScan } from '@/hooks/useScan';
import { Search, Zap } from 'lucide-react';

export default function Home() {
  const { sports, isLoading: sportsLoading, remainingCredits: sportsCredits } = useSports();
  const { bookmakers, isLoading: bookmakersLoading } = useBookmakers();
  const {
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
  } = useScan();

  const [selectedSport, setSelectedSport] = useState('');
  const [selectedBookmakers, setSelectedBookmakers] = useState<string[]>([
    'draftkings',
    'fanduel',
  ]);
  const [includeProps, setIncludeProps] = useState(true);

  const handleToggleBookmaker = useCallback((key: string) => {
    setSelectedBookmakers((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  }, []);

  const handleSelectAllBookmakers = useCallback(() => {
    setSelectedBookmakers(bookmakers.map((b) => b.key));
  }, [bookmakers]);

  const handleDeselectAllBookmakers = useCallback(() => {
    setSelectedBookmakers([]);
  }, []);

  const handleScan = useCallback(() => {
    if (selectedBookmakers.length < 2) return;

    clearResults();

    if (selectedSport === 'all') {
      scanMultipleSports(sports, selectedBookmakers, includeProps);
    } else if (selectedSport) {
      scanSingleSport(selectedSport, selectedBookmakers, includeProps);
    }
  }, [
    selectedSport,
    selectedBookmakers,
    includeProps,
    sports,
    scanSingleSport,
    scanMultipleSports,
    clearResults,
  ]);

  const canScan = selectedSport && selectedBookmakers.length >= 2 && !isScanning;
  const displayCredits = remainingCredits || sportsCredits;

  return (
    <div className="min-h-screen flex flex-col">
      <Header remainingCredits={displayCredits} />

      <main className="flex-1 container mx-auto px-4 py-6 space-y-6">
        {/* Configuration Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              Scan Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              <SportSelector
                sports={sports}
                selectedSport={selectedSport}
                onSelect={setSelectedSport}
                isLoading={sportsLoading}
                disabled={isScanning}
              />

              <div className="space-y-2">
                <label className="text-sm font-medium">Options</label>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeProps}
                      onChange={(e) => setIncludeProps(e.target.checked)}
                      disabled={isScanning}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <span className="text-sm">Include player props</span>
                  </label>
                </div>
                <p className="text-xs text-muted-foreground">
                  Player props use more API credits but find more opportunities
                </p>
              </div>
            </div>

            <BookmakerSelector
              bookmakers={bookmakers}
              selectedBookmakers={selectedBookmakers}
              onToggle={handleToggleBookmaker}
              onSelectAll={handleSelectAllBookmakers}
              onDeselectAll={handleDeselectAllBookmakers}
              isLoading={bookmakersLoading}
              disabled={isScanning}
            />

            <div className="flex gap-4">
              <Button
                onClick={handleScan}
                disabled={!canScan}
                size="lg"
                className="flex-1 md:flex-none"
              >
                <Search className="h-4 w-4 mr-2" />
                {isScanning ? 'Scanning...' : 'Scan for Opportunities'}
              </Button>

              {opportunities.length > 0 && !isScanning && (
                <Button variant="outline" onClick={clearResults}>
                  Clear Results
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Progress Section */}
        <ScanProgress
          progress={progress}
          currentSport={currentSport}
          isScanning={isScanning}
        />

        {/* Results Section */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Arbitrage Opportunities</h2>
          <OpportunityList
            opportunities={opportunities}
            isLoading={isScanning && opportunities.length === 0}
            error={error}
            totalFound={totalFound}
          />
        </div>
      </main>

      <footer className="border-t py-4">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          Powered by The Odds API | For educational purposes only
        </div>
      </footer>
    </div>
  );
}
