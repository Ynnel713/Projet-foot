<#
Detection de "ce texte invoque-t-il git commit/push", dot-sourcee par
verrou-commit.ps1. Voir les limites documentees : pas un parseur shell
complet (alias, substitutions de commande, interpreteurs imbriques et
guillemets contenant un separateur avant la sous-commande non couverts).
#>

function Test-CommandeGit {
    param([string]$Texte)

    if ([string]::IsNullOrWhiteSpace($Texte)) { return $false }

    # -P/--no-pager (booleen) et --exec-path (valeur optionnelle, uniquement
    # via = selon git) sont volontairement ABSENTS de cette liste : ils ne
    # consomment jamais de token separe. Les y mettre a tort fait sauter la
    # sous-commande qui suit (bug trouve et corrige : "git -P commit" et
    # "git --exec-path commit" passaient inaperçus).
    $optionsAvecValeurSeparee = @(
        '-C', '--git-dir', '--work-tree', '-c', '--namespace',
        '--super-prefix', '--config-env'
    )

    $segments = @($Texte)
    foreach ($sep in @(';', '&&', '||', '|', "`n")) {
        $segments = $segments | ForEach-Object { $_ -split [regex]::Escape($sep) }
    }

    foreach ($segment in $segments) {
        if ([string]::IsNullOrWhiteSpace($segment)) { continue }

        $tokens = [regex]::Matches($segment, '"[^"]*"|''[^'']*''|\S+') |
            ForEach-Object {
                $v = $_.Value
                if ($v.Length -ge 2 -and (($v[0] -eq '"' -and $v[-1] -eq '"') -or ($v[0] -eq "'" -and $v[-1] -eq "'"))) {
                    $v.Substring(1, $v.Length - 2)
                } else { $v }
            }
        if (-not $tokens -or $tokens.Count -eq 0) { continue }

        $i = 0
        while ($i -lt $tokens.Count -and $tokens[$i] -match '^[A-Za-z_][A-Za-z0-9_]*=') { $i++ }
        if ($i -ge $tokens.Count) { continue }

        if ($tokens[$i] -notmatch '^(git|git\.exe)$') { continue }
        $i++

        while ($i -lt $tokens.Count -and $tokens[$i] -match '^-') {
            $tok = $tokens[$i]
            if ($tok -match '=') { $i++; continue }
            if ($optionsAvecValeurSeparee -contains $tok) { $i += 2; continue }
            $i++
        }

        if ($i -lt $tokens.Count -and $tokens[$i] -match '^(commit|push)$') {
            return $true
        }
    }
    return $false
}

# Extrait recursivement toutes les valeurs texte (feuilles string) d'un objet
# issu de ConvertFrom-Json, quelle que soit sa forme (tool_input differe selon
# Bash/PowerShell/outils MCP). Operer sur le texte reel plutot que sur le JSON
# serialise : le JSON echappe les guillemets internes (\"), ce qui casse la
# tokenisation de Test-CommandeGit si on lui donne directement le JSON.
function Get-ValeursTexteRecursif {
    param($Objet)
    $resultat = @()
    if ($null -eq $Objet) { return $resultat }
    if ($Objet -is [string]) { return @($Objet) }
    if ($Objet -is [System.Collections.IEnumerable] -and $Objet -isnot [string]) {
        foreach ($item in $Objet) { $resultat += Get-ValeursTexteRecursif $item }
        return $resultat
    }
    if ($Objet -is [System.Management.Automation.PSCustomObject]) {
        foreach ($prop in $Objet.PSObject.Properties) { $resultat += Get-ValeursTexteRecursif $prop.Value }
        return $resultat
    }
    return $resultat
}

# Point d'entree unique pour les scripts appelants : true si une des valeurs
# texte de tool_input ressemble a un git commit/push.
function Test-EvenementEstGit {
    param($ToolInput)
    foreach ($v in (Get-ValeursTexteRecursif $ToolInput)) {
        if (Test-CommandeGit $v) { return $true }
    }
    return $false
}
