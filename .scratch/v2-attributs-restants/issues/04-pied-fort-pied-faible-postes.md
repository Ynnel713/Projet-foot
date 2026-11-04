# 04: Pied fort, pied faible et postes naturels

**What to build:** Partie individuelle de la phase 10 du plan V2.

- **Pieds** et **Weak foot (/5)** : une passe, un tir, un centre ou un dribble joué du côté faible est plus difficile (difficulté de la fonction partagée, v2-socle/04), et moins souvent choisi. Le côté est déduit de la position du porteur, de sa direction et du but.
- **Postes FM naturels** : un joueur aligné hors de ses postes naturels subit une pénalité sur Positioning, Decisions et Marking (carte des attributs), graduée selon la distance entre le poste joué et le poste naturel.

**Attributs :** Weak foot, Pieds, Postes naturels.

**Blocked by:** v2-collectif/19.

**Status:** découpé (04/11/2026, audit de granularité) en 04a (pied fort et pied faible) et 04b (postes naturels). Ticket chapeau : ne pas l'implémenter tel quel ; le texte ci-dessous reste la référence de détail. Une référence à ce ticket sans lettre vaut pour tous ses morceaux.

**Point de vigilance :** Pieds est vide pour 61 % des joueurs. Proposer au propriétaire un repli (neutre, ou déduction depuis Weak foot = 5 → ambidextre) avant le code ; enrichissement des données en ticket 06.

- [ ] Weak foot 1 : réussite des actions du côté faible mesurablement plus basse et choix de ce côté plus rare ; Weak foot 5 : pas d'écart
- [ ] Un ailier droitier aligné à gauche rentre plus souvent vers l'axe (cohérent avec le pied fort)
- [ ] Joueur hors poste : erreurs de placement et de marquage mesurablement plus fréquentes, proportionnées à l'écart de poste
- [ ] Données manquantes : comportement neutre, jamais d'erreur
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Suite V2 verte ; V1 inchangée
