import { useEffect, useMemo, useRef, useState } from "react";
import { BASE_URL, getMatchAnimation } from "../../api/client";
import {
  CANVAS_SOURCE,
  PROTOCOL_VERSION,
  buildAnimationPayload,
  canvasSrc,
  initMessage,
  unavailableMessage,
} from "../../utils/matchAnimation";

// Délai max entre le MONTAGE de l'iframe (donc APRÈS l'arrivée du payload) et son message `ready` : sinon lecteur injoignable (ex. API/URL
// erronée). Le chronomètre démarre dans l'effet du handshake, qui n'existe qu'une fois le payload reçu -- il ne compte JAMAIS la durée de
// l'appel API (13,6 s mesurées pour 22 clips), donc ne peut pas se déclencher pendant la génération de l'animation. Voir docs §2.11.
const HANDSHAKE_TIMEOUT_MS = 10000;

// Indicateur de chargement : pastille qui tourne + message. Utilisé pendant l'appel API (génération côté serveur) ET entre le montage de
// l'iframe et le premier frame du lecteur : le retour visuel n'est jamais interrompu entre le clic et le premier `clipchange`.
function LoadingNotice({ message, detail, testId }) {
  return (
    <div role="status" aria-live="polite" data-testid={testId} className="flex items-center gap-3 p-4 text-sm text-gray-300">
      <span aria-hidden="true" className="inline-block h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-white/20 border-t-accent" />
      <span className="flex flex-col">
        <span>{message}</span>
        {detail && <span className="text-[11px] text-gray-500 tabular-nums">{detail}</span>}
      </span>
    </div>
  );
}

// Animation d'un match dans une iframe `render/canvas.html` (docs/canvas_integration_state.md §2.11, protocole v1).
// `matchParams` : mêmes paramètres que getPitchView ({ home, away, journee } | { home, away, group, matchday } |
// { home, away, round_number, leg }). Match sans compo persistée : message de la §2.10, AUCUNE iframe montée.
export default function MatchAnimation({ competitionId, matchParams }) {
  const [state, setState] = useState({ status: "loading" }); // loading | unavailable{reason} | ready{payload}
  const [clip, setClip] = useState(null); // { index, total, minute } -- dernier `clipchange`
  const [ended, setEnded] = useState(false);
  const [failure, setFailure] = useState(null); // code d'erreur remonté par l'iframe / handshake
  const [elapsedS, setElapsedS] = useState(0); // secondes écoulées depuis l'ouverture, affichées pendant la génération
  const iframeRef = useRef(null);

  const paramsKey = JSON.stringify(matchParams);
  useEffect(() => {
    let cancelled = false;
    // Pas de remise à zéro de l'état ici : un autre match = un autre composant (le parent fournit `key={paramsKey}`).
    getMatchAnimation(competitionId, JSON.parse(paramsKey))
      .then((response) => {
        if (cancelled) return;
        const built = buildAnimationPayload(response);
        setState(built.available ? { status: "ready", payload: built.payload } : { status: "unavailable", reason: built.reason });
      })
      .catch(() => {
        if (!cancelled) setState({ status: "unavailable", reason: "load_error" });
      });
    return () => {
      cancelled = true;
    };
  }, [competitionId, paramsKey]);

  // Compteur visible tant que le payload n'est pas arrivé (feedback pendant les 7 à 14 s de génération côté serveur).
  const isLoading = state.status === "loading";
  useEffect(() => {
    if (!isLoading) return undefined;
    const startedAt = Date.now();
    const timer = setInterval(() => setElapsedS(Math.floor((Date.now() - startedAt) / 1000)), 500);
    return () => clearInterval(timer);
  }, [isLoading]);

  const src = useMemo(() => canvasSrc(BASE_URL, window.location.origin), []);
  const payload = state.status === "ready" ? state.payload : null;

  // Handshake + écoute des messages : seulement quand le payload existe (donc quand l'iframe est montée).
  useEffect(() => {
    if (!payload) return undefined;
    const iframeOrigin = new URL(src, window.location.href).origin;
    let initSent = false;
    let ready = false;

    function onMessage(event) {
      const frame = iframeRef.current;
      if (!frame || event.source !== frame.contentWindow || event.origin !== iframeOrigin) return;
      const msg = event.data;
      if (!msg || msg.source !== CANVAS_SOURCE) return;
      if (msg.version !== PROTOCOL_VERSION) {
        setFailure("version_mismatch");
        return;
      }
      switch (msg.type) {
        case "ready":
          ready = true;
          if (!initSent) {
            initSent = true;
            frame.contentWindow.postMessage(initMessage(payload), iframeOrigin);
          }
          break;
        case "clipchange":
          setEnded(false);
          setClip({ index: msg.index, total: msg.total, minute: msg.minute });
          break;
        case "ended":
          setEnded(true);
          break;
        case "error":
          setFailure(msg.code ?? "render_error");
          break;
        default:
          break; // tout autre message est ignoré (protocole fermé : 4 types sortants seulement)
      }
    }

    window.addEventListener("message", onMessage);
    const timer = setTimeout(() => {
      if (!ready) setFailure("no_handshake");
    }, HANDSHAKE_TIMEOUT_MS);
    return () => {
      window.removeEventListener("message", onMessage); // l'iframe, elle, est démontée avec ce composant
      clearTimeout(timer);
    };
  }, [payload, src]);

  if (state.status === "loading") {
    return (
      <LoadingNotice
        testId="animation-loading"
        message="Calcul des temps forts du match en cours…"
        detail={`${elapsedS} s — cela peut durer une quinzaine de secondes pour un match riche en occasions.`}
      />
    );
  }
  if (state.status === "unavailable") {
    // Aucune iframe montée : le lecteur n'est jamais chargé pour un match non animable.
    return (
      <p role="status" data-testid="animation-unavailable" data-reason={state.reason} className="text-sm text-gray-300 p-4">
        {unavailableMessage(state.reason)}
      </p>
    );
  }

  const failureMessage =
    failure === "no_handshake"
      ? unavailableMessage("no_handshake")
      : failure === "version_mismatch"
        ? unavailableMessage("protocol_version_mismatch")
        : failure
          ? `Erreur d'affichage de l'animation (${failure}).`
          : null;

  return (
    <div className="flex flex-col gap-2 w-full" data-testid="animation-ready">
      {failureMessage && (
        <p role="alert" className="text-sm text-red-400 px-1">
          {failureMessage}
        </p>
      )}
      <div className="relative">
        <iframe
          ref={iframeRef}
          src={src}
          title={`Animation ${state.payload.match.home} - ${state.payload.match.away}`}
          // Pas d'allow-top-navigation : l'iframe ne peut déclencher aucune navigation de la PWA. allow-same-origin est
          // nécessaire pour que event.origin soit l'origine réelle de l'iframe (sinon "null") et valider le handshake.
          sandbox="allow-scripts allow-same-origin"
          className="w-full rounded-lg bg-black"
          style={{ height: "min(80vh, 780px)", border: 0 }}
        />
        {!clip && !failureMessage && (
          <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-black">
            <LoadingNotice testId="animation-player-loading" message="Chargement du lecteur…" />
          </div>
        )}
      </div>
      <p className="text-[11px] text-gray-500 px-1 tabular-nums" data-testid="animation-status">
        {clip ? `Temps fort ${clip.index + 1}/${clip.total} · ${clip.minute}'` : "Chargement du lecteur…"}
        {ended ? " · fin des temps forts" : ""}
      </p>
    </div>
  );
}
