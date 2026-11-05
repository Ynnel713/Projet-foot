# 04a: Pied fort et pied faible

**Découpé du ticket 04 le 04/11/2026** (audit de granularité). Détail : `04-pied-fort-pied-faible-postes.md`.

**What to build:** **Pieds** et **Weak foot (/5)** : une passe, un tir, un centre ou un dribble joué du côté faible est plus difficile (fonction de difficulté partagée, v2-socle/04) et moins souvent choisi. Le côté est déduit de la position du porteur, de sa direction et du but.

**Attributs :** Weak foot, Pieds.

**Blocked by:** `v2-collectif/19` ; passe après `v2-collectif/22c` (contrôle de non-régression).

**Bloque :** 10a (côté ouvert ou fermé selon le pied fort, sans bloquer) ; lignes « Pied » du catalogue 05.

**Status:** à faire (constantes à proposer avant le code)

**Point de vigilance :** Pieds est vide pour 61 % des joueurs. Proposer au propriétaire un repli (neutre, ou Weak foot = 5 → ambidextre) avant le code ; enrichissement des données au ticket 06.

## Acceptance criteria

- [ ] Weak foot 1 : réussite des actions du côté faible mesurablement plus basse et choix de ce côté plus rare ; Weak foot 5 : pas d'écart
- [ ] Un ailier droitier aligné à gauche rentre plus souvent vers l'axe
- [ ] Ajout du 05/11/2026 (propriétaire) : le pied de frappe se déduit de la position du ballon par rapport au corps et de la direction du tir. Un ailier droitier aligné à gauche qui repique au centre frappe de son pied fort ; un gaucher aligné à gauche qui repique frappe du droit, son pied faible, et sa frappe est moins bonne (scène contrôlée)
- [ ] Ajout du 05/11/2026 : le pied faible s'applique aussi aux gestes des tickets `v2-collectif/34a` à `36b` (tir de première, volée, passe à une touche, passe en course) : un ballon qui arrive du côté du pied faible est plus difficile
- [ ] Données manquantes : comportement neutre, jamais d'erreur
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
