$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskRoot = Join-Path $taskRepo 'private/skin-eyes-v1'
$taskWork = Join-Path $taskRoot 'dual'
$taskMods = 'F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods'
function Assert-GameExited {
    if (@(Get-Process | Where-Object { $_.ProcessName -match '(?i)PBZ|PhantomBlade' }).Count) {
        throw 'PBZ is running; exit the game before installing this candidate.'
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
function Write-Json($path,$value) {
    [IO.File]::WriteAllText($path,($value | ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
}
Assert-GameExited
$taskVerified = Get-Content -LiteralPath (Join-Path $taskWork 'verification.json') -Raw | ConvertFrom-Json
$taskEyes = Get-Content -LiteralPath (Join-Path $taskRoot 'variant/eye-geometry-verification.json') -Raw | ConvertFrom-Json
$taskTextures = Get-Content -LiteralPath (Join-Path $taskRoot 'variant/texture-contract-verification.json') -Raw | ConvertFrom-Json
if ($taskVerified.status -ne 'independent-final-container-verified-runtime-pending' -or !$taskVerified.all_appearance_rows_unchanged -or !$taskVerified.jk_geometry_and_cloth_payloads_unchanged -or !$taskEyes.passed -or !$taskTextures.passed) { throw 'Candidate verification is incomplete' }
$taskBuild = Get-Content -LiteralPath (Join-Path $taskWork 'build-report.json') -Raw | ConvertFrom-Json
if ($taskEyes.source_fbx_sha256 -ne $taskBuild.source_fbx_sha256) { throw 'Stale eye verification' }
$taskExpected = @(Get-Content -LiteralPath (Join-Path $taskWork 'installed-before.json') -Raw | ConvertFrom-Json)
$taskOld = @($taskExpected | Where-Object { $_.name -like 'z_Sui_DualOutfit_*' } | ForEach-Object name)
$taskNew = @('pak','ucas','utoc' | ForEach-Object { 'z_Sui_DualOutfit_JK5_JiraiR6_SkinEyes1_P.' + $_ })
if ($taskOld.Count -ne 3 -or @($taskVerified.container_files).Count -ne 3) { throw 'Expected one old and one new model container triple' }
$taskBefore = Snapshot
if ($taskBefore.Count -ne $taskExpected.Count) { throw 'Installed MOD set changed; rebuild against the current model' }
foreach ($item in $taskExpected) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
foreach ($item in $taskVerified.container_files) {
    if ($item.name -notin $taskNew) { throw 'Unexpected candidate name' }
    Assert-Hash (Join-Path (Join-Path $taskWork 'container') $item.name) $item.sha256
    if (Test-Path -LiteralPath (Join-Path $taskMods $item.name)) { throw 'Candidate path is already occupied' }
}
$taskTime = [DateTimeOffset]::UtcNow.ToOffset([TimeSpan]::FromHours(8))
$taskBackup = [IO.Path]::GetFullPath((Join-Path $taskWork ('backup-' + $taskTime.ToString('yyyyMMdd-HHmmss-fff'))))
if (!$taskBackup.StartsWith(([IO.Path]::GetFullPath($taskWork) + [IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid backup location' }
New-Item -ItemType Directory -Path $taskBackup | Out-Null
Write-Json (Join-Path $taskBackup 'before.json') $taskBefore
Assert-GameExited
try {
    foreach ($name in $taskOld) {
        $taskSource = [IO.Path]::GetFullPath((Join-Path $taskMods $name))
        if ([IO.Path]::GetDirectoryName($taskSource) -ne [IO.Path]::GetFullPath($taskMods)) { throw 'Invalid old container path' }
        Move-Item -LiteralPath $taskSource -Destination (Join-Path $taskBackup $name)
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
    $taskReceipt = [ordered]@{status='installed-hash-verified-runtime-pending';installed_at=$taskTime.ToString('o');target=$taskMods;backup=$taskBackup;before=$taskBefore;after=$taskAfter;voice_unchanged=$true;game_runtime_tested=$false}
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
