import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import CompetitionLayout, { CompetitionIndex } from "./components/layout/CompetitionLayout";
import Home from "./routes/Home";
import Leagues from "./routes/Leagues";
import Nations from "./routes/Nations";
import CustomCompetition from "./routes/CustomCompetition";
import Simulation from "./routes/Simulation";
import Standings from "./routes/Standings";
import TeamRoster from "./routes/TeamRoster";
import PlayerPage from "./routes/PlayerPage";
import PitchView from "./routes/PitchView";
import Groups from "./routes/Groups";
import Bracket from "./routes/Bracket";
import Leaderboards from "./routes/Leaderboards";
import V2Match from "./routes/V2Match";

export default function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/leagues" element={<Leagues />} />
          <Route path="/nations" element={<Nations />} />
          <Route path="/custom" element={<CustomCompetition />} />
          {/* Espace de compétition à onglets (refonte UI, lot 2) ; la vue terrain reste plein écran, hors onglets. */}
          <Route path="/competition/:id/pitch" element={<PitchView />} />
          <Route path="/competition/:id" element={<CompetitionLayout />}>
            <Route index element={<CompetitionIndex />} />
            <Route path="simulate" element={<Simulation />} />
            <Route path="standings" element={<Standings />} />
            <Route path="clubs/:clubName" element={<TeamRoster />} />
            <Route path="clubs/:clubName/players/:playerName" element={<PlayerPage />} />
            <Route path="groups" element={<Groups />} />
            <Route path="bracket" element={<Bracket />} />
            <Route path="leaderboards" element={<Leaderboards />} />
          </Route>
          <Route path="/v2" element={<V2Match />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  );
}
