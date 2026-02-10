import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";

// Pages
import Dashboard from "@/pages/Dashboard";
import RaceAnalysis from "@/pages/RaceAnalysis";
import Results from "@/pages/Results";
import BetHistory from "@/pages/BetHistory";
import Statistics from "@/pages/Statistics";
import Settings from "@/pages/Settings";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Default user for no-auth mode
const defaultUser = {
  user_id: "default_user",
  email: "user@racinganalyzer.com",
  name: "Racing Pro"
};

function App() {
  const [user] = useState(defaultUser);

  return (
    <div className="dark">
      <BrowserRouter>
        <Routes>
          <Route path="/dashboard" element={<Dashboard user={user} />} />
          <Route path="/analyze" element={<RaceAnalysis user={user} />} />
          <Route path="/results" element={<Results user={user} />} />
          <Route path="/history" element={<BetHistory user={user} />} />
          <Route path="/statistics" element={<Statistics user={user} />} />
          <Route path="/settings" element={<Settings user={user} />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
