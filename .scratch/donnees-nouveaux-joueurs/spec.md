# Nouveaux joueurs FMInside (2 000 joueurs absents de la base)

Demande du propriétaire (22/11/2026) : enrichir `data/joueurs.xlsx` de 2 000 joueurs absents de la base, avec leurs attributs FM26, pris dans les clubs des championnats simulés.

## Décisions du propriétaire (22/11/2026)
- Clubs cibles : les 174 clubs des 9 championnats simulables (hors « Autres clubs »).
- Sélection : quota égal par club, les mieux notés FM d'abord, effectif plafonné à 40 joueurs. Cible totale : 2 000.
- Note V1 des nouveaux : placée sur la courbe FM -> Moyenne FM des joueurs existants de la même famille de poste ; les notes des joueurs existants ne bougent pas.
- La collecte sur fminside.net est lancée par le propriétaire depuis son poste : le `robots.txt` du site interdit les robots d'Anthropic. Claude écrit et teste le code hors ligne, puis vérifie le classeur produit.

## Tickets
- 01 : mode découverte dans le script de collecte (sélection, écriture des nouvelles lignes).
- 02 : Moyenne FM des lignes sans Moyenne joueur.
- 03 : intégration après la collecte (vérifications, mesures, suite complète).
