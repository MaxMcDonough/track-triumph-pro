import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { BankrollWidget } from "@/components/dashboard/BankrollWidget";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Search, 
  TrendingUp, 
  Trophy,
  History,
  BarChart3,
  ArrowRight,
  Zap,
  Target,
  CheckCircle2,
  Clock
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Dashboard({ user }) {
  const [bankroll, setBankroll] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [recentBets, setRecentBets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [bankrollRes, statsRes, betsRes] = await Promise.all([
        axios.get(`${API}/bankroll`, { withCredentials: true }),
        axios.get(`${API}/statistics`, { withCredentials: true }),
        axios.get(`${API}/bets`, { withCredentials: true })
      ]);

      setBankroll(bankrollRes.data);
      setStatistics(statsRes.data);
      setRecentBets(betsRes.data.bets?.slice(0, 5) || []);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
      toast.error("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  const quickStats = [
    {
      label: "Win Rate",
      value: statistics?.overall?.win_rate || "0%",
      icon: Target,
      color: "text-primary"
    },
    {
      label: "Total Bets",
      value: statistics?.overall?.total_bets || 0,
      icon: History,
      color: "text-secondary"
    },
    {
      label: "ROI",
      value: statistics?.overall?.roi || "0%",
      icon: TrendingUp,
      color: parseFloat(statistics?.overall?.roi) >= 0 ? "text-primary" : "text-destructive"
    },
    {
      label: "Total Profit",
      value: `$${statistics?.overall?.total_profit || "0.00"}`,
      icon: Trophy,
      color: parseFloat(statistics?.overall?.total_profit) >= 0 ? "text-primary" : "text-destructive"
    }
  ];

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
      <div className="space-y-8" data-testid="dashboard-page">
        {/* Header */}
        <div className="dashboard-header-bg rounded-2xl p-8 -m-4 md:-m-8 mb-4">
          <div className="max-w-2xl">
            <h1 className="text-3xl md:text-4xl font-heading font-bold mb-2">
              Welcome back, {user?.name?.split(' ')[0]}
            </h1>
            <p className="text-muted-foreground text-lg">
              Ready to find today's best bets with data-driven analysis
            </p>
            <Link to="/analyze">
              <Button className="mt-6 btn-glow" size="lg" data-testid="analyze-race-btn">
                <Search className="w-5 h-5 mr-2" />
                Analyze Race
              </Button>
            </Link>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column - Bankroll & Quick Stats */}
          <div className="lg:col-span-5 space-y-6">
            <BankrollWidget bankroll={bankroll} />

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-4">
              {quickStats.map((stat, idx) => {
                const Icon = stat.icon;
                return (
                  <Card 
                    key={idx} 
                    className="border-border/50 bg-card/50 backdrop-blur-sm stat-box"
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Icon className={`w-4 h-4 ${stat.color}`} />
                        <span className="text-xs text-muted-foreground">{stat.label}</span>
                      </div>
                      <p className={`text-xl font-mono font-bold ${stat.color}`}>
                        {stat.value}
                      </p>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>

          {/* Right Column - Quick Actions & Recent Bets */}
          <div className="lg:col-span-7 space-y-6">
            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Link to="/analyze">
                <Card className="border-border/50 bg-card/50 backdrop-blur-sm card-hover cursor-pointer h-full">
                  <CardContent className="p-5 flex flex-col h-full">
                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                      <Search className="w-6 h-6 text-primary" />
                    </div>
                    <h3 className="font-heading font-semibold mb-1">Analyze Race</h3>
                    <p className="text-sm text-muted-foreground flex-1">
                      Run 8-criteria analysis on any race
                    </p>
                    <ArrowRight className="w-4 h-4 text-muted-foreground mt-3" />
                  </CardContent>
                </Card>
              </Link>

              <Link to="/history">
                <Card className="border-border/50 bg-card/50 backdrop-blur-sm card-hover cursor-pointer h-full">
                  <CardContent className="p-5 flex flex-col h-full">
                    <div className="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center mb-4">
                      <History className="w-6 h-6 text-secondary" />
                    </div>
                    <h3 className="font-heading font-semibold mb-1">Bet History</h3>
                    <p className="text-sm text-muted-foreground flex-1">
                      Track and settle your bets
                    </p>
                    <ArrowRight className="w-4 h-4 text-muted-foreground mt-3" />
                  </CardContent>
                </Card>
              </Link>

              <Link to="/statistics">
                <Card className="border-border/50 bg-card/50 backdrop-blur-sm card-hover cursor-pointer h-full">
                  <CardContent className="p-5 flex flex-col h-full">
                    <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4">
                      <BarChart3 className="w-6 h-6 text-accent" />
                    </div>
                    <h3 className="font-heading font-semibold mb-1">Statistics</h3>
                    <p className="text-sm text-muted-foreground flex-1">
                      View performance by score level
                    </p>
                    <ArrowRight className="w-4 h-4 text-muted-foreground mt-3" />
                  </CardContent>
                </Card>
              </Link>
            </div>

            {/* Recent Bets */}
            <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg font-heading">Recent Bets</CardTitle>
                  <Link to="/history">
                    <Button variant="ghost" size="sm" className="text-muted-foreground">
                      View All
                      <ArrowRight className="w-4 h-4 ml-1" />
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                {recentBets.length === 0 ? (
                  <div className="text-center py-8">
                    <Zap className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                    <p className="text-muted-foreground">No bets yet</p>
                    <Link to="/analyze">
                      <Button variant="outline" className="mt-4" size="sm">
                        Place Your First Bet
                      </Button>
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {recentBets.map((bet, idx) => (
                      <div 
                        key={idx}
                        className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border/50"
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-8 rounded-full ${
                            bet.result === "WIN" ? "bg-primary" :
                            bet.result === "LOSS" ? "bg-destructive" : "bg-muted-foreground"
                          }`} />
                          <div>
                            <p className="font-medium">{bet.horse_name}</p>
                            <p className="text-xs text-muted-foreground">
                              {bet.track} R{bet.race_number} • {bet.bet_type}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge 
                            variant="outline" 
                            className={
                              bet.result === "WIN" ? "badge-win" :
                              bet.result === "LOSS" ? "badge-loss" : "badge-pending"
                            }
                          >
                            {bet.result || "Pending"}
                          </Badge>
                          <p className={`text-sm font-mono mt-1 ${
                            bet.profit_loss > 0 ? "text-primary" :
                            bet.profit_loss < 0 ? "text-destructive" : "text-muted-foreground"
                          }`}>
                            {bet.profit_loss ? 
                              `${bet.profit_loss > 0 ? "+" : ""}$${bet.profit_loss.toFixed(2)}` :
                              `$${bet.stake?.toFixed(2)}`
                            }
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Algorithm Info */}
            <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
              <CardContent className="p-5">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <CheckCircle2 className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-heading font-semibold mb-1">8-Criteria Algorithm</h3>
                    <p className="text-sm text-muted-foreground mb-3">
                      Every bet is scored across 8 proven criteria including expert consensus, 
                      hot statistics, odds value, and market confidence.
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="secondary" className="text-xs">Track Type</Badge>
                      <Badge variant="secondary" className="text-xs">Statistics</Badge>
                      <Badge variant="secondary" className="text-xs">Expert Tips</Badge>
                      <Badge variant="secondary" className="text-xs">Hot Form</Badge>
                      <Badge variant="secondary" className="text-xs">Odds Value</Badge>
                      <Badge variant="secondary" className="text-xs">Market</Badge>
                      <Badge variant="secondary" className="text-xs">Timeform</Badge>
                      <Badge variant="secondary" className="text-xs">Angles</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
