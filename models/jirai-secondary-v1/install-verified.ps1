$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskWork = Join-Path $taskRepo 'private/jirai-secondary-v1/dual'
$taskMods = 'F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods'
function Assert-GameExited {
    if (@(Get-Process | Where-Object { $_.ProcessName -match '(?i)PBZ|PhantomBlade' }).Count) {
        throw 'PBZ is running; exit it before installation.'
    }
}
function Assert-Hash($path, $expected) {
    if (!(Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected.ToLowerInvariant()) {
        throw "Missing or changed file: $path"
    }
}
function Snapshot {
    @(Get-ChildItem -LiteralPath $taskMods -File | Sort-Object Name | ForEach-Object {
        [ordered]@{name=$_.Name;bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
    })
}
function Write-Json($path, $data) {
    [IO.File]::WriteAllText($path, ($data | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
}
Assert-GameExited
$taskVerified = Get-Content -LiteralPath (Join-Path $taskWork 'verification.json') -Raw | ConvertFrom-Json
if ($taskVerified.status -ne 'independent-final-container-verified-runtime-pending' -or !$taskVerified.jk5_and_all_appearance_rows_unchanged) { throw 'Candidate not verified' }
$taskExpected = @(Get-Content -LiteralPath (Join-Path $taskWork 'installed-before.json') -Raw | ConvertFrom-Json)
$taskOld = @('pak','ucas','utoc' | ForEach-Object { 'z_Sui_DualOutfit_JK5_JiraiR5_P.' + $_ })
$taskNew = @('pak','ucas','utoc' | ForEach-Object { 'z_Sui_DualOutfit_JK5_JiraiR6_P.' + $_ })
$taskBefore = Snapshot
if ($taskBefore.Count -ne $taskExpected.Count) { throw 'Installed MOD set changed' }
foreach ($item in $taskExpected) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
foreach ($item in $taskVerified.container_files) {
    if ($item.name -notin $taskNew) { throw 'Unexpected candidate name' }
    Assert-Hash (Join-Path (Join-Path $taskWork 'container') $item.name) $item.sha256
    if (Test-Path -LiteralPath (Join-Path $taskMods $item.name)) { throw 'Candidate already installed' }
}
if (@($taskVerified.container_files).Count -ne 3) { throw 'Expected container triple' }
$taskTime = [DateTimeOffset]::UtcNow.ToOffset([TimeSpan]::FromHours(8))
$taskBackup = [IO.Path]::GetFullPath((Join-Path $taskWork ('backup-' + $taskTime.ToString('yyyyMMdd-HHmmss-fff'))))
if (!$taskBackup.StartsWith(([IO.Path]::GetFullPath($taskWork) + [IO.Path]::DirectorySeparatorChar), [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid backup location' }
New-Item -ItemType Directory -Path $taskBackup | Out-Null
Write-Json (Join-Path $taskBackup 'before.json') $taskBefore
Assert-GameExited
try {
    foreach ($name in $taskOld) {
        Move-Item -LiteralPath (Join-Path $taskMods $name) -Destination (Join-Path $taskBackup $name)
        $entry = $taskExpected | Where-Object name -eq $name
        Assert-Hash (Join-Path $taskBackup $name) $entry.sha256
    }
    foreach ($item in $taskVerified.container_files) {
        Copy-Item -LiteralPath (Join-Path (Join-Path $taskWork 'container') $item.name) -Destination (Join-Path $taskMods $item.name)
        Assert-Hash (Join-Path $taskMods $item.name) $item.sha256
    }
    foreach ($item in $taskExpected | Where-Object { $_.name -notin $taskOld }) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
    $taskAfter = Snapshot
    $taskAllowed = @($taskNew) + @($taskExpected | Where-Object { $_.name -notin $taskOld } | ForEach-Object name)
    if (@(Compare-Object $taskAllowed @($taskAfter | ForEach-Object name)).Count) { throw 'Unexpected final files' }
    $taskReceipt = [ordered]@{status='installed-hash-verified-runtime-pending';installed_at=$taskTime.ToString('o');target=$taskMods;backup=$taskBackup;before=$taskBefore;after=$taskAfter;voice_unchanged=$true;jk5_unchanged=$true;game_runtime_tested=$false}
    Write-Json (Join-Path $taskWork 'installation-receipt.json') $taskReceipt
    Write-Json (Join-Path $taskBackup 'installation-receipt.json') $taskReceipt
    Write-Output ('INSTALLED_HASH_VERIFIED; backup=' + $taskBackup)
} catch {
    $taskFailure = $_.Exception.Message
    $taskRejected = Join-Path $taskBackup 'incomplete-new'
    New-Item -ItemType Directory -Path $taskRejected | Out-Null
    foreach ($name in $taskNew) {
        $path = Join-Path $taskMods $name
        if (Test-Path -LiteralPath $path) { Move-Item -LiteralPath $path -Destination (Join-Path $taskRejected $name) }
    }
    foreach ($name in $taskOld) {
        $path = Join-Path $taskBackup $name
        if (Test-Path -LiteralPath $path) { Copy-Item -LiteralPath $path -Destination (Join-Path $taskMods $name) -Force }
    }
    foreach ($item in $taskExpected) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
    Write-Json (Join-Path $taskBackup 'failed.json') @{status='rolled-back';reason=$taskFailure}
    throw "Installation failed; previous version restored: $taskFailure"
}
