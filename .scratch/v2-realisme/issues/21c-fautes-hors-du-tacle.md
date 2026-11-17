# 21c: Fautes hors du tacle : tirage de maillot, charge, faute tactique

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, `docs/AUDIT_ROADMAP_V2.md`). **Priorité :** P1 (le volume de fautes manque d'un mécanisme, il ne doit pas se combler par un réglage). **Catégorie :** arbitrage.

**Constat vérifié :** seules les tentatives de tacle produisent des fautes (`duel.py`) : 9,4 fautes par match contre 21 à 26 en réel (ticket `v2-collectif/30`, écart renvoyé au 22a). Règle des calibrations : un écart dû à un mécanisme absent devient un ticket.

**What to build:** Trois sources nouvelles : contact irrégulier au duel d'épaule (11c) ou à la protection du ballon (04i) ; tirage de maillot du défenseur battu (après un contournement 04g ou un appel dans son dos) ; faute tactique volontaire pour casser une transition (choix du joueur, Decisions ; gravité 21b).

**Complément du propriétaire (16/11/2026, validé) :**
- **Tenir un adversaire** (loi 12) : tirage de maillot **ou bras retenu**, par le défenseur battu ou au marquage (dans la surface, notamment sur coup de pied arrêté).
- **Charge dans le dos** du porteur (défenseur qui arrive derrière lui) ou au **duel aérien** (sauter dans le dos de l'adversaire). Le volet aérien attend le jeu aérien (`v2-attributs-restants/01`).
- **Faute du gardien dans ses sorties** : sur un ballon libre (course au ballon, `gardien.race`) ou aérien (poing ou sortie qui percute l'attaquant). Penalty dans la surface ; le volet face-à-face (gardien qui fauche le dribbleur) reste au `v2-attributs-restants/10b`.
- **Prudence dans sa surface pour toutes ces fautes**, comme pour le tacle (ticket 11h : prudence de surface réglée par Decisions, 99 -> 0,35, 55 -> 0,5, 11 -> 0,75) : la faute y coûte un penalty, donc le joueur retient son geste (moins de maillots tirés, de charges, de fautes tactiques ; la faute tactique n'y a presque aucun sens). **Moins rare ne veut pas dire jamais** : des fautes et des penalties restent possibles. Valeurs par source à proposer avant le code ; réutiliser le facteur du 11h si le propriétaire le valide (pas de seconde courbe Decisions pour le même discernement, règle R1).

**Attributs :** Decisions (choisir la faute tactique ; prudence dans sa surface, même discernement que le 11h) ; Aggression inchangée (fréquence des contacts) ; gardien : Rushing Out et One on Ones (sorties), à trancher pour la faute.

**Blocked by:** 11c, 04g, 04i, 21b ; 11h (prudence de surface, ajouté le 16/11/2026) ; volet aérien : `v2-attributs-restants/01` (jeu aérien).

**Bloque :** `v2-collectif/22a` (volume des fautes).

**Status:** découpé (16/11/2026, validé par le propriétaire) en 21c1 à 21c7 ; clos quand tous ses sous-tickets sont livrés et la mesure du volume de fautes faite (critères ci-dessous).

## Découpage (16/11/2026)

Note : le constat est en partie dépassé, puisque le duel d'épaule du 11c produit déjà des fautes de charge (`duel.shoulder_foul_probability`).

| Sous-ticket | Contenu | Bloqué par |
|---|---|---|
| 21c1 | Prudence de surface commune (courbe du 11h, extraite), appliquée d'abord à la charge du 11c | aucun |
| 21c2 | Faute du gardien en sortie sur un ballon libre | 21c1 |
| 21c3 | Charge dans le dos du porteur (au sol) | 21c1 |
| 21c4 | Tenir un adversaire (maillot, bras) : marquage ; défenseur battu | 21c1 ; volet défenseur battu : 04g |
| 21c5 | Contact irrégulier à la protection du ballon | 21c1, 04i |
| 21c6 | Faute tactique pour casser une transition | 21c1, 21b |
| 21c7 | Fautes aériennes (charge au saut, sortie aérienne du gardien) | 21c1, 15b |

Total des sous-tickets : 9 h 20 de travail effectif, à comparer aux 2 h de l'estimation initiale, qui ne comptait pas le complément du 16/11.

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : chaque source réutilise une situation déjà détectée par le moteur.

**À découper avant le code (16/11/2026) :** le complément du propriétaire ajoute trois sources (tenir le bras, charge dans le dos, faute du gardien en sortie) et la prudence de surface ; le total dépasse nettement le seuil de 2 h (estimation à refaire par sous-ticket, par exemple : tenir un adversaire ; charges ; faute tactique ; faute du gardien en sortie ; prudence de surface commune).
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** défenseur battu sur un contournement : tirage de maillot possible, plus fréquent si la transition est dangereuse ; même scène dans sa surface : faute plus rare, mais possible ; gardien en sortie qui percute l'attaquant : penalty
- **Statistiques (séries de matchs) :** 50 matchs : fautes par match par source

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Sources tracées : contact irrégulier, tenir un adversaire (maillot, bras), charge dans le dos, faute tactique, faute du gardien en sortie
- [ ] Dans sa surface : chaque source plus rare qu'ailleurs à situation égale, jamais nulle ; penalties par match rapportés (repère réel à chercher, ou « non trouvé »)
- [ ] Fautes par match ramenées vers le repère réel 21-26, écart restant rapporté (décision du propriétaire du 16/11/2026 : le 11h fait passer les fautes de 19,8 à 10,9 par match sur 50 matchs appariés, en évitant les tacles par derrière et de côté ; le 21c compense par les fautes hors tacle, sans revenir sur les constantes du 11h)
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
