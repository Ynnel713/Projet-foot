import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import Home from "./routes/Home";
import Leagues from "./routes/Leagues";
import Nations from "./routes/Nations";
import CustomCompetition from "./routes/CustomCompetition";
import Simulation from "./routes/Simulation";
import Standings from "./routes/Standings";
import PitchView from "./routes/PitchView";
import Groups from "./routes/Groups";
import Bracket from "./routes/Bracket";
import Leaderboards from "./routes/Leaderboards";

export default function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/leagues" element={<Leagues />} />
          <Route path="/nations" element={<Nations />} />
          <Route path="/custom" element={<CustomCompetition />} />
          <Route path="/competition/:id/simulate" element={<Simulation />} />
          <Route path="/competition/:id/standings" element={<Standings />} />
          <Route path="/competition/:id/pitch" element={<PitchView />} />
          <Route path="/competition/:id/groups" element={<Groups />} />
          <Route path="/competition/:id/bracket" element={<Bracket />} />
          <Route path="/competition/:id/leaderboards" element={<Leaderboards />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}
