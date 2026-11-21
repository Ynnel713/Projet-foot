# 25i: Dédoublement du latéral

**Chantier :** `v2-realisme` (remarque du propriétaire du 21/11/2026, à l'écran : « le jeu était très axial et les joueurs s'obstinaient dans l'axe alors que des solutions existaient sur les côtés ; on voit donc très peu de centres, de dédoublements de latéraux »). **Priorité :** P1. **Catégorie :** décision.

**Constat vérifié (21/11/2026) :** le dédoublement figure dans le descriptif du `v2-collectif/14` (combinaisons collectives, livré) mais en est explicitement sorti (« Hors périmètre : dédoublement et changement de position (tickets 16 et 17) ») ; le 16 (livré) n'en contient pas, le 17 (surcharges, à faire) non plus ; aucune trace dans `v2engine/` (recherche « dédoubl », « overlap »). Le diagnostic du `18l` (section 56) compte 0,04 tir par équipe sur centre.

**What to build:** Quand l'ailier (ou le joueur du couloir extérieur) a le ballon ou le reçoit, fixé par un défenseur, le latéral du même côté peut partir à l'extérieur de lui, dans son dos, vers la ligne de fond ; le porteur voit cette option (passe dans la course) et peut la jouer, ou rentrer dans l'axe avec le défenseur fixé. Le latéral qui monte est compensé (défense préventive, `09g` ; compensation, `25f`). Mesure : dédoublements par match, part servis, centres et entrées dans la surface qui en suivent.

**Hors de ce ticket :** le centre lui-même (`v2-attributs-restants/01`, puis `11`) ; les surcharges (`v2-collectif/17`).

**Attributs :** Off the Ball et Work Rate du latéral (rayons existants : appel, volume), Teamwork (accepter de courir pour l'autre) ; Vision et Decisions du porteur (voir et choisir). Cumuls à justifier dans `docs/CARTE_ATTRIBUTS_V2.md` (ADR 0002).

**Constantes à proposer avant le code :** déclencheur (porteur fixé : distance du défenseur ; position du latéral), fréquence, limite de montée selon la défense préventive. Chiffre réel : dédoublements par match (non trouvé à ce jour).

**Blocked by:** `25a` (espaces candidats), `09b` (occupation de la largeur).

**Bloque :** `25h` (validation du jeu sans ballon).

**Status:** à faire (constantes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 25 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 30 min |
| Intégration et vérifications (50 matchs appariés) | 30 min |
| **Total (travail effectif)** | **2 h 15** |

Confiance : faible (dépend de 25a et 09b ; découpage à examiner avant le code : course du latéral, puis option du porteur). Hypothèses : la course passe par la sélection des appelants (`cerveau._runs_or_holds`) ; l'option par la passe dans la course existante (`possession.pass_aim`).
Temps machine, non compté : suite complète ; série appariée de 50 matchs.

## Acceptance criteria

- [ ] Constantes et chiffre réel validés par le propriétaire avant le code ; découpage examiné
- [ ] Scène : ailier fixé sur le côté, latéral derrière lui avec de l'espace : le latéral part à l'extérieur ; sans défense préventive suffisante, il reste
- [ ] Dédoublements par match et part servie mesurés ; centres et entrées dans la surface qui suivent rapportés
- [ ] Pas de régression mesurée (50 matchs appariés) : buts encaissés en transition, pertes, buts, tirs avec intervalle
- [ ] Déterminisme à graine fixée ; durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 %
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
