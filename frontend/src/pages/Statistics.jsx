import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown,
  Target,
  Trophy,
  Percent,
  DollarSign,
  Activity
} from "lucide-react";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid
} from "recharts";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Statistics({ user, setUser }) {
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      const response = await axios.get(`${API}/statistics`, { withCredentials: true });
      setStatistics(response.data);
    } catch (error) {
      console.error("Error fetching statistics:", error);
      toast.error("Failed to load statistics");
    } finally {
      setLoading(false);
    }
  };

  // Transform score data for chart
  const scoreChartData = statistics?.by_score 
    ? Object.entries(statistics.by_score).map(([score, data]) => ({
        score: `${score}/8`,
        winRate: parseFloat(data.win_rate),
        roi: parseFloat(data.roi),
        bets: data.bets
      }))
    : [];

  // Parse recent form for display
  const recentForm = statistics?.recent_form?.last_10_bets?.split('') || [];

  if (loading) {
    return (
      <DashboardLayout user={user} setUser={setUser}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout user={user} setUser={setUser}>
      <div className="space-y-8" data-testid="statistics-page">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-heading font-bold mb-2">Statistics</h1>
          <p className="text-muted-foreground">
            Track your betting performance and ROI
          </p>
        </div>

        {/* Overall Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <Trophy className="w-4 h-4 text-primary" />
                <span className="text-xs text-muted-foreground">Total Bets</span>
              </div>
              <p className="text-3xl font-mono font-bold">
                {statistics?.overall?.total_bets || 0}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {statistics?.overall?.wins || 0}W - {statistics?.overall?.losses || 0}L
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4 text-secondary" />
                <span className="text-xs text-muted-foreground">Win Rate</span>
              </div>
              <p className="text-3xl font-mono font-bold text-secondary">
                {statistics?.overall?.win_rate || "0%"}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Target: 35-45%
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <Percent className="w-4 h-4 text-accent" />
                <span className="text-xs text-muted-foreground">ROI</span>
              </div>
              <p className={`text-3xl font-mono font-bold ${
                parseFloat(statistics?.overall?.roi) >= 0 ? "text-primary" : "text-destructive"
              }`}>
                {statistics?.overall?.roi || "0%"}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Target: 15-25%
              </p>
            </CardContent>
          </Card>

          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <DollarSign className={`w-4 h-4 ${
                  parseFloat(statistics?.overall?.total_profit) >= 0 ? "text-primary" : "text-destructive"
                }`} />
                <span className="text-xs text-muted-foreground">Total Profit</span>
              </div>
              <p className={`text-3xl font-mono font-bold ${
                parseFloat(statistics?.overall?.total_profit) >= 0 ? "text-primary" : "text-destructive"
              }`}>
                ${statistics?.overall?.total_profit || "0.00"}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Staked: ${statistics?.overall?.total_staked || "0.00"}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Win Rate by Score */}
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-lg font-heading flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Win Rate by Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              {scoreChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={scoreChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis 
                      dataKey="score" 
                      stroke="hsl(var(--muted-foreground))"
                      fontSize={12}
                    />
                    <YAxis 
                      stroke="hsl(var(--muted-foreground))"
                      fontSize={12}
                      tickFormatter={(v) => `${v}%`}
                    />
                    <Tooltip 
                      contentStyle={{
                        background: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px'
                      }}
                      formatter={(value, name) => [`${value}%`, name === 'winRate' ? 'Win Rate' : 'ROI']}
                    />
                    <Bar 
                      dataKey="winRate" 
                      fill="hsl(var(--primary))" 
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                  No data yet - place some bets to see statistics
                </div>
              )}
            </CardContent>
          </Card>

          {/* ROI by Score */}
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-lg font-heading flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                ROI by Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              {scoreChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={scoreChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis 
                      dataKey="score" 
                      stroke="hsl(var(--muted-foreground))"
                      fontSize={12}
                    />
                    <YAxis 
                      stroke="hsl(var(--muted-foreground))"
                      fontSize={12}
                      tickFormatter={(v) => `${v}%`}
                    />
                    <Tooltip 
                      contentStyle={{
                        background: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px'
                      }}
                      formatter={(value) => [`${value}%`, 'ROI']}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="roi" 
                      stroke="hsl(var(--accent))" 
                      strokeWidth={2}
                      dot={{ fill: 'hsl(var(--accent))', strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                  No data yet - place some bets to see statistics
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Performance by Score Table */}
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-lg font-heading flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Performance by Score Level
            </CardTitle>
          </CardHeader>
          <CardContent>
            {scoreChartData.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground">Score</th>
                      <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground">Bets</th>
                      <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground">Wins</th>
                      <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground">Win Rate</th>
                      <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground">Staked</th>
                      <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground">Profit</th>
                      <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground">ROI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(statistics?.by_score || {}).map(([score, data]) => (
                      <tr key={score} className="border-b border-border/50 table-row-hover">
                        <td className="py-3 px-4">
                          <Badge variant="outline" className={
                            parseInt(score) >= 7 ? "score-excellent" :
                            parseInt(score) >= 6 ? "score-good" :
                            parseInt(score) >= 4 ? "score-borderline" : "score-weak"
                          }>
                            {score}/8
                          </Badge>
                        </td>
                        <td className="text-center py-3 px-4 font-mono">{data.bets}</td>
                        <td className="text-center py-3 px-4 font-mono">{data.wins}</td>
                        <td className="text-center py-3 px-4">
                          <span className={`font-mono ${
                            parseFloat(data.win_rate) >= 40 ? "text-primary" :
                            parseFloat(data.win_rate) >= 30 ? "text-accent" : "text-destructive"
                          }`}>
                            {data.win_rate}
                          </span>
                        </td>
                        <td className="text-center py-3 px-4 font-mono">${data.total_staked}</td>
                        <td className="text-center py-3 px-4">
                          <span className={`font-mono ${
                            parseFloat(data.total_profit) >= 0 ? "text-primary" : "text-destructive"
                          }`}>
                            ${data.total_profit}
                          </span>
                        </td>
                        <td className="text-center py-3 px-4">
                          <span className={`font-mono font-semibold ${
                            parseFloat(data.roi) >= 0 ? "text-primary" : "text-destructive"
                          }`}>
                            {data.roi}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No betting data yet. Place bets to see performance statistics.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Form */}
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-lg font-heading">Recent Form (Last 10 Bets)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {recentForm.length > 0 ? (
                recentForm.map((result, idx) => (
                  <div 
                    key={idx}
                    className={`w-10 h-10 rounded-lg flex items-center justify-center font-mono font-bold ${
                      result === "W" 
                        ? "bg-primary/20 text-primary border border-primary/30" 
                        : "bg-destructive/20 text-destructive border border-destructive/30"
                    }`}
                  >
                    {result}
                  </div>
                ))
              ) : (
                <p className="text-muted-foreground">No completed bets yet</p>
              )}
            </div>
            {statistics?.recent_form?.consecutive_losses > 0 && (
              <p className="text-sm text-accent mt-4">
                Current consecutive losses: {statistics.recent_form.consecutive_losses}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Algorithm Performance Info */}
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardContent className="p-6">
            <h3 className="font-heading font-semibold mb-4">Target Performance Benchmarks</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm text-muted-foreground mb-2">8/8 Score Bets</p>
                <p className="font-mono">Win Rate: 45-50%</p>
                <p className="font-mono text-primary">ROI: 20-25%</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">6-7/8 Score Bets</p>
                <p className="font-mono">Win Rate: 35-45%</p>
                <p className="font-mono text-primary">ROI: 10-20%</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">4-5/8 Score Bets</p>
                <p className="font-mono">Win Rate: 25-35%</p>
                <p className="font-mono text-accent">ROI: 0-10%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
