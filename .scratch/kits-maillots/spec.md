# Chantier « kits-maillots » — couleurs de maillot réelles (09/11/2026)

Demande du propriétaire (09/11/2026) : utiliser les packs de kits téléchargés (16 archives FM Slovakia, saison 2025/26,
« FC'12 kitpack » par einherjer83) pour donner aux clubs et sélections leurs vraies couleurs. Décision du propriétaire :
**seules les couleurs sont retenues et versionnées** (« je souhaite tout avoir dans git, peux tu retenir les couleurs ?
ça suffira ») ; aucune image dans le dépôt ni dans l'application.

- Source : `~/Downloads/*.zip` (hors dépôt), lue par `scripts/extract_kit_colors.py` sans extraction.
- Cible : `src/ligue1sim/kits.py` (`CLUB_KIT`), puis `/api/v2/lineup` (EM-02) et l'écran (EM-03).
- Crédit demandé par le readme des packs : einherjer83 + FM Slovakia (cité dans `kits.py` et le script).

| Ticket | Objet | Estimation |
|---|---|---|
| KM-01 | Extraction des couleurs + correspondance fichiers -> clubs + planche de contrôle | 120 min |
| KM-02 | Intégration dans `kits.py` (domicile + extérieur) et l'API V2 | 120 min |
| KM-03 | Sélections nationales | 90 min |
