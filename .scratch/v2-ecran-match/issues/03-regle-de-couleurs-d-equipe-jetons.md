# EM-03 — Règle de couleurs d'équipe + jetons (V) — 120 min (moyenne)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Objectif** : couleurs d'équipe fidèles aux clubs, toujours distinctes, numéros lisibles ; variables CSS d'équipe.
- **Problème** : bleu et or codés en dur, sans lien avec les clubs.
- **Résultat** : `teamColors.js` applique la règle de 2.2 ; variables `--team-home|away` et `-ink` posées à la racine ;
  les huit couleurs en dur remplacées.
- **Périmètre** : couleurs seulement (aucune mise en page).
- **Composants** : `utils/teamColors.js`, `V2Match.jsx`, `index.css` (jetons ajoutés).
- **Critères** : ΔE ≥ seuil entre équipes dans 100 % des paires testées (toutes les paires d'un échantillon de ≥ 40 clubs
  dont blanc/blanc, rouge/rouge, club vert, club noir) ; contraste du numéro ≥ 4,5:1 ; domicile garde sa principale dans
  100 % des cas ; résultat identique à chaque appel (pas d'aléa).
- **Tests** : `node --test` sur la règle (paires pathologiques, déterminisme).
- **Dépendances** : EM-02. **Constantes à valider avant code** : seuil ΔE (25), pas de décalage de clarté, anneau.
- **Risques** : club à la couleur proche du gazon ; un seuil trop strict dénature les clubs.

## Comments
