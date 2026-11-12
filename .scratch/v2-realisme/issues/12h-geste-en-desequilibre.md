# 12h: Qualité du geste en déséquilibre

**Chantier :** `v2-realisme` (revue du réalisme du 12/11/2026, demandée par le propriétaire). **Priorité :** P1 (le geste dépend de l'état du corps). **Catégorie :** physique.

**Constat vérifié (12/11/2026) :** la qualité d'un tir (`shooting.shot_error_sigma` : note, distance, pression), d'une passe (`possession.pass_difficulty` : distance, pression, receveur marqué) et d'un contrôle (`possession.control_difficulty` : vitesse du ballon, pression) ne dépend jamais de l'état du corps du joueur. Le 12c prévoit après un contact une perte de vitesse et un délai avant d'agir, mais aucun effet sur la qualité du geste ; les tickets 34c et 36b traitent l'élan vers le ballon, pas le déséquilibre.

**What to build :** Un joueur en déséquilibre exécute moins bien : juste après un contact perdu (12c), en reculant ou en pleine course de côté par rapport à la direction du geste (orientation, 07a), la difficulté du tir, de la passe et du contrôle augmente pendant une courte durée. Balance ne réduit que la part de la pénalité due au CONTACT (rayon de `docs/CARTE_ATTRIBUTS_V2.md` : continuer l'action après un contact ; même rayon qu'au 12c), sans double comptage avec Strength pendant le contact, ni avec Composure (part due à la pression). La part due à la course de côté ou à reculons ne dépend d'aucun attribut nouveau : l'orientation et le déplacement relèvent de 07a, 07b et Agility (07f) ; découpage à examiner avant le code (revue de l'expert du 12/11/2026).

**Hors de ce ticket :** élan et timing du tireur (`v2-collectif/34c`), passe en course (`v2-collectif/36b`), délai et perte de vitesse après le contact (12c), pied faible (`v2-attributs-restants/04a`).

**Attributs :** Balance (rayon de `docs/CARTE_ATTRIBUTS_V2.md` ; aucun rôle nouveau).

**Blocked by :** 12c (Balance : rester debout et continuer après un contact) ; 07a (Orientation du corps).

**Bloque :** 12g.

**Status :** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 30 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible (chiffres réels à trouver ; recouvrement avec 12c, 34c et 36b à délimiter). À examiner pour découpage avant le code. Temps machine, hors total : séries de 50 matchs, suite complète.

## Tests

- **Unitaires :** même tir, même passe, même contrôle, joueur équilibré contre juste après un contact, et à reculons contre de face : difficulté plus grande en déséquilibre
- **Comportementaux (scènes A/B) :** Balance 99 contre 11 après le même contact

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Effet du déséquilibre et de Balance mesuré en scènes A/B ; aucun effet d'attribut inversé ni annulé
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (12c, Strength, Composure)
- [ ] Table de passe du 18g remesurée et indicateur de calibration de la passe sous 5 points par tranche (50 matchs)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite complète comparée à l'attendu de `CLAUDE.md`

## Comments
