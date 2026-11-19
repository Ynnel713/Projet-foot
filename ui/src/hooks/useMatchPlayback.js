import { useCallback, useEffect, useRef, useState } from "react";

// Boucle de lecture de l'écran V2 (ticket v2-ecran-match/01 : déplacée telle quelle depuis routes/V2Match.jsx).
// Vitesses en multiples du TEMPS RÉEL (demande du propriétaire, 03/11/2026) : x1 par défaut ; liste x1, x1,5, x2,
// x8, x32 (décision du propriétaire du 19/11/2026, ticket v2-ecran-match/09 : x4 retiré, x32 ajouté). Entre deux
// positions enregistrées (~1 s de match d'écart, voir api/routers/v2.py), joueurs et ballon glissent en ligne droite
// au lieu de sauter (voir `interpolatedTick`).
export const SPEED_OPTIONS = [1, 1.5, 2, 8, 32];
const DEFAULT_SPEED = 1;
// Ralenti de chaque but : une fois le but vu (et REPLAY_AFTER_S de plus), on revient REPLAY_BEFORE_S avant et on
// rejoue l'action à REPLAY_SPEED, puis la lecture reprend là où elle était.
const REPLAY_BEFORE_S = 8;
const REPLAY_AFTER_S = 2;
const REPLAY_SPEED = 0.4;
const HALF_TIME_BANNER_MS = 3000; // bandeau « MI-TEMPS », en temps réel quelle que soit la vitesse (ticket 07)
// Bandeaux de but et de coup d'envoi (ticket v2-ecran-match/13, décision du propriétaire du 19/11/2026) : 2 s réelles
// quelle que soit la vitesse ; ils ne bloquent pas la lecture (contrairement au bandeau de mi-temps).
const EVENT_BANNER_MS = 2000;

export default function useMatchPlayback() {
  const [trace, setTrace] = useState(null);
  const [seconds, setSeconds] = useState(0); // temps de match lu (s)
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(DEFAULT_SPEED);
  const [replaying, setReplaying] = useState(false);
  const secondsRef = useRef(0);
  const [seen, setSeen] = useState(0); // instant le plus avancé déjà vu : le score ne recule pas pendant un ralenti
  const replayRef = useRef(null); // { end } : instant où le ralenti en cours s'arrête
  const replayedRef = useRef(0); // buts déjà rejoués au ralenti
  const [halfBanner, setHalfBanner] = useState(false);
  const halfRef = useRef({ shown: false, until: 0 }); // bandeau de mi-temps : déjà montré, fin (horloge réelle)
  const [goalBanner, setGoalBanner] = useState(null); // indice du but annoncé (bandeau de but), ou null
  const [kickoffBanner, setKickoffBanner] = useState(false);
  const bannersRef = useRef({ announced: 0, goalUntil: 0, kickoffUntil: 0 }); // buts déjà annoncés, fins (horloge réelle)
  const traceRef = useRef(null); // dernière trace reçue, lue par la boucle de lecture sans la relancer à chaque lecture

  useEffect(() => {
    if (!playing || !traceRef.current) return undefined;
    let frame;
    let previous = performance.now();
    const loop = (now) => {
      const elapsed = (now - previous) / 1000;
      previous = now;
      const live = traceRef.current;
      const end = (live.ticks.length - 1) * live.tick_seconds;
      const replay = replayRef.current;
      let next = Math.min(end, secondsRef.current + elapsed * (replay ? REPLAY_SPEED : speed));
      const half = halfRef.current;
      const halfS = live.second_half_start_minute != null ? live.second_half_start_minute * 60 : null;
      if (half.until) {
        next = secondsRef.current; // bandeau en cours : le match attend
        if (now >= half.until) {
          half.until = 0;
          setHalfBanner(false);
        }
      } else if (!half.shown && !replay && halfS != null && next >= halfS) {
        half.shown = true;
        half.until = now + HALF_TIME_BANNER_MS;
        setHalfBanner(true);
        next = halfS;
      } else if (replay && next >= replay.end) {
        replayRef.current = null;
        setReplaying(false);
      } else if (!replay) {
        const goal = live.goals[replayedRef.current];
        if (goal && next >= goal.minute * 60 + REPLAY_AFTER_S) {
          replayedRef.current += 1;
          replayRef.current = { end: next };
          setReplaying(true);
          next = Math.max(0, goal.minute * 60 - REPLAY_BEFORE_S);
        }
      }
      // bandeaux de but et de coup d'envoi : n'influent pas sur `next` (lecture inchangée)
      const banners = bannersRef.current;
      if (banners.kickoffUntil === -1) banners.kickoffUntil = now + EVENT_BANNER_MS; // compté dès la 1re image jouée
      if (banners.kickoffUntil > 0 && now >= banners.kickoffUntil) {
        banners.kickoffUntil = 0;
        setKickoffBanner(false);
      }
      const announce = live.goals[banners.announced];
      if (announce && next >= announce.minute * 60) {
        setGoalBanner(banners.announced);
        banners.announced += 1;
        banners.goalUntil = now + EVENT_BANNER_MS;
      } else if (banners.goalUntil && now >= banners.goalUntil) {
        banners.goalUntil = 0;
        setGoalBanner(null);
      }
      secondsRef.current = next;
      setSeen((s) => Math.max(s, next));
      setSeconds(next);
      // fin de la lecture seulement si le calcul est fini ; sinon on attend les images suivantes
      if (next >= end && live.done && !replayRef.current) setPlaying(false);
      frame = requestAnimationFrame(loop);
    };
    frame = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frame);
  }, [playing, speed, trace]);

  // Nouvelle trace reçue pendant le calcul : lue par la boucle ; affichée seulement si `show` (lecture démarrée).
  const receive = useCallback((live, show) => {
    traceRef.current = live;
    if (show) setTrace(live);
  }, []);

  // Démarre la lecture de `live` à `start` secondes : les buts et la mi-temps d'avant `start` sont réputés déjà vus
  // (pas de ralenti ni de bandeau rétroactifs).
  const begin = useCallback((live, start, play) => {
    const halfS = live.second_half_start_minute != null ? live.second_half_start_minute * 60 : null;
    traceRef.current = live;
    setTrace(live);
    secondsRef.current = start;
    setSeen(start);
    setSeconds(start);
    replayRef.current = null;
    replayedRef.current = live.goals.filter((g) => g.minute * 60 + REPLAY_AFTER_S <= start).length;
    halfRef.current = { shown: halfS != null && start >= halfS, until: 0 };
    setHalfBanner(false);
    // buts d'avant `start` réputés annoncés ; coup d'envoi seulement pour une lecture qui part du début
    bannersRef.current = {
      announced: live.goals.filter((g) => g.minute * 60 <= start).length,
      goalUntil: 0,
      kickoffUntil: start === 0 ? -1 : 0,
    };
    setGoalBanner(null);
    setKickoffBanner(start === 0);
    setReplaying(false);
    setPlaying(play);
  }, []);

  // Bouton « RALENTI ⏭ » : reprend là où la lecture en était avant le ralenti.
  const skipReplay = useCallback(() => {
    secondsRef.current = replayRef.current?.end ?? secondsRef.current;
    replayRef.current = null;
    setReplaying(false);
  }, []);

  return {
    trace,
    seconds,
    seen,
    playing,
    setPlaying,
    speed,
    setSpeed,
    replaying,
    halfBanner,
    goalBanner,
    kickoffBanner,
    receive,
    begin,
    skipReplay,
  };
}
