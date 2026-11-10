# 16j: Tireurs désignés : une table par équipe pour penalty, corner, coup franc et touche longue

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, complément hors-jeu et coups de pied arrêtés, `docs/AUDIT_ROADMAP_V2.md` §12). **Priorité :** P2 (un seul endroit choisit les tireurs, au lieu de quatre tickets qui le refont chacun). **Catégorie :** données.

**Constat vérifié :** le preneur est le joueur le plus proche du point (`restart._taker`) : le gardien sur sa sortie de but, le joueur offensif le plus proche sur un corner, le plus proche sur un coup franc et sur le penalty provisoire. Corners, Free Kick Taking, Penalty Taking et Long Throws ne sont lus nulle part. 16d, 16e, 16f et `v2-attributs-restants/02a` prévoient chacun « le meilleur » de leur attribut.

**What to build:** Au coup d'envoi, chaque équipe désigne ses tireurs par type (penalty, corner à gauche, corner à droite, coup franc direct, coup franc centré, touche longue), selon l'attribut du geste, le pied si `v2-attributs-restants/04a` est livré (ballon rentrant ou sortant), et le geste préféré « Demands to Take Penalties » ; mise à jour après un remplacement, une expulsion ou une blessure (le suivant de la liste). Le preneur d'une remise en jeu est le tireur désigné s'il est sur le terrain, sinon le plus proche comme aujourd'hui. Tracé.

**Attributs :** Corners, Free Kick Taking, Penalty Taking, Long Throws (choix du tireur seulement ; la qualité du geste reste aux tickets 16d, 16e, 16f et 02a).

**Blocked by:** `v2-collectif/29` (livré).

**Bloque :** 16d, 16e, 16f ; `v2-attributs-restants/02a`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 35 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 10 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : table calculée une fois, relue à chaque remise en jeu.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires :** équipe avec un tireur à Corners 90 et les autres à 40 : il tire tous les corners tant qu'il est sur le terrain ; après sa sortie, le suivant
- **Statistiques (séries de matchs) :** 20 matchs : part des corners, coups francs et penalties tirés par le tireur désigné

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Table tracée par équipe ; mise à jour après un changement d'effectif
- [ ] Chaque type de remise utilise le tireur désigné quand il est sur le terrain
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
