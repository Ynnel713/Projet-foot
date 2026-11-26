# 09: Temps additionnel : chaque cause jouée remplace sa part du fond

**Chantier :** `v2-coach-et-gestion-de-match` (audit de la gestion de match du 26/11/2026, demande du propriétaire, ticket proposé « G3 »). **Catégorie :** mesure et règle.

**Constat vérifié (26/11/2026) :**
- Le temps additionnel est livré (ticket 03) et appliqué en fin de chaque période. `added_time.added_minutes` compte les buts (`GOAL_LOST_S`), les penalties (`PENALTY_LOST_S`), et un fond tiré par période (`BACKGROUND_S`, 60 à 150 s puis 180 à 330 s) pour les causes que le moteur ne joue pas encore : blessures, VAR, cartons, remplacements.
- Chaque cause a son ticket, mais un seul retire sa part du fond. Les tickets qui comptent déjà le temps perdu :
  - remplacements (05a, retire sa part) ;
  - blessures (`v2-attributs-restants/09b`, `v2-realisme/20g`) ;
  - échauffourées (`09c`) ;
  - VAR sur but et penalty (`v2-realisme/21g`).
- Deux tickets ne comptent rien : cartons (`09a`) et VAR sur rouge direct (`21h`). Ils sont complétés le 26/11/2026.
- Sans règle commune, chaque cause livrée s'ajoute au fond qui la contient déjà : le temps additionnel grossit à chaque livraison.

**What to build:**
1. **Règle commune**, écrite dans `added_time` : le fond est la somme de parts nommées (blessures, VAR, cartons, remplacements, autres), chacune avec sa fourchette proposée. Une cause jouée par le moteur met sa part à zéro et compte son temps réel à la place. Le fond actuel est découpé sans changer son total, donc sans changer le jeu.
2. **Bilan** (banc, `docs/INDICATEURS_V2.md`) : temps additionnel annoncé par période et par match, décomposé par cause jouée et part de fond restante, comparé au réel. Pas de réglage ici.

**Attributs :** aucun.

**Constantes à proposer avant le code :** découpage du fond actuel en parts nommées (même total). Chiffres réels à sourcer, sinon « non trouvé » : temps additionnel moyen par période après la directive IFAB 2023, et sa décomposition par cause si elle est publiée.

**Lien avec l'existant :** ne modifie pas la règle livrée au ticket 03 (Loi 7 : seul le temps réellement perdu est rattrapé). Les tickets de cause appellent la règle du point 1 au lieu de retoucher le fond chacun à sa façon.

**Blocked by:** 03 (livré). La règle (point 1) est démarrable seule. Le bilan complet (point 2) se refait à la livraison de chaque cause : 05a, `v2-attributs-restants/09a`, `09b`, `09c`, `v2-realisme/20g`, `21g`, `21h`, qui listent ce ticket dans « Bloque ».

**Bloque :** 05a, `v2-attributs-restants/09a`, `09b`, `09c`, `v2-realisme/20g`, `21g`, `21h` (la règle commune doit exister avant qu'une cause retire sa part).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement (parts nommées, indicateur) | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : élevée. Hypothèses : `added_minutes` seul point de calcul ; total du fond inchangé (empreintes de match identiques avant et après le découpage) ; recherche du chiffre réel non comptée (environ 20 min).
Temps machine, non compté : suite complète (environ 10 min) ; 50 matchs.

## Tests

- **Unitaires :** la somme des parts égale l'ancien fond pour la même clé ; une cause déclarée jouée met sa part à zéro et ajoute son temps réel ; aucune cause comptée deux fois.
- **Statistiques (50 matchs) :** temps additionnel par période, décomposé, comparé au réel.

## Acceptance criteria

- [ ] Découpage du fond et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Découpage sans effet sur le jeu : empreintes de match identiques avant et après, à graine fixée
- [ ] Règle testée : une cause jouée ne s'ajoute jamais à sa propre part de fond
- [ ] Bilan publié dans `docs/INDICATEURS_V2.md` : temps additionnel par période, par cause et part de fond restante, écart au réel renvoyé à un ticket
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
