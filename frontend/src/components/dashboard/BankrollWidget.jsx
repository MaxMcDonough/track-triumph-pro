import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Wallet, TrendingUp, TrendingDown, ShieldAlert, Target } from "lucide-react";

export const BankrollWidget = ({ bankroll }) => {
  const {
    current_bankroll = 250,
    starting_bankroll = 250,
    stop_loss = 60,
    today_pl = 0,
    cushion = 190,
    percent_above_stop_loss = 0,
    consecutive_losses = 0
  } = bankroll || {};

  const netChange = current_bankroll - starting_bankroll;
  const netChangePercent = ((netChange / starting_bankroll) * 100).toFixed(1);
  const cushionPercent = Math.min(100, Math.max(0, (cushion / (starting_bankroll - stop_loss)) * 100));

  const getCushionColor = () => {
    if (percent_above_stop_loss < 30) return "bg-destructive";
    if (percent_above_stop_loss < 60) return "bg-accent";
    return "bg-primary";
  };

  return (
    <Card className="border-border/50 bg-card/50 backdrop-blur-sm" data-testid="bankroll-widget">
      <CardContent className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Wallet className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="font-heading font-semibold text-lg">Bankroll</h3>
            <p className="text-xs text-muted-foreground">Real-time tracking</p>
          </div>
        </div>

        {/* Main Stats Grid */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          {/* Current Bankroll */}
          <div className="stat-box p-4 rounded-lg bg-muted/30 border border-border/50">
            <p className="text-xs text-muted-foreground mb-1">Current</p>
            <p className="text-2xl font-mono font-bold text-foreground">
              ${current_bankroll.toFixed(2)}
            </p>
          </div>

          {/* Today's P/L */}
          <div className="stat-box p-4 rounded-lg bg-muted/30 border border-border/50">
            <p className="text-xs text-muted-foreground mb-1">Today P/L</p>
            <div className="flex items-center gap-2">
              {today_pl >= 0 ? (
                <TrendingUp className="w-4 h-4 text-primary" />
              ) : (
                <TrendingDown className="w-4 h-4 text-destructive" />
              )}
              <p className={cn(
                "text-2xl font-mono font-bold",
                today_pl >= 0 ? "text-primary" : "text-destructive"
              )}>
                {today_pl >= 0 ? "+" : ""}${today_pl.toFixed(2)}
              </p>
            </div>
          </div>

          {/* Stop-Loss */}
          <div className="stat-box p-4 rounded-lg bg-muted/30 border border-border/50">
            <p className="text-xs text-muted-foreground mb-1">Stop-Loss</p>
            <p className="text-xl font-mono font-semibold text-foreground">
              ${stop_loss.toFixed(2)}
            </p>
          </div>

          {/* Cushion */}
          <div className="stat-box p-4 rounded-lg bg-muted/30 border border-border/50">
            <p className="text-xs text-muted-foreground mb-1">Cushion</p>
            <p className={cn(
              "text-xl font-mono font-semibold",
              percent_above_stop_loss < 30 ? "text-destructive" : 
              percent_above_stop_loss < 60 ? "text-accent" : "text-primary"
            )}>
              ${cushion.toFixed(2)}
            </p>
          </div>
        </div>

        {/* Cushion Progress Bar */}
        <div className="space-y-2 mb-6">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Distance to Stop-Loss</span>
            <span className={cn(
              "font-mono font-medium",
              percent_above_stop_loss < 30 ? "text-destructive" : 
              percent_above_stop_loss < 60 ? "text-accent" : "text-primary"
            )}>
              {percent_above_stop_loss.toFixed(0)}%
            </span>
          </div>
          <div className="bankroll-progress">
            <div 
              className={cn("bankroll-progress-fill", getCushionColor())}
              style={{ width: `${cushionPercent}%` }}
            />
          </div>
        </div>

        {/* Net Performance */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-muted/20 border border-border/30">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Net Performance</span>
          </div>
          <span className={cn(
            "font-mono font-semibold",
            netChange >= 0 ? "text-primary" : "text-destructive"
          )}>
            {netChange >= 0 ? "+" : ""}{netChangePercent}%
          </span>
        </div>

        {/* Warning Banner */}
        {consecutive_losses >= 1 && (
          <div className={cn(
            "mt-4 p-3 rounded-lg flex items-center gap-2",
            consecutive_losses >= 2 
              ? "bg-destructive/10 border border-destructive/30" 
              : "bg-accent/10 border border-accent/30"
          )}>
            <ShieldAlert className={cn(
              "w-4 h-4",
              consecutive_losses >= 2 ? "text-destructive" : "text-accent"
            )} />
            <p className={cn(
              "text-sm font-medium",
              consecutive_losses >= 2 ? "text-destructive" : "text-accent"
            )}>
              {consecutive_losses >= 2 
                ? "STOP: 2 consecutive losses - No more bets today"
                : "Warning: 1 loss - Next bet is critical"
              }
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default BankrollWidget;
