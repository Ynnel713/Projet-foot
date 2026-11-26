# 13i: Validation des styles : des équipes différentes, pas meilleures

**Chantier :** `v2-realisme` (audit de réalisme du 05/11/2026, `spec.md`). **Priorité :** P1 (le style déplace le risque, il ne doit pas créer de niveau). **Catégorie :** validation.

**Constat vérifié :** critère du ticket `v2-coach-et-gestion-de-match/01` : différence de buts non systématiquement en faveur d'un style.

**What to build:** Série appariée : chaque style contre le même adversaire neutre, 200 matchs par style (01e) ; indicateurs de style et différence de buts avec intervalle de confiance. Adaptation au score : tickets `v2-collectif/21` et `v2-coach-et-gestion-de-match/02`, non dupliqués ici.

**Attributs :** aucun

**Blocked by:** 13b (Style Pressing); 13c (Style Défensif); 13d (Style Offensif); 13e (Style Contre-attaque); 13f (Style Possession et tempo); 13g (Consigne de largeur); 13h (Rôles cohérents avec la formation); 13j (Arbitrage des styles par phase); 13k (Note du coach); 13l (Le plan bute sur l'effectif); 01e (Banc : séries de 500 à 2 000 matchs, parallélisées, avec intervalles de confiance).

**Bloque :** rien.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 50 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 55** |

Confiance : moyenne. Hypothèses : temps machine important (1 000 matchs).
Temps machine, non compté : suite complète (environ 40 min) ; série de 1 000 matchs.

## Tests

- **Statistiques (séries de matchs) :** 1 000 matchs appariés : rapport par style, par phase de jeu, plus une série « coach à 2 styles » contre « coach à 4 styles contenant les mêmes 2 »

## Acceptance criteria

- [ ] Indicateurs définis dans `docs/INDICATEURS_V2.md` et ajoutés à `scripts/v2_indicators.py` avant la mesure : PPDA (passes adverses par action défensive dans les 60 % de terrain adverses), récupérations hautes (tiers adverse), part de possession, passes courtes, hauteur moyenne de circulation du ballon, vitesse de progression verticale après récupération, part des tirs issus de transitions rapides, distance entre lignes, tirs concédés depuis l'axe, distance à haute intensité
- [ ] Signature attendue de chaque style, dans le sens attendu (intervalle de confiance) : Possession, possession, passes courtes et hauteur de circulation en hausse ; Contre-attaque, progression verticale après récupération et tirs de transition en hausse ; Pressing, PPDA en baisse (pression plus forte) et récupérations hautes en hausse, avec distance à haute intensité et occasions concédées dans le dos en hausse ; Défensif, hauteur du bloc, distance entre lignes et tirs concédés depuis l'axe en baisse ; Offensif, joueurs dans la surface adverse en hausse
- [ ] Coach à 4 styles contre le coach à 2 styles qu'il contient : sur les indicateurs des deux styles communs, pas plus extrême, à une marge de non-infériorité fixée avant la mesure (budget de 13j) ; les indicateurs des styles ajoutés ne sont pas comparés
- [ ] Possession seul : joueurs engagés dans le contre-pressing en hausse par rapport au neutre (13j)
- [ ] Chaque style mesurablement différent
- [ ] Amplitude modérée (principe du propriétaire, 26/11/2026) : écart de différence de buts entre un style et le neutre petit devant l'écart dû au niveau d'effectif (seuil proposé avant la mesure)
- [ ] Aucun style systématiquement gagnant (intervalle de confiance)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`

## Complément de l'audit des styles du coach (26/11/2026)

Source : audit des styles demandé par le propriétaire (26/11/2026). Banc de validation des identités tactiques complété : liste d'indicateurs, signature attendue par style, contrôle du budget tactique (13j). **PPDA** : un pressing plus intense le fait **baisser** (moins de passes adverses par action défensive), pas monter. Adaptation au score et fatigue toujours hors de ce ticket (`v2-coach-et-gestion-de-match/02`, `v2-realisme/20e`). Estimation portée de 1 h 40 à 1 h 55 (indicateurs à écrire).
