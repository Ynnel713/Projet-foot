<#
Journal de controle qualite (qc/journal.jsonl).
Tracabilite : append-only par convention de ce script. La protection contre
une falsification directe du fichier est assuree par integrite.ps1 (hash),
pas par ce script.
#>
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Append","CountRefus","Read","Validate")]
    [string]$Action,

    [string]$SousEtape,
    [ValidateSet("VALIDÉ","REFUSÉ","BLOQUÉ")]
    [string]$Verdict,
    [string]$Justification
)

$ErrorActionPreference = "Stop"
$journalPath = Join-Path $PSScriptRoot "journal.jsonl"
$champsObligatoires = @("id","sous_etape","horodatage","verdict","justification")
$verdictsValides = @("VALIDÉ","REFUSÉ","BLOQUÉ")

function Read-JournalEntries {
    $entries = @()
    $invalidLines = @()
    if (-not (Test-Path $journalPath)) {
        return [pscustomobject]@{ Entries = $entries; Invalid = $invalidLines }
    }
    $lineNumber = 0
    foreach ($line in Get-Content -Path $journalPath -Encoding UTF8) {
        $lineNumber++
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        try {
            $obj = $line | ConvertFrom-Json -ErrorAction Stop
        } catch {
            $invalidLines += "Ligne $lineNumber : JSON illisible - $($_.Exception.Message)"
            continue
        }
        $missing = @()
        foreach ($field in $champsObligatoires) {
            if (-not (Get-Member -InputObject $obj -Name $field -ErrorAction SilentlyContinue)) {
                $missing += $field
            }
        }
        if ($missing.Count -gt 0) {
            $invalidLines += "Ligne $lineNumber : champs manquants ($($missing -join ', '))"
            continue
        }
        if ($verdictsValides -notcontains $obj.verdict) {
            $invalidLines += "Ligne $lineNumber : verdict invalide ('$($obj.verdict)')"
            continue
        }
        $entries += $obj
    }
    return [pscustomobject]@{ Entries = $entries; Invalid = $invalidLines }
}

switch ($Action) {
    "Append" {
        if (-not $SousEtape -or -not $Verdict -or -not $Justification) {
            Write-Error "Append exige -SousEtape, -Verdict et -Justification."
            exit 1
        }
        $entry = [ordered]@{
            id            = [guid]::NewGuid().ToString()
            sous_etape    = $SousEtape
            horodatage    = (Get-Date).ToUniversalTime().ToString("o")
            verdict       = $Verdict
            justification = $Justification
        }
        $json = $entry | ConvertTo-Json -Compress
        Add-Content -Path $journalPath -Value $json -Encoding UTF8
        Write-Output "AJOUTE:$($entry.id)"
        exit 0
    }
    "CountRefus" {
        if (-not $SousEtape) { Write-Error "CountRefus exige -SousEtape."; exit 1 }
        $result = Read-JournalEntries
        if ($result.Invalid.Count -gt 0) {
            Write-Warning "Journal contient des lignes invalides, compteur non fiable :"
            $result.Invalid | ForEach-Object { Write-Warning "  $_" }
            Write-Output "ERREUR:journal invalide, compteur non fiable"
            exit 2
        }
        $matches = @($result.Entries | Where-Object { $_.sous_etape -eq $SousEtape -and $_.verdict -eq "REFUSÉ" })
        Write-Output "REFUS:$($matches.Count)"
        exit 0
    }
    "Read" {
        $result = Read-JournalEntries
        if ($result.Invalid.Count -gt 0) {
            Write-Warning "Lignes invalides detectees :"
            $result.Invalid | ForEach-Object { Write-Warning "  $_" }
        }
        if ($SousEtape) {
            $result.Entries | Where-Object { $_.sous_etape -eq $SousEtape } | ConvertTo-Json
        } else {
            $result.Entries | ConvertTo-Json
        }
        exit 0
    }
    "Validate" {
        $result = Read-JournalEntries
        if ($result.Invalid.Count -eq 0) {
            Write-Output "OK:$($result.Entries.Count) entree(s) valide(s), aucune ligne invalide."
            exit 0
        } else {
            Write-Output "PROBLEMES:"
            $result.Invalid | ForEach-Object { Write-Output "  $_" }
            Write-Output "$($result.Entries.Count) entree(s) valide(s) malgre tout."
            exit 2
        }
    }
}
