# 15a: Court ou long selon le pressing, depuis la zone de construction

**Découpé du ticket 15 le 17/11/2026** (décision du propriétaire : « Je valide le découpage »). Détail d'origine : `15-construction-face-au-pressing.md`. **Chantier :** `v2-collectif`. **Priorité :** P1 (la sortie de balle ne s'adapte pas au pressing). **Catégorie :** décision.

**Constat vérifié (17/11/2026, série de 50 matchs du ticket `v2-realisme/25b`, graines du banc) :**
- le gardien relance court (passe de moins de 25 m) dans **97,7 %** des cas ; 92,1 % des relances sont gardées ; pertes dans son propre tiers : 14,6 par match ;
- en jeu, aucune passe longue aérienne n'existe : le ballon aérien n'est utilisé qu'aux remises en jeu (`match.py`, `restart.is_aerial`, vol jusqu'au point de chute à `AERIAL_LANDING_M` près, `restart.LONG_RESTART_M` = 25 m). La passe lobée générale est le ticket `32b`, bloqué par `32a` et `v2-hauteur-ballon/03` ;
- le placement de construction (25b) crée maintenant les solutions courtes et mesure le pressing haut (`Bloc.build_up` : part de l'écartement gardée, 1 sans pressing, 0,5 sous pressing).

**What to build:** quand le porteur est dans sa zone de construction (gardien, ou défenseur dans ses 35 m : la phase du 25b), il compare la meilleure solution courte et une relance longue vers un coéquipier haut (attaquant ou milieu offensif), selon le risque de perte de chacune. Sous pressing haut, la passe courte devient plus risquée et le jeu long plus fréquent ; sans pressing, il joue court. La relance longue en jeu réutilise le vol aérien des remises (point de chute, pas d'interception en vol), sans attendre la passe lobée générale (32b, qui la généralisera).

**Hors de ce ticket :** attirer le pressing, troisième homme (15b) ; qualité du geste du gardien, Kicking et Throwing (`v2-attributs-restants/03c`) ; passe lobée dans tout le jeu (32b).

**Attributs :** Decisions (choisir l'option qui sert, courbe partagée existante), Composure (garder son choix sous pression) ; Passing reste l'exécution de la passe longue, déjà lue. Rayons à vérifier dans `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage avec la décision existante (`decision.py`).

**Blocked by:** `v2-realisme/25b` (livré), 08 (livré), 13 (livré).

**Bloque :** 15b.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 30 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 35 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible. Hypothèses : le vol aérien des remises se réutilise en jeu sans changer `ball.py` ni le moteur de vol ; la valeur de la passe longue se calcule avec les fonctions existantes de `decision.py` (chance de réussite, valeur future du ticket 13). Au-dessus du seuil de 2 h de peu : découpage examiné, le choix et son exécution sont indivisibles (le choix sans passe longue n'a pas d'effet mesurable).
Temps machine, non compté : suite complète ; séries de 50 matchs avant et après.

## Tests

- **Scènes :** gardien porteur, sortie de but jouée : sans pressing, il joue court ; avec 4 adversaires dans ses 35 m et ses solutions courtes couvertes, il joue long plus souvent (part mesurée sur des tirages à graine fixée).
- **Statistiques (50 matchs) :** part de relances longues du gardien et des défenseurs, avec et sans pressing haut ; pertes dans son propre tiers ; relances gardées.

## Acceptance criteria

- [ ] Constantes produit (seuils, valeur du jeu long) et chiffres réels (part de relances longues, pertes dans son propre tiers : sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Part de jeu long mesurablement plus forte face à un pressing haut qu'en son absence, à situation égale (scène et 50 matchs)
- [ ] Pertes de balle dans son propre tiers rapportées avant et après, comparées à la fourchette réelle si elle est trouvée (indicateur de calibration, pas objectif : pas de réglage générique, ticket 22)
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Choix tracé (journal des décisions : court ou long, et pourquoi)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
