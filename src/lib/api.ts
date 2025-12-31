import type {
  SportsResponse,
  BookmakersResponse,
  ScanResponse,
  ScanRequest,
} from './types';

const API_BASE = '/api';

export async function fetchSports(): Promise<SportsResponse> {
  const response = await fetch(`${API_BASE}/sports`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch sports');
  }
  return response.json();
}

export async function fetchBookmakers(): Promise<BookmakersResponse> {
  const response = await fetch(`${API_BASE}/bookmakers`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch bookmakers');
  }
  return response.json();
}

export async function scanSport(request: ScanRequest): Promise<ScanResponse> {
  const response = await fetch(`${API_BASE}/scan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Scan failed');
  }
  return response.json();
}
