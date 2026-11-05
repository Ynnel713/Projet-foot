# 02h: Validation de la structure : côtés, rôles, appels, distances

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (point de contrôle avant d'empiler l'occupation tactique). **Catégorie :** validation.

**Constat vérifié :** aucun indicateur ne vérifie aujourd'hui le côté moyen occupé par poste ni la cohérence rôle / position.

**What to build:** Ajouter au banc : position moyenne (x, y) par poste et par phase, part du temps de chaque poste latéral dans son couloir, appels et km par poste. Rapport sur 50 matchs, comparé à la référence du 01d ; aucune calibration.

**Attributs :** aucun

**Blocked by:** 02a (Côté gauche ou droit selon le poste, et non selon le nom); 02b (Largeur de référence propre à chaque poste); 02d (Place de référence avec ballon selon le rôle); 02e (Place de référence sans ballon selon le rôle); 02g (Qui fait un appel, et quand); 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée).

**Bloque :** 18a.

**Status:** à faire

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

- [ ] Indicateurs ajoutés et définis dans `docs/INDICATEURS_V2.md`
- [ ] Rapport 50 matchs publié ; écarts au réel listés sans réglage
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
