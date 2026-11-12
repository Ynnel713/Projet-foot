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
# Racine du depot (.claude/qc -> .claude -> racine). Les fichiers surveilles sont reperes
# par leur chemin relatif a cette racine, avec "/" : memes cles sous Windows et Linux.
$racineDepot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$fichiersSurveilles = @(
    ".claude/agents/controle-qualite.md",
    ".claude/skills/valider-etape/SKILL.md",
    ".claude/qc/append.ps1",
    ".claude/qc/verrou-commit.ps1",
    ".claude/qc/detection-git.ps1",
    # cloture.py est execute par le verrou ; expert.md fixe les outils (lecture seule) de l'expert.
    ".claude/skills/valider-ticket-simulafoot/cloture.py",
    ".claude/agents/expert.md"
)
# Exemplaires globaux du poste (~/.claude), qui peuvent l'emporter sur ceux du depot :
# s'ils existent, ils doivent etre identiques a l'exemplaire du depot ; absents, ignores.
$exemplairesGlobaux = @(
    @{ Global = (Join-Path $HOME ".claude/agents/controle-qualite.md"); Depot = ".claude/agents/controle-qualite.md" },
    @{ Global = (Join-Path $HOME ".claude/skills/valider-etape/SKILL.md"); Depot = ".claude/skills/valider-etape/SKILL.md" }
)

function Get-CheminDepot {
    param([string]$Relatif)
    return (Join-Path $racineDepot $Relatif)
}

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
            $chemin = Get-CheminDepot $fichier
            $presentSurDisque = Test-Path $chemin
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
            $hashActuel = (Get-FileHash -Path $chemin -Algorithm SHA256).Hash
            $hashRef = $refData.$fichier.sha256
            if ($hashActuel -eq $hashRef) {
                $conformes += $fichier
            } else {
                $problemes += "MODIFIE:$fichier"
            }
        }

        foreach ($paire in $exemplairesGlobaux) {
            if (-not (Test-Path $paire.Global)) { continue }
            $cheminDepot = Get-CheminDepot $paire.Depot
            if (-not (Test-Path $cheminDepot)) { continue }  # deja signale MANQUANT ci-dessus
            $hashGlobal = (Get-FileHash -Path $paire.Global -Algorithm SHA256).Hash
            $hashDepot = (Get-FileHash -Path $cheminDepot -Algorithm SHA256).Hash
            if ($hashGlobal -ne $hashDepot) {
                $problemes += "DIVERGENT:$($paire.Global) differe de $($paire.Depot)"
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
            $chemin = Get-CheminDepot $fichier
            if (-not (Test-Path $chemin)) {
                $manquants += $fichier
                continue
            }
            $hash = (Get-FileHash -Path $chemin -Algorithm SHA256).Hash
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
