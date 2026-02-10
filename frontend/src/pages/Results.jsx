import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Trophy,
  Flag,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  Medal,
  Target,
  Layers,
  Shield,
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const betTypeIcons = {
  WIN: Trophy,
  PLACE: Target,
  BOX_TRIFECTA: Layers,
  SAFETY_PLACE: Shield,
};

export default function Results({ user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [settleDialog, setSettleDialog] = useState(null);
  const [settling, setSettling] = useState(false);

  useEffect(() => {
    fetchResults();
  }, []);

  const fetchResults = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/results`);
      setData(response.data);
    } catch (error) {
      console.error("Error fetching results:", error);
      toast.error("Failed to load results");
    } finally {
      setLoading(false);
    }
  };

  const handleSettle = async (betId, result) => {
    setSettling(true);
    try {
      const response = await axios.post(`${API}/bets/${betId}/settle`, {
        result,
      });
      toast.success(response.data.message);
      setSettleDialog(null);
      fetchResults();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to settle bet");
    } finally {
      setSettling(false);
    }
  };

  const liveResults = data?.live_results || [];
  const settledBets = data?.settled_bets || [];
  const pendingBets = data?.pending_bets || [];

  const totalProfit = settledBets.reduce(
    (sum, b) => sum + (b.profit_loss || 0),
    0
  );
  const wonBets = settledBets.filter((b) => b.result === "WIN").length;
  const lostBets = settledBets.filter((b) => b.result === "LOSS").length;

  if (loading) {
    return (
      <DashboardLayout user={user}>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout user={user}>
      <div className="space-y-8" data-testid="results-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-heading font-bold mb-2">Results</h1>
            <p className="text-muted-foreground">
              Race results and your bet outcomes
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchResults}
            disabled={loading}
            data-testid="refresh-results-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-1">
                <Flag className="w-4 h-4 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">
                  Race Results
                </span>
              </div>
              <p className="text-2xl font-mono font-bold">
                {liveResults.length}
              </p>
            </CardContent>
          </Card>
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-1">
                <Clock className="w-4 h-4 text-accent" />
                <span className="text-xs text-muted-foreground">
                  Pending Bets
                </span>
              </div>
              <p className="text-2xl font-mono font-bold text-accent">
                {pendingBets.length}
              </p>
            </CardContent>
          </Card>
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-1">
                <Trophy className="w-4 h-4 text-primary" />
                <span className="text-xs text-muted-foreground">
                  Won / Lost
                </span>
              </div>
              <p className="text-2xl font-mono font-bold">
                <span className="text-primary">{wonBets}</span>
                <span className="text-muted-foreground mx-1">/</span>
                <span className="text-destructive">{lostBets}</span>
              </p>
            </CardContent>
          </Card>
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-1">
                <Medal className="w-4 h-4 text-primary" />
                <span className="text-xs text-muted-foreground">
                  Total P/L
                </span>
              </div>
              <p
                className={`text-2xl font-mono font-bold ${
                  totalProfit >= 0 ? "text-primary" : "text-destructive"
                }`}
              >
                {totalProfit >= 0 ? "+" : ""}${totalProfit.toFixed(2)}
              </p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="my-bets">
          <TabsList>
            <TabsTrigger value="my-bets">
              My Bets ({pendingBets.length + settledBets.length})
            </TabsTrigger>
            <TabsTrigger value="race-results">
              Race Results ({liveResults.length})
            </TabsTrigger>
          </TabsList>

          {/* My Bets Tab */}
          <TabsContent value="my-bets" className="space-y-6 mt-4">
            {/* Pending Bets */}
            {pendingBets.length > 0 && (
              <div>
                <h3 className="text-lg font-heading font-semibold mb-3 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-accent" />
                  Pending ({pendingBets.length})
                </h3>
                <div className="space-y-3">
                  {pendingBets.map((bet, idx) => {
                    const Icon = betTypeIcons[bet.bet_type] || Trophy;
                    return (
                      <Card
                        key={idx}
                        className="border-accent/20 bg-accent/5"
                        data-testid={`pending-bet-${idx}`}
                      >
                        <CardContent className="p-4">
                          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                            <div className="flex items-center gap-4">
                              <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                                <Icon className="w-5 h-5 text-accent" />
                              </div>
                              <div>
                                <p className="font-semibold">
                                  {bet.horse_name}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  {bet.track} R{bet.race_number} &middot;{" "}
                                  {bet.bet_type} &middot; Score {bet.score}/8
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="text-center">
                                <p className="text-xs text-muted-foreground">
                                  Stake
                                </p>
                                <p className="font-mono font-semibold">
                                  ${bet.stake?.toFixed(2)}
                                </p>
                              </div>
                              <div className="text-center">
                                <p className="text-xs text-muted-foreground">
                                  Odds
                                </p>
                                <p className="font-mono font-semibold">
                                  {bet.odds?.toFixed(2)}
                                </p>
                              </div>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setSettleDialog(bet)}
                                data-testid={`settle-pending-${idx}`}
                              >
                                Settle
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Settled Bets */}
            <div>
              <h3 className="text-lg font-heading font-semibold mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary" />
                Settled ({settledBets.length})
              </h3>
              {settledBets.length === 0 ? (
                <Card className="border-border/50 bg-card/50">
                  <CardContent className="p-8 text-center">
                    <Trophy className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
                    <p className="text-muted-foreground">
                      No settled bets yet. Place and settle bets to see results
                      here.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3">
                  {settledBets.map((bet, idx) => {
                    const Icon = betTypeIcons[bet.bet_type] || Trophy;
                    const isWin = bet.result === "WIN";
                    return (
                      <Card
                        key={idx}
                        className={`border-border/50 ${
                          isWin ? "bg-primary/5" : "bg-destructive/5"
                        }`}
                        data-testid={`settled-bet-${idx}`}
                      >
                        <CardContent className="p-4">
                          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                            <div className="flex items-center gap-4">
                              <div
                                className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                                  isWin
                                    ? "bg-primary/10"
                                    : "bg-destructive/10"
                                }`}
                              >
                                <Icon
                                  className={`w-5 h-5 ${
                                    isWin
                                      ? "text-primary"
                                      : "text-destructive"
                                  }`}
                                />
                              </div>
                              <div>
                                <p className="font-semibold">
                                  {bet.horse_name}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  {bet.track} R{bet.race_number} &middot;{" "}
                                  {bet.bet_type} &middot; Score {bet.score}/8
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  {new Date(bet.timestamp).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="text-center">
                                <p className="text-xs text-muted-foreground">
                                  Stake
                                </p>
                                <p className="font-mono text-sm">
                                  ${bet.stake?.toFixed(2)}
                                </p>
                              </div>
                              <div className="text-center">
                                <p className="text-xs text-muted-foreground">
                                  Odds
                                </p>
                                <p className="font-mono text-sm">
                                  {bet.odds?.toFixed(2)}
                                </p>
                              </div>
                              <div className="text-right min-w-[80px]">
                                <Badge
                                  className={
                                    isWin ? "badge-win" : "badge-loss"
                                  }
                                >
                                  {bet.result}
                                </Badge>
                                <p
                                  className={`text-sm font-mono mt-1 ${
                                    isWin
                                      ? "text-primary"
                                      : "text-destructive"
                                  }`}
                                >
                                  {bet.profit_loss > 0 ? "+" : ""}$
                                  {bet.profit_loss?.toFixed(2)}
                                </p>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          </TabsContent>

          {/* Race Results Tab */}
          <TabsContent value="race-results" className="space-y-4 mt-4">
            {liveResults.length === 0 ? (
              <Card className="border-border/50 bg-card/50">
                <CardContent className="p-12 text-center">
                  <Flag className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="font-heading font-semibold text-lg mb-2">
                    No results yet today
                  </h3>
                  <p className="text-muted-foreground">
                    Race results will appear here as races finish. Check back
                    after the first race of the day.
                  </p>
                </CardContent>
              </Card>
            ) : (
              liveResults.map((race, idx) => (
                <Card
                  key={idx}
                  className="border-border/50 bg-card/50 backdrop-blur-sm"
                  data-testid={`race-result-${idx}`}
                >
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Badge variant="outline" className="font-mono text-sm">
                          {race.off_time}
                        </Badge>
                        <CardTitle className="text-base font-heading">
                          {race.course}
                        </CardTitle>
                        {race.race_type && (
                          <Badge variant="secondary" className="text-xs">
                            {race.race_type}
                          </Badge>
                        )}
                      </div>
                      {race.winner && (
                        <Badge className="bg-primary/20 text-primary border-primary/30">
                          <Trophy className="w-3 h-3 mr-1" />
                          {race.winner}
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {race.race_name}
                    </p>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-1">
                      {race.runners?.slice(0, 5).map((runner, rIdx) => (
                        <div
                          key={rIdx}
                          className={`flex items-center justify-between p-2 rounded-lg text-sm ${
                            runner.position === "1"
                              ? "bg-primary/10 border border-primary/20"
                              : rIdx < 3
                              ? "bg-muted/20"
                              : ""
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <span
                              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-mono font-bold ${
                                runner.position === "1"
                                  ? "bg-primary text-primary-foreground"
                                  : runner.position === "2"
                                  ? "bg-muted text-foreground"
                                  : runner.position === "3"
                                  ? "bg-accent/20 text-accent"
                                  : "text-muted-foreground"
                              }`}
                            >
                              {runner.position || "-"}
                            </span>
                            <span
                              className={
                                runner.position === "1" ? "font-semibold" : ""
                              }
                            >
                              {runner.horse}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>{runner.jockey}</span>
                            {runner.sp && (
                              <span className="font-mono">{runner.sp}</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>
        </Tabs>

        {/* Settle Dialog */}
        <Dialog
          open={!!settleDialog}
          onOpenChange={() => setSettleDialog(null)}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="font-heading">Settle Bet</DialogTitle>
              <DialogDescription>
                What was the result of this bet?
              </DialogDescription>
            </DialogHeader>
            {settleDialog && (
              <div className="py-4">
                <div className="p-4 rounded-lg bg-muted/30 border border-border/50 mb-4">
                  <p className="font-semibold">{settleDialog.horse_name}</p>
                  <p className="text-sm text-muted-foreground">
                    {settleDialog.track} R{settleDialog.race_number} &middot;{" "}
                    {settleDialog.bet_type}
                  </p>
                  <div className="flex gap-4 mt-2 text-sm">
                    <span>
                      Stake: <strong>${settleDialog.stake?.toFixed(2)}</strong>
                    </span>
                    <span>
                      Odds: <strong>{settleDialog.odds?.toFixed(2)}</strong>
                    </span>
                    <span>
                      Potential:{" "}
                      <strong className="text-primary">
                        +$
                        {(
                          settleDialog.stake * settleDialog.odds -
                          settleDialog.stake
                        ).toFixed(2)}
                      </strong>
                    </span>
                  </div>
                </div>
              </div>
            )}
            <DialogFooter className="flex gap-2">
              <Button
                variant="outline"
                className="flex-1 border-destructive text-destructive hover:bg-destructive/10"
                onClick={() =>
                  handleSettle(settleDialog.bet_id, "LOSS")
                }
                disabled={settling}
                data-testid="settle-loss-btn"
              >
                {settling ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <XCircle className="w-4 h-4 mr-2" />
                )}
                Lost
              </Button>
              <Button
                className="flex-1 btn-glow"
                onClick={() =>
                  handleSettle(settleDialog.bet_id, "WIN")
                }
                disabled={settling}
                data-testid="settle-win-btn"
              >
                {settling ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                )}
                Won
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
