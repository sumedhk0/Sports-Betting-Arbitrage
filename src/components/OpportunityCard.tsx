"use client";

import { useState } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ChevronDown, ChevronUp, Clock, DollarSign } from 'lucide-react';
import { formatOdds, formatCurrency, getRoiColor, getRoiBgColor } from '@/lib/utils';
import type { Opportunity } from '@/lib/types';

interface OpportunityCardProps {
  opportunity: Opportunity;
  rank: number;
}

export function OpportunityCard({ opportunity, rank }: OpportunityCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [stake, setStake] = useState(100);

  const calculateBetAmount = (percentage: number) => {
    return (percentage / 100) * stake;
  };

  const expectedProfit = (opportunity.roi / 100) * stake;

  return (
    <Card className="overflow-hidden">
      <CardHeader
        className="cursor-pointer py-4"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-muted-foreground">#{rank}</span>
              <h3 className="font-semibold">{opportunity.event}</h3>
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>{opportunity.commence_time}</span>
              <span className="mx-1">|</span>
              <span>{opportunity.market}</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Badge
              className={`${getRoiBgColor(opportunity.roi)} ${getRoiColor(opportunity.roi)} border-0 text-base px-3 py-1`}
            >
              +{opportunity.roi.toFixed(2)}% ROI
            </Badge>
            {isExpanded ? (
              <ChevronUp className="h-5 w-5 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-5 w-5 text-muted-foreground" />
            )}
          </div>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-0 space-y-4">
          {/* Bets */}
          <div className="space-y-2">
            {opportunity.bets.map((bet, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
              >
                <div className="space-y-1">
                  <div className="font-medium">{bet.outcome}</div>
                  <div className="text-sm text-muted-foreground">
                    @ {bet.bookmaker}
                  </div>
                </div>
                <div className="text-right space-y-1">
                  <div className="font-bold text-lg">
                    {formatOdds(bet.odds)}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {bet.bet_percentage.toFixed(1)}% ({formatCurrency(calculateBetAmount(bet.bet_percentage))})
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Stake Calculator */}
          <div className="flex items-center gap-4 p-4 rounded-lg bg-primary/5 border border-primary/20">
            <div className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-primary" />
              <span className="font-medium">Total Stake:</span>
            </div>
            <Input
              type="number"
              value={stake}
              onChange={(e) => setStake(Number(e.target.value) || 0)}
              className="w-32"
              min={0}
            />
            <div className="ml-auto text-right">
              <div className="text-sm text-muted-foreground">Expected Profit</div>
              <div className={`font-bold text-lg ${getRoiColor(opportunity.roi)}`}>
                {formatCurrency(expectedProfit)}
              </div>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
