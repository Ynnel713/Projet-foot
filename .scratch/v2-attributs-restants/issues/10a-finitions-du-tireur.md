# 10a: Finitions : placée, puissante, enroulée, première intention

**Découpé du ticket 10 le 04/11/2026** (audit de granularité). Détail et points de vigilance (variété artificielle interdite, D-V03, pas de double comptage) : `10-types-de-finition.md`.

**What to build:** le tireur choisit **comment** finir selon la situation (distance, angle, gardien avancé ou sur sa ligne, pression, ballon reçu en mouvement ou arrêté) : frappe placée ou puissante (précision contre temps de réaction du gardien), enroulée (Technique), première intention ou volée (Technique), côté ouvert ou côté fermé selon la position du gardien (et le pied fort quand 04a est livré). Decisions choisit, Flair ajoute les options risquées, les gestes préférés biaisent seulement la fréquence.

**Attributs :** Decisions, Flair, Technique, Finishing ; gestes préférés en penchants.

**Blocked by:** `v2-collectif/28a` et `28b`, `v2-collectif/19` (principe des penchants), `v2-collectif/22c` (passe après la calibration).

**Bloque :** 10b.

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Constantes produit (poids de chaque type selon la situation) et critères validés par le propriétaire avant le code
- [ ] Test de cohérence (scènes fixes) : la frappe placée est plus fréquente avec Finishing élevé ; la première intention suit un ballon reçu en mouvement ; le côté fermé est choisi quand le gardien couvre le côté ouvert
- [ ] Chaque type apparaît au moins une fois sur 50 matchs et aucun ne domine
- [ ] Diversité des buts mesurée sur 50 matchs ou plus (zone × type × issue × origine), comparée avant / après
- [ ] Type de finition tracé et rejoué par le rendu, sans changer l'issue
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée

## Limite d'angle du 14a2b (27/11/2026)

**Limite d'angle de départ héritée du `v2-realisme/14a2b` (note du propriétaire, 27/11/2026)** : La limite de 45° (vz <= vh * tan(45°)) imposée au 14a2b est un garde-fou moteur contre les trajectoires aberrantes. Elle interdit les lobs verticaux. Lors de l'implémentation des gestes spécifiques (Lob au 10a, centres au 11), cette limite devra être contournée. Un geste explicitement identifié comme 'Lob' ou 'Chandelle' devra avoir l'autorisation de dépasser cette limite d'angle pour reproduire la réalité du terrain. Ici : le lob (ou piqué) au-dessus d'un gardien avancé est un geste de finition ; il doit pouvoir partir au-delà de 45°. Au 14a2b, la borne ne s'applique qu'aux passes et relances aériennes (`hauteur.max_launch_vz` dans `launch_vz`), pas aux tirs (`launch_vz_to`) : vérifier à l'ouverture du 10a par quel chemin le lob est frappé avant de prévoir le contournement.
