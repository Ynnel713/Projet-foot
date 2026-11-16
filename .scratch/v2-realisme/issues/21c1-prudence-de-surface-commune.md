# 21c1: Prudence de surface commune aux fautes hors tacle

**Chantier :** `v2-realisme`, découpage du ticket 21c (16/11/2026, validé par le propriétaire). **Priorité :** P1. **Catégorie :** arbitrage.

**Constat vérifié :** la prudence de surface (Decisions 99 -> 0,35, 55 -> 0,5, 11 -> 0,75) n'existe qu'à l'intérieur de `duel.tackle_attempt_factor` (11h). La faute de charge du duel d'épaule (11c, `duel.shoulder_foul_probability`) ne l'applique pas : un défenseur charge aussi fautivement dans sa surface qu'au milieu de terrain.

**What to build:** Extraire la prudence de surface en une fonction publique unique de `duel` (une seule courbe Decisions, règle R1), réutilisée par le tacle (comportement du 11h inchangé) et par toutes les fautes hors tacle. Première application : la faute de charge du duel d'épaule, quand le contact a lieu dans la surface que défend le chargeur. Les sous-tickets 21c2 à 21c7 s'y branchent.

**Attributs :** Decisions (prudence de surface, même courbe que le 11h, pas de seconde courbe).

**Blocked by:** aucun (11c et 11h livrés).

**Constantes validées par le propriétaire (16/11/2026) :**
1. Courbe de prudence du 11h réutilisée telle quelle : Decisions 99 -> 0,35, 55 -> 0,5, 11 -> 0,75, interpolée linéairement (une seule courbe dans le moteur, R1).
2. Elle multiplie la probabilité de **faute** de la charge (le duel d'épaule reste un réflexe ; aucun tirage ajouté). Surface jugée au lieu de la faute (position du joueur chargé, comme le coup de pied de réparation de `restart.foul_restart`), dans la surface que défend le chargeur.
3. Penalties par match en Ligue 1 : « à sourcer » (aucun chiffre avancé de mémoire).

Le propriétaire accepte la baisse temporaire des fautes (relevées par 21c2 à 21c4).

**Status:** livré (16/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 15 min |
| Tests unitaires et comportementaux | 15 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **50 min** |

Confiance : élevée. Hypothèses : extraction sans changement du tacle ; un seul point d'application (duel d'épaule).
Temps machine, non compté : suite complète (environ 10 min) ; mesure 50 matchs.

## Tests

- **Unitaires :** `tackle_attempt_factor` inchangé (mêmes valeurs qu'avant l'extraction) ; probabilité de faute de charge dans sa surface = hors surface x prudence (Decisions 11, 55, 99) ; jamais nulle
- **Statistiques :** 50 matchs : fautes de charge par match, dans et hors surface, avant et après

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Une seule courbe de prudence de surface dans le moteur, utilisée par le tacle et par la charge
- [ ] Charge dans sa surface plus rare qu'ailleurs à situation égale, jamais nulle
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md` ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**Implémentation (16/11/2026).** `duel.box_prudence` (fonction publique, courbe du 11h) utilisée par `tackle_attempt_factor` (valeurs inchangées) et par `shoulder_foul_probability(charger, in_own_box)` ; `resolve_shoulder_duel` juge la surface à la position du perdant (`in_penalty_area(loser.team, ...)`, même règle que `restart.foul_restart`). Banc : neutralisation `--neutraliser 21c1` (même tirage, séries appariées). Tests : `tests/test_v2engine_prudence_surface.py` (13 tests), deux doublures de `tests/test_v2engine_duel_epaule.py` adaptées à la nouvelle signature. Carte des attributs : rôle de Decisions complété.

**Mesures.** 50 matchs appariés (`docs/INDICATEURS_V2.md` section 53) : fautes de charge 0,92 → 0,88, penaltys 0,12 → 0,08, fautes 16,68 → 16,70, buts et tirs inchangés ; aucun écart significatif. Le banc ne sépare pas les fautes de charge par lieu : effet établi en scène contrôlée (6 000 duels, rapport 0,5 ± 0,15 à Decisions 55, jamais nul). Penaltys réels par match : à sourcer.

**Vérifications.** Suite complète : 3 226 passés, 0 ignoré, 14 désélectionnés (3 213 attendus + 13 nouveaux). Déterminisme : 1 match rejoué deux fois à graine fixée, empreinte des agrégats identique (`fdcf80ef20f04e73`). V1 non touchée.

**Clôture (16/11/2026, passage 1).** Expert : APPROVED (anomalies facultatives : A1 fichiers de suivi hors empreinte, admis par le verrou comme suivi documentaire ; A2 nom `TACKLE_BOX_FACTOR_BY_DECISIONS` à généraliser éventuellement en 21c2-21c7). QC : VALIDÉ (mesures hors diff non relues). Décision de clôture journalisée : VALIDÉ.

**Durée.** Estimée 50 min, réelle environ 35 min (analyse 5, développement 10, tests 10, intégration et vérifications 10), écart − 30 % : changement plus local que prévu (une fonction extraite, un appel) ; temps machine hors total : suite complète 13 min, deux séries de 50 matchs (environ 65 min), déterminisme sur 1 match.
