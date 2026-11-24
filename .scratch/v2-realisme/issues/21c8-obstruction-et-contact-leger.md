# 21c8: Obstruction et contact léger toléré

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur la défense, point 5 « tirage de maillot et obstruction : parfois inaperçu, parfois coup franc, parfois carton » ; découpé du `21c4` le 24/11/2026, réserve A1 de l'expert). **Priorité :** P2. **Catégorie :** exécution et arbitrage.

**Constat vérifié (24/11/2026) :** toute faute tirée est sifflée (`duel.should_attempt_tackle`, `duel.tackle_probabilities`, `match._foul` ; constat du `21a`) ; il n'existe ni obstruction (couper la route d'un adversaire sans jouer le ballon), ni contact qui reste léger et toléré : un contact est soit une faute, soit rien.

**What to build:**
- **Obstruction** : un défenseur sur la trajectoire d'un appel ou d'un adversaire qui va au ballon peut lui couper la route sans jouer le ballon (sa cible devient le point de passage de l'adversaire) ; l'adversaire perd de l'élan (contact du `11a`, `11b`). Le volet aérien reste au `21c7`.
- **Contact léger toléré** : un maintien (`21c4`) ou une obstruction a une intensité ; seule une part, croissante avec la durée et l'effet sur l'adversaire (élan cassé, duel perdu), devient une faute ; le reste est un contact toléré, tracé. Ce que l'arbitre voit relève du `21a` (inaperçu) ; la gravité, et l'occasion manifeste annulée par le dernier défenseur, du `21b` ; la répétition, du `v2-attributs-restants/09a`.
- Fréquence selon la situation (défenseur en retard ou battu), pas selon une note ; prudence de surface du `21c1`.

**Attributs (ADR 0002) :** Aggression (fréquence, existante) ; Decisions (prudence de surface, `21c1`). Le défenseur « malin qui dose » n'a pas d'attribut de plus : à confirmer par le propriétaire (R1).

**Blocked by:** `21c4` ; `21b` (gravité, occasion manifeste) ; `21a` (contact vu ou non, volet arbitre ; sinon tout contact au-delà du seuil est sifflé).

**Bloque :** `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : faible. Hypothèses : l'obstruction est une cible de déplacement, le contact passe par la physique des collisions ; l'intensité est une seule grandeur (durée, perte d'élan). Temps machine, non compté : série de 50 matchs (environ 40 min), suite complète (environ 20 min).

## Tests

- **Scènes :** appel dans le dos d'un défenseur battu : obstruction possible, l'attaquant perd de l'élan ; maintien bref sans effet : toléré, tracé, pas sifflé ; maintien long qui casse un appel lancé : faute ; même scène dans la surface : plus rare, jamais nulle.
- **Statistiques (50 matchs) :** obstructions et contacts tolérés par match, part sifflée, fautes totales par match (repère réel 21 à 26).

## Acceptance criteria

- [ ] Constantes produit (seuil d'intensité, part sifflée) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code ; absence d'attribut « dosage » confirmée par le propriétaire
- [ ] Obstruction et contact toléré tracés, distincts de la faute
- [ ] Scènes ci-dessus
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments
