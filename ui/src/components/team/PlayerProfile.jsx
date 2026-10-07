import { useState } from "react";
import { Wrench, Brain, Dumbbell, Target, Star, Sparkles } from "lucide-react";
import { BASE_URL } from "../../api/client";
import { fmTierColor } from "../../utils/fmTier";
import { attributesByCategory, radarCategories } from "../../utils/fmAttributes";
import { nationalityFlagUrl } from "../../utils/nationalityFlags";
import { posteCoordinates } from "../../utils/posteCoordinates";
import { posteLabel } from "../../utils/posteLabels";
import RadarChart from "./RadarChart";
import StarRating from "./StarRating";
import SectionPanel from "./SectionPanel";

const PIED_LABELS = { D: "Droit", G: "Gauche" };
const CATEGORY_ICONS = { Technique: Wrench, Gardien: Wrench, Mental: Brain, Physique: Dumbbell, "Coups de pied arrêtés": Target };

// Équivalent PWA de app._render_player_profile_card (Streamlit), redessiné
// le 28/09/2026 puis resserré sur la maquette le même jour (retour "encore
// très éloigné visuellement") : en-tête à l'échelle d'un écran joueur (photo,
// nom et badge de note bien plus grands), colonnes d'attributs à plat --
// sans encadré, comme sur la maquette -- seuls le radar et le mini-terrain
// gardent un panneau bordé. Pas de section "Carrière" ni de texte de
// scouting narratif comme sur la maquette -- aucune donnée d'historique de
// transferts dans data/joueurs.xlsx, et un texte généré inventerait un
// contenu non vérifiable ; à construire séparément si une source de données
// existe pour ça.
export default function PlayerProfile({ player }) {
  const tags = [`${player.age} ans`, player.postes_fm || player.poste];
  if (player.taille_fm != null) tags.push(`${player.taille_fm} cm`);

  const pied = PIED_LABELS[player.pied] ?? "";
  const flagUrl = nationalityFlagUrl(player.nationalite);

  return (
    <div className="rounded-2xl bg-surface border border-white/10 p-5 sm:p-7 flex flex-col gap-6">
      <div className="flex items-start gap-5 flex-wrap">
        {player.photo_url ? (
          <img
            src={`${BASE_URL}${player.photo_url}`}
            alt=""
            className="w-28 h-28 rounded-2xl object-cover border border-white/10 shrink-0"
          />
        ) : (
          <div className="w-28 h-28 rounded-2xl flex items-center justify-center bg-white/[0.06] text-white/35 text-4xl shrink-0">
            ?
          </div>
        )}

        <div className="flex-1 min-w-[220px] pt-1">
          <div className="flex items-center gap-2">
            {flagUrl && <img src={flagUrl} alt={player.nationalite} className="h-4 rounded-sm shrink-0" />}
            <span className="text-sm text-gray-400">{player.nationalite}</span>
          </div>
          <div className="font-extrabold text-3xl text-white leading-tight mt-1">{player.name}</div>
          {pied && (
            <div className="flex items-center gap-2 mt-1.5">
              <span className="text-[13px] text-gray-400">Pied {pied.toLowerCase()}</span>
              {player.weak_foot != null && <StarRating value={player.weak_foot} size={14} />}
            </div>
          )}
          <div className="flex flex-wrap gap-1.5 mt-3">
            {tags.filter(Boolean).map((t) => (
              <span key={t} className="text-[12px] font-semibold px-2.5 py-1 rounded-full bg-white/[0.07] border border-white/10 text-white/85">
                {t}
              </span>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3 pt-1">
          <MiniPitchLandscape poste={player.poste} secondaryPostes={player.poste_secondaire} width={96} height={76} />
          <div className="text-[12px] text-white/80 max-w-[180px] flex flex-col gap-2.5">
            <div>
              <div className="text-white/55 font-bold uppercase tracking-wide mb-0.5">Poste(s) préféré(s)</div>
              <div className="text-white font-semibold">{posteLabel(player.poste)}</div>
              {player.poste_secondaire?.length > 0 && (
                <div className="text-white/60">{player.poste_secondaire.map(posteLabel).join(" / ")}</div>
              )}
            </div>
            {player.attributes && <PointsForts player={player} />}
          </div>
        </div>

        <div
          className="w-24 h-24 rounded-2xl flex flex-col items-center justify-center shrink-0"
          style={{ backgroundColor: fmTierColor(player.note) }}
        >
          <div className="font-extrabold text-5xl text-white leading-none">{player.note.toFixed(0)}</div>
          <div className="text-[10px] font-bold uppercase tracking-wide text-white/85 mt-1">Note</div>
        </div>
      </div>

      {player.preferred_moves && (
        <div className="text-[12.5px] text-white/75 -mt-3">
          <b className="text-white">Preferred moves :</b> {player.preferred_moves}
        </div>
      )}

      {player.attributes ? (
        <PlayerAttributesBody player={player} />
      ) : (
        <p className="text-[13px] italic text-white/45">
          Caractéristiques FM26 pas encore récupérées pour ce joueur.
        </p>
      )}
    </div>
  );
}

function PointsForts({ player }) {
  const best = Object.entries(player.attributes)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([name]) => name)
    .join(", ");

  return (
    <div>
      <div className="text-white/55 font-bold uppercase tracking-wide mb-0.5">Points forts</div>
      <div className="text-white/85">{best}</div>
    </div>
  );
}

// Petit terrain en paysage (but propre à gauche, but adverse à droite) --
// utilisé uniquement dans l'en-tête à côté de "Poste(s) préféré(s)". Seul
// terrain de la fiche joueur (28/09/2026 : le second, plus bas dans le
// panneau "Position sur le terrain", faisait doublon -- retiré). Affiche
// aussi les postes secondaires (`secondaryPostes`), en plus petit et dans
// une couleur neutre pour ne pas rivaliser visuellement avec le poste
// principal -- même traitement que l'ancien MiniPitch qu'il remplace.
function MiniPitchLandscape({ poste, secondaryPostes = [], width = 96, height = 76 }) {
  // x (latéral, voir posteCoordinates.js : 0=flanc gauche de l'équipe,
  // LB=14 ; 100=flanc droit, RB=86) -> cy SANS inversion : un terrain
  // vertical qui attaque vers le haut (MiniPitch, retiré le 28/09/2026)
  // pivoté à 90° pour attaquer vers la droite envoie son flanc GAUCHE en
  // HAUT et son flanc DROIT en BAS -- une inversion ici y mettait le
  // flanc droit en haut (retour terrain du 28/09/2026 : "le rond arrière
  // droit... à gauche" -- symptôme de cette inversion sur le petit terrain).
  const toScreen = (p) => {
    const { x, y } = posteCoordinates(p);
    return { cx: (y / 100) * width, cy: (x / 100) * height };
  };
  const main = toScreen(poste);
  const secondary = (secondaryPostes ?? []).filter((p) => p !== poste).map(toScreen);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} width={width} height={height} className="shrink-0">
      <rect x="1" y="1" width={width - 2} height={height - 2} rx="10" fill="#0d3320" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
      <line x1={width / 2} y1="1" x2={width / 2} y2={height - 1} stroke="rgba(255,255,255,0.18)" strokeWidth="1" />
      <circle cx={width / 2} cy={height / 2} r={height * 0.18} fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth="1" />
      <rect x="1" y={height * 0.22} width={width * 0.16} height={height * 0.56} fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth="1" />
      <rect x={width - 1 - width * 0.16} y={height * 0.22} width={width * 0.16} height={height * 0.56} fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth="1" />
      {secondary.map(({ cx, cy }, i) => (
        <circle key={i} cx={cx} cy={cy} r={height * 0.075} fill="rgba(230,230,235,0.35)" stroke="#0d3320" strokeWidth="1" />
      ))}
      <circle cx={main.cx} cy={main.cy} r={height * 0.11} fill="#3ddc70" stroke="#0d3320" strokeWidth="1.5" />
    </svg>
  );
}

// Colonne d'attributs "à plat" (icône + titre, liste nom/valeur) -- sans
// encadré ni fond, contrairement à SectionPanel : c'est ainsi que la
// maquette affiche Style de jeu / Technique / Mental / Physique / Coups de
// pied arrêtés (seuls le radar et le mini-terrain sont dans un panneau
// bordé sur la maquette).
function FlatCategory({ icon: Icon, title, children }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 mb-2">
        {Icon && <Icon size={14} className="text-white/45 shrink-0" />}
        <span className="text-[11px] font-bold uppercase tracking-wide text-white/55">{title}</span>
      </div>
      {children}
    </div>
  );
}

function AttributeRows({ rows, highlight }) {
  return (
    <div className="flex flex-col gap-[3px]">
      {rows.map(({ name, value }) => {
        const isHighlighted = highlight?.has(name);
        return (
          <div
            key={name}
            className={`flex justify-between gap-3 text-[13px] leading-[1.6] px-1.5 -mx-1.5 rounded transition-colors ${
              isHighlighted ? "bg-[#3ddc70]/15 text-white" : "text-white/85"
            }`}
          >
            <span className="truncate">{name}</span>
            <b style={{ color: fmTierColor(value) }} className="tabular-nums shrink-0">
              {value}
            </b>
          </div>
        );
      })}
    </div>
  );
}

function PlayerAttributesBody({ player }) {
  const categories = attributesByCategory(player.attributes, player.poste);
  const radar = radarCategories(player.attributes, player.poste);
  const byCategory = Object.fromEntries(categories.map((c) => [c.category, c]));

  // Répartition des 3 colonnes -- pour un gardien, Technique ne compte que
  // 2-3 lignes (First Touch/Passing/Technique) : la laisser seule dans la
  // colonne du milieu crée un grand vide sous elle pendant que Mental (14
  // lignes) est repoussé loin à droite (retour terrain du 28/09/2026). On
  // l'empile donc sous Gardien pour équilibrer, et Mental/Physique
  // remontent d'une colonne vers la gauche. Pour un joueur de champ,
  // Technique (~10 lignes) reste seule au milieu : déjà équilibré avec
  // Mental et Physique+Coups de pied.
  const isGoalkeeper = player.poste === "GK";
  const colA = isGoalkeeper ? [byCategory.Gardien, byCategory.Technique] : [byCategory.Technique];
  const colB = [byCategory.Mental];
  const colC = [byCategory.Physique, byCategory["Coups de pied arrêtés"]];

  // Nom de l'axe radar sélectionné (clic) -- ses attributs sont surlignés
  // dans les colonnes à plat ci-dessous (retour terrain du 28/09/2026).
  const [selectedAxis, setSelectedAxis] = useState(null);
  const highlight = selectedAxis
    ? new Set(radar.find((c) => c.name === selectedAxis)?.names ?? [])
    : null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-8">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 items-start">
        <div className="flex flex-col gap-6">
          {player.categorie && (
            <FlatCategory icon={Sparkles} title="Style de jeu">
              <div className="text-[13px] text-white/90">{player.categorie.replaceAll("_", " ")}</div>
            </FlatCategory>
          )}
          {colA.filter(Boolean).map(({ category, rows }) => (
            <FlatCategory key={category} icon={CATEGORY_ICONS[category]} title={category}>
              <AttributeRows rows={rows} highlight={highlight} />
            </FlatCategory>
          ))}
        </div>

        <div className="flex flex-col gap-6">
          {colB.filter(Boolean).map(({ category, rows }) => (
            <FlatCategory key={category} icon={CATEGORY_ICONS[category]} title={category}>
              <AttributeRows rows={rows} highlight={highlight} />
            </FlatCategory>
          ))}
        </div>

        <div className="flex flex-col gap-6">
          {colC.filter(Boolean).map(({ category, rows }) => (
            <FlatCategory key={category} icon={CATEGORY_ICONS[category]} title={category}>
              <AttributeRows rows={rows} highlight={highlight} />
            </FlatCategory>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-6">
        <SectionPanel icon={Star} title="Résumé des qualités">
          <div className="flex justify-center">
            <RadarChart categories={radar} size={340} selected={selectedAxis} onSelect={setSelectedAxis} />
          </div>
        </SectionPanel>
      </div>
    </div>
  );
}
