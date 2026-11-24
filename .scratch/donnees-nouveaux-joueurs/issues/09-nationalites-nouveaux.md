# 09: Nationalités des 600 nouveaux joueurs

**Status:** livré (24/11/2026), validé expert + QC

**Blocked by:** 07b (fichier des nations), 08 (retraites internationales)

**What to build:** `scripts/apply_nations.py` : lit le fichier des nations rempli par le propriétaire (Nom, Prénom, Poste, Club, Nation), uniformise les noms de pays sur les libellés de la base, et les reporte dans « Nationalité » des 600 joueurs ajoutés au 07b (retrouvés par Nom, Prénom, Poste, Club ; seules les lignes « À renseigner » sont modifiées). Le fichier uniformisé remplace `data/nouveaux_joueurs_nations.xlsx`. Puis `generate_national_teams.py`.

**Demande du propriétaire (24/11/2026) :** « voici les nations. Uniformise les noms de pays ».

**Estimation (travail effectif) :** analyse 15 min, développement 25 min, tests 20 min, vérifications 20 min ; total 1 h 20 ; confiance élevée.

## Mesures préalables
- Fichier reçu : 600 lignes, 0 vide, mêmes lignes et même ordre que le fichier envoyé ; 65 libellés.
- Libellés hors base : Bréso (David Luiz) -> Brésil ; Danemarl (Carlo Holse) -> Danemark ; Ecosse -> Écosse ; Egypte -> Égypte ; Etats Unis -> États-Unis ; Israel -> Israël ; Macédoine (Enis Bardhi) -> Macédoine du Nord ; Nigéria -> Nigeria ; Pays Bas -> Pays-Bas ; Tchéquie -> République tchèque ; Iles Feroé -> Îles Féroé ; Tchad inchangé. Îles Féroé et Tchad n'ont pas de sélection dans le classeur (ignorés par la génération, comme les 6 nationalités déjà dans ce cas).
- « Congo » (Makoumbou, Makouta) gardé : Congo-Brazzaville, distinct de « RD Congo ».

## Critères d'acceptation
- [x] 600 joueurs retrouvés sans ambiguïté (clé Nom, Prénom, Poste, Club unique) ; seule la colonne Nationalité change, et seulement sur des lignes « À renseigner ».
- [x] Après correction, tous les libellés existent dans la base ou sont signalés (pays sans sélection).
- [x] Sélections régénérées ; Messi et Griezmann (retraite internationale) absents ; bilan avant / après publié.
- [x] Script idempotent ; tests hors ligne ; suite complète passée.

## Journal

24/11/2026 — implémenté.
- `scripts/apply_nations.py` (nouveau), `NATION_FIXES` (11 libellés uniformisés, voir Mesures préalables) ; fichier reçu conservé hors dépôt, version uniformisée dans `data/nouveaux_joueurs_nations.xlsx`.
- Application : 600 lignes lues, 62 pays après uniformisation, 600 appliqués (0 introuvable, 0 ambigu, 0 vide) ; relance : 0 appliqué, 600 déjà à jour. Classeur : seule la colonne Nationalité change (600 cellules), plus aucun « À renseigner ».
- Sélections régénérées : 129 pays, 91 complets (inchangé) ; 50 sélections modifiées, 83 nouveaux joueurs entrés (Mexique 6, Japon 5, Croatie 4, Chili, Uruguay, Venezuela 3…) ; Casemiro entre au Brésil ; Argentine, France, Espagne inchangées ; 5 sélections incomplètes renforcées (Bolivie 2 -> 3, Congo 1 -> 3, Estonie 3 -> 4, Jamaïque 12 -> 13, Kenya 5 -> 6). Aucun retraité international sélectionné (Messi et Griezmann, désormais argentin et français, écartés). Tchad et Îles Féroé : pas de sélection dans le classeur, ignorés (signalés).
- Tests : 5 dans `tests/test_apply_nations.py` ; suite complète 3566 passés, 14 désélectionnés.

## Comments

24/11/2026 — expert : APPROVED (empreinte ae200128). QC : VALIDÉ. Clôture journalisée : VALIDÉ.
- Remarques facultatives : correction des libellés sensible à la casse ; fichier vide mal signalé ; compte attendu de `CLAUDE.md` périmé (3 566).
- Tchad et Îles Féroé sans sélection tant qu'aucun onglet n'est créé pour eux (décision du propriétaire).
- Durée : estimée 80 min, réelle environ 55 min (− 31 %) : analyse 15, développement 15, tests 10, vérifications 15. Écart > 30 % : fichier reçu dans le même ordre que l'envoyé, aucune ambiguïté de clé ; un seul passage d'expert. Temps machine hors total : suite complète (15 min).
