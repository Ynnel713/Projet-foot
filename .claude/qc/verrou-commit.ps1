<#
Verrou de commit/push.
Hook PreToolUse : recoit l'evenement JSON de l'outil sur stdin. Si une valeur
texte de tool_input ressemble a un "git commit" ou "git push" reel (voir
detection-git.ps1), verifie que :
  1. Le journal (qc/journal.jsonl) est lisible et bien forme (via append.ps1 -Action Validate).
  2. Sa derniere ligne porte le verdict VALIDE (lue directement, pas via Read,
     pour eviter un reparsing multi-ligne fragile).
  3. Le controle d'integrite (qc/integrite.ps1 -Action Verifier) est conforme.
Bloque (exit 2) si une verification echoue OU est indeterminee. Necessite
Claude Code >= 2.1.295 pour que exit 2 + onFailure:"block" bloque reellement
le tour (pas de wrapper de secours ici, la version installee le supporte
nativement).

LIMITE IMPORTANTE, documentee et non cachee : une derniere entree VALIDE ne
prouve pas que le diff reellement commite a ete relu - rien ne lie une
sous-etape du journal aux fichiers effectivement modifies.

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
    $lignes = @(Get-Content -Path $journalPath -Encoding UTF8 | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($lignes.Count -eq 0) { Bloquer "journal vide, aucune sous-etape validee" }

    $derniere = $lignes[-1] | ConvertFrom-Json -ErrorAction Stop
    if ($derniere.verdict -ne "VALIDÉ") { Bloquer "derniere entree du journal = '$($derniere.verdict)', pas VALIDÉ" }

    if (-not (Test-Path $integriteScript)) { Bloquer "integrite.ps1 introuvable, controle d'integrite impossible" }

    & $integriteScript -Action Verifier *> $null
    if ($LASTEXITCODE -ne 0) { Bloquer "controle d'integrite non conforme ou indetermine (code $LASTEXITCODE)" }

    exit 0
} catch {
    Bloquer "erreur interne du verrou : $($_.Exception.Message)"
}
