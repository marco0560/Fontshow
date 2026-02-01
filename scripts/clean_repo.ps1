<#
.SYNOPSIS
Clean repository by removing ignored (untracked) artifacts.

.DESCRIPTION
Removes files and directories that are:
- ignored by git
- currently present in the working tree

Protected paths are never removed.

Supports:
  --dry-run   Show what would be removed without deleting anything
#>

param(
    [switch]$DryRun
)

# ----------------------------
# CONFIG
# ----------------------------

$PROTECTED_PATHS = @(
    ".venv",
    ".vscode",
    "node_modules"
)

# ----------------------------
# FUNCTIONS
# ----------------------------

function Get-GitIgnoredPaths {
    $output = git status --ignored --porcelain 2>$null

    foreach ($line in $output) {
        if ($line.StartsWith("!! ")) {
            $path = $line.Substring(3)
            if ($path) {
                [System.IO.Path]::GetFullPath($path)
            }
        }
    }
}

function Remove-PathSafe {
    param (
        [string]$Path,
        [bool]$DryRun
    )

    if ($DryRun) {
        Write-Host "[DRY-RUN] Would remove: $Path"
        return
    }

    if (Test-Path $Path -PathType Container) {
        Remove-Item -Recurse -Force -Path $Path
        Write-Host "Removed directory: $Path"
    }
    elseif (Test-Path $Path) {
        Remove-Item -Force -Path $Path
        Write-Host "Removed file: $Path"
    }
}

# ----------------------------
# MAIN
# ----------------------------

Write-Host "Cleaning repository (ignored artifacts only)..."

if ($DryRun) {
    Write-Host "Running in DRY-RUN mode.`n"
} else {
    Write-Host ""
}

$repoRoot = Get-Location

$ignored = Get-GitIgnoredPaths | Where-Object {
    $top = Split-Path $_ -Leaf
    $top -notin $PROTECTED_PATHS
}

if (-not $ignored) {
    Write-Host "Nothing to clean. Repository is already clean."
    return
}

foreach ($path in $ignored) {
    Remove-PathSafe -Path $path -DryRun:$DryRun
}

if ($DryRun) {
    Write-Host "`nDry-run completed. No files were removed."
} else {
    Write-Host "`nDone. Repository is clean."
}
