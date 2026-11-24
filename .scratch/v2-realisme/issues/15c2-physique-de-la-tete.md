# 15c2: Physique de la tête

**Chantier :** `v2-realisme` (découpe du `15c`, validée par le propriétaire le 24/11/2026). **Priorité :** P2. **Catégorie :** exécution.

**Constat vérifié :** un ballon joué de la tête est un contrôle (`possession.attempt_control`) posé au pied, puis une décision au sol ; Heading n'est lu nulle part (24/11/2026).

**What to build:** vitesse et direction du ballon après une tête : énergie du ballon entrant (restitution) plus poussée du cou ; dispersion d'angle et de dosage selon l'état au contact (au sol ou en l'air, élan, contact perdu ou bousculé, `12c` et `15b1`), l'angle de déviation demandé par rapport au ballon entrant et à l'orientation du corps, la hauteur d'impact et la vitesse du ballon entrant ; départ du ballon à la hauteur de la tête. Heading règle la précision du geste. Fatigue : via les notes (tickets 20).

**Attributs :** Heading (précision et puissance du geste, rôle nouveau).

**Blocked by:** `15c1`. **Bloque :** `15c3`, `15c4`, `15d`.

**Status:** à faire (constantes à proposer avant le code)

## Estimation

**Total (travail effectif) : 2 h 15**, détail posé au lancement. Confiance : moyenne. Temps machine, non compté : série de 50 matchs (environ 45 min), suite complète (environ 23 min).

## Acceptance criteria

- [ ] Constantes validées par le propriétaire avant le code
- [ ] Effet mesuré en scène et en série de 50 matchs, indicateurs globaux dans le bruit
- [ ] Rayon des attributs conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage ; test de rayon à jour
- [ ] Déterminisme à graine fixée ; suite complète au compte attendu ; durée réelle relevée

## Comments
