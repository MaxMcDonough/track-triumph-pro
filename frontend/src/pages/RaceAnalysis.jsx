import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { RecommendationCard } from "@/components/dashboard/RecommendationCard";
import { WarningBanner } from "@/components/dashboard/WarningBanner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Search, 
  Loader2, 
  MapPin, 
  Calendar,
  Trophy,
  Target,
  Layers,
  Shield,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Star
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function RaceAnalysis({ user }) {
  const [tracks, setTracks] = useState({ uk_tracks: [], us_tracks: [] });
  const [selectedTrack, setSelectedTrack] = useState("");
  const [selectedRace, setSelectedRace] = useState("");
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [placeBetDialog, setPlaceBetDialog] = useState(null);
  const [placingBet, setPlacingBet] = useState(false);

  useEffect(() => {
    fetchTracks();
  }, []);

  const fetchTracks = async () => {
    try {
      const response = await axios.get(`${API}/tracks`, { withCredentials: true });
      setTracks(response.data);
    } catch (error) {
      console.error("Error fetching tracks:", error);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedTrack || !selectedRace) {
      toast.error("Please select a track and race");
      return;
    }

    setLoading(true);
    setAnalysisResult(null);

    try {
      const response = await axios.post(`${API}/analyze`, {
        track: selectedTrack,
        race_number: parseInt(selectedRace)
      }, { withCredentials: true });

      setAnalysisResult(response.data);
      toast.success("Race analysis complete!");
    } catch (error) {
      console.error("Analysis error:", error);
      toast.error(error.response?.data?.detail || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const handlePlaceBet = (recommendation) => {
    setPlaceBetDialog(recommendation);
  };

  const confirmPlaceBet = async () => {
    if (!placeBetDialog) return;

    setPlacingBet(true);
    try {
      await axios.post(`${API}/bets`, {
        track: analysisResult.race_info.track,
        race_number: analysisResult.race_info.race_number,
        horse_name: placeBetDialog.horse,
        draw_number: placeBetDialog.draw_number,
        bet_type: placeBetDialog.type,
        stake: placeBetDialog.stake,
        odds: placeBetDialog.odds,
        score: placeBetDialog.score
      }, { withCredentials: true });

      toast.success(`Bet placed on ${placeBetDialog.horse}!`);
      setPlaceBetDialog(null);
      
      // Refresh analysis to update bankroll
      handleAnalyze();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to place bet");
    } finally {
      setPlacingBet(false);
    }
  };

  const getCriteriaIcon = (text) => {
    if (text?.includes("✅")) return <CheckCircle2 className="w-4 h-4 text-primary" />;
    if (text?.includes("⚠️")) return <AlertCircle className="w-4 h-4 text-accent" />;
    return <XCircle className="w-4 h-4 text-destructive" />;
  };

  return (
    <DashboardLayout user={user}>
      <div className="space-y-8" data-testid="race-analysis-page">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-heading font-bold mb-2">Race Analysis</h1>
          <p className="text-muted-foreground">
            Select a race to run our 8-criteria scoring algorithm
          </p>
        </div>

        {/* Race Selector */}
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-lg font-heading flex items-center gap-2">
              <Search className="w-5 h-5" />
              Select Race
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Track Selection */}
              <div className="space-y-2">
                <Label>Track</Label>
                <Select value={selectedTrack} onValueChange={setSelectedTrack}>
                  <SelectTrigger data-testid="track-select">
                    <SelectValue placeholder="Select track..." />
                  </SelectTrigger>
                  <SelectContent>
                    {tracks.uk_tracks.map((track) => (
                      <SelectItem key={track.id} value={track.id}>
                        {track.name}
                      </SelectItem>
                    ))}
                    {tracks.us_tracks.map((track) => (
                      <SelectItem key={track.id} value={track.id}>
                        {track.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Race Selection */}
              <div className="space-y-2">
                <Label>Race Number</Label>
                <Select value={selectedRace} onValueChange={setSelectedRace}>
                  <SelectTrigger data-testid="race-select">
                    <SelectValue placeholder="Select race..." />
                  </SelectTrigger>
                  <SelectContent>
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
                      <SelectItem key={num} value={num.toString()}>
                        Race {num}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Analyze Button */}
              <div className="flex items-end">
                <Button 
                  className="w-full btn-glow"
                  onClick={handleAnalyze}
                  disabled={loading || !selectedTrack || !selectedRace}
                  data-testid="analyze-btn"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" />
                      Analyze Race
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Analysis Results */}
        {analysisResult && (
          <div className="space-y-6 animate-fade-in">
            {/* Race Info Banner */}
            <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
              <CardContent className="p-4">
                <div className="flex flex-wrap items-center gap-4">
                  <Badge variant="outline" className="text-sm">
                    {analysisResult.race_info.track.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </Badge>
                  <Badge variant="secondary" className="text-sm">
                    Race {analysisResult.race_info.race_number}
                  </Badge>
                  <Badge variant="secondary" className="text-sm">
                    {analysisResult.race_info.field_size} Runners
                  </Badge>
                  <Badge variant="secondary" className="text-sm">
                    {analysisResult.race_info.date}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Warnings */}
            {analysisResult.warnings?.length > 0 && (
              <WarningBanner warnings={analysisResult.warnings} />
            )}

            {/* Recommendations Grid */}
            <div>
              <h2 className="text-xl font-heading font-semibold mb-4">Betting Recommendations</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {analysisResult.recommendations.win && (
                  <RecommendationCard 
                    recommendation={analysisResult.recommendations.win}
                    onPlaceBet={handlePlaceBet}
                  />
                )}
                {analysisResult.recommendations.place && (
                  <RecommendationCard 
                    recommendation={analysisResult.recommendations.place}
                    onPlaceBet={handlePlaceBet}
                  />
                )}
                {analysisResult.recommendations.trifecta && (
                  <RecommendationCard 
                    recommendation={analysisResult.recommendations.trifecta}
                  />
                )}
                {analysisResult.recommendations.safety && (
                  <RecommendationCard 
                    recommendation={analysisResult.recommendations.safety}
                    onPlaceBet={handlePlaceBet}
                  />
                )}
              </div>
            </div>

            {/* All Horses Table */}
            <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-lg font-heading">All Horses Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="scores">
                  <TabsList className="mb-4">
                    <TabsTrigger value="scores">Score Overview</TabsTrigger>
                    <TabsTrigger value="detailed">Detailed Breakdown</TabsTrigger>
                  </TabsList>

                  <TabsContent value="scores">
                    <div className="space-y-3">
                      {analysisResult.all_horses
                        ?.sort((a, b) => b.place_score?.score - a.place_score?.score)
                        .map((horse, idx) => (
                          <div 
                            key={idx}
                            className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border/50 table-row-hover"
                          >
                            <div className="flex items-center gap-4">
                              <span className="w-8 h-8 rounded-full bg-muted flex items-center justify-center font-mono text-sm">
                                #{horse.draw_number}
                              </span>
                              <div>
                                <p className="font-medium">{horse.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  {horse.jockey_name} • {horse.trainer_name}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="text-right">
                                <p className="text-xs text-muted-foreground">Win</p>
                                <p className="font-mono text-sm">{horse.best_win_odds?.toFixed(2)}</p>
                              </div>
                              <div className="text-right">
                                <p className="text-xs text-muted-foreground">Place</p>
                                <p className="font-mono text-sm">{horse.best_place_odds?.toFixed(2)}</p>
                              </div>
                              <div className="flex items-center gap-1">
                                {[...Array(5)].map((_, i) => (
                                  <Star 
                                    key={i}
                                    className={`w-3 h-3 ${
                                      i < (horse.place_score?.star_rating || 0) 
                                        ? "text-accent fill-accent" 
                                        : "text-muted"
                                    }`}
                                  />
                                ))}
                              </div>
                              <Badge 
                                variant="outline" 
                                className={
                                  horse.place_score?.score >= 7 ? "score-excellent" :
                                  horse.place_score?.score >= 6 ? "score-good" :
                                  horse.place_score?.score >= 4 ? "score-borderline" : "score-weak"
                                }
                              >
                                {horse.place_score?.score || 0}/8
                              </Badge>
                            </div>
                          </div>
                        ))}
                    </div>
                  </TabsContent>

                  <TabsContent value="detailed">
                    <div className="space-y-4">
                      {analysisResult.all_horses
                        ?.sort((a, b) => b.place_score?.score - a.place_score?.score)
                        .slice(0, 5)
                        .map((horse, idx) => (
                          <Card key={idx} className="border-border/50 bg-muted/20">
                            <CardContent className="p-4">
                              <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                  <span className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center font-mono text-sm text-primary">
                                    #{horse.draw_number}
                                  </span>
                                  <div>
                                    <p className="font-heading font-semibold">{horse.name}</p>
                                    <p className="text-xs text-muted-foreground">
                                      Form: {horse.form}
                                    </p>
                                  </div>
                                </div>
                                <Badge 
                                  variant="outline" 
                                  className={
                                    horse.place_score?.score >= 7 ? "score-excellent" :
                                    horse.place_score?.score >= 6 ? "score-good" :
                                    horse.place_score?.score >= 4 ? "score-borderline" : "score-weak"
                                  }
                                >
                                  {horse.place_score?.score || 0}/8 - {horse.place_score?.recommendation}
                                </Badge>
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                {horse.place_score?.criteria_breakdown && 
                                  Object.entries(horse.place_score.criteria_breakdown).map(([key, value]) => (
                                    <div key={key} className="flex items-start gap-2 text-xs">
                                      {getCriteriaIcon(value)}
                                      <span className="text-muted-foreground line-clamp-2">
                                        {value?.replace(/[✅⚠️❌]/g, '').trim()}
                                      </span>
                                    </div>
                                  ))
                                }
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Place Bet Dialog */}
        <Dialog open={!!placeBetDialog} onOpenChange={() => setPlaceBetDialog(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="font-heading">Confirm Bet</DialogTitle>
              <DialogDescription>
                You are about to place the following bet
              </DialogDescription>
            </DialogHeader>
            
            {placeBetDialog && (
              <div className="space-y-4 py-4">
                <div className="p-4 rounded-lg bg-muted/30 border border-border/50">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Horse</p>
                      <p className="font-semibold">{placeBetDialog.horse}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Type</p>
                      <p className="font-semibold">{placeBetDialog.type}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Odds</p>
                      <p className="font-mono font-semibold">{placeBetDialog.odds?.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Stake</p>
                      <p className="font-mono font-semibold text-primary">
                        ${placeBetDialog.stake?.toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="flex justify-between p-3 rounded-lg bg-primary/5 border border-primary/10">
                  <span className="text-muted-foreground">Potential Profit</span>
                  <span className="font-mono font-semibold text-primary">
                    +${placeBetDialog.potential_profit?.toFixed(2)}
                  </span>
                </div>
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setPlaceBetDialog(null)}>
                Cancel
              </Button>
              <Button 
                onClick={confirmPlaceBet}
                disabled={placingBet}
                className="btn-glow"
                data-testid="confirm-bet-btn"
              >
                {placingBet ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Placing Bet...
                  </>
                ) : (
                  "Confirm Bet"
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
