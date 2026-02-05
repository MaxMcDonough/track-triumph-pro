import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Trophy, 
  Target, 
  Shield, 
  Layers,
  Star,
  CheckCircle2,
  AlertCircle,
  XCircle,
  ArrowRight
} from "lucide-react";

const betTypeIcons = {
  WIN: Trophy,
  PLACE: Target,
  BOX_TRIFECTA: Layers,
  SAFETY_PLACE: Shield
};

const betTypeLabels = {
  WIN: "Win Bet",
  PLACE: "Place Bet",
  BOX_TRIFECTA: "Box Trifecta",
  SAFETY_PLACE: "Safety Bet"
};

const getScoreClass = (score) => {
  if (score >= 7) return "excellent";
  if (score >= 6) return "good";
  if (score >= 4) return "borderline";
  return "weak";
};

const getCriteriaIcon = (text) => {
  if (text?.includes("✅")) return <CheckCircle2 className="w-4 h-4 text-primary flex-shrink-0" />;
  if (text?.includes("⚠️")) return <AlertCircle className="w-4 h-4 text-accent flex-shrink-0" />;
  return <XCircle className="w-4 h-4 text-destructive flex-shrink-0" />;
};

export const RecommendationCard = ({ recommendation, onPlaceBet }) => {
  if (!recommendation) return null;

  const {
    type,
    horse,
    horses,
    draw_number,
    odds,
    bookmaker,
    score,
    max_score = 8,
    confidence,
    star_rating,
    stake,
    potential_profit,
    potential_return,
    criteria_breakdown,
    recommendation: recommendationText
  } = recommendation;

  const Icon = betTypeIcons[type] || Trophy;
  const scoreClass = getScoreClass(score);
  const scorePercent = (score / max_score) * 100;

  // For trifecta
  if (type === "BOX_TRIFECTA" && horses) {
    return (
      <Card 
        className={cn(
          "border-border/50 bg-card/50 backdrop-blur-sm card-hover",
          `bet-card-${scoreClass}`
        )}
        data-testid={`recommendation-${type.toLowerCase()}`}
      >
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center",
                scoreClass === "excellent" ? "bg-primary/10" :
                scoreClass === "good" ? "bg-secondary/10" :
                scoreClass === "borderline" ? "bg-accent/10" : "bg-destructive/10"
              )}>
                <Icon className={cn(
                  "w-4 h-4",
                  scoreClass === "excellent" ? "text-primary" :
                  scoreClass === "good" ? "text-secondary" :
                  scoreClass === "borderline" ? "text-accent" : "text-destructive"
                )} />
              </div>
              <div>
                <span className="text-xs uppercase tracking-wider text-muted-foreground font-medium">
                  {betTypeLabels[type]}
                </span>
              </div>
            </div>
            <Badge variant="outline" className={`score-${scoreClass}`}>
              {recommendation.avg_score?.toFixed(1)}/8 avg
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Horses List */}
          <div className="space-y-2">
            {horses.map((h, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-muted/30">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-muted flex items-center justify-center text-xs font-mono">
                    {h.position}
                  </span>
                  <span className="font-medium">{h.name}</span>
                  <span className="text-xs text-muted-foreground">#{h.draw_number}</span>
                </div>
                <span className="text-xs font-mono text-muted-foreground">{h.score}/8</span>
              </div>
            ))}
          </div>

          {/* Stake Info */}
          <div className="p-3 rounded-lg bg-muted/20 border border-border/30">
            <div className="flex justify-between items-center text-sm">
              <span className="text-muted-foreground">Total Stake (6 combos)</span>
              <span className="font-mono font-semibold">${recommendation.total_stake}</span>
            </div>
          </div>

          <p className="text-xs text-muted-foreground">{recommendation.recommendation}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card 
      className={cn(
        "border-border/50 bg-card/50 backdrop-blur-sm card-hover",
        `bet-card-${scoreClass}`
      )}
      data-testid={`recommendation-${type.toLowerCase()}`}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center",
              scoreClass === "excellent" ? "bg-primary/10" :
              scoreClass === "good" ? "bg-secondary/10" :
              scoreClass === "borderline" ? "bg-accent/10" : "bg-destructive/10"
            )}>
              <Icon className={cn(
                "w-4 h-4",
                scoreClass === "excellent" ? "text-primary" :
                scoreClass === "good" ? "text-secondary" :
                scoreClass === "borderline" ? "text-accent" : "text-destructive"
              )} />
            </div>
            <div>
              <span className="text-xs uppercase tracking-wider text-muted-foreground font-medium">
                {betTypeLabels[type]}
              </span>
            </div>
          </div>
          <Badge variant="outline" className={`score-${scoreClass}`}>
            {score}/{max_score}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Horse Name & Draw */}
        <div>
          <h3 className="text-xl font-heading font-bold">{horse}</h3>
          <p className="text-sm text-muted-foreground">Draw #{draw_number}</p>
        </div>

        {/* Confidence Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Confidence</span>
            <span className="font-mono font-medium">{confidence}</span>
          </div>
          <div className="h-2 rounded-full bg-muted overflow-hidden">
            <div 
              className="h-full confidence-gradient transition-all duration-300"
              style={{ width: `${scorePercent}%` }}
            />
          </div>
        </div>

        {/* Star Rating */}
        <div className="flex items-center gap-1">
          {[...Array(5)].map((_, i) => (
            <Star 
              key={i}
              className={cn(
                "w-4 h-4",
                i < star_rating ? "text-accent fill-accent" : "text-muted"
              )}
            />
          ))}
          <span className="text-xs text-muted-foreground ml-2">{recommendationText}</span>
        </div>

        {/* Odds & Bookmaker */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-muted/20 border border-border/30">
          <div>
            <p className="text-xs text-muted-foreground">Best Odds</p>
            <p className="text-lg font-mono font-bold odds-display">{odds?.toFixed(2)}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted-foreground">Bookmaker</p>
            <p className="text-sm font-medium">{bookmaker}</p>
          </div>
        </div>

        {/* Criteria Breakdown */}
        {criteria_breakdown && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Criteria Breakdown
            </p>
            <div className="space-y-1.5 max-h-40 overflow-y-auto">
              {Object.entries(criteria_breakdown).map(([key, value]) => (
                <div key={key} className="flex items-start gap-2 text-xs">
                  {getCriteriaIcon(value)}
                  <span className="text-muted-foreground">{value?.replace(/[✅⚠️❌]/g, '').trim()}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Stake Info */}
        <div className="p-3 rounded-lg bg-primary/5 border border-primary/10">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-muted-foreground">Recommended Stake</span>
            <span className="text-lg font-mono font-bold text-primary">${stake?.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Potential Return</span>
            <span className="font-mono">${potential_return?.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-xs mt-1">
            <span className="text-muted-foreground">Potential Profit</span>
            <span className="font-mono text-primary">+${potential_profit?.toFixed(2)}</span>
          </div>
        </div>

        {/* Place Bet Button */}
        {onPlaceBet && (
          <Button 
            className="w-full btn-glow"
            onClick={() => onPlaceBet(recommendation)}
            data-testid={`place-bet-${type.toLowerCase()}`}
          >
            Place Bet
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

export default RecommendationCard;
