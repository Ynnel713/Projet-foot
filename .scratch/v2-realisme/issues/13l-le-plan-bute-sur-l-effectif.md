# 13l: Validation : le plan du coach bute sur les limites de l'effectif

**Chantier :** `v2-realisme` (audit des styles du coach du 26/11/2026, demande du propriétaire). **Priorité :** P1 (un style ne doit pas transformer des joueurs moyens en grande équipe). **Catégorie :** validation.

**Constat vérifié :** le ticket chapeau `v2-coach-et-gestion-de-match/01` pose le principe (« les attributs restent responsables de la qualité d'exécution ») mais aucun ticket ne le vérifie : 13b à 13f et 13i comparent un style à son absence sur la même équipe, jamais le même style sur deux effectifs.

**What to build:** Série appariée, même coach et mêmes styles (Pressing + Possession, puis Défensif + Contre-attaque), sur un effectif fort et un effectif faible (vitesse, endurance, technique, passes, décisions) contre le même adversaire neutre. Aucun nouveau mécanisme : si le plan ne grippe pas, le défaut est rapporté et renvoyé au levier concerné (13b à 13f, 20e).

**Attributs :** aucun nouveau (lecture des effets existants : Pace, Stamina, Technique, Passing, First Touch, Decisions).

**Blocked by:** 13b, 13c, 13e, 13f, 13k, 20e ; 01e (séries longues et intervalles).

**Dépendance non réciproque :** 20e n'est pas modifié par l'audit des styles du 26/11/2026 (ticket déjà couvert, laissé intact) ; sa ligne « Bloque » est à compléter de 13k et 13l à sa prochaine mise à jour.

**Bloque :** 13i.

**Dépendance non réciproque :** 01e (livré) n'est pas modifié par l'audit des styles du 26/11/2026 ; sa ligne « Bloque » ne cite pas 13l.

**Principe d'amplitude (propriétaire, 26/11/2026) :** l'impact des styles et de la note du coach reste modéré et réaliste. Un bon coach compense un peu un effectif moyen sans faire de miracle ; un coach moyen n'effondre pas une grande équipe. Le niveau de l'effectif reste le premier déterminant du résultat.

**Status:** à faire

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 15 min |
| Développement | 30 min |
| Tests unitaires et comportementaux | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 30** |

Confiance : moyenne. Hypothèses : les effectifs sont construits par la fabrique de scènes (01f) ou choisis dans la base.
Temps machine, non compté : suite complète (environ 40 min) ; quatre séries (avec et sans style, effectif fort et faible), taille fixée depuis 01e, au moins 400 matchs au total.

## Tests

- **Statistiques (séries de matchs) :** Pressing + Possession, effectif faible contre effectif fort : pertes de balle dans sa moitié de terrain, distance entre lignes après la 75e, réserve d'énergie moyenne après la 75e, récupérations hautes ; Défensif + Contre-attaque : réussite des passes verticales après récupération

## Acceptance criteria

- [ ] Critères chiffrés (écarts minimaux attendus) validés par le propriétaire avant la mesure ; taille d'échantillon fixée avant la mesure à partir de la dispersion du banc 01e (la comparaison de deux écarts, quatre séries avec et sans style sur chaque effectif, a une variance environ double d'un écart simple)
- [ ] Effectif faible : plus de pertes dans sa moitié, bloc plus étiré et réserve plus basse en fin de match que l'effectif fort, au même style (intervalle de confiance)
- [ ] L'effectif faible tire moins de bénéfice du style que l'effectif fort (écart d'indicateur de style avec et sans style)
- [ ] Amplitude : effectif moyen avec le coach le mieux noté de la base contre effectif moyen avec un coach neutre, puis grande équipe avec un coach de note basse contre la même avec un coach neutre : écart de différence de buts nettement inférieur à celui qui sépare l'effectif moyen de la grande équipe (seuil proposé au propriétaire avant la mesure)
- [ ] Durée réelle relevée, comparée à l'estimation et expliquée si l'écart dépasse 30 % (rapport de clôture et `docs/agents/suivi-estimations.md`)
- [ ] Déterminisme à graine fixée : mêmes empreintes sur deux exécutions
- [ ] Suite V2 verte ; V1 inchangée ; compte de la suite complète comparé à l'attendu de `CLAUDE.md`
