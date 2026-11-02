# 08: Garde de couverture : 100 % des caractéristiques branchées

**What to build:** Un test qui liste les colonnes de caractéristiques de `data/joueurs.xlsx` (47 attributs + Taille FM, Weak foot, Pieds, Preferred moves, Postes FM naturels) et échoue si l'une d'elles n'est lue par aucun module de `v2engine/`, sauf si elle figure dans une liste d'exceptions explicite et justifiée. Étend la garde existante `tests/test_v2engine_rayon_attributs.py` plutôt que d'en créer une seconde.

Exceptions attendues au départ (à valider par le propriétaire) : Natural Fitness, **exception assumée et permanente pour un match isolé** (il ne joue qu'entre les matchs, D-V09/D-V10 : il ne pourra s'exprimer qu'une fois la V2 branchée aux compétitions), et chaque attribut dont le ticket porteur n'est pas encore livré, la liste se vidant au fil des tickets 01 à 07 et 09.

**Attributs :** tous.

**Blocked by:** — (posé tout de suite, liste d'exceptions longue au départ).

**Status:** à faire

**Point de vigilance :** « lu par le moteur » n'est pas « exprimé dans le comportement ». Chaque ticket porteur garde son propre critère mesuré ; cette garde empêche seulement l'oubli.

- [ ] Le test échoue si une caractéristique n'est ni lue par `v2engine/` ni dans la liste d'exceptions
- [ ] Chaque exception cite le ticket qui la lèvera
- [ ] Suite V2 verte
