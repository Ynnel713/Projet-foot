# 10l: Cadrage en un contre un : reculer, orienter le porteur vers l'extérieur, attendre le soutien

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur la défense, point 2 « évaluation du danger : reculer, temporiser, sortir fort, couvrir » et point 3 « cadrage et duel en 1v1 »). **Priorité :** P1. **Catégorie :** décision et placement.

**Constat vérifié (24/11/2026) :** le presseur se présente à une distance d'arrêt réglée par Aggression, du côté de la ligne de passe ou de tir qu'il ferme, à au plus `SHADOW_M` de son approche directe (`defense.press_point`, tickets `v2-collectif/08`, `10k`) ; la décision de tacler ou d'attendre relève du contexte « choix défensif » (Decisions, Anticipation, `duel.tackle_attempt_factor`, `v2-attributs-contextes/04a`). Le volet « le presseur attend le soutien » a été abandonné au `v2-attributs-contextes/04a` (réduction du 17/11/2026). Aucune règle n'oriente le porteur vers la touche ou l'extérieur, et le presseur n'a ni règle de recul ni d'attente : sa cible suit le porteur à sa distance d'arrêt, quel que soit le soutien de ses partenaires.

**What to build:**
- **Fermer l'intérieur** : hors ligne de passe ou de tir plus dangereuse à fermer, le presseur se place côté axe et but, de façon à pousser le porteur vers la touche ou la zone la moins dangereuse (même monnaie que `danger.py`) ; pied faible du porteur : volet fait seulement quand `v2-attributs-restants/04a` est livré.
- **Temporiser** : porteur lancé face à lui, sans soutien défensif à portée, le presseur recule en gardant sa distance d'arrêt (pas de duel), jusqu'à l'arrivée d'un partenaire ou jusqu'à une zone où le danger impose d'engager (surface, dernier défenseur : urgence du `11h`).
- **Sortir fort** : porteur qui reçoit dos au jeu ou contrôle mal (ballon loin du pied, `04e`, `26a`), le presseur engage tout de suite (lien `10m`).
- **Ne pas plonger** : le tacle sur une feinte ou un geste reste réglé par le « choix défensif » (`v2-attributs-contextes/04a`) et la lecture du `04o` ; rien de nouveau ici.

**Attributs (ADR 0002) :** aucun nouveau : distance par Aggression (existant) ; engager ou attendre par le contexte « choix défensif » existant, étendu au presseur sans ballon disputé (à valider : réintroduit le volet abandonné au `v2-attributs-contextes/04a`, décision explicite du propriétaire avant le code). Pas de double comptage avec le `04o` (état du défenseur battu).

**Blocked by:** `v2-collectif/08`, `10k`, `v2-attributs-contextes/04a` (livrés) ; `04o` (lecture du défenseur face au dribble) ; `10m` (volet « sortir fort » sur le receveur dos au jeu).

**Bloque :** `40`, `v2-collectif/22a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : le côté à fermer et le recul sont des cibles de `press_point` ; le soutien est le partenaire le plus proche à moins d'une distance proposée. Temps machine, non compté : série de 50 matchs (environ 40 min), suite complète (environ 20 min).

## Tests

- **Scènes :** porteur sur l'aile face au presseur : il part vers la touche plus souvent que vers l'axe ; porteur lancé, presseur seul : recul sans duel, puis engagement à l'arrivée d'un partenaire ; porteur qui reçoit dos au jeu : engagement immédiat.
- **Statistiques (50 matchs, avant / après) :** entrées dans la surface par l'axe et par les côtés, duels un contre un perdus par le défenseur, fautes du presseur, buts (dans le bruit).

## Acceptance criteria

- [ ] Constantes produit (côté fermé, distance de soutien, recul) et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code ; réintroduction du volet « attendre le soutien » tranchée par le propriétaire
- [ ] Choix (fermer, temporiser, sortir) tracé au journal des décisions
- [ ] Scènes ci-dessus
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments
