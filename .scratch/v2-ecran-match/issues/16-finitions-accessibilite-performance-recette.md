# EM-16 — Finitions, accessibilité, performance, recette (V/E) — 120 min (moyenne)

**Status:** à faire (chantier validé par le propriétaire le 07/11/2026 ; constantes à proposer avant le code)

Chantier : `.scratch/v2-ecran-match/spec.md` (audit, direction artistique, décisions).

- **Résultat** : animations (score qui tombe, tiroirs), `prefers-reduced-motion`, focus clavier, libellés ARIA, contrastes
  vérifiés ; mesure finale de fluidité x1 et x8 sur build de production (avant/après EM-01) ; recette sur les 8 états.
- **Critères** : tableau de captures (début, en cours, but, mi-temps, fin, x1, x8, stats ouvertes) à 4 tailles ; images par
  seconde ≥ mesure d'avant ; contraste ≥ 4,5:1 sur tout texte utile ; `npm run build` et `npm run lint` sans régression.
- **Dépendances** : tous. **Risques** : accumulation de petits écarts : recette à faire avec vos yeux (points à vérifier à l'écran).

### Hors chantier (à ouvrir si vous le voulez)
- **EM-X1** Carton rouge réel : dépend du ticket moteur `v2-attributs-restants/09a` ; l'écran est déjà prêt (EM-12).
- **EM-X2** Écran de réglage du match (choix des clubs) : aujourd'hui deux `<select>` ; hors de votre périmètre actuel.
- **EM-X3** Vraie perspective (point de fuite) : exige de changer le contrat de projection avec le moteur d'affichage ;
  exclu.
- **EM-X4** Vrai momentum « danger créé » (qualité des tirs, `quality` de `ShotEvent`) : après EM-D2 et validation du calcul.

---

## Comments
