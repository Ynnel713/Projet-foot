# 01b: Taxonomie des moments et score d'intérêt

**Chantier :** `v2-mise-en-scene` (audit du mode « moments clés », 26/11/2026). **Catégorie :** lecture de la trace (moteur inchangé).

**Constat vérifié (26/11/2026) :** aucun classement des événements par intérêt n'existe. Les éléments du score se lisent tous dans la trace : type et issue (`ShotEvent`, `ChanceEvent`, `FoulEvent`, `GoalEvent`), minute, score au moment (buts horodatés), zone (x, y), xG neutre et après frappe (`v2-realisme/06a`), danger au pic (`v2-collectif/28c`), origine (`01a`).

**What to build:** un module Python hors de `v2engine/` (proposé : `api/moments.py`, fonctions publiques, importable par l'API et les scripts de mesure) qui lit une `MatchTrace` finie et produit des **candidats** : ancre (instant de l'événement principal), type, tier, score d'intérêt, équipe, joueur, issue.

1. **Taxonomie** :
   - Tier 1 : but (dont csc), penalty (faute sifflée penalty puis tir), grosse occasion (`ChanceEvent`, toutes issues). Emplacements prévus, vides tant que le moteur ne les produit pas : carton rouge (`v2-attributs-restants/09a`), décision VAR (`v2-realisme/21g`, `21h`).
   - Tier 2 : tir hors grosse occasion au-dessus d'un seuil d'xG neutre ; arrêt décisif (`post_shot_xg` au-dessus d'un seuil, tir arrêté) ; coup franc direct cadré ; poteau ou barre (vide jusqu'au `v2-collectif/35c`) ; bonus « belle construction » (vide jusqu'au `v2-realisme/31b`).
   - Tier 3 : faute, corner, hors-jeu (puis carton jaune, remplacement) : jamais candidats, seulement des surimpressions (01g, 03).
2. **Score d'intérêt** = poids du type × modificateurs de contexte, chacun borné :
   - minute (fin de période plus forte) ;
   - écart au score avant l'action (égalité ou un but d'écart plus fort qu'un écart de trois) ;
   - zone ou xG de l'action (le plus fort des deux, pas les deux : pas de double comptage du même danger) ;
   - contre-attaque : action née d'une récupération sur l'adversaire (origine du `01a`) et conclue dans les 15 s (définition partagée avec `v2-realisme/10n`, fonction publique réutilisée si elle existe déjà dans `scripts/v2_indicators.py`, sinon écrite ici et reprise par 10n).
3. Le score sert à **ordonner** les candidats du même tier ; il ne fait jamais passer un Tier 2 devant un Tier 1.

**Attributs :** aucun.

**Constantes à proposer avant le code :** poids par type ; bornes et pentes des quatre modificateurs ; seuils d'xG neutre et d'xG après frappe du Tier 2. Repères réels à sourcer ou « non trouvé » : ce que montrent les résumés télévisés (part des buts, occasions, arrêts ; durée par action).

**Blocked by:** 01a.

**Bloque :** 01c.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Hypothèses : toutes les entrées sont dans la trace finie ; scènes de test construites par la fabrique `v2-realisme/01f` ou par des traces artificielles minimales (`MatchTrace` remplie à la main).
Temps machine, non compté : suite complète (environ 10 min).

## Tests

- Traces construites à la main : un but, une grosse occasion sans tir, un penalty, un tir de loin anodin : tiers et types attendus ; le tir de loin n'est pas candidat.
- Modificateurs : le même tir à la 89e à 1-1 a un score plus élevé qu'à la 20e à 3-0 ; chaque modificateur reste dans ses bornes.
- Aucun candidat Tier 3.

## Acceptance criteria

- [ ] Constantes et repères réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Module hors de `v2engine/`, fonctions publiques, aucune lecture d'un nom privé d'un autre module (ticket 19)
- [ ] Taxonomie testée sur traces construites : chaque type au bon tier, tir anodin exclu
- [ ] Modificateurs bornés et testés un par un ; zone et xG non cumulés
- [ ] Sortie identique sur deux exécutions pour la même trace (fonction pure, aucun tirage)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
