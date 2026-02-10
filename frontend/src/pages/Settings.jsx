import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  Settings as SettingsIcon, 
  Wallet,
  ShieldAlert,
  RotateCcw,
  Save,
  Loader2,
  Database,
  CheckCircle2,
  XCircle,
  AlertTriangle
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Settings({ user }) {
  const [bankroll, setBankroll] = useState(null);
  const [scraperStatus, setScraperStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  
  const [formData, setFormData] = useState({
    current_bankroll: "",
    stop_loss: "",
    max_daily_bets: ""
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [bankrollRes, scraperRes] = await Promise.all([
        axios.get(`${API}/bankroll`, { withCredentials: true }),
        axios.get(`${API}/scraper/status`, { withCredentials: true })
      ]);

      setBankroll(bankrollRes.data);
      setScraperStatus(scraperRes.data);
      setFormData({
        current_bankroll: bankrollRes.data.current_bankroll?.toString() || "",
        stop_loss: bankrollRes.data.stop_loss?.toString() || "",
        max_daily_bets: bankrollRes.data.max_daily_bets?.toString() || ""
      });
    } catch (error) {
      console.error("Error fetching settings:", error);
      toast.error("Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updateData = {};
      if (formData.current_bankroll) updateData.current_bankroll = parseFloat(formData.current_bankroll);
      if (formData.stop_loss) updateData.stop_loss = parseFloat(formData.stop_loss);
      if (formData.max_daily_bets) updateData.max_daily_bets = parseInt(formData.max_daily_bets);

      await axios.put(`${API}/bankroll`, updateData, { withCredentials: true });
      toast.success("Settings saved!");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm("Reset bankroll to starting amount? This cannot be undone.")) return;
    
    setResetting(true);
    try {
      await axios.post(`${API}/bankroll/reset`, {}, { withCredentials: true });
      toast.success("Bankroll reset to starting amount!");
      fetchData();
    } catch (error) {
      toast.error("Failed to reset bankroll");
    } finally {
      setResetting(false);
    }
  };

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
      <div className="space-y-8 max-w-4xl" data-testid="settings-page">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-heading font-bold mb-2">Settings</h1>
          <p className="text-muted-foreground">
            Manage your bankroll and data source configurations
          </p>
        </div>

        {/* Bankroll Settings */}
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-lg font-heading flex items-center gap-2">
              <Wallet className="w-5 h-5" />
              Bankroll Settings
            </CardTitle>
            <CardDescription>
              Configure your betting bankroll and risk management rules
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <Label htmlFor="current_bankroll">Current Bankroll ($)</Label>
                <Input
                  id="current_bankroll"
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.current_bankroll}
                  onChange={(e) => setFormData({ ...formData, current_bankroll: e.target.value })}
                  className="font-mono"
                  data-testid="current-bankroll-input"
                />
                <p className="text-xs text-muted-foreground">
                  Your current betting balance
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="stop_loss">Stop-Loss ($)</Label>
                <Input
                  id="stop_loss"
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.stop_loss}
                  onChange={(e) => setFormData({ ...formData, stop_loss: e.target.value })}
                  className="font-mono"
                  data-testid="stop-loss-input"
                />
                <p className="text-xs text-muted-foreground">
                  Stop betting when balance drops to this level
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="max_daily_bets">Max Daily Bets</Label>
                <Input
                  id="max_daily_bets"
                  type="number"
                  min="1"
                  max="10"
                  value={formData.max_daily_bets}
                  onChange={(e) => setFormData({ ...formData, max_daily_bets: e.target.value })}
                  className="font-mono"
                  data-testid="max-daily-bets-input"
                />
                <p className="text-xs text-muted-foreground">
                  Maximum bets per day (recommended: 5)
                </p>
              </div>
            </div>

            <Separator />

            <div className="flex flex-col md:flex-row gap-4">
              <Button 
                onClick={handleSave}
                disabled={saving}
                className="btn-glow"
                data-testid="save-settings-btn"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Settings
                  </>
                )}
              </Button>

              <Button 
                variant="outline"
                onClick={handleReset}
                disabled={resetting}
                className="border-accent text-accent hover:bg-accent/10"
                data-testid="reset-bankroll-btn"
              >
                {resetting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Resetting...
                  </>
                ) : (
                  <>
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Reset Bankroll
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Discipline Rules */}
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-lg font-heading flex items-center gap-2">
              <ShieldAlert className="w-5 h-5" />
              Discipline Rules
            </CardTitle>
            <CardDescription>
              Active risk management rules protecting your bankroll
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/30 border border-border/50">
                <CheckCircle2 className="w-5 h-5 text-primary mt-0.5" />
                <div>
                  <p className="font-medium">Stop-Loss Protection</p>
                  <p className="text-sm text-muted-foreground">
                    Betting automatically stops when balance reaches ${bankroll?.stop_loss?.toFixed(2)}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/30 border border-border/50">
                <CheckCircle2 className="w-5 h-5 text-primary mt-0.5" />
                <div>
                  <p className="font-medium">Two-Loss Rule</p>
                  <p className="text-sm text-muted-foreground">
                    Betting stops for the day after 2 consecutive losses
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/30 border border-border/50">
                <CheckCircle2 className="w-5 h-5 text-primary mt-0.5" />
                <div>
                  <p className="font-medium">Maximum Stake Rule</p>
                  <p className="text-sm text-muted-foreground">
                    Individual bets capped at 3% of current bankroll
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/30 border border-border/50">
                <CheckCircle2 className="w-5 h-5 text-primary mt-0.5" />
                <div>
                  <p className="font-medium">Daily Bet Limit</p>
                  <p className="text-sm text-muted-foreground">
                    Maximum {bankroll?.max_daily_bets || 5} bets per day to maintain discipline
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/30 border border-border/50">
                <CheckCircle2 className="w-5 h-5 text-primary mt-0.5" />
                <div>
                  <p className="font-medium">Chasing Detection</p>
                  <p className="text-sm text-muted-foreground">
                    Warning triggered if stake increases after consecutive losses
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Data Sources Status */}
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-lg font-heading flex items-center gap-2">
              <Database className="w-5 h-5" />
              Data Sources Configuration
            </CardTitle>
            <CardDescription>
              Configure API keys for live racing data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {scraperStatus && Object.entries(scraperStatus)
                .filter(([key]) => key !== 'message')
                .map(([key, value]) => (
                  <div 
                    key={key}
                    className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border/50"
                  >
                    <div className="flex items-center gap-3">
                      {value.configured ? (
                        <CheckCircle2 className="w-5 h-5 text-primary" />
                      ) : (
                        <AlertTriangle className="w-5 h-5 text-accent" />
                      )}
                      <div>
                        <p className="font-medium">{value.source}</p>
                        <p className="text-xs text-muted-foreground">
                          {key.toUpperCase().replace(/_/g, ' ')}
                        </p>
                      </div>
                    </div>
                    <Badge variant={value.configured ? "default" : "secondary"}>
                      {value.configured ? "Configured" : "Not Configured"}
                    </Badge>
                  </div>
                ))}

              <div className="p-4 rounded-lg bg-secondary/10 border border-secondary/30">
                <p className="text-sm text-secondary">
                  {scraperStatus?.message || "Add API keys to backend/.env to enable live data scraping"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Account Info */}
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-lg font-heading">Account Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Email</span>
                <span className="font-medium">{user?.email}</span>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Name</span>
                <span className="font-medium">{user?.name}</span>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">User ID</span>
                <span className="font-mono text-sm text-muted-foreground">{user?.user_id}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
