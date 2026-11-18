param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskWork = Join-Path $taskRepo 'private/jirai-skirt-v1/dual'
$taskReceipt = Get-Content -LiteralPath (Join-Path $taskWork 'installation-receipt.json') -Raw | ConvertFrom-Json
$taskMods = [IO.Path]::GetFullPath('F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods')
$taskSource = [IO.Path]::GetFullPath($taskReceipt.backup)
$taskOldStem = 'z_Sui_DualOutfit_JK5_JiraiR6_SkinEyes1_Fishnet1_P'
$taskNewStem = 'z_Sui_DualOutfit_JK5_JiraiR7Skirt_P'
function Assert-GameExited {
    if (@(Get-Process | Where-Object { $_.ProcessName -match '(?i)PBZ|PhantomBlade' }).Count) {
        throw 'PBZ is running; exit it before rollback. No game process will be stopped.'
    }
}
function Assert-Within($root, $path) {
    if (![IO.Path]::GetFullPath($path).StartsWith(([IO.Path]::GetFullPath($root).TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar), [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path outside expected root: $path"
    }
}
function Assert-File($root, $entry) {
    if ([IO.Path]::GetFileName($entry.name) -ne $entry.name) { throw 'Invalid filename' }
    $path = Join-Path $root $entry.name
    Assert-Within $root $path
    $file = Get-Item -LiteralPath $path
    if ($file.Length -ne $entry.bytes -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw "File changed: $path" }
}
function Snapshot {
    @(Get-ChildItem -LiteralPath $taskMods -File | Sort-Object Name | ForEach-Object {
        [ordered]@{name=$_.Name;bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
    })
}
function Assert-Set($expected) {
    $actual = Snapshot
    if (@(Compare-Object @($expected | ForEach-Object name) @($actual | ForEach-Object name)).Count) { throw 'Installed file set changed' }
    foreach ($entry in $expected) { Assert-File $taskMods $entry }
}
function Write-Json($path, $data) {
    [IO.File]::WriteAllText($path, ($data | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
}
Assert-Within $taskWork $taskSource
if ([IO.Path]::GetFullPath($taskReceipt.target) -ne $taskMods) { throw 'Receipt target mismatch' }
$taskOld = @($taskReceipt.before | Where-Object { $_.name -like ($taskOldStem + '.*') })
$taskNew = @($taskReceipt.after | Where-Object { $_.name -like ($taskNewStem + '.*') })
$taskVoice = @($taskReceipt.before | Where-Object { $_.name -like 'z_Sui_Hun_NaturalVoice_Compact_v5_P.*' })
foreach ($triple in @(@{items=$taskOld;stem=$taskOldStem}, @{items=$taskNew;stem=$taskNewStem}, @{items=$taskVoice;stem='z_Sui_Hun_NaturalVoice_Compact_v5_P'})) {
    $names = @('pak','ucas','utoc' | ForEach-Object { $triple.stem + '.' + $_ })
    if (@($triple.items).Count -ne 3 -or @(Compare-Object $names @($triple.items | ForEach-Object name)).Count) { throw 'Invalid container triple' }
}
if (@($taskReceipt.before).Count -ne 6 -or @($taskReceipt.after).Count -ne 6) { throw 'Unexpected receipt file set' }
foreach ($entry in $taskOld) { Assert-File $taskSource $entry }
foreach ($entry in $taskVoice) {
    $voiceAfter = @($taskReceipt.after | Where-Object name -eq $entry.name)
    if ($voiceAfter.Count -ne 1 -or $voiceAfter[0].sha256 -ne $entry.sha256 -or $voiceAfter[0].bytes -ne $entry.bytes) { throw 'Voice receipt changed' }
}
$taskCurrentNames = @(Get-ChildItem -LiteralPath $taskMods -File | ForEach-Object Name)
if (@($taskOld | Where-Object { $_.name -in $taskCurrentNames }).Count -eq 3 -and !@($taskNew | Where-Object { $_.name -in $taskCurrentNames }).Count) {
    foreach ($entry in $taskReceipt.before) { Assert-File $taskMods $entry }
    Write-Output ('ALREADY_RESTORED_HASH_VERIFIED; later additional files untouched=' + ($taskCurrentNames.Count-@($taskReceipt.before).Count))
    return
}
Assert-Set $taskReceipt.after
if (!$Apply) {
    Write-Output 'ROLLBACK_READY_HASH_VERIFIED; game must exit before -Apply; no files changed'
    return
}
Assert-GameExited
$taskTime = [DateTimeOffset]::Now
$taskQuarantine = [IO.Path]::GetFullPath((Join-Path $taskWork ('rejected-r7-' + $taskTime.ToString('yyyyMMdd-HHmmss-fff'))))
Assert-Within $taskWork $taskQuarantine
New-Item -ItemType Directory -Path $taskQuarantine | Out-Null
Write-Json (Join-Path $taskQuarantine 'before.json') (Snapshot)
$taskMoved = @()
$taskCopied = @()
Assert-GameExited
try {
    foreach ($entry in $taskNew) {
        Move-Item -LiteralPath (Join-Path $taskMods $entry.name) -Destination (Join-Path $taskQuarantine $entry.name)
        $taskMoved += $entry
        Assert-File $taskQuarantine $entry
    }
    foreach ($entry in $taskOld) {
        $taskCopied += $entry
        Copy-Item -LiteralPath (Join-Path $taskSource $entry.name) -Destination (Join-Path $taskMods $entry.name)
        Assert-File $taskMods $entry
    }
    Assert-Set $taskReceipt.before
    $result = [ordered]@{status='restored-r6-fishnet1-hash-verified';restored_at=$taskTime.ToString('o');target=$taskMods;source_backup=$taskSource;rejected_r7_backup=$taskQuarantine;before=$taskReceipt.after;after=(Snapshot);voice_unchanged=$true;jk5_unchanged=$true;new_runtime_test_performed=$false}
    Write-Json (Join-Path $taskQuarantine 'rollback-receipt.json') $result
    Write-Json (Join-Path $taskWork 'rollback-receipt.json') $result
    Write-Output ('RESTORED_R6_FISHNET1_HASH_VERIFIED; rejected R7 retained at ' + $taskQuarantine)
} catch {
    $reason = $_.Exception.Message
    foreach ($entry in $taskCopied) {
        $path = Join-Path $taskMods $entry.name
        if (Test-Path -LiteralPath $path) { Move-Item -LiteralPath $path -Destination (Join-Path $taskQuarantine ('incomplete-' + $entry.name)) }
    }
    foreach ($entry in $taskMoved) { Copy-Item -LiteralPath (Join-Path $taskQuarantine $entry.name) -Destination (Join-Path $taskMods $entry.name) }
    Assert-Set $taskReceipt.after
    Write-Json (Join-Path $taskQuarantine 'failed.json') @{status='rollback-failed-r7-restored';reason=$reason}
    throw "Rollback failed; original installed R7 files restored: $reason"
}
