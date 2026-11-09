import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getPersoClubs, getV2Lineup, getV2Match, startV2Match } from "../api/client";
import MatchScreen from "../components/match/MatchScreen";
import MatchSetup from "../components/match/MatchSetup";
import useMatchPlayback, { SPEED_OPTIONS } from "../hooks/useMatchPlayback";

// Le rejeu démarre quand ce nombre d'images (~1 s de match chacune) est calculé ; le reste arrive pendant qu'on regarde.
const START_BUFFER_TICKS = 60;
const POLL_MS = 1000;

// Écran V2 (docs/PRD_PRODUIT.md US-27 à 29, docs/PLAN_V2.md Phase 4) : lance un match isolé, puis
// rejoue sa trace déjà calculée (voir v2engine/match.py) -- le score n'est révélé qu'au fil des
// buts horodatés dans la trace, jamais affiché avant que la lecture ne les atteigne (US-29).
// Assembleur (ticket v2-ecran-match/01) : réglage dans MatchSetup, lecture dans MatchScreen, boucle dans
// useMatchPlayback.
export default function V2Match() {
  const navigate = useNavigate();
  const [clubs, setClubs] = useState([]);
  const [home, setHome] = useState("");
  const [away, setAway] = useState("");
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null); // joueur dont on lit l'intention (ADR 0001)
  const [computed, setComputed] = useState(0); // images déjà calculées, pendant l'attente avant le démarrage
  const [lineups, setLineups] = useState(null); // { home, away } : feuilles de match numérotées
  const playback = useMatchPlayback();
  const { begin, receive, setSpeed } = playback;
  const runRef = useRef(0); // numéro du lancement en cours : un lancement périmé ou un démontage arrête sa lecture
  useEffect(() => () => { runRef.current += 1; }, []);

  useEffect(() => {
    getPersoClubs()
      .then((list) => {
        setClubs(list);
        if (list.length >= 2) {
          setHome(list[0].name);
          setAway(list[1].name);
        }
      })
      .catch(() => setError("Impossible de charger les clubs."));
  }, []);

  // Rejeu de développement, absent du build de production (ticket v2-ecran-match/00) :
  // /v2?fixture=<nom>[&t=<minute>][&speed=<x>][&paused=1] rejoue une trace réelle enregistrée, sans l'API.
  useEffect(() => {
    if (!import.meta.env.DEV) return undefined;
    const query = new URLSearchParams(window.location.search);
    const name = query.get("fixture");
    if (!name) return undefined;
    let cancelled = false;
    import("../dev/fixture.js")
      .then(({ loadFixture }) => loadFixture(name))
      .then(({ lineups: recorded, ...live }) => {
        if (cancelled) return;
        const asked_t = Number(query.get("t") || 0);
        const start = Number.isFinite(asked_t) ? Math.min(Math.max(0, asked_t) * 60, (live.ticks.length - 1) * live.tick_seconds) : 0;
        const asked = Number(query.get("speed"));
        if (SPEED_OPTIONS.includes(asked)) setSpeed(asked);
        setLineups(recorded);
        setComputed(live.ticks.length);
        begin(live, start, query.get("paused") !== "1");
      })
      .catch(() => setError(`Trace « ${name} » introuvable (voir scripts/record_v2_trace.py).`));
    return () => {
      cancelled = true;
    };
    // `begin` et `setSpeed` sont stables : effet de montage seulement
  }, [begin, setSpeed]);

  async function handleLaunch() {
    if (!home || !away || home === away) {
      setError("Choisis deux clubs différents.");
      return;
    }
    setLaunching(true);
    setError(null);
    setComputed(0);
    const run = ++runRef.current;
    try {
      const [{ id }, homeLineup, awayLineup] = await Promise.all([
        startV2Match({ home, away }),
        getV2Lineup(home),
        getV2Lineup(away),
      ]);
      setLineups({ home: homeLineup, away: awayLineup });
      let ticks = [];
      let started = false;
      for (;;) {
        const res = await getV2Match(id, ticks.length);
        if (run !== runRef.current) return;
        if (res.error) throw new Error(res.error);
        ticks = ticks.concat(res.ticks);
        const live = { ...res, ticks };
        receive(live, started);
        setComputed(ticks.length);
        if (!started && (ticks.length >= START_BUFFER_TICKS || (res.done && ticks.length > 1))) {
          started = true;
          setSelected(null); // le joueur sélectionné n'est peut-être pas de ce match
          begin(live, 0, true);
          setLaunching(false);
        }
        if (res.done) break;
        await new Promise((resolve) => setTimeout(resolve, POLL_MS));
      }
    } catch {
      if (run === runRef.current) setError("Échec de la simulation.");
    } finally {
      if (run === runRef.current) setLaunching(false);
    }
  }

  if (!playback.trace) {
    return (
      <MatchSetup
        clubs={clubs}
        home={home}
        away={away}
        onHome={setHome}
        onAway={setAway}
        error={error}
        launching={launching}
        progress={computed > 0 ? Math.floor((computed * 100) / START_BUFFER_TICKS) : null}
        onLaunch={handleLaunch}
        onBack={() => navigate("/")}
      />
    );
  }

  return (
    <MatchScreen
      playback={playback}
      lineups={lineups}
      selected={selected}
      onSelect={setSelected}
      onBack={() => navigate("/")}
    />
  );
}
