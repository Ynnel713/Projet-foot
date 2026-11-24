# 05f: Tir au-dessus de la barre par la vraie hauteur

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (la moitié des tirs non cadrés partent au-dessus). **Catégorie :** exécution.

**Constat vérifié :** le moteur est à plat ; le ticket `v2-collectif/35b` trace l'issue « au-dessus » sans trajectoire en hauteur ; `v2-hauteur-ballon/02a` (à faire) apporte la hauteur.

**What to build:** Le tir reçoit une hauteur de départ et un angle d'élévation issus de l'exécution (35b) ; avec la gravité de 02a, il passe sous ou au-dessus de la barre ; l'arrêt du 05b tient compte de la hauteur atteignable par le gardien.

**Ajout du 24/11/2026 (demande du propriétaire du 24/11/2026, éléments sur la frappe et la finition, point 4) : hauteur et trajectoire.** Trois hauteurs à distinguer, avec leurs conséquences pour le gardien : au ras du sol (long à aller chercher près du poteau, plongeon au sol), à mi-hauteur (plus facile à capter ou repousser pour un gardien bien placé), haute sous la barre ou en lucarne (détente, plus souvent repoussée). La portée du gardien selon la hauteur (05b, plongeon du `v2-attributs-restants/03d`) et le choix capter ou repousser (`v2-attributs-restants/03b2`, livré) lisent cette hauteur. Les tirs sur les montants sont au `v2-collectif/35c`.

**Ajout du 24/11/2026 (demande du propriétaire du 24/11/2026, éléments sur le gardien, point 3) : zones fortes et faibles du gardien.** Ballon à portée de main, au buste ou à la poitrine : le plus facile à capter ou repousser ; à mi-hauteur sur le côté (hanche), entre la portée debout et le plongeon, plus délicat à bloquer proprement qu'il n'y paraît ; au ras du sol près du poteau : plongeon bas et explosif ; sous la barre ou en lucarne : détente et allonge. La portée en hauteur se calcule ici, avec la taille du gardien (champ partagé du `v2-attributs-restants/03d`) ; Jumping Reach n'y entre pas (duel aérien, `v2-realisme/15b1`).

**Attributs :** aucun

**Blocked by:** 05b (Arrêt : le gardien atteint ou non le ballon); `v2-hauteur-ballon/02a`; `v2-collectif/35b`.

**Bloque :** rien.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 45 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **2 h** |

Confiance : moyenne. Hypothèses : hauteur de la barre et portée verticale du gardien : valeurs proposées.
Temps machine, non compté : suite complète (environ 40 min) ; mesure 50 matchs.

## Tests

- **Unitaires (scène contrôlée) :** tir avec élévation excessive : au-dessus ; tir tendu : sous la barre
- **Statistiques (séries de matchs) :** 50 matchs : part des tirs au-dessus

## Acceptance criteria

- [ ] Constantes produit et chiffres réels (sourcés ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Tirs au-dessus tracés avec leur hauteur au franchissement
- [ ] Arrêts tenant compte de la hauteur (scène)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
