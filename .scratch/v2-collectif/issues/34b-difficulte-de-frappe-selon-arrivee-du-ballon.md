# 34b: Difficulté de frappe selon l'arrivée du ballon

**Origine (05/11/2026) :** remarques du propriétaire après le ticket 28a : la façon dont le ballon et le joueur arrivent l'un vers l'autre (ballon fort ou arrêté, de face, de côté ou de dos, joueur lancé ou arrêté, bon ou mauvais pied) change la qualité, la puissance et le dosage d'un tir comme d'une passe. Découpage en petits tickets (environ 2 h chacun, mesure comprise), validé par le propriétaire.

**What to build:** Sur un tir de première intention (34a), la difficulté dépend de **l'angle entre la direction d'arrivée du ballon et la direction du tir** (ballon de face : facile ; de côté : moyen ; de dos, ballon qui file vers le but : le plus dur) et de **la vitesse du ballon** (un ballon fort est plus dur à cadrer, mais part plus vite). Un ballon arrêté ou contrôlé n'a pas cette difficulté. La difficulté baisse la chance du tir (28a) et augmente le risque de tir non cadré (35b). Technique l'amortit, comme au 34a, sans recouvrir Finishing.

**Attributs :** Technique (amortit), aucun nouvel attribut.

**Blocked by:** 34a.

**Bloque :** 34c, 36a.

**Status:** à faire (constantes à proposer avant le code)

**Hors de ce ticket :** pied fort et pied faible (`v2-attributs-restants/04a`, qui s'applique ensuite à chacun de ces gestes) ; choix du geste (placée, enroulée, `v2-attributs-restants/10a`).

## Acceptance criteria

- [ ] Constantes et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Scènes contrôlées à même endroit : ballon de face > ballon de côté > ballon de dos pour la chance du tir ; ballon fort plus difficile que ballon lent ; ballon arrêté sans pénalité
- [ ] Origine du tir (trace du 28b) croisée avec la conversion, sur 50 matchs : les tirs de première sur centre ou passe de dos convertissent moins que sur passe en retrait
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
