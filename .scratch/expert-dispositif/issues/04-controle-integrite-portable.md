# 04: Contrôle d'intégrité portable (Windows et Linux)

**What to build:** Le contrôle d'intégrité du socle qualité (`.claude/qc/integrite.ps1`, références dans `.claude/qc/empreintes.json`) repérait ses fichiers par des chemins absolus propres au poste Windows (`C:\Users\omariani\...\OneDrive...`). Hors de ce poste (session cloud Linux, autre PC), tous les fichiers sont déclarés MANQUANT ou NOUVEAU, le verrou de commit bloque tout, et aucun ticket ne peut être commité. Demande du propriétaire (12/11/2026) : « faisons le nécessaire pour que tout fonctionne d'ici ».

Changement :
- Les fichiers surveillés sont repérés par leur chemin relatif à la racine du dépôt, avec `/` (`.claude/qc/append.ps1`, ..., `.claude/agents/controle-qualite.md`, `.claude/skills/valider-etape/SKILL.md`) ; les clés de `empreintes.json` sont ces chemins relatifs. Les empreintes SHA-256 ne changent pas pour les fichiers non modifiés.
- Les exemplaires globaux (`~/.claude/agents/controle-qualite.md`, `~/.claude/skills/valider-etape/SKILL.md`) ne sont plus comparés à une référence propre au poste : s'ils existent, ils doivent être identiques octet pour octet à l'exemplaire du dépôt (sinon anomalie DIVERGENT) ; absents, ils sont ignorés. Cela garde la protection sur le poste Windows (où le skill global peut l'emporter sur celui du dépôt) et traite le point « deux exemplaires qui peuvent diverger » du ticket 03.
- Le banc `test-verrou.sh` copie aussi ces deux fichiers dans son dépôt jetable.
- Hors dépôt : l'environnement cloud `projet-foot` installe PowerShell 7 et les liens `powershell` / `powershell.exe` vers `pwsh` (setup script), pour que le hook et le skill `valider-etape` tournent sous Linux.

**Blocked by:** 03.

**Status:** livré (12/11/2026), validé expert + QC

## Critères d'acceptation

- [x] `integrite.ps1 -Action Verifier` : CONFORME, 7 fichiers, sous Linux (session cloud) ; aucun chemin absolu ni nom de poste dans `integrite.ps1` et `empreintes.json`.
- [x] Les 7 empreintes SHA-256 de `empreintes.json` sont identiques aux précédentes (aucun fichier surveillé modifié ; `integrite.ps1` n'est pas dans la liste).
- [x] Banc `test-verrou.sh` sous Linux : 39 réussis, 0 échoué (avant : 32 réussis / 4 échoués sur 36, les 4 cas favorables S0, I14, I26, I33 bloqués par l'intégrité).
- [x] Nouveaux cas du banc : I36 `controle-qualite.md` du dépôt modifié → bloqué (2) ; I37 exemplaires globaux identiques → passe (0) ; I38 exemplaire global divergent → bloqué (2). I37-I38 ne s'exécutent que si PowerShell lit `$HOME` dans `HOME` (pwsh Linux/macOS) ; sous Windows le banc les annonce NON EXÉCUTÉS.
- [x] `cloture.py --selftest` : OK.
- [x] Suite complète (code Python non touché, contrôle de non-régression de l'environnement cloud) : 2 749 passés, 5 ignorés, 14 désélectionnés (2 749 + 5 = 2 754). Les 5 ignorés sont les tests NLG (`skipif` sur `simulafoot_nlg/.venv/Scripts/python.exe`, chemin Windows) ; écart accepté par le propriétaire le 12/11/2026 (« oui pour tout »), portabilité traitée au ticket 05.
- [x] ~~Vérifier sur le poste Windows : `integrite.ps1 -Action Verifier` CONFORME avec Windows PowerShell 5.1.~~ Sans objet : le propriétaire ne code plus que dans les sessions cloud (12/11/2026 : « je n'utiliserais que ce pc dorénavant pour coder? aucun autre », puis « oui pour tout »). Si un poste Windows est réutilisé un jour, lancer cette vérification avant le premier commit (réserve A1 de l'expert).

## Estimation

| Poste | Durée |
|---|---|
| Analyse | 20 min |
| Développement | 20 min |
| Tests | 15 min |
| Intégration et vérifications | 25 min |
| **Total (travail effectif)** | **1 h 20** |

Temps machine, hors total : suite complète ~40 min, banc du verrou ~2 min.

Confiance : moyenne. Hypothèses : `cloture.py` et `verrou-commit.ps1` fonctionnent déjà sous pwsh/Linux (banc : seuls les cas bloqués par l'intégrité échouent) ; pas de différence de comportement entre Windows PowerShell 5.1 et pwsh 7 sur `Join-Path`, `Get-FileHash`, `ConvertFrom-Json`.

## Comments

**12/11/2026, passage 1.** Expert : APPROVED_WITH_RESERVATIONS. QC : BLOQUÉ (suite 2 749 + 5 ignorés au lieu de 2 754 passés ; vérification PS 5.1 non faite). Pas de décision de clôture.
- A1 [réserve] : poste Windows non vérifié (PS 5.1, fins de ligne CRLF sans `.gitattributes`). Acceptée par le propriétaire : « je n'utiliserais que ce pc dorénavant pour coder? aucun autre », puis « oui pour tout ». Consigne si un poste Windows revient : `integrite.ps1 -Action Verifier` CONFORME:7 sans DIVERGENT avant le premier commit ; si écart CRLF, `.gitattributes` avec `.claude/** -text`.
- A2 [facultatif] : integrite.ps1 et empreintes.json ne se surveillent pas eux-mêmes (limite préexistante, documentée).
- A3 [facultatif] : le banc utilise le `$HOME` réel hors I37-I38 ; un `~/.claude` divergent sur la machine de test ferait échouer S0, I14, I26, I33.

**12/11/2026, passage 2.** Critères 6 et 7 reformulés sur décision du propriétaire (« oui pour tout ») ; ticket 05 créé pour les tests NLG. Code inchangé (même empreinte 766dad87). Expert : APPROVED_WITH_RESERVATIONS (rapport du passage 1, réserve A1 acceptée). QC : VALIDÉ. Clôture : VALIDÉ.

**Durée.** Estimée 1 h 20, réelle environ 1 h 40 (+ 25 %, non chronométrée) : installation de PowerShell dans la session cloud et deuxième passage du QC.
