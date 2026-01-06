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
  if (roi >= 2) return 'text-green-500 dark:text-green-400';
  if (roi >= 1) return 'text-yellow-500 dark:text-yellow-400';
  return 'text-orange-500 dark:text-orange-400';
}

export function getRoiBgColor(roi: number): string {
  if (roi >= 2) return 'bg-green-100 dark:bg-blue-900';
  if (roi >= 1) return 'bg-yellow-100 dark:bg-purple-900';
  return 'bg-orange-100 dark:bg-black';
}
