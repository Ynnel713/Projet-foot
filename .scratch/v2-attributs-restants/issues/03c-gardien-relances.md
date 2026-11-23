# 03c: Gardien : relances au pied et à la main

**Découpé du ticket 03 le 04/11/2026** (audit de granularité). Détail : `03-gardien-complet.md`.

**What to build:** relance au pied (Kicking : sortie de but, dégagement) et à la main (Throwing), dont le geste préféré « Uses Long Throw To Start Counter Attacks » (relance longue à la main, ticket 05).

**Attributs :** Kicking, Throwing (exécution). ADR 0002 (17/11/2026) : le choix de la relance (cible, court ou long) passe par un contexte de décision avec Vision et Decisions (poids à proposer) ; Kicking et Throwing ne règlent que la qualité du geste.

**Blocked by:** 01, 02 (a, b) (dépendances d'origine du ticket 03, sans doute levables : les sorties de but existent depuis `v2-collectif/29`) ; `v2-realisme/25b` (placement de construction, ajouté le 14/11/2026).

**Bloque :** `v2-collectif/22a`.

**Status:** livré (23/11/2026) par ses deux morceaux `03c1` et `03c2`, validés expert + QC. Découpé (23/11/2026, recommandation de Claude sous la délégation du propriétaire) en `03c1` (relance au pied, Kicking) et `03c2` (relance à la main, Throwing, avec l'état « ballon en main » à créer) : estimé à 2 h 40 en confiance faible, au-delà du seuil de 2 h. Le geste préféré « Uses Long Throw To Start Counter Attacks » est branché au `05a` (ligne « Gardien »). Clos quand les deux sont livrés.

## Acceptance criteria

- [ ] Kicking / Throwing : distance et précision des relances mesurablement liées à l'attribut
- [ ] Constantes produit et critères chiffrés validés par le propriétaire avant le code
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
