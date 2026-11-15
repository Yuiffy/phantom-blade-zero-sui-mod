$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskWork = Join-Path $taskRepo 'private/dual-outfit-v2'
$taskDelivery = Join-Path $taskWork 'delivery'
$taskMods = 'F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods'

function Assert-GameExited {
    $running = @(Get-Process | Where-Object { $_.ProcessName -match '(?i)PBZ|PhantomBlade' })
    if ($running.Count -ne 0) { throw 'PBZ is running; exit the game before installation.' }
}
function Assert-FileHash($path, $expected) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing file: $path" }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected.ToLowerInvariant()) {
        throw "Hash mismatch: $path"
    }
}
function Get-ModSnapshot {
    @(Get-ChildItem -LiteralPath $taskMods -File | Sort-Object Name | ForEach-Object {
        [ordered]@{name=$_.Name;bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
    })
}
function Write-TaskJson($path, $value) {
    [IO.File]::WriteAllText($path, ($value | ConvertTo-Json -Depth 15), [Text.UTF8Encoding]::new($false))
}

Assert-GameExited
$taskManifest = Get-Content -LiteralPath (Join-Path $taskDelivery 'manifest.json') -Raw | ConvertFrom-Json
foreach ($entry in $taskManifest.files) {
    if ([IO.Path]::GetFileName($entry.name) -ne $entry.name) { throw 'Unexpected manifest path' }
    Assert-FileHash (Join-Path $taskDelivery $entry.name) $entry.sha256
}
$taskVerified = Get-Content -LiteralPath (Join-Path $taskDelivery 'verification.json') -Raw | ConvertFrom-Json
if ($taskVerified.status -ne 'independent-final-container-verified-runtime-pending' -or $taskVerified.package_count -ne 88) {
    throw 'Expected independently verified dual outfit candidate'
}
$taskPlan = Get-Content -LiteralPath (Join-Path $taskDelivery 'installation-plan.json') -Raw | ConvertFrom-Json
if ([IO.Path]::GetFullPath($taskPlan.target) -ne [IO.Path]::GetFullPath($taskMods)) { throw 'Unexpected install target' }
$taskBefore = Get-ModSnapshot
$taskExpected = @(Get-Content -LiteralPath (Join-Path $taskWork 'installed-before.json') -Raw | ConvertFrom-Json)
if ($taskBefore.Count -ne $taskExpected.Count) { throw 'Installed MOD set changed since candidate verification' }
foreach ($entry in $taskExpected) { Assert-FileHash (Join-Path $taskMods $entry.name) $entry.sha256 }
$taskOldNames = @('z_Sui_DualOutfit_JK_Jirai_v1_P.pak','z_Sui_DualOutfit_JK_Jirai_v1_P.ucas','z_Sui_DualOutfit_JK_Jirai_v1_P.utoc')
$taskNewNames = @('z_Sui_DualOutfit_JK_Jirai_v2_P.pak','z_Sui_DualOutfit_JK_Jirai_v2_P.ucas','z_Sui_DualOutfit_JK_Jirai_v2_P.utoc')
if (@(Compare-Object $taskOldNames @($taskPlan.replace_model_files)).Count -ne 0) { throw 'Unexpected replacement plan' }
if (@(Compare-Object $taskNewNames @($taskPlan.add_files)).Count -ne 0) { throw 'Unexpected candidate plan' }
foreach ($name in $taskNewNames) {
    if (Test-Path -LiteralPath (Join-Path $taskMods $name)) { throw 'Candidate is already present; inspect before installing' }
}
$taskLocalTime = [DateTimeOffset]::UtcNow.ToOffset([TimeSpan]::FromHours(8))
$taskBackup = Join-Path $taskWork ('installation-backup-' + $taskLocalTime.ToString('yyyyMMdd-HHmmss-fff'))
$taskBackup = [IO.Path]::GetFullPath($taskBackup)
if (-not $taskBackup.StartsWith(([IO.Path]::GetFullPath($taskWork) + [IO.Path]::DirectorySeparatorChar), [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Backup path escaped workspace'
}
New-Item -ItemType Directory -Path $taskBackup | Out-Null
Write-TaskJson (Join-Path $taskBackup 'installed-before.json') $taskBefore
$taskStaged = Join-Path $taskBackup 'staged-new'
New-Item -ItemType Directory -Path $taskStaged | Out-Null
foreach ($name in $taskNewNames) {
    Copy-Item -LiteralPath (Join-Path $taskDelivery $name) -Destination (Join-Path $taskStaged $name)
    $entry = $taskManifest.files | Where-Object name -eq $name
    Assert-FileHash (Join-Path $taskStaged $name) $entry.sha256
}
Assert-GameExited
try {
    foreach ($name in $taskOldNames) {
        Move-Item -LiteralPath (Join-Path $taskMods $name) -Destination (Join-Path $taskBackup $name)
        $entry = $taskExpected | Where-Object name -eq $name
        Assert-FileHash (Join-Path $taskBackup $name) $entry.sha256
    }
    foreach ($name in $taskNewNames) {
        Copy-Item -LiteralPath (Join-Path $taskStaged $name) -Destination (Join-Path $taskMods $name)
        $entry = $taskManifest.files | Where-Object name -eq $name
        Assert-FileHash (Join-Path $taskMods $name) $entry.sha256
    }
    foreach ($entry in $taskExpected | Where-Object { $_.name -notin $taskOldNames }) {
        Assert-FileHash (Join-Path $taskMods $entry.name) $entry.sha256
    }
    $taskAfter = Get-ModSnapshot
    $taskAllowed = @($taskNewNames) + @($taskExpected | Where-Object { $_.name -notin $taskOldNames } | ForEach-Object name)
    if (@(Compare-Object $taskAllowed @($taskAfter | ForEach-Object { $_.name })).Count -ne 0) { throw 'Unexpected final MOD files' }
    $taskReceipt = [ordered]@{
        status='installed-hash-verified-runtime-pending';installed_at=$taskLocalTime.ToString('o');target=$taskMods
        backup=$taskBackup;game_build='26367565';outfits=$taskVerified.outfits
        before=$taskBefore;after=$taskAfter;removed_model_files=$taskOldNames;installed_model_files=$taskNewNames
        source_manifest_sha256=(Get-FileHash -LiteralPath (Join-Path $taskDelivery 'manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant()
        voice_unchanged=$true;runtime_tested=$false
    }
    Write-TaskJson (Join-Path $taskWork 'installation-receipt.json') $taskReceipt
    Write-TaskJson (Join-Path $taskBackup 'installation-receipt.json') $taskReceipt
    Write-Output 'INSTALLED_HASH_VERIFIED: JK=black wound fugitive; Jirai=black wound; voice unchanged.'
    Write-Output ('Backup: ' + $taskBackup)
}
catch {
    $taskFailure = $_.Exception.Message
    $taskRejected = Join-Path $taskBackup 'incomplete-new'
    New-Item -ItemType Directory -Path $taskRejected -Force | Out-Null
    foreach ($name in $taskNewNames) {
        $path = Join-Path $taskMods $name
        if (Test-Path -LiteralPath $path) { Move-Item -LiteralPath $path -Destination (Join-Path $taskRejected $name) }
    }
    foreach ($name in $taskOldNames) {
        $path = Join-Path $taskBackup $name
        if (Test-Path -LiteralPath $path) { Copy-Item -LiteralPath $path -Destination (Join-Path $taskMods $name) -Force }
    }
    foreach ($entry in $taskExpected) { Assert-FileHash (Join-Path $taskMods $entry.name) $entry.sha256 }
    Write-TaskJson (Join-Path $taskBackup 'failed-install.json') @{status='rolled-back';reason=$taskFailure;restored_files=(Get-ModSnapshot)}
    throw "Install failed and original files restored: $taskFailure"
}
