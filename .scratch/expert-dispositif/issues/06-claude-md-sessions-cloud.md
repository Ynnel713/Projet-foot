# 06: CLAUDE.md adapté au développement en session cloud

**What to build:** Le propriétaire ne code plus que dans les sessions cloud Linux (12/11/2026 : « je n'utiliserais que ce pc dorénavant pour coder? aucun autre », puis « oui pour tout », push compris ; « ok fais le ticket 5 puis le CLAUDE.md »). `CLAUDE.md` décrit encore le poste Windows (`simulafoot.bat`, OneDrive, jonction `ui/node_modules`, arbre en CRLF), une durée de suite de 40 min et la règle « push uniquement sur demande », dangereuse dans un conteneur éphémère. Mettre à jour ces lignes, et seulement elles, d'après ce qui a été constaté dans la session cloud.

**Blocked by:** 05.

**Status:** livré (12/11/2026), validé expert + QC

## Critères d'acceptation

- [x] Commandes : lancement API + UI par `uv run uvicorn` et `npm run dev --prefix ui` ; `simulafoot.bat` n'est plus la commande principale.
- [x] Tests : durée constatée en cloud (~10 min) ; attendu 2 754 passés, 0 ignoré, 14 désélectionnés, référencé au ticket expert-dispositif/05.
- [x] UI : `npm run build` OK et `npm run lint` 0 erreur (code 0), 5 avertissements, constatés en cloud le 12/11/2026 après `npm ci` : la ligne existante de CLAUDE.md est exacte, laissée telle quelle.
- [x] La ligne OneDrive / jonction / CRLF est remplacée par la description de l'environnement cloud `projet-foot` (PowerShell 7 et liens pour le verrou, venvs Python et NLG, dépendances npm) ; « garder les fins de ligne du fichier modifié » est conservé.
- [x] Push : sur la branche de travail de la session, juste après chaque commit validé ; jamais sur `main` sans demande.
- [x] Aucune autre règle de CLAUDE.md modifiée (diff limité à ces lignes).

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 10 min |
| Développement | 10 min |
| Tests | 5 min |
| Intégration et vérifications | 15 min |
| **Total (travail effectif)** | **40 min** |

Temps machine, hors total : aucun (mesures reprises des tickets 04 et 05 et de la session du 12/11/2026).

Confiance : élevée. Hypothèse : documentation seule, aucun code.

## Comments

**12/11/2026, passage 1.** Expert : APPROVED. QC : VALIDÉ. Clôture : VALIDÉ.
- A1 [facultatif] : durée du marqueur `integration` (~30 min) héritée du poste Windows, à remesurer en cloud.
- A2 [facultatif] : setup script de `projet-foot` décrit dans CLAUDE.md mais pas encore exécuté dans une session neuve ; à la première, vérifier `pwsh` et ses liens, `simulafoot_nlg/.venv`, `ui/node_modules`, et la suite à 2 754 passés, 0 ignoré.

**Durée.** Estimée 40 min, réelle environ 35 min (− 13 %, non chronométrée).
