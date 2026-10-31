<#
Controle d'integrite des fichiers du socle qualite.
Detecte une modification, une absence ou une nouveaute par rapport a des
empreintes SHA-256 de reference (qc/empreintes.json).

LIMITE IMPORTANTE : ceci ne protege pas contre une falsification deliberee.
Le fichier d'empreintes et les fichiers surveilles sont modifiables par la
meme personne ou le meme agent. Rien n'empeche de modifier un fichier puis
de relancer MettreAJour pour faire disparaitre toute trace de l'ecart. Ce
mecanisme detecte une modification non accompagnee d'une mise a jour
deliberee des empreintes - pas une falsification coordonnee par la meme main.
#>
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Verifier","MettreAJour")]
    [string]$Action
)

$ErrorActionPreference = "Stop"
$empreintesPath = Join-Path $PSScriptRoot "empreintes.json"
$fichiersSurveilles = @(
    "C:\Users\omariani\.claude\agents\controle-qualite.md",
    "C:\Users\omariani\.claude\skills\valider-etape\SKILL.md",
    (Join-Path $PSScriptRoot "append.ps1"),
    (Join-Path $PSScriptRoot "verrou-commit.ps1"),
    (Join-Path $PSScriptRoot "detection-git.ps1"),
    # cloture.py est execute par le verrou ; expert.md fixe les outils (lecture seule) de l'expert.
    (Join-Path $PSScriptRoot "..\skills\valider-ticket-simulafoot\cloture.py"),
    (Join-Path $PSScriptRoot "..\agents\expert.md")
)

function Get-EmpreintesReference {
    if (-not (Test-Path $empreintesPath)) {
        return [pscustomobject]@{ Ok = $false; Erreur = "Fichier d'empreintes absent : $empreintesPath"; Data = $null }
    }
    $raw = Get-Content -Path $empreintesPath -Encoding UTF8 -Raw
    if ([string]::IsNullOrWhiteSpace($raw)) {
        return [pscustomobject]@{ Ok = $false; Erreur = "Fichier d'empreintes vide."; Data = $null }
    }
    try {
        $data = $raw | ConvertFrom-Json -ErrorAction Stop
    } catch {
        return [pscustomobject]@{ Ok = $false; Erreur = "Fichier d'empreintes illisible (JSON invalide) : $($_.Exception.Message)"; Data = $null }
    }
    foreach ($prop in $data.PSObject.Properties) {
        if (-not (Get-Member -InputObject $prop.Value -Name "sha256" -ErrorAction SilentlyContinue)) {
            return [pscustomobject]@{ Ok = $false; Erreur = "Entree mal formee pour '$($prop.Name)' : champ sha256 manquant."; Data = $null }
        }
    }
    return [pscustomobject]@{ Ok = $true; Erreur = $null; Data = $data }
}

switch ($Action) {
    "Verifier" {
        $ref = Get-EmpreintesReference
        if (-not $ref.Ok) {
            Write-Output "ERREUR:$($ref.Erreur)"
            exit 2
        }
        $refData = $ref.Data
        $problemes = @()
        $conformes = @()

        foreach ($fichier in $fichiersSurveilles) {
            $presentSurDisque = Test-Path $fichier
            $presentDansRef = [bool](Get-Member -InputObject $refData -Name $fichier -ErrorAction SilentlyContinue)

            if (-not $presentSurDisque -and -not $presentDansRef) { continue }
            if (-not $presentSurDisque -and $presentDansRef) {
                $problemes += "MANQUANT:$fichier"
                continue
            }
            if ($presentSurDisque -and -not $presentDansRef) {
                $problemes += "NOUVEAU:$fichier (aucune empreinte de reference)"
                continue
            }
            $hashActuel = (Get-FileHash -Path $fichier -Algorithm SHA256).Hash
            $hashRef = $refData.$fichier.sha256
            if ($hashActuel -eq $hashRef) {
                $conformes += $fichier
            } else {
                $problemes += "MODIFIE:$fichier"
            }
        }

        if ($problemes.Count -eq 0) {
            Write-Output "CONFORME:$($conformes.Count) fichier(s) verifie(s), aucune anomalie."
            exit 0
        } else {
            Write-Output "ANOMALIES:"
            $problemes | ForEach-Object { Write-Output "  $_" }
            Write-Output "$($conformes.Count) fichier(s) conforme(s) par ailleurs."
            exit 2
        }
    }
    "MettreAJour" {
        $nouvelles = [ordered]@{}
        $manquants = @()
        foreach ($fichier in $fichiersSurveilles) {
            if (-not (Test-Path $fichier)) {
                $manquants += $fichier
                continue
            }
            $hash = (Get-FileHash -Path $fichier -Algorithm SHA256).Hash
            $nouvelles[$fichier] = @{ sha256 = $hash; maj = (Get-Date).ToUniversalTime().ToString("o") }
        }
        if ($manquants.Count -gt 0) {
            Write-Output "ERREUR:fichier(s) manquant(s), mise a jour annulee :"
            $manquants | ForEach-Object { Write-Output "  $_" }
            exit 2
        }
        $nouvelles | ConvertTo-Json | Set-Content -Path $empreintesPath -Encoding UTF8
        Write-Output "MAJ:$($nouvelles.Count) empreinte(s) enregistree(s)."
        exit 0
    }
}
