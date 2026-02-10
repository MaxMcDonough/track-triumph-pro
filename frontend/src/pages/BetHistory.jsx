import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  History, 
  CheckCircle2, 
  XCircle, 
  Clock,
  Trophy,
  Target,
  Layers,
  Shield,
  Loader2,
  Filter
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const betTypeIcons = {
  WIN: Trophy,
  PLACE: Target,
  BOX_TRIFECTA: Layers,
  SAFETY_PLACE: Shield
};

export default function BetHistory({ user }) {
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [settleDialog, setSettleDialog] = useState(null);
  const [settling, setSettling] = useState(false);

  useEffect(() => {
    fetchBets();
  }, []);

  const fetchBets = async () => {
    try {
      const response = await axios.get(`${API}/bets`, { withCredentials: true });
      setBets(response.data.bets || []);
    } catch (error) {
      console.error("Error fetching bets:", error);
      toast.error("Failed to load bet history");
    } finally {
      setLoading(false);
    }
  };

  const handleSettle = async (result) => {
    if (!settleDialog) return;

    setSettling(true);
    try {
      const response = await axios.post(
        `${API}/bets/${settleDialog.bet_id}/settle`,
        { result },
        { withCredentials: true }
      );

      toast.success(response.data.message);
      setSettleDialog(null);
      fetchBets();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to settle bet");
    } finally {
      setSettling(false);
    }
  };

  const filteredBets = bets.filter(bet => {
    if (filter === "all") return true;
    if (filter === "pending") return !bet.result;
    if (filter === "won") return bet.result === "WIN";
    if (filter === "lost") return bet.result === "LOSS";
    return true;
  });

  const pendingCount = bets.filter(b => !b.result).length;
  const wonCount = bets.filter(b => b.result === "WIN").length;
  const lostCount = bets.filter(b => b.result === "LOSS").length;

  if (loading) {
    return (
      <DashboardLayout user={user}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout user={user} setUser={setUser}>
      <div className="space-y-8" data-testid="bet-history-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-heading font-bold mb-2">Bet History</h1>
            <p className="text-muted-foreground">
              Track and settle your bets
            </p>
          </div>
          
          {/* Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <Select value={filter} onValueChange={setFilter}>
              <SelectTrigger className="w-[180px]" data-testid="filter-select">
                <SelectValue placeholder="Filter bets" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Bets ({bets.length})</SelectItem>
                <SelectItem value="pending">Pending ({pendingCount})</SelectItem>
                <SelectItem value="won">Won ({wonCount})</SelectItem>
                <SelectItem value="lost">Lost ({lostCount})</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-3 gap-4">
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                <Clock className="w-5 h-5 text-accent" />
              </div>
              <div>
                <p className="text-2xl font-mono font-bold">{pendingCount}</p>
                <p className="text-xs text-muted-foreground">Pending</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-mono font-bold text-primary">{wonCount}</p>
                <p className="text-xs text-muted-foreground">Won</p>
              </div>
            </CardContent>
          </Card>
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-destructive/10 flex items-center justify-center">
                <XCircle className="w-5 h-5 text-destructive" />
              </div>
              <div>
                <p className="text-2xl font-mono font-bold text-destructive">{lostCount}</p>
                <p className="text-xs text-muted-foreground">Lost</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Bets List */}
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-lg font-heading flex items-center gap-2">
              <History className="w-5 h-5" />
              All Bets
            </CardTitle>
          </CardHeader>
          <CardContent>
            {filteredBets.length === 0 ? (
              <div className="text-center py-12">
                <History className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">
                  {filter === "all" ? "No bets placed yet" : `No ${filter} bets`}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredBets.map((bet, idx) => {
                  const Icon = betTypeIcons[bet.bet_type] || Trophy;
                  
                  return (
                    <div 
                      key={idx}
                      className="flex flex-col md:flex-row md:items-center justify-between p-4 rounded-lg bg-muted/30 border border-border/50 gap-4"
                      data-testid={`bet-row-${idx}`}
                    >
                      <div className="flex items-center gap-4">
                        {/* Status Indicator */}
                        <div className={`w-2 h-12 rounded-full ${
                          bet.result === "WIN" ? "bg-primary" :
                          bet.result === "LOSS" ? "bg-destructive" : "bg-accent"
                        }`} />
                        
                        {/* Bet Type Icon */}
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                          bet.result === "WIN" ? "bg-primary/10" :
                          bet.result === "LOSS" ? "bg-destructive/10" : "bg-muted"
                        }`}>
                          <Icon className={`w-5 h-5 ${
                            bet.result === "WIN" ? "text-primary" :
                            bet.result === "LOSS" ? "text-destructive" : "text-muted-foreground"
                          }`} />
                        </div>

                        {/* Bet Details */}
                        <div>
                          <p className="font-medium">{bet.horse_name}</p>
                          <p className="text-xs text-muted-foreground">
                            {bet.track?.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} R{bet.race_number} • {bet.bet_type}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {new Date(bet.timestamp).toLocaleDateString()} {new Date(bet.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-6 md:gap-8">
                        {/* Odds & Score */}
                        <div className="text-center">
                          <p className="text-xs text-muted-foreground">Odds</p>
                          <p className="font-mono font-semibold">{bet.odds?.toFixed(2)}</p>
                        </div>
                        <div className="text-center">
                          <p className="text-xs text-muted-foreground">Score</p>
                          <Badge variant="outline" className="text-xs">{bet.score}/8</Badge>
                        </div>
                        <div className="text-center">
                          <p className="text-xs text-muted-foreground">Stake</p>
                          <p className="font-mono font-semibold">${bet.stake?.toFixed(2)}</p>
                        </div>

                        {/* Result / Settle Button */}
                        <div className="min-w-[100px] text-right">
                          {bet.result ? (
                            <div>
                              <Badge className={
                                bet.result === "WIN" ? "badge-win" : "badge-loss"
                              }>
                                {bet.result}
                              </Badge>
                              <p className={`text-sm font-mono mt-1 ${
                                bet.profit_loss > 0 ? "text-primary" : "text-destructive"
                              }`}>
                                {bet.profit_loss > 0 ? "+" : ""}${bet.profit_loss?.toFixed(2)}
                              </p>
                            </div>
                          ) : (
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => setSettleDialog(bet)}
                              data-testid={`settle-btn-${idx}`}
                            >
                              Settle
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Settle Dialog */}
        <Dialog open={!!settleDialog} onOpenChange={() => setSettleDialog(null)}>
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
                    {settleDialog.track} R{settleDialog.race_number} • {settleDialog.bet_type}
                  </p>
                  <div className="flex gap-4 mt-2 text-sm">
                    <span>Stake: <strong>${settleDialog.stake?.toFixed(2)}</strong></span>
                    <span>Odds: <strong>{settleDialog.odds?.toFixed(2)}</strong></span>
                  </div>
                </div>
              </div>
            )}

            <DialogFooter className="flex gap-2">
              <Button 
                variant="outline" 
                className="flex-1 border-destructive text-destructive hover:bg-destructive/10"
                onClick={() => handleSettle("LOSS")}
                disabled={settling}
                data-testid="settle-loss-btn"
              >
                {settling ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4 mr-2" />}
                Lost
              </Button>
              <Button 
                className="flex-1 btn-glow"
                onClick={() => handleSettle("WIN")}
                disabled={settling}
                data-testid="settle-win-btn"
              >
                {settling ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4 mr-2" />}
                Won
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
