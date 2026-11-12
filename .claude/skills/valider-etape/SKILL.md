---
name: valider-etape
description: Soumet un changement de code (diff ou fichiers) au sous-agent controle-qualite, affiche son verdict VALIDÉ/REFUSÉ/BLOQUÉ justifié, et l'enregistre dans le journal de traçabilité du projet (qc/journal.jsonl). Version sous-phase 0.2 : journal append-only et recalcul du nombre de refus par sous-étape — pas encore de hash d'intégrité, pas de hook Git, pas de seuil bloquant automatique. Utilise sur /valider-etape, "valide cette étape", "fais relire ce changement".
---

Version 0.2 : revue + journal de traçabilité. Pas encore construit : vérification d'intégrité par hash, hook Git empêchant un commit non validé, passage automatique en BLOQUÉ au-delà d'un seuil de refus. Ne simule aucun de ces mécanismes.

**Le journal (`.claude/qc/journal.jsonl`, propre au projet courant) est un registre de traçabilité, pas une garantie d'intégrité.** Il n'est protégé par aucun hash ni aucun verrou à ce stade — rien n'empêche techniquement une modification directe du fichier ou du script `append.ps1`. Ne jamais présenter ce journal comme inviolable ou comme une preuve infalsifiable.

## Process

1. Détermine l'identifiant de la sous-étape (`S-xx` du PLAN.md si disponible, sinon demande-le à l'utilisateur — jamais inventé).
2. Détermine ce qui doit être revu : un diff git réel (`git diff`, `git diff --staged`) si on travaille sur un changement en cours, ou le contenu fourni directement par l'utilisateur pour un cas de test.
3. Si l'exigence ou le critère d'acceptation visé est connu (PRD, TRD, ou énoncé par l'utilisateur), joins-le. Sinon, dis-le explicitement au sous-agent plutôt que d'en inventer un.
4. Invoque le sous-agent `controle-qualite` avec uniquement le diff/contenu et l'exigence s'il y en a — jamais l'historique de la conversation qui a produit le changement.
5. Affiche le verdict et sa justification telle que rendue par le sous-agent, sans la reformuler ni l'adoucir.
6. Enregistre le verdict dans le journal du projet courant :
   `powershell -File .claude/qc/append.ps1 -Action Append -SousEtape "<id>" -Verdict "<VALIDÉ|REFUSÉ|BLOQUÉ>" -Justification "<texte>"`
   Si `.claude/qc/append.ps1` n'existe pas dans le projet courant, dis-le à l'utilisateur plutôt que d'improviser un autre mécanisme d'écriture.
7. Si le verdict est REFUSÉ, recalcule le nombre de refus cumulés pour cette sous-étape :
   `powershell -File .claude/qc/append.ps1 -Action CountRefus -SousEtape "<id>"`
   Si la sortie commence par `ERREUR:` (code de sortie 2) : le journal contient des lignes invalides, **le nombre n'est pas fiable** — dis-le explicitement à l'utilisateur, n'affiche aucun chiffre. Seule une sortie `REFUS:<n>` (code de sortie 0) est un compteur exploitable, à afficher à titre d'information. **Aucun seuil n'est appliqué automatiquement en 0.2** — pas de passage forcé en BLOQUÉ, ça viendra dans une sous-phase ultérieure si elle est autorisée.

## Règles

- N'écrit jamais directement dans `journal.jsonl` — toujours via `append.ps1`.
- Ne transforme jamais un BLOQUÉ en VALIDÉ par défaut, ni un REFUSÉ en simple remarque.
- Ne prétend jamais que le journal protège contre une falsification délibérée.
