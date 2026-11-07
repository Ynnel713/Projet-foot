# 02h: Validation de la structure : côtés, rôles, appels, distances

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (point de contrôle avant d'empiler l'occupation tactique). **Catégorie :** validation.

**Constat vérifié :** aucun indicateur ne vérifie aujourd'hui le côté moyen occupé par poste ni la cohérence rôle / position.

**What to build:** Ajouter au banc : (réserves A1 et A2 de l'expert au 02g) nombre d'épisodes `APPEL` par poste et par 90 min, maximum d'appelants simultanés par équipe et par situation, passages APPEL / TENIR à l'intérieur d'une même possession et leur part de moins de 1,5 s, via `Collector.on_role` ; position moyenne (x, y) par poste et par phase, part du temps de chaque poste latéral dans son couloir, appels et km par poste. Rapport sur 50 matchs, comparé à la référence du 01d ; aucune calibration.

**Attributs :** aucun

**Blocked by:** 02a (Côté gauche ou droit selon le poste, et non selon le nom); 02b (Largeur de référence propre à chaque poste); 02d (Place de référence avec ballon selon le rôle); 02e (Place de référence sans ballon selon le rôle); 02g (Qui fait un appel, et quand); 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée).

**Bloque :** 18a.

**Status:** livré (07/11/2026), validé expert + QC

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : indicateurs de lecture seulement.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** position moyenne calculée sur trajectoires synthétiques
- **Statistiques (séries de matchs) :** 50 matchs : latéraux gauches à gauche plus de 90 % du temps hors transition (seuil à valider)

## Acceptance criteria

- [x] Indicateurs ajoutés et définis dans `docs/INDICATEURS_V2.md` (indicateurs 17 à 23, seuils de la section 3)
- [x] Rapport 50 matchs publié (section 9 de `docs/INDICATEURS_V2.md`, mesure `.scratch/v2-realisme/mesures/02h-serie.json`) ; écarts au réel listés sans réglage
- [x] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [x] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [x] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md` : 2 473 passés, 14 désélectionnés sur l'état final (07/11/2026, 21 min 35 s) ; attendu 2 464 + 9 nouveaux

## Comments

- 07/11/2026 : **Critères chiffrés posés avant le code** : (1) chaque indicateur de « What to build » existe, est défini dans `docs/INDICATEURS_V2.md` et testé sur une scène contrôlée ; (2) lecture seule : mêmes buts, passes et appels du banc qu'au 02g à graine égale (3,88 ; 1 044 ; 45,4) ; (3) 50 matchs à la graine d'audit ; (4) postes latéraux du bon côté plus de 90 % du temps hors transition ; (5) deux exécutions, même empreinte. Seuils de mesure (1,5 s ; bon côté de l'axe) proposés par Claude, acceptés d'office par le propriétaire.
- 07/11/2026 : **Réalisé** (`scripts/v2_indicators.py`, `scripts/measure_v2.py`, `scripts/bench_series.py`, `tests/test_v2_indicators.py`, `docs/INDICATEURS_V2.md`). Épisodes APPEL par poste et par 90 min ; appelants simultanés par situation (moyenne, maximum, part des instants au-dessus de `CALLER_CAP`) ; passages APPEL / TENIR dans une possession, avec la part de moins de 1,5 s **et séparément les appels qui s'arrêtent en moins de 1,5 s** (TENIR → APPEL est le délai voulu d'Off the Ball, pas un clignotement) ; rôle des joueurs au départ des courses que le banc compte comme appels (réserve A1) ; part des appelants qui sont une solution de passe ouverte (réserve A3) ; place moyenne (profondeur, côté) par poste, avec et sans ballon ; part du temps du côté de son poste, hors transition aussi. Aucun fichier du moteur modifié. La première série de 50 matchs (passage 1) a montré qu'un indicateur de passages mélangeait délai et clignotement et que le plafond semblait dépassé : l'indicateur a été scindé et la part des instants au-dessus du plafond ajoutée, puis la série a été relancée (conservée : `02h-serie-passe1.json`).
- 07/11/2026 : **Résultats (50 matchs, détail section 9 de `docs/INDICATEURS_V2.md`)** : postes latéraux du bon côté 98,9 à 99,4 % hors transition (critère 90 % tenu) ; 33 % des « appels » du banc partent d'un joueur en `TENIR`, 30 % seulement d'un rôle `APPEL` (hypothèse du 02g confirmée : les volumes du banc ne jugent pas la sélection) ; épisodes APPEL par 90 min : DC 2,3, latéraux 10 à 17, MDC 17, MC 55, MOC 167, ailiers 177 à 186, BU 211 ; plafond de 2 appelants dépassé sur 2,6 % des instants de possession installée (maximum 3, jamais ailleurs, cause non vérifiée : situation réelle du banc contre situation perçue du joueur) ; 40 % des appels qui s'arrêtent le font en moins de 1,5 s (diagnostic du 02g : 24 %, autre définition) ; seulement 30 % des appelants sont une solution de passe ouverte du porteur (A3 du 02g : le filtre « espace exploitable » mérite un ticket dédié). Écarts au réel listés, aucun réglage.
- Déterminisme : deux exécutions de 15 minutes à graine fixée, même empreinte `cba102f800d46f86` (code final) ; la série de 50 matchs redonne exactement les buts, passes et appels du 02g. Tests : 9 nouveaux dans `tests/test_v2_indicators.py` (place moyenne vue de son but et miroir de l'équipe visiteuse, côté faux et filtre de transition, appelants simultanés, instants au-dessus du plafond, épisodes par 90 min, passages dans une possession et appels arrêtés, rôle au départ des courses du banc, appelant et passe ouverte, rapport), plus 3 assertions ajoutées au test sur match réel. Suite complète : un premier passage (2 472 passés, 41 min 34 s, machine partagée avec la série) précédait les dernières retouches de scripts ; le contrôle qualité l'a refusé comme preuve (BLOQUÉ) ; passage final sur l'état exact du ticket : 2 473 passés, 14 désélectionnés, 21 min 35 s (`02h-suite-finale.txt`).
- Durée : estimée 1 h 30 (90 min ; 15/40/20/15), réelle environ 2 h 05 (125 min ; 20/45/25/35, non chronométrée), écart environ + 39 % : un second passage de mesure (indicateur de passages scindé par direction, part des instants au-dessus du plafond) après la première série, et deux séries de 50 matchs au lieu d'une. Temps machine, hors total : suites complètes 41 min 34 s puis 21 min 35 s, séries de 50 matchs environ 45 min (première) et 25 min (seconde).
- 07/11/2026 : **Clôture.** Passage 1 du contrôle qualité : `BLOQUÉ` (suite complète non prouvée sur l'état final, deux fichiers de scripts retouchés après le premier passage de 2 472) ; la suite a été relancée sur l'état final (2 473 passés, 21 min 35 s), passage 2 : `VALIDÉ`. Expert `APPROVED_WITH_RESERVATIONS` (empreinte `7c04ca3c`), clôture `VALIDÉ` (journal). Réserves acceptées d'office par le propriétaire (règle permanente, rappelée dans le message qui a lancé 02h, 03a et 03b le 06/11/2026 : « Je valide par défaut toutes tes recommandations ainsi que celles des experts »). **A1** : la part des instants au-dessus du plafond compare à la situation réelle du banc, le moteur applique la situation perçue ; le maximum de 3 en possession installée vaut le plafond de la transition offensive : ne pas corriger la sélection sur ce chiffre avant de recompter avec la situation perçue (doc corrigée). **A2** : « du bon côté de l'axe » est un critère tolérant, à citer avec la place moyenne (doc corrigée). **A3** : « appelants couverts » n'est pas démontré, la chance de réception dépend aussi de la distance et du Passing (doc corrigée). Facultatif A4 : asymétrie LB 17,5 / RB 10,0 épisodes APPEL, à suivre aux tickets 09 et 18a. À surveiller : 40 % des appels arrêtés en moins de 1,5 s, défenseurs centraux plus hauts sans ballon (29,5 m contre 26,6 m), épisodes APPEL très nombreux pour les offensifs. Suites possibles, hors de ce ticket (non créées) : recomptage du plafond avec la situation perçue ; filtre « espace exploitable » de l'appelant (30 % seulement sont une solution de passe) ; clignotement de l'appel.
- QC, remarques non bloquantes retenues : les lignes « au-dessus du plafond » de « défense placée » et « transition défensive » valent 0 par construction (pas de plafond dans `CALLER_CAP`), dit dans la doc ; durée réelle estimée, non chronométrée.
