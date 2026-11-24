# 32: Garde-fous de la frappe en match

**Chantier :** `v2-realisme` (demande du propriétaire du 24/11/2026, éléments sur la frappe et la finition, point 6 : « Mesures et garde-fous de réalisme sur match »). **Priorité :** P1. **Catégorie :** validation.

**Constat vérifié (24/11/2026) :** le banc mesure déjà tirs par équipe, part cadrée, conversion, tirs par distance et xG (`scripts/measure_v2.py`, `docs/INDICATEURS_V2.md`) ; la validation des tirs du `05g` (livré) a été faite une fois, sans garde permanente ; aucune mesure des tirs absurdes (frappe lointaine alors qu'un partenaire est bien mieux placé) ni des occasions franches refusées. Niveau actuel (série « après » de 50 matchs du `15c1`, refaite après revue, sortie de `scripts.bench_series` du 24/11/2026 ; buts et tirs repris dans `docs/INDICATEURS_V2.md` § 81, écarts appariés dans `.scratch/v2-realisme/mesures/15c1-comparaison.txt` ; part cadrée et conversion lues dans la sortie de la série, à relever de nouveau au lancement) : 4,86 buts par match, 15,3 tirs par équipe, 37,7 % cadrés, conversion 15,8 % (repères réels de Ligue 1, de mémoire et à sourcer : environ 2,7 buts, 12 à 13 tirs, 33 à 35 % cadrés, 10 à 11 %).

**What to build:** des indicateurs et des scènes de garde que chaque ticket du chantier de la frappe (`v2-collectif/34a` à `35a`, `v2-realisme/05f`, `05i`, `05k`, `03l`, `v2-attributs-restants/10a`, `04a`) rapporte avant et après, sans réglage ici (le niveau se règle au `v2-collectif/22c`) :
- **Volumes et répartition** : tirs par match et par équipe, part cadrée, tirs dans la surface et hors de la surface (et au-delà de 25 m), conversion par zone, buts par rapport à l'xG des occasions créées, part des buts par origine (jeu placé, contre, centre, coup de pied arrêté, ballon dévié).
- **Qualité des situations** :
  - « tir-passe » : tirs au-delà de 25 m (et de 30 m) alors qu'un partenaire non hors-jeu avait une occasion nettement meilleure et une passe sûre ; suites de tirs lointains de la même équipe dans une même possession ;
  - occasions franches refusées : porteur à 10 m ou moins du but, angle ouvert, sans défenseur au contact ni entre lui et le but, qui ne tire pas (et ce qu'il fait à la place) ;
  - frappes dans de mauvaises conditions : tir en déséquilibre, dos au but, sur le mauvais pied (quand les tickets correspondants sont livrés).
- **Stabilité globale** : passes réussies, possession, attaques placées et contres, arrêts, ballons repoussés et seconds ballons, rapportés à côté.
- **Scènes de garde** (tests permanents) : seul à 8 m face au but, il tire presque toujours ; à 35 m avec un partenaire démarqué dans la surface et une passe sûre, il ne tire presque jamais ; une frappe facile réussit parfois même pour un mauvais tireur, une frappe difficile échoue parfois même pour un très bon (règle « jamais binaire »).

**Attributs :** aucun.

**Expertise :** le relevé est à faire **avant** les tickets de geste : il sert de point de départ et de garde à chacun ; les seuils des scènes et des indicateurs absurdes sont des constantes de mesure, proposées au propriétaire avant le code.

**Blocked by:** rien. **Bloque :** rien (recommandé avant `v2-collectif/34a`, `35a`, `v2-realisme/05f`).

**Status:** à faire (seuils des indicateurs et des scènes à proposer avant le code)

## Estimation

| Poste | Durée |
|---|---|
| Analyse et compréhension du code | 20 min |
| Développement (indicateurs du banc) | 40 min |
| Tests (scènes de garde) | 25 min |
| Intégration et vérifications | 20 min |
| **Total (travail effectif)** | **1 h 45** |

Confiance : moyenne. Temps machine, non compté : série de 50 matchs (environ 45 min), suite complète (environ 23 min).

## Acceptance criteria

- [ ] Seuils validés par le propriétaire avant le code
- [ ] Moteur inchangé (mêmes empreintes à graine fixée)
- [ ] Indicateurs ajoutés au banc et rapportés sur 50 matchs (point de départ du chantier de la frappe) ; repères réels sourcés ou « non trouvé »
- [ ] Scènes de garde ajoutées à la suite et vertes sur le moteur actuel, ou écart signalé au propriétaire
- [ ] Durée réelle relevée

## Comments
