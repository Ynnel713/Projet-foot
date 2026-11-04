# 08: Garde de couverture : 100 % des caractéristiques et des 58 gestes branchés

**Fusion du 04/11/2026** (audit de granularité) : la garde du ticket 05 (les 58 gestes préférés tous rattachés à un mécanisme) est la même garde que celle-ci, avec la même liste d'exceptions. Elle est reprise ici. Le ticket 05 reste ouvert : il garde la grille et le branchement mesuré de chaque geste (fréquence, réussite inchangée).

**What to build:** Un test qui liste les colonnes de caractéristiques de `data/joueurs.xlsx` (47 attributs + Taille FM, Weak foot, Pieds, Preferred moves, Postes FM naturels) et échoue si l'une d'elles n'est lue par aucun module de `v2engine/`, sauf si elle figure dans une liste d'exceptions explicite et justifiée. Étend la garde existante `tests/test_v2engine_rayon_attributs.py` plutôt que d'en créer une seconde.

Exceptions attendues au départ (à valider par le propriétaire) : Natural Fitness, **exception assumée et permanente pour un match isolé** (il ne joue qu'entre les matchs, D-V09/D-V10 : il ne pourra s'exprimer qu'une fois la V2 branchée aux compétitions), et chaque attribut dont le ticket porteur n'est pas encore livré, la liste se vidant au fil des tickets 01 à 07 et 09.

**Attributs :** tous.

**Blocked by:** — (posé tout de suite, liste d'exceptions longue au départ).

**Status:** à faire

**Point de vigilance :** « lu par le moteur » n'est pas « exprimé dans le comportement ». Chaque ticket porteur garde son propre critère mesuré ; cette garde empêche seulement l'oubli.

- [ ] Le test échoue si une caractéristique n'est ni lue par `v2engine/` ni dans la liste d'exceptions
- [ ] Chaque exception cite le ticket qui la lèvera
- [ ] Repris du ticket 05 : les 58 valeurs distinctes de `Preferred moves` sont toutes rattachées à un mécanisme et à un ticket porteur (grille du ticket 05) ; le test échoue si une nouvelle valeur apparaît sans rattachement, ou si une paire contradictoire est additionnée au lieu d'être signalée
- [ ] Suite V2 verte
