# 03a: Gardien : sous-système propre, fin du presseur générique

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P0 (le gardien fausse aujourd'hui tous les tirs). **Catégorie :** placement.

**Constat vérifié :** le gardien est exclu des rôles défensifs, mais `cerveau.interpret` lui applique la règle générale : à moins de 15 m d'un porteur adverse il prend `PRESSEUR` (`cerveau.py:123-128`) et court au ballon ; à moins de 15 m de son propre porteur il prend `SOUTIEN`. Sinon il garde sa place de coup d'envoi (`bloc.py:184`, `bloc.py:224`).

**What to build:** Créer un module `v2engine/gardien.py` et un rôle `GARDIEN` : le gardien ne passe plus par la règle générale (ni presseur, ni soutien, ni indiscipline), seulement par son module, avec des états tracés (placement, sortie, intervention, relance). Dans ce ticket, l'état « placement » garde la place actuelle : seul le comportement de presseur disparaît.

**Hors de ce ticket :** placement sur l'angle (03b) et sorties (03d, 03e). le ticket `v2-attributs-restants/03b` ajoutera les tendances et notes du gardien (Rushing Out, Eccentricity, One on Ones…) sur ces mécanismes neutres ; aucun attribut de gardien ici.

**Attributs :** aucun

**Blocked by:** 01f (Fabrique de scènes de test partagée).

**Bloque :** 03b.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement | 40 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 50** |

Confiance : élevée. Hypothèses : les remises en jeu (`restart.py`) gardent leur logique propre du gardien.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 20 matchs.

## Tests

- **Unitaires (scène contrôlée) :** porteur adverse à 10 m du gardien : le gardien ne court plus vers lui ; porteur de son équipe à 10 m : idem
- **Statistiques (séries de matchs) :** 20 matchs : distance maximale du gardien à son but rapportée avant / après

## Acceptance criteria

- [ ] Rôle `GARDIEN` et états tracés
- [ ] Plus aucune intention « presser » ou « aller au ballon » du gardien hors ballon libre à sa portée
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
