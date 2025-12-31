"use client";

import { Progress } from '@/components/ui/progress';
import { Loader2 } from 'lucide-react';

interface ScanProgressProps {
  progress: number;
  currentSport: string;
  isScanning: boolean;
}

export function ScanProgress({ progress, currentSport, isScanning }: ScanProgressProps) {
  if (!isScanning) return null;

  return (
    <div className="space-y-2 p-4 rounded-lg bg-primary/5 border border-primary/20">
      <div className="flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin text-primary" />
        <span className="font-medium">Scanning for opportunities...</span>
      </div>
      <Progress value={progress} className="h-2" />
      <div className="flex justify-between text-sm text-muted-foreground">
        <span>{currentSport || 'Initializing...'}</span>
        <span>{progress}%</span>
      </div>
    </div>
  );
}
