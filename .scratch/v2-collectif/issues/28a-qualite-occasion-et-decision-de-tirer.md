# 28a: Qualité de l'occasion et décision de tirer

**Découpé du ticket 28 le 04/11/2026** (audit de granularité). Détail et points de vigilance : `28-occasion-et-issue-du-tir.md`, points 1, 3, 4 et 8.

**What to build:**

1. **Qualité de l'occasion, géométrique, pour chaque attaquant** : angle sous lequel il voit le but entre les poteaux, défenseurs dans ce cône, position du gardien, distance. « S'il touchait le ballon ici, quelle serait sa chance de marquer ? », y compris pour un joueur qui ne tire pas. Remplace la chance de but héritée du ticket 33 (divisée par deux tous les 5 m au-delà de 6 m).
2. **Tirer ou jouer encore** : le tireur décide sur la qualité **perçue** de l'occasion, comparée à la passe, dans le cadre du ticket 33.
3. **Fin de la dérogation A2** : Finishing seul règle la qualité d'exécution ; Composure réduit seulement la part de difficulté due à la pression. Nouvelle constante : pression sur le tir.
4. **Frontière Finishing / Long Shots** tranchée ici (distance liée à la surface, sans zone où les deux comptent) ; la frappe de loin est résolue par le même calcul.

L'issue reste celle d'aujourd'hui (but ou ballon au gardien, contre minimal du 33) jusqu'au 28b.

**Attributs :** Finishing, Composure (pression seulement), Long Shots, Decisions.

**Blocked by:** 33, 16, 29 (tous livrés) : démarrable.

**Bloque :** 28b, 28c ; `v2-attributs-restants/01` (l'issue d'une tête passe par ce calcul), `v2-attributs-restants/10a` ; 17, 19, 22a.

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Constantes produit (pression sur le tir, frontière Long Shots, perception de l'occasion) et critères chiffrés, sourcés ou « non trouvé », validés par le propriétaire avant le code
- [ ] Scène contrôlée : à distance égale, un défenseur dans le cône ou un angle fermé baisse mesurablement la qualité de l'occasion ; un gardien avancé la change
- [ ] Scène contrôlée : un porteur à faibles Decisions tire plus souvent sur une occasion médiocre qu'un porteur à Decisions élevées, à situation égale
- [ ] A2 levée : Composure n'agit que sous pression (test) ; test de rayon des attributs et carte (`docs/CARTE_ATTRIBUTS_V2.md`) à jour, sans double comptage Finishing / Long Shots
- [ ] En match (50 matchs, graine d'audit) : part des tirs dans la surface et qualité moyenne d'un tir hors penalty rapportées, comparées aux indicateurs à sourcer (ordres de grandeur du ticket 28) ; nombre de tirs par équipe rapporté (33 au ticket 33)
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique avant le ticket 22
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
