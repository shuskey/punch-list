# install-skills.ps1
# Creates directory junctions so Claude Code can discover skills from this repo.
#
# Chain: ~/.claude/skills/<name> -> ~/.agents/skills/<name> -> <repo>/skills/<name>
# Edit skills in <repo>/skills/ — changes are live immediately.
#
# Usage: .\install-skills.ps1 [-Force]

param(
    [switch]$Force
)

$SkillsDir = Join-Path $PSScriptRoot "skills"
$AgentsDir = Join-Path $HOME ".agents\skills"
$ClaudeDir = Join-Path $HOME ".claude\skills"

New-Item -ItemType Directory -Path $AgentsDir -Force | Out-Null
New-Item -ItemType Directory -Path $ClaudeDir  -Force | Out-Null

Write-Host "Installing skills from: $SkillsDir"
Write-Host ""

$installed = 0
$skipped   = 0
$replaced  = 0

function Link-One {
    param(
        [string]$Target,   # path where the junction will live
        [string]$Dest,     # path the junction points to
        [string]$Label,
        [string]$Name
    )

    $item = Get-Item -LiteralPath $Target -ErrorAction SilentlyContinue

    if ($item -and $item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        # It's already a junction/symlink — check where it points
        $existing = (Get-Item -LiteralPath $Target).Target
        $destNorm  = $Dest.TrimEnd('\')
        $existNorm = if ($existing) { $existing.TrimEnd('\') } else { "" }

        if ($existNorm -eq $destNorm) {
            Write-Host "  = [$Label] $Name"
            $script:skipped++
        } elseif ($Force) {
            Remove-Item -LiteralPath $Target -Force -Recurse
            New-Item -ItemType Junction -Path $Target -Target $Dest | Out-Null
            Write-Host "  r [$Label] $Name  (replaced)"
            $script:replaced++
        } else {
            Write-Host "  ! [$Label] $Name  (points elsewhere — use -Force)"
            $script:skipped++
        }
    } elseif ($item) {
        if ($Force) {
            Remove-Item -LiteralPath $Target -Force -Recurse
            New-Item -ItemType Junction -Path $Target -Target $Dest | Out-Null
            Write-Host "  r [$Label] $Name  (replaced existing)"
            $script:replaced++
        } else {
            Write-Host "  ! [$Label] $Name  (path exists — use -Force)"
            $script:skipped++
        }
    } else {
        New-Item -ItemType Junction -Path $Target -Target $Dest | Out-Null
        Write-Host "  + [$Label] $Name"
        $script:installed++
    }
}

foreach ($skillPath in Get-ChildItem -Path $SkillsDir -Directory) {
    $name = $skillPath.Name
    Link-One -Target (Join-Path $AgentsDir $name) -Dest $skillPath.FullName       -Label "agents" -Name $name
    Link-One -Target (Join-Path $ClaudeDir $name) -Dest (Join-Path $AgentsDir $name) -Label "claude" -Name $name
}

Write-Host ""
Write-Host "Installing punchlist.py to ~/.punch-list/"
$PunchListDir = Join-Path $HOME ".punch-list"
New-Item -ItemType Directory -Path $PunchListDir -Force | Out-Null
Copy-Item -Path (Join-Path $PSScriptRoot "punchlist.py") -Destination (Join-Path $PunchListDir "punchlist.py") -Force
Write-Host "  + punchlist.py"

Write-Host ""
Write-Host "Installing Python dependency: typer"
try {
    pip install typer --quiet 2>&1 | Out-Null
    Write-Host "  + typer"
} catch {
    Write-Host "  ! pip install typer failed — install manually"
}

Write-Host ""
Write-Host "Done. Installed: $installed  Replaced: $replaced  Skipped: $skipped"
Write-Host ""
Write-Host "Edit skills in: $SkillsDir"
