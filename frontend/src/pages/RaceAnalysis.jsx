import { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { RecommendationCard } from "@/components/dashboard/RecommendationCard";
import { WarningBanner } from "@/components/dashboard/WarningBanner";
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
  Search,
  Loader2,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Star,
  Radio,
  Clock,
  MapPin,
  ChevronRight,
  RefreshCw,
  Zap,
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function RaceAnalysis({ user }) {
  const [raceData, setRaceData] = useState(null);
  const [loadingRaces, setLoadingRaces] = useState(true);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [selectedRace, setSelectedRace] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [placeBetDialog, setPlaceBetDialog] = useState(null);
  const [placingBet, setPlacingBet] = useState(false);

  useEffect(() => {
    fetchTodaysRaces();
  }, []);

  const fetchTodaysRaces = async () => {
    setLoadingRaces(true);
    try {
      const response = await axios.get(`${API}/racecards/today`);
      setRaceData(response.data);
    } catch (error) {
      console.error("Error fetching racecards:", error);
      toast.error("Failed to load today's races");
    } finally {
      setLoadingRaces(false);
    }
  };

  const handleAnalyze = async (raceId) => {
    setLoading(true);
    setAnalysisResult(null);
    try {
      const response = await axios.post(`${API}/analyze`, { race_id: raceId });
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
    if (!placeBetDialog || !analysisResult) return;
    setPlacingBet(true);
    try {
      await axios.post(`${API}/bets`, {
        track: analysisResult.race_info.track,
        race_number: analysisResult.race_info.race_number || 1,
        horse_name: placeBetDialog.horse,
        draw_number: placeBetDialog.draw_number,
        bet_type: placeBetDialog.type,
        stake: placeBetDialog.stake,
        odds: placeBetDialog.odds,
        score: placeBetDialog.score,
      });
      toast.success(`Bet placed on ${placeBetDialog.horse}!`);
      setPlaceBetDialog(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to place bet");
    } finally {
      setPlacingBet(false);
    }
  };

  const getCriteriaIcon = (text) => {
    if (text?.startsWith("PASS")) return <CheckCircle2 className="w-4 h-4 text-primary" />;
    if (text?.startsWith("PARTIAL") || text?.startsWith("NEUTRAL")) return <AlertCircle className="w-4 h-4 text-accent" />;
    return <XCircle className="w-4 h-4 text-destructive" />;
  };

  const courses = raceData?.courses || [];
  const allRaces = raceData?.races || [];
  const courseRaces = selectedCourse
    ? allRaces.filter((r) => r.course === selectedCourse)
    : [];

  return (
    <DashboardLayout user={user}>
      <div className="space-y-8" data-testid="race-analysis-page">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-heading font-bold mb-2">Race Analysis</h1>
            <div className="text-muted-foreground text-sm">
              {raceData?.data_source === "LIVE - The Racing API" ? (
                <span className="flex items-center gap-2">
                  <Radio className="w-4 h-4 text-primary animate-pulse" />
                  <span>Live data from The Racing API</span>
                  <Badge variant="outline" className="text-xs ml-1" data-testid="live-badge">
                    LIVE
                  </Badge>
                </span>
              ) : (
                "Select a race to run our 8-criteria scoring algorithm"
              )}
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchTodaysRaces}
            disabled={loadingRaces}
            data-testid="refresh-races-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loadingRaces ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        {/* Loading state */}
        {loadingRaces && (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        )}

        {/* No analysis yet - show race picker */}
        {!loadingRaces && !analysisResult && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Course List */}
            <div className="lg:col-span-4 space-y-4">
              <h2 className="text-lg font-heading font-semibold flex items-center gap-2">
                <MapPin className="w-5 h-5" />
                Today's Courses ({courses.length})
              </h2>
              <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
                {courses.map((course) => (
                  <button
                    key={course.course}
                    onClick={() => {
                      setSelectedCourse(course.course);
                      setSelectedRace(null);
                    }}
                    className={`w-full text-left p-4 rounded-lg border transition-all ${
                      selectedCourse === course.course
                        ? "border-primary bg-primary/5"
                        : "border-border/50 bg-card/50 hover:border-primary/30"
                    }`}
                    data-testid={`course-${course.course.toLowerCase().replace(/\s+/g, "-")}`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-heading font-semibold">{course.course}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {course.races.length} races &middot; {course.going} &middot; {course.surface}
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    </div>
                  </button>
                ))}
                {courses.length === 0 && !loadingRaces && (
                  <Card className="border-border/50 bg-card/50">
                    <CardContent className="p-8 text-center">
                      <Zap className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
                      <p className="text-muted-foreground">No races available today</p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>

            {/* Race List for selected course */}
            <div className="lg:col-span-8 space-y-4">
              {selectedCourse ? (
                <>
                  <h2 className="text-lg font-heading font-semibold flex items-center gap-2">
                    <Clock className="w-5 h-5" />
                    {selectedCourse} - Races
                  </h2>
                  <div className="space-y-3">
                    {courseRaces.map((race) => (
                      <Card
                        key={race.race_id}
                        className="border-border/50 bg-card/50 backdrop-blur-sm card-hover cursor-pointer"
                        data-testid={`race-card-${race.race_id}`}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <Badge variant="outline" className="font-mono text-sm">
                                  {race.off_time}
                                </Badge>
                                <Badge variant="secondary" className="text-xs">
                                  {race.race_type}
                                </Badge>
                                <Badge variant="secondary" className="text-xs">
                                  {race.race_class}
                                </Badge>
                              </div>
                              <p className="font-medium text-sm line-clamp-1">
                                {race.race_name}
                              </p>
                              <p className="text-xs text-muted-foreground mt-1">
                                {race.distance}f &middot; {race.field_size} runners &middot; {race.going} &middot; {race.prize}
                              </p>
                            </div>
                            <Button
                              className="ml-4 btn-glow"
                              size="sm"
                              onClick={() => handleAnalyze(race.race_id)}
                              disabled={loading}
                              data-testid={`analyze-${race.race_id}`}
                            >
                              {loading ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <>
                                  <Search className="w-4 h-4 mr-1" />
                                  Analyze
                                </>
                              )}
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </>
              ) : (
                <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
                  <CardContent className="p-12 text-center">
                    <MapPin className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="font-heading font-semibold text-lg mb-2">
                      Select a course
                    </h3>
                    <p className="text-muted-foreground">
                      Pick a racecourse from the left to see today's races
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}

        {/* Analysis Results */}
        {analysisResult && (
          <div className="space-y-6 animate-fade-in">
            {/* Back button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAnalysisResult(null)}
              data-testid="back-to-races-btn"
            >
              Back to Races
            </Button>

            {/* Race Info Banner */}
            <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
              <CardContent className="p-4">
                <div className="flex flex-wrap items-center gap-3">
                  <Badge variant="outline" className="text-sm font-semibold">
                    {analysisResult.race_info.track}
                  </Badge>
                  {analysisResult.race_info.off_time && (
                    <Badge variant="secondary" className="text-sm font-mono">
                      {analysisResult.race_info.off_time}
                    </Badge>
                  )}
                  {analysisResult.race_info.race_type && (
                    <Badge variant="secondary" className="text-sm">
                      {analysisResult.race_info.race_type}
                    </Badge>
                  )}
                  <Badge variant="secondary" className="text-sm">
                    {analysisResult.race_info.field_size} Runners
                  </Badge>
                  {analysisResult.race_info.going && (
                    <Badge variant="secondary" className="text-sm">
                      {analysisResult.race_info.going}
                    </Badge>
                  )}
                  {analysisResult.race_info.distance && (
                    <Badge variant="secondary" className="text-sm">
                      {analysisResult.race_info.distance}f
                    </Badge>
                  )}
                  {analysisResult.data_source?.includes("LIVE") && (
                    <Badge className="bg-primary/20 text-primary border-primary/30 text-xs" data-testid="analysis-live-badge">
                      LIVE DATA
                    </Badge>
                  )}
                </div>
                {analysisResult.race_info.race_name && (
                  <p className="text-sm text-muted-foreground mt-2">
                    {analysisResult.race_info.race_name}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Warnings */}
            {analysisResult.warnings?.length > 0 && (
              <WarningBanner warnings={analysisResult.warnings} />
            )}

            {/* Recommendations Grid */}
            <div>
              <h2 className="text-xl font-heading font-semibold mb-4">
                Betting Recommendations
              </h2>
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
                <CardTitle className="text-lg font-heading">
                  All Horses Analysis
                </CardTitle>
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
                        ?.sort(
                          (a, b) =>
                            (b.place_score?.score || 0) -
                            (a.place_score?.score || 0)
                        )
                        .map((horse, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-4 rounded-lg bg-muted/30 border border-border/50 table-row-hover"
                            data-testid={`horse-row-${idx}`}
                          >
                            <div className="flex items-center gap-4">
                              <span className="w-8 h-8 rounded-full bg-muted flex items-center justify-center font-mono text-sm">
                                {horse.number || horse.draw_number || idx + 1}
                              </span>
                              <div>
                                <p className="font-medium">{horse.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  {horse.jockey_name} &middot;{" "}
                                  {horse.trainer_name}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  Form: {horse.form || "N/A"} &middot; OR:{" "}
                                  {horse.official_rating || "N/A"}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-4">
                              <div className="flex items-center gap-1">
                                {[...Array(5)].map((_, i) => (
                                  <Star
                                    key={i}
                                    className={`w-3 h-3 ${
                                      i <
                                      (horse.place_score?.star_rating || 0)
                                        ? "text-accent fill-accent"
                                        : "text-muted"
                                    }`}
                                  />
                                ))}
                              </div>
                              <Badge
                                variant="outline"
                                className={
                                  (horse.place_score?.score || 0) >= 7
                                    ? "score-excellent"
                                    : (horse.place_score?.score || 0) >= 6
                                    ? "score-good"
                                    : (horse.place_score?.score || 0) >= 4
                                    ? "score-borderline"
                                    : "score-weak"
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
                        ?.sort(
                          (a, b) =>
                            (b.place_score?.score || 0) -
                            (a.place_score?.score || 0)
                        )
                        .slice(0, 5)
                        .map((horse, idx) => (
                          <Card
                            key={idx}
                            className="border-border/50 bg-muted/20"
                          >
                            <CardContent className="p-4">
                              <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                  <span className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center font-mono text-sm text-primary">
                                    {horse.number || horse.draw_number || idx + 1}
                                  </span>
                                  <div>
                                    <p className="font-heading font-semibold">
                                      {horse.name}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                      Form: {horse.form || "N/A"} &middot; Age:{" "}
                                      {horse.age} &middot; OR:{" "}
                                      {horse.official_rating || "N/A"}
                                    </p>
                                  </div>
                                </div>
                                <Badge
                                  variant="outline"
                                  className={
                                    (horse.place_score?.score || 0) >= 7
                                      ? "score-excellent"
                                      : (horse.place_score?.score || 0) >= 6
                                      ? "score-good"
                                      : (horse.place_score?.score || 0) >= 4
                                      ? "score-borderline"
                                      : "score-weak"
                                  }
                                >
                                  {horse.place_score?.score || 0}/8 -{" "}
                                  {horse.place_score?.recommendation}
                                </Badge>
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                {horse.place_score?.criteria_breakdown &&
                                  Object.entries(
                                    horse.place_score.criteria_breakdown
                                  ).map(([key, value]) => (
                                    <div
                                      key={key}
                                      className="flex items-start gap-2 text-xs"
                                    >
                                      {getCriteriaIcon(value)}
                                      <span className="text-muted-foreground line-clamp-2">
                                        {value}
                                      </span>
                                    </div>
                                  ))}
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
        <Dialog
          open={!!placeBetDialog}
          onOpenChange={() => setPlaceBetDialog(null)}
        >
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
                      <p className="font-mono font-semibold">
                        {placeBetDialog.odds?.toFixed(2)}
                      </p>
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
                  <span className="text-muted-foreground">
                    Potential Profit
                  </span>
                  <span className="font-mono font-semibold text-primary">
                    +${placeBetDialog.potential_profit?.toFixed(2)}
                  </span>
                </div>
              </div>
            )}

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setPlaceBetDialog(null)}
              >
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
