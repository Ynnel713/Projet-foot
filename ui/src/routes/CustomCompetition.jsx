import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Shield, Globe2, Trophy, Layers, Swords, Check } from "lucide-react";
import { getPersoClubs, getNations, createCompetition } from "../api/client";
import { useGameStore } from "../store/useGameStore";
import { parseFlaggedName, flagUrl } from "../utils/flags";
import { starRating } from "../utils/stars";
import ClubLogo from "../components/common/ClubLogo";

const LEGS_LABELS = { 1: "Aller simple", 2: "Aller-retour", 4: "Double aller-retour" };
const LEAGUE_MIN = 2;
const LEAGUE_MAX = 50;
// Nombre d'équipes proposé pour "Championnat + élimination" -- multiples de
// 4 uniquement (poules de 4 minimum, voir groups.make_groups) pour arriver
// pile sur 8/16/32 qualifiés, sans poule incomplète.
const HYBRID_TEAM_OPTIONS = [
  { teams: 16, qualifiers: 8 },
  { teams: 32, qualifiers: 16 },
  { teams: 64, qualifiers: 32 },
];
const KNOCKOUT_TEAM_OPTIONS = [4, 8, 16, 32, 64, 128];

const FORMATS = [
  {
    id: "LEAGUE",
    icon: Trophy,
    title: "Championnat",
    description: "Tout le monde affronte tout le monde, classement à la fin. De 2 à 50 équipes.",
  },
  {
    id: "HYBRID",
    icon: Layers,
    title: "Championnat + élimination",
    description: "Poules de 4, façon Coupe du Monde, puis les qualifiés s'affrontent en élimination directe.",
  },
  {
    id: "KNOCKOUT",
    icon: Swords,
    title: "Élimination directe",
    description: "Un tableau à élimination directe pure, façon Coupe de France.",
  },
];

export default function CustomCompetition() {
  const navigate = useNavigate();
  const setActiveCompetition = useGameStore((s) => s.setActiveCompetition);

  // 1: type (clubs/sélections) -- 2: format -- 3: réglages -- 4: choix des équipes.
  const [step, setStep] = useState(1);
  const [entityType, setEntityType] = useState(null); // "club" | "nation"
  const [format, setFormat] = useState(null); // "LEAGUE" | "HYBRID" | "KNOCKOUT"
  const [teamCount, setTeamCount] = useState(LEAGUE_MIN);
  const [legs, setLegs] = useState(2); // championnat / phase de poules
  const [knockoutLegs, setKnockoutLegs] = useState(2);
  const [finalLegs, setFinalLegs] = useState(2);
  const [creating, setCreating] = useState(false);

  function goToFormat(type) {
    setEntityType(type);
    setStep(2);
  }

  function goToParams(f) {
    setFormat(f);
    if (f === "LEAGUE") setTeamCount(18);
    else if (f === "HYBRID") setTeamCount(HYBRID_TEAM_OPTIONS[0].teams);
    else setTeamCount(KNOCKOUT_TEAM_OPTIONS[1]); // 8
    setStep(3);
  }

  async function handleCreate(selected) {
    setCreating(true);
    try {
      const body = { source: "custom", club_names: selected, format };
      if (format === "LEAGUE") {
        body.legs = legs;
      } else if (format === "HYBRID") {
        body.legs = legs;
        body.knockout_legs = knockoutLegs;
        body.final_legs = finalLegs;
      } else {
        body.legs = knockoutLegs;
        body.knockout_legs = knockoutLegs;
        body.final_legs = finalLegs;
      }
      const status = await createCompetition(body);
      setActiveCompetition(status.id, status.championnat);
      const dest = format === "LEAGUE" ? "simulate" : format === "HYBRID" ? "groups" : "bracket";
      navigate(`/competition/${status.id}/${dest}`);
    } finally {
      setCreating(false);
    }
  }

  function back() {
    if (step === 1) navigate("/");
    else setStep((s) => s - 1);
  }

  return (
    <div className="flex flex-col h-full">
      <WizardHeader step={step} onBack={back} />
      <div className="flex-1 min-h-0">
        {step === 1 && <StepType onSelect={goToFormat} />}
        {step === 2 && <StepFormat onSelect={goToParams} />}
        {step === 3 && (
          <StepParams
            format={format}
            teamCount={teamCount}
            setTeamCount={setTeamCount}
            legs={legs}
            setLegs={setLegs}
            knockoutLegs={knockoutLegs}
            setKnockoutLegs={setKnockoutLegs}
            finalLegs={finalLegs}
            setFinalLegs={setFinalLegs}
            onNext={() => setStep(4)}
          />
        )}
        {step === 4 && (
          <StepTeams entityType={entityType} teamCount={teamCount} creating={creating} onCreate={handleCreate} />
        )}
      </div>
    </div>
  );
}

const STEP_LABELS = ["Type", "Format", "Réglages", "Équipes"];

function WizardHeader({ step, onBack }) {
  return (
    <div className="shrink-0 px-4 pt-4 pb-3 border-b border-white/5">
      <button onClick={onBack} className="flex items-center gap-1 text-xs text-gray-400 mb-3">
        <ArrowLeft size={14} /> {step === 1 ? "Accueil" : "Retour"}
      </button>
      <div className="flex items-center gap-2">
        {STEP_LABELS.map((label, i) => {
          const n = i + 1;
          const done = n < step;
          const active = n === step;
          return (
            <div key={label} className="flex items-center gap-2 flex-1">
              <div
                className={`h-6 w-6 shrink-0 rounded-full flex items-center justify-center text-[11px] font-bold border ${
                  active
                    ? "bg-accent border-accent text-white"
                    : done
                      ? "bg-accent/20 border-accent/50 text-accent"
                      : "bg-surface border-white/10 text-gray-500"
                }`}
              >
                {done ? <Check size={12} /> : n}
              </div>
              <span className={`text-[11px] font-medium hidden sm:inline ${active ? "text-white" : "text-gray-500"}`}>
                {label}
              </span>
              {n < STEP_LABELS.length && <div className={`h-px flex-1 ${done ? "bg-accent/50" : "bg-white/10"}`} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function BigChoice({ icon: Icon, title, description, onClick }) {
  return (
    <button
      onClick={onClick}
      className="rounded-2xl p-5 flex flex-col items-start gap-2 text-left bg-surface border border-white/10
                 hover:bg-white/[0.04] hover:border-accent/50 transition-colors min-h-[140px]"
    >
      <Icon size={26} className="text-accent" />
      <h3 className="font-semibold text-sm text-white">{title}</h3>
      <p className="text-[13px] leading-snug text-[#9AA9C3]">{description}</p>
    </button>
  );
}

function StepType({ onSelect }) {
  return (
    <div className="p-4 sm:p-6 max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-white mb-1">Clubs ou sélections ?</h1>
      <p className="text-[13px] text-[#9AA9C3] mb-5">Le vivier de la compétition sera composé uniquement de l'un ou de l'autre.</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <BigChoice
          icon={Shield}
          title="Clubs"
          description="Tous les clubs des 8 championnats européens, plus les clubs hors championnat."
          onClick={() => onSelect("club")}
        />
        <BigChoice
          icon={Globe2}
          title="Sélections"
          description="Les équipes nationales complètes, groupées par confédération."
          onClick={() => onSelect("nation")}
        />
      </div>
    </div>
  );
}

function StepFormat({ onSelect }) {
  return (
    <div className="p-4 sm:p-6 max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-white mb-1">Quel format ?</h1>
      <p className="text-[13px] text-[#9AA9C3] mb-5">Le format choisit aussi comment les équipes seront départagées.</p>
      <div className="grid grid-cols-1 gap-3">
        {FORMATS.map((f) => (
          <BigChoice key={f.id} icon={f.icon} title={f.title} description={f.description} onClick={() => onSelect(f.id)} />
        ))}
      </div>
    </div>
  );
}

function LegsPicker({ label, value, onChange }) {
  return (
    <div>
      <label className="text-xs text-gray-400">{label}</label>
      <div className="grid grid-cols-3 gap-1.5 mt-1.5">
        {Object.entries(LEGS_LABELS).map(([v, l]) => (
          <button
            key={v}
            onClick={() => onChange(Number(v))}
            className={`h-11 rounded-lg text-[12px] font-medium border transition-colors px-1 ${
              value === Number(v) ? "bg-accent border-accent text-white" : "bg-surface border-white/10 text-gray-300"
            }`}
          >
            {l}
          </button>
        ))}
      </div>
    </div>
  );
}

function StepParams({
  format,
  teamCount,
  setTeamCount,
  legs,
  setLegs,
  knockoutLegs,
  setKnockoutLegs,
  finalLegs,
  setFinalLegs,
  onNext,
}) {
  return (
    <div className="p-4 sm:p-6 max-w-2xl mx-auto flex flex-col gap-5">
      <div>
        <h1 className="text-xl font-bold text-white mb-1">Réglages</h1>
        <p className="text-[13px] text-[#9AA9C3]">
          {format === "LEAGUE" && "Nombre d'équipes et format des confrontations."}
          {format === "HYBRID" && "Nombre d'équipes (poules de 4) et confrontations de chaque phase."}
          {format === "KNOCKOUT" && "Nombre d'équipes et confrontations du tableau."}
        </p>
      </div>

      {format === "LEAGUE" && (
        <>
          <div>
            <label className="text-xs text-gray-400">Nombre d'équipes</label>
            <div className="flex items-center gap-3 mt-1.5">
              <input
                type="range"
                min={LEAGUE_MIN}
                max={LEAGUE_MAX}
                step={1}
                value={teamCount}
                onChange={(e) => setTeamCount(Number(e.target.value))}
                className="flex-1 accent-accent"
              />
              <span className="w-8 text-right font-semibold tabular-nums text-white">{teamCount}</span>
            </div>
          </div>
          <LegsPicker label="Confrontations" value={legs} onChange={setLegs} />
        </>
      )}

      {format === "HYBRID" && (
        <>
          <div>
            <label className="text-xs text-gray-400">Nombre d'équipes</label>
            <div className="grid grid-cols-3 gap-1.5 mt-1.5">
              {HYBRID_TEAM_OPTIONS.map((o) => (
                <button
                  key={o.teams}
                  onClick={() => setTeamCount(o.teams)}
                  className={`h-14 rounded-lg text-xs font-medium border transition-colors flex flex-col items-center justify-center gap-0.5 ${
                    teamCount === o.teams ? "bg-accent border-accent text-white" : "bg-surface border-white/10 text-gray-300"
                  }`}
                >
                  <span className="font-bold text-sm">{o.teams}</span>
                  <span className="text-[10px] opacity-80">{o.qualifiers} qualifiés</span>
                </button>
              ))}
            </div>
          </div>
          <LegsPicker label="Phase de championnat (poules)" value={legs} onChange={setLegs} />
          <LegsPicker label="Phase d'élimination" value={knockoutLegs} onChange={setKnockoutLegs} />
          <LegsPicker label="Finale" value={finalLegs} onChange={setFinalLegs} />
        </>
      )}

      {format === "KNOCKOUT" && (
        <>
          <div>
            <label className="text-xs text-gray-400">Nombre d'équipes</label>
            <div className="grid grid-cols-3 gap-1.5 mt-1.5">
              {KNOCKOUT_TEAM_OPTIONS.map((n) => (
                <button
                  key={n}
                  onClick={() => setTeamCount(n)}
                  className={`h-11 rounded-lg text-sm font-semibold border transition-colors ${
                    teamCount === n ? "bg-accent border-accent text-white" : "bg-surface border-white/10 text-gray-300"
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
          <LegsPicker label="Confrontations du tableau" value={knockoutLegs} onChange={setKnockoutLegs} />
          <LegsPicker label="Finale" value={finalLegs} onChange={setFinalLegs} />
        </>
      )}

      <button
        onClick={onNext}
        className="mt-2 h-12 rounded-xl bg-accent text-white font-semibold active:scale-[0.98] transition-transform"
      >
        Choisir les équipes →
      </button>
    </div>
  );
}

function StepTeams({ entityType, teamCount, creating, onCreate }) {
  const [pool, setPool] = useState(null);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("Toutes");
  const [selected, setSelected] = useState([]);

  useEffect(() => {
    setPool(null);
    setError(null);
    const load = entityType === "club" ? getPersoClubs() : getNations();
    load
      .then((rows) => {
        const mapped =
          entityType === "club"
            ? rows.map((c) => ({ name: c.name, category: c.championnat, strength: c.strength }))
            : rows.map((n) => ({ name: n.name, category: n.confederation, strength: n.strength }));
        setPool(mapped.sort((a, b) => b.strength - a.strength));
      })
      // Sans ce catch, un échec réseau/API laissait `pool` bloqué sur
      // "Chargement…" indéfiniment, sans jamais dire à l'utilisateur que ça a
      // échoué (retour terrain du 28/09/2026, "écran noir" sur Championnats
      // nationaux -- même risque ici).
      .catch(() => setError("Impossible de charger la liste. Réessaie dans un instant."));
  }, [entityType]);

  const categories = useMemo(() => {
    if (!pool) return [];
    return ["Toutes", ...new Set(pool.map((c) => c.category))];
  }, [pool]);

  const filtered = useMemo(() => {
    if (!pool) return [];
    return pool.filter(
      (c) => (categoryFilter === "Toutes" || c.category === categoryFilter) && c.name.toLowerCase().includes(search.toLowerCase()),
    );
  }, [pool, categoryFilter, search]);

  const allStrengths = useMemo(() => (pool ? pool.map((c) => c.strength) : []), [pool]);

  function toggle(name) {
    setSelected((prev) => (prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]));
  }

  const canCreate = selected.length === teamCount;

  return (
    <div className="flex flex-col h-full p-4 sm:p-6 gap-2 max-w-3xl mx-auto">
      <div className="flex items-center justify-between shrink-0">
        <h1 className="text-lg font-bold text-white">
          {entityType === "club" ? "Choisis tes clubs" : "Choisis tes sélections"}
        </h1>
        <span
          className={`text-sm font-semibold tabular-nums ${canCreate ? "text-accent" : "text-gray-400"}`}
        >
          {selected.length} / {teamCount}
        </span>
      </div>

      <input
        type="text"
        placeholder={entityType === "club" ? "Rechercher un club…" : "Rechercher une sélection…"}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="h-10 shrink-0 rounded-lg bg-surface border border-white/10 px-3 text-sm outline-none focus:border-accent"
      />

      {categories.length > 0 && (
        <div className="flex gap-1.5 overflow-x-auto shrink-0 pb-1">
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => setCategoryFilter(c)}
              className={`h-8 px-3 rounded-full text-xs font-medium whitespace-nowrap border ${
                categoryFilter === c ? "bg-accent border-accent text-white" : "bg-surface border-white/10 text-gray-300"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      )}

      {/* min-h-0 : indispensable pour qu'un enfant flex-1 overflow-y-auto se
          limite réellement à l'espace restant au lieu de pousser tout le
          parent à s'agrandir (voir AppShell pour le même besoin). */}
      <div className="flex-1 min-h-0 overflow-y-auto grid grid-cols-2 sm:grid-cols-3 gap-1.5 content-start">
        {!pool && !error && <p className="text-sm text-gray-400 col-span-full">Chargement…</p>}
        {error && <p className="text-sm text-red-400 col-span-full">{error}</p>}
        {pool &&
          filtered.map((c) => {
            const isSelected = selected.includes(c.name);
            const { code, label } = parseFlaggedName(c.name);
            return (
              <button
                key={c.name}
                onClick={() => toggle(c.name)}
                disabled={!isSelected && selected.length >= teamCount}
                className={`flex flex-col gap-0.5 px-3 py-2 rounded-lg text-sm min-h-[52px] text-left ${
                  isSelected ? "bg-accent/20 border border-accent/50" : "bg-surface border border-transparent"
                } disabled:opacity-30`}
              >
                <div className="flex items-center gap-2">
                  {code && <img src={flagUrl(code)} alt="" className="h-4 w-6 rounded-sm object-cover shrink-0" />}
                  {entityType === "club" && <ClubLogo clubName={c.name} size={18} />}
                  <span className="flex-1 min-w-0 truncate">{label}</span>
                </div>
                <div className="flex items-center justify-between text-[10px] text-gray-500">
                  <span className="truncate">{c.category}</span>
                  <span className="text-gold shrink-0 pl-2">{starRating(c.strength, allStrengths)}</span>
                </div>
              </button>
            );
          })}
      </div>

      <button
        onClick={() => onCreate(selected)}
        disabled={!canCreate || creating}
        className="shrink-0 h-12 rounded-xl bg-accent text-white font-semibold disabled:opacity-30 active:scale-[0.98] transition-transform"
      >
        {creating ? "Création…" : "Créer et lancer"}
      </button>
    </div>
  );
}
