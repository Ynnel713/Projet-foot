# 07c: Réception de face, de profil ou dos au jeu

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (avancé le 05/11/2026 sur décision du propriétaire : base du contrôle orienté et du jeu à une touche (`v2-collectif/31`)). **Catégorie :** perception.

**Constat vérifié :** la réception ne tient compte que de la vitesse du ballon et de la pression (`possession.control_difficulty`) ; pendant la réception le joueur avance toujours vers le but adverse (`cerveau.py:151-153`).

**What to build:** Classer chaque réception selon le cap du receveur, la direction d'arrivée du ballon et la direction du but adverse : de face, de profil (ouvert), dos au jeu. Le type est tracé ; le receveur qui a le temps se met de profil avant l'arrivée du ballon (rotation du 07a).

**Hors de ce ticket :** effet sur le temps de contrôle (07d).

**Attributs :** aucun

**Blocked by:** 07a (Orientation du corps : état propre et rotation bornée).

**Bloque :** 04i, 07d, 07g, 08c, `v2-collectif/31`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : élevée. Hypothèses : seuils d'angle : valeurs proposées.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** trois scènes (ballon venant de derrière, de côté, de face) : trois types attendus
- **Statistiques (séries de matchs) :** 20 matchs : répartition des types par poste

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Type de réception tracé
- [ ] Répartition par poste rapportée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
