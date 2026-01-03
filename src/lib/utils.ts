import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatOdds(odds: number): string {
  if (odds > 0) {
    return `+${odds}`;
  }
  return odds.toString();
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(2)}%`;
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}

export function getRoiColor(roi: number): string {
  if (roi >= 2) return 'text-green-600 dark:text-green-400';
  if (roi >= 1) return 'text-yellow-600 dark:text-yellow-400';
  return 'text-orange-600 dark:text-orange-400';
}

export function getRoiBgColor(roi: number): string {
  if (roi >= 2) return 'bg-orange-100 dark:bg-orange-900/30';
  if (roi >= 1) return 'bg-yellow-100 dark:bg-yellow-900/30';
  return 'bg-orange-100 dark:bg-orange-900/30';
}
