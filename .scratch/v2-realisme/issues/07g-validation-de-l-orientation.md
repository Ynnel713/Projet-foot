# 07g: Validation de l'orientation

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (contrôle avant la perception (08)). **Catégorie :** validation.

**Constat vérifié :** aucun indicateur d'orientation.

**What to build:** Indicateurs : part des réceptions par type et par poste, délai moyen de rotation avant une action, vitesse à reculons des défenseurs. Scènes de référence et rapport sur 50 matchs.

**Attributs :** aucun

**Blocked by:** 07b (Se déplacer de face, de côté ou à reculons); 07c (Réception de face, de profil ou dos au jeu); 07d (Temps de contrôle et enchaînement selon l'orientation); 07e (Se réorienter avant une passe, un tir ou une conduite); 07f (Agility : vitesse de rotation du corps); 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée).

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : lecture de la trace.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : rapport publié

## Acceptance criteria

- [ ] Indicateurs définis et ajoutés
- [ ] Rapport publié
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Comments

**13/11/2026, repris du 07b (réserve A1 du passage 2, acceptée par le propriétaire).** Tirs en face-à-face 13,9 → 15,7 par match après le 07b (+ 13 %, environ 2,4 écarts-types ; 16,2 avant la correction du pivot sur l'appel dans le dos), cause non établie. À isoler ici, sur les graines du 08f (`.scratch/v2-realisme/mesures/08f-50-lot*`), avant toute calibration des face-à-face : pas chassés à 90 % au lieu de 80 % ; vitesse de cible (`target_velocity`) des cibles de ligne et de couverture. Aucune constante changée sans validation du propriétaire. Aussi (facultatif A2 du passage 2) : vérifier qu'un marqueur dont l'attaquant court autour de sa vitesse à reculons ne fait pas trembler son cap.
