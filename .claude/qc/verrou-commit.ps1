<#
Verrou de commit/push.
Hook PreToolUse : recoit l'evenement JSON de l'outil sur stdin. Si une valeur
texte de tool_input ressemble a un "git commit" ou "git push" reel (voir
detection-git.ps1), verifie que :
  1. Le journal (qc/journal.jsonl) est lisible et bien forme (via append.ps1 -Action Validate).
  2. Le controle d'integrite (qc/integrite.ps1 -Action Verifier) est conforme
     (il couvre aussi cloture.py et expert.md, lances ou lus a l'etape 3).
  3. cloture.py verrou : la derniere ligne est une cloture "<ticket>/cloture"
     VALIDE complete, qui cite le dernier QC VALIDE du ticket, dont le rapport
     expert existe inchange et favorable, dont l'empreinte du code revu est
     toujours celle du depot, et dont les fichiers indexes sont ceux revus.
     Une entree QC VALIDE seule ne suffit jamais.
Bloque (exit 2) si une verification echoue OU est indeterminee. Necessite
Claude Code >= 2.1.295 pour que exit 2 + onFailure:"block" bloque reellement
le tour (pas de wrapper de secours ici, la version installee le supporte
nativement).

LIMITES, documentees : "git commit -a" ou "git commit <chemin>" commitent
l'arbre de travail et pas l'index (les fichiers revus restent proteges par
l'empreinte, pas les autres fichiers modifies) ; un commit lance depuis un
script n'est pas detecte (voir detection-git.ps1).

Toute exception non prevue est capturee et force un blocage. Un code de
sortie different de 2 est traite par Claude Code comme une erreur NON
bloquante - sans ce filet, un bug ici laisserait passer le commit au lieu
de le bloquer.
#>

$ErrorActionPreference = "Stop"

function Bloquer {
    param([string]$Raison)
    [Console]::Error.WriteLine("BLOQUE: $Raison")
    exit 2
}

try {
    $stdin = [Console]::In.ReadToEnd()
    if ([string]::IsNullOrWhiteSpace($stdin)) {
        exit 0
    }

    $evenement = $stdin | ConvertFrom-Json -ErrorAction Stop
    . (Join-Path $PSScriptRoot "detection-git.ps1")

    if (-not (Test-EvenementEstGit $evenement.tool_input)) {
        exit 0
    }

    $appendScript = Join-Path $PSScriptRoot "append.ps1"
    $integriteScript = Join-Path $PSScriptRoot "integrite.ps1"
    $journalPath = Join-Path $PSScriptRoot "journal.jsonl"

    if (-not (Test-Path $appendScript)) { Bloquer "append.ps1 introuvable, verification du journal impossible" }

    & $appendScript -Action Validate *> $null
    if ($LASTEXITCODE -ne 0) { Bloquer "journal illisible ou invalide (Validate code $LASTEXITCODE)" }

    if (-not (Test-Path $journalPath)) { Bloquer "journal absent, aucune sous-etape validee" }

    if (-not (Test-Path $integriteScript)) { Bloquer "integrite.ps1 introuvable, controle d'integrite impossible" }

    & $integriteScript -Action Verifier *> $null
    if ($LASTEXITCODE -ne 0) { Bloquer "controle d'integrite non conforme ou indetermine (code $LASTEXITCODE)" }

    $clotureScript = Join-Path $PSScriptRoot "..\skills\valider-ticket-simulafoot\cloture.py"
    if (-not (Test-Path $clotureScript)) { Bloquer "cloture.py introuvable, cloture du ticket inverifiable" }

    $sortie = @(& python -I $clotureScript verrou)
    if ($LASTEXITCODE -ne 0) { Bloquer "cloture du ticket non prouvee (code $LASTEXITCODE) : $($sortie -join ' | ')" }

    exit 0
} catch {
    Bloquer "erreur interne du verrou : $($_.Exception.Message)"
}
