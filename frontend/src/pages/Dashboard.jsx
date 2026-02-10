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
  Clock,
  Star,
  Radio,
  Loader2,
  Flag,
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Dashboard({ user }) {
  const [bankroll, setBankroll] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [recentBets, setRecentBets] = useState([]);
  const [bestBets, setBestBets] = useState(null);
  const [loading, setLoading] = useState(true);
  const [bestBetsLoading, setBestBetsLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    fetchBestBets();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [bankrollRes, statsRes, betsRes] = await Promise.all([
        axios.get(`${API}/bankroll`),
        axios.get(`${API}/statistics`),
        axios.get(`${API}/bets`),
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

  const fetchBestBets = async () => {
    setBestBetsLoading(true);
    try {
      const res = await axios.get(`${API}/best-bets`);
      setBestBets(res.data);
    } catch (error) {
      console.error("Error fetching best bets:", error);
    } finally {
      setBestBetsLoading(false);
    }
  };

  const quickStats = [
    {
      label: "Win Rate",
      value: statistics?.overall?.win_rate || "0%",
      icon: Target,
      color: "text-primary",
    },
    {
      label: "Total Bets",
      value: statistics?.overall?.total_bets || 0,
      icon: History,
      color: "text-secondary",
    },
    {
      label: "ROI",
      value: statistics?.overall?.roi || "0%",
      icon: TrendingUp,
      color:
        parseFloat(statistics?.overall?.roi) >= 0
          ? "text-primary"
          : "text-destructive",
    },
    {
      label: "Total Profit",
      value: `$${statistics?.overall?.total_profit || "0.00"}`,
      icon: Trophy,
      color:
        parseFloat(statistics?.overall?.total_profit) >= 0
          ? "text-primary"
          : "text-destructive",
    },
  ];

  const topPicks = bestBets?.picks?.slice(0, 5) || [];

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
    <DashboardLayout user={user}>
      <div className="space-y-8" data-testid="dashboard-page">
        {/* Header */}
        <div className="dashboard-header-bg rounded-2xl p-8 -m-4 md:-m-8 mb-4">
          <div className="max-w-2xl">
            <h1 className="text-3xl md:text-4xl font-heading font-bold mb-2">
              Welcome back{user?.name ? `, ${user.name.split(" ")[0]}` : ""}
            </h1>
            <p className="text-muted-foreground text-lg">
              Ready to find today's best bets with data-driven analysis
            </p>
            <div className="flex gap-3 mt-6">
              <Link to="/analyze">
                <Button
                  className="btn-glow"
                  size="lg"
                  data-testid="analyze-race-btn"
                >
                  <Search className="w-5 h-5 mr-2" />
                  Analyze Race
                </Button>
              </Link>
              <Link to="/results">
                <Button variant="outline" size="lg" data-testid="view-results-btn">
                  <Flag className="w-5 h-5 mr-2" />
                  Results
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Today's Best Bets */}
        <Card className="border-primary/20 bg-primary/[0.02] backdrop-blur-sm" data-testid="best-bets-section">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-heading flex items-center gap-2">
                <Radio className="w-5 h-5 text-primary animate-pulse" />
                Today's Best Bets
                {bestBets?.data_source?.includes("LIVE") && (
                  <Badge
                    variant="outline"
                    className="text-xs ml-1 border-primary/30 text-primary"
                  >
                    LIVE
                  </Badge>
                )}
              </CardTitle>
              {bestBets && (
                <span className="text-xs text-muted-foreground">
                  {bestBets.total_races_scanned} races scanned &middot;{" "}
                  {bestBets.total_qualifying} qualifying picks
                </span>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {bestBetsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
                <span className="ml-3 text-muted-foreground">
                  Scanning all races...
                </span>
              </div>
            ) : topPicks.length === 0 ? (
              <div className="text-center py-8">
                <Zap className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground">
                  No qualifying picks yet today. Check back when races are
                  available.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {topPicks.map((pick, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col md:flex-row md:items-center justify-between p-4 rounded-lg bg-muted/30 border border-border/50 table-row-hover"
                    data-testid={`best-bet-${idx}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex flex-col items-center min-w-[40px]">
                        <span className="text-xl font-heading font-bold text-primary">
                          #{idx + 1}
                        </span>
                        <div className="flex items-center gap-0.5 mt-1">
                          {[...Array(5)].map((_, i) => (
                            <Star
                              key={i}
                              className={`w-2.5 h-2.5 ${
                                i < pick.star_rating
                                  ? "text-accent fill-accent"
                                  : "text-muted"
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="font-heading font-semibold">
                          {pick.horse}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {pick.course} &middot; {pick.off_time} &middot;{" "}
                          {pick.race_type}
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {pick.jockey} &middot; Form: {pick.form || "N/A"}{" "}
                          &middot; OR: {pick.official_rating || "N/A"}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 mt-3 md:mt-0">
                      <Badge
                        variant="outline"
                        className={
                          pick.score >= 7
                            ? "score-excellent"
                            : pick.score >= 6
                            ? "score-good"
                            : pick.score >= 4
                            ? "score-borderline"
                            : "score-weak"
                        }
                      >
                        {pick.score}/8
                      </Badge>
                      <div className="text-center">
                        <p className="text-xs text-muted-foreground">Stake</p>
                        <p className="font-mono text-sm font-semibold">
                          ${pick.recommended_stake?.toFixed(2)}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-muted-foreground">Profit</p>
                        <p className="font-mono text-sm font-semibold text-primary">
                          +${pick.potential_profit?.toFixed(2)}
                        </p>
                      </div>
                      <Link to="/analyze">
                        <Button size="sm" variant="outline">
                          <Search className="w-3 h-3 mr-1" />
                          Analyze
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

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
                        <span className="text-xs text-muted-foreground">
                          {stat.label}
                        </span>
                      </div>
                      <p
                        className={`text-xl font-mono font-bold ${stat.color}`}
                      >
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
                    <h3 className="font-heading font-semibold mb-1">
                      Analyze Race
                    </h3>
                    <p className="text-sm text-muted-foreground flex-1">
                      Run 8-criteria analysis on any race
                    </p>
                    <ArrowRight className="w-4 h-4 text-muted-foreground mt-3" />
                  </CardContent>
                </Card>
              </Link>

              <Link to="/results">
                <Card className="border-border/50 bg-card/50 backdrop-blur-sm card-hover cursor-pointer h-full">
                  <CardContent className="p-5 flex flex-col h-full">
                    <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4">
                      <Flag className="w-6 h-6 text-accent" />
                    </div>
                    <h3 className="font-heading font-semibold mb-1">
                      Results
                    </h3>
                    <p className="text-sm text-muted-foreground flex-1">
                      Race results and bet outcomes
                    </p>
                    <ArrowRight className="w-4 h-4 text-muted-foreground mt-3" />
                  </CardContent>
                </Card>
              </Link>

              <Link to="/statistics">
                <Card className="border-border/50 bg-card/50 backdrop-blur-sm card-hover cursor-pointer h-full">
                  <CardContent className="p-5 flex flex-col h-full">
                    <div className="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center mb-4">
                      <BarChart3 className="w-6 h-6 text-secondary" />
                    </div>
                    <h3 className="font-heading font-semibold mb-1">
                      Statistics
                    </h3>
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
                  <CardTitle className="text-lg font-heading">
                    Recent Bets
                  </CardTitle>
                  <Link to="/history">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-muted-foreground"
                    >
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
                          <div
                            className={`w-2 h-8 rounded-full ${
                              bet.result === "WIN"
                                ? "bg-primary"
                                : bet.result === "LOSS"
                                ? "bg-destructive"
                                : "bg-muted-foreground"
                            }`}
                          />
                          <div>
                            <p className="font-medium">{bet.horse_name}</p>
                            <p className="text-xs text-muted-foreground">
                              {bet.track} R{bet.race_number} &middot;{" "}
                              {bet.bet_type}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge
                            variant="outline"
                            className={
                              bet.result === "WIN"
                                ? "badge-win"
                                : bet.result === "LOSS"
                                ? "badge-loss"
                                : "badge-pending"
                            }
                          >
                            {bet.result || "Pending"}
                          </Badge>
                          <p
                            className={`text-sm font-mono mt-1 ${
                              bet.profit_loss > 0
                                ? "text-primary"
                                : bet.profit_loss < 0
                                ? "text-destructive"
                                : "text-muted-foreground"
                            }`}
                          >
                            {bet.profit_loss
                              ? `${bet.profit_loss > 0 ? "+" : ""}$${bet.profit_loss.toFixed(2)}`
                              : `$${bet.stake?.toFixed(2)}`}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
