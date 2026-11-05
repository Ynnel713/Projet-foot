# 12g: Validation de la physique des déplacements

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (contrôle des volumes avant la calibration 22a). **Catégorie :** validation.

**Constat vérifié :** voir 01d ; volumes de course très au-dessus du réel dans les dernières mesures publiées.

**What to build:** Rapport sur 50 matchs : km par poste, temps et distance au-dessus de 19,8 et 25 km/h, sprints, baisse en fin de match, comparés aux repères du 01c (indicatifs ou bloquants selon 01c). Aucun réglage générique : les écarts restants vont au 22a.

**Attributs :** aucun

**Blocked by:** 12a (Freinage individualisé : Agility); 12b (Perte de vitesse en virage); 12c (Balance : rester debout et continuer après un contact); 12d (Intensité de course selon le rôle); 12e (Réserve d'énergie qui dépend de l'effort); 12f (Répéter les sprints et récupérer); 01d (Banc : distance par poste, temps et distance à haute intensité, appels selon la définition sourcée).

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 10 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 20 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 15** |

Confiance : élevée. Hypothèses : lecture de la trace.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Statistiques (séries de matchs) :** 50 matchs : rapport publié

## Acceptance criteria

- [ ] Rapport publié ; écarts au réel listés et attribués
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
