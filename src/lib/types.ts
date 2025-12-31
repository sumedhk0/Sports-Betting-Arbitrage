export interface Sport {
  key: string;
  title: string;
  group: string;
  active: boolean;
}

export interface Bookmaker {
  key: string;
  name: string;
}

export interface Bet {
  outcome: string;
  bookmaker: string;
  odds: number;
  bet_percentage: number;
  bet_amount_100: number;
}

export interface Opportunity {
  event: string;
  sport: string;
  market: string;
  roi: number;
  commence_time: string;
  bets: Bet[];
}

export interface SportsResponse {
  sports: Sport[];
  remaining_credits: string;
}

export interface BookmakersResponse {
  bookmakers: Bookmaker[];
}

export interface ScanResponse {
  opportunities: Opportunity[];
  total_found: number;
  remaining_credits: string;
}

export interface ScanRequest {
  sport_key: string;
  bookmakers: string[];
  include_props?: boolean;
}
