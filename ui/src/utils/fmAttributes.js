// Même table que players.FM_ATTRIBUTE_CATEGORIES côté Python -- ne pas
// laisser diverger (voir le commentaire de la source sur ce risque).
export const FM_ATTRIBUTE_CATEGORIES = {
  Technique: ["Crossing", "Dribbling", "Finishing", "First Touch", "Heading", "Long Shots", "Marking", "Passing", "Tackling", "Technique"],
  Gardien: ["Aerial Reach", "Command of Area", "Communication", "Eccentricity", "Handling", "Kicking", "One on Ones", "Punching (Tendency)", "Reflexes", "Rushing Out (Tendency)", "Throwing"],
  Mental: ["Aggression", "Anticipation", "Bravery", "Composure", "Concentration", "Decisions", "Determination", "Flair", "Leadership", "Off the Ball", "Positioning", "Teamwork", "Vision", "Work Rate"],
  Physique: ["Acceleration", "Agility", "Balance", "Jumping Reach", "Natural Fitness", "Pace", "Stamina", "Strength"],
  "Coups de pied arrêtés": ["Corners", "Free Kick Taking", "Long Throws", "Penalty Taking"],
};

// Catégories dans l'ordre d'affichage pour ce joueur -- gardien en premier
// pour un gardien (retour terrain du 27/09/2026), sinon l'ordre habituel.
export function categoryOrder(poste) {
  const entries = Object.entries(FM_ATTRIBUTE_CATEGORIES);
  if (poste !== "GK") return entries;
  return [...entries].sort((a, b) => (a[0] === "Gardien" ? -1 : b[0] === "Gardien" ? 1 : 0));
}

// [{ category, rows: [{name, value}] }] -- catégories sans aucun attribut
// connu pour ce joueur omises. Utilisé pour la liste des attributs (barres
// retirées le 28/09/2026, voir PlayerProfile) -- reste sur les catégories
// FM_ATTRIBUTE_CATEGORIES d'origine, contrairement au radar (voir
// RADAR_CATEGORIES ci-dessous, un découpage différent, propre au radar).
export function attributesByCategory(attributes, poste) {
  return categoryOrder(poste)
    .map(([category, names]) => ({
      category,
      rows: names.filter((name) => name in attributes).map((name) => ({ name, value: attributes[name] })),
    }))
    .filter((c) => c.rows.length > 0);
}

// Découpage du radar (28/09/2026, retour terrain) -- distinct de
// FM_ATTRIBUTE_CATEGORIES ci-dessus (qui reste utilisé pour la liste des
// attributs à gauche) : Marking/Tackling passent en Défense malgré leur
// catégorie FM "Technique", Concentration/Positioning/Anticipation/Bravery
// en Défense malgré "Mental", etc. -- regroupement par fonction plutôt que
// par la taxonomie FM. Chaque élément est un nom d'attribut, ou un
// sous-groupe (tableau de noms) moyenné d'abord entre eux puis compté comme
// un seul élément dans la moyenne de l'axe -- pour que Corners et Free Kick
// Taking (très corrélés, rarement les deux travaillés à égalité) ne pèsent
// pas deux fois plus que les autres compétences techniques (retour terrain
// du 28/09/2026). Long Throws exclu de l'axe Technique (trop marginal, faussait
// la moyenne pour la plupart des postes) ; Stamina rejoint Puissance (lu comme
// de l'endurance physique plutôt que de la vivacité).
const RADAR_CATEGORIES = {
  Technique: ["Dribbling", "First Touch", "Passing", "Technique", ["Corners", "Free Kick Taking"], "Penalty Taking"],
  Attaque: ["Crossing", "Finishing", "Heading", "Long Shots", "Flair", "Off the Ball"],
  Défense: ["Marking", "Tackling", "Anticipation", "Bravery", "Concentration", "Positioning"],
  "QI foot": ["Composure", "Decisions", "Teamwork", "Vision"],
  Combativité: ["Aggression", "Determination", "Leadership", "Work Rate"],
  Puissance: ["Balance", "Jumping Reach", "Strength", "Stamina"],
  Vivacité: ["Acceleration", "Agility", "Natural Fitness", "Pace"],
};

// Radar propre aux gardiens (28/09/2026, retour terrain) -- les 7 axes
// outfield ci-dessus (Attaque, Défense...) ne veulent rien dire pour un
// gardien ; celui-ci reprend les attributs Gardien (FM_ATTRIBUTE_CATEGORIES)
// regroupés par fonction (arrêt, jeu aérien, relance, communication), plus
// les axes mentaux/physiques déjà pertinents pour un gardien. Les
// "tendances" (Punching/Rushing Out (Tendency)) sont volontairement
// exclues : ce sont des propensions comportementales, pas des notes de
// niveau -- les moyenner avec de vraies compétences fausserait l'axe.
const GARDIEN_RADAR_CATEGORIES = {
  Réflexes: ["Reflexes", "One on Ones", "Handling"],
  "Jeu aérien": ["Aerial Reach", "Command of Area"],
  Relance: ["Kicking", "Throwing", "Passing"],
  Communication: ["Communication", "Leadership"],
  "QI foot": RADAR_CATEGORIES["QI foot"],
  Combativité: ["Aggression", "Determination", "Work Rate", "Bravery"],
  Puissance: RADAR_CATEGORIES.Puissance,
  Vivacité: RADAR_CATEGORIES.Vivacité,
};

// Valeur (0-99) d'un élément d'axe pour ce joueur, et les attributs connus
// qui la composent -- un élément est soit un nom d'attribut, soit un
// sous-groupe (tableau de noms) moyenné d'abord. Retourne null si aucun des
// attributs de l'élément n'est connu pour ce joueur.
function radarItemValue(item, attributes) {
  const names = Array.isArray(item) ? item : [item];
  const known = names.filter((n) => n in attributes);
  if (!known.length) return null;
  const value = known.reduce((sum, n) => sum + attributes[n], 0) / known.length;
  return { value, names: known };
}

// [{ name, value, names }] -- moyenne par axe, pour le radar (GARDIEN_RADAR_CATEGORIES
// pour un gardien, RADAR_CATEGORIES sinon). Axe omis si aucun de ses
// attributs n'est connu pour ce joueur. `names` (les attributs connus qui
// composent l'axe, sous-groupes aplatis) sert à surligner la colonne
// correspondante quand on clique un axe du radar (voir RadarChart / PlayerProfile).
export function radarCategories(attributes, poste) {
  const groups = poste === "GK" ? GARDIEN_RADAR_CATEGORIES : RADAR_CATEGORIES;
  return Object.entries(groups)
    .map(([name, items]) => {
      const results = items.map((item) => radarItemValue(item, attributes)).filter(Boolean);
      if (!results.length) return null;
      const value = results.reduce((sum, r) => sum + r.value, 0) / results.length;
      const names = results.flatMap((r) => r.names);
      return { name, value, names };
    })
    .filter(Boolean);
}
