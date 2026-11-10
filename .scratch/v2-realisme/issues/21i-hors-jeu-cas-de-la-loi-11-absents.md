# 21i: Hors-jeu : rebond après un tir, déviation contre jeu volontaire, gêne d'un adversaire

**Chantier :** `v2-realisme` (audit de la roadmap du 10/11/2026, complément hors-jeu et coups de pied arrêtés, `docs/AUDIT_ROADMAP_V2.md` §12). **Priorité :** P1 (le premier cas fait accorder des buts qui devraient être refusés). **Catégorie :** arbitrage.

**Constat vérifié :** le hors-jeu est jugé au départ d'une passe seulement (`offside.offside_at_pass`, appelé seulement au départ d'une passe dans `match._step_ball`) ; un tir efface le signalement (`match._step_ball`, branche du tir : « la passe signalée est morte : le ballon est tiré ») : un attaquant hors-jeu au moment du tir de son coéquipier qui reprend le ballon repoussé par le gardien ou renvoyé par un poteau n'est jamais sifflé. Le module l'écrit lui-même (`offside.py`, « Non modélisé ») : pas de distinction entre un ballon dévié par un adversaire (le hors-jeu tient) et un ballon joué volontairement par lui (le hors-jeu tombe, sauf arrêt volontaire, par le gardien ou par n'importe quel joueur), alors que la déviation existe depuis le ticket 05d ; pas de sanction pour un attaquant hors-jeu qui gêne un adversaire sans toucher le ballon (devant le gardien sur un tir, ou qui dispute le ballon). Le coup franc joué en passe est, lui, déjà contrôlé (il passe par la décision du porteur).

**What to build:** Loi 11 complète pour ce qui existe dans le moteur : (1) le jugement est aussi pris au départ d'un tir ; le signalement survit à un arrêt, à un poteau et à une déviation, et tombe sur un jeu volontaire d'un adversaire (passe, dégagement, contrôle ; jamais un arrêt volontaire, par le gardien ou un autre joueur) ; (2) « jeu volontaire » et « déviation » sont lus dans le journal des événements (19b) ; (3) gêne d'un adversaire : un attaquant signalé, sur la ligne de vue du gardien au tir (à moins d'une distance à proposer) ou qui dispute le ballon à un défenseur, est sanctionné ; (4) l'assistant juge ces cas comme les autres (21a). La sanction est un coup franc indirect (16h).

**Attributs :** aucun nouveau (Off the Ball règle déjà le respect de la ligne).

**Lien avec l'existant :** `v2-collectif/23` (hors-jeu livré) ; `v2-realisme/05d` (déviation) ; 21g (la VAR revoit ces cas sur un but).

**Blocked by:** 19b, 21a, 16h.

**Bloque :** 21g.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : la ligne de vue du gardien est un segment ballon-gardien ; la distance de gêne est une constante unique.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** tir arrêté, attaquant hors-jeu au tir qui reprend : sifflé ; même scène, défenseur qui dégage volontairement avant : pas sifflé ; ballon dévié par un défenseur : sifflé
- **Unitaires (scène contrôlée) :** attaquant hors-jeu devant le gardien sur un tir de 20 m : sifflé ; à 10 m de côté : pas sifflé
- **Statistiques (séries de matchs) :** 50 matchs : hors-jeu par match et par cas (repère 3,2 à 3,5 par match, ticket 23), buts refusés

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les trois cas de la loi 11 couverts par des scènes, dans le bon sens
- [ ] Hors-jeu par match rapportés par cas (aucun réglage pour viser le repère)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
