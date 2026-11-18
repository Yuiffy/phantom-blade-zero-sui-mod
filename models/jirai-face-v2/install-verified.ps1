$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskWork = Join-Path $taskRepo 'private/jirai-face-v2'
$taskMods = 'F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods'
function Assert-GameExited {
    if (@(Get-Process | Where-Object { $_.ProcessName -match '(?i)PBZ|PhantomBlade' }).Count) { throw 'PBZ is running; exit it before installation.' }
}
function Assert-Hash($path, $expected) {
    if (!(Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected.ToLowerInvariant()) { throw "Missing or changed file: $path" }
}
function Snapshot {
    @(Get-ChildItem -LiteralPath $taskMods -File | Sort-Object Name | ForEach-Object { [ordered]@{name=$_.Name;bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()} })
}
function Write-Json($path, $data) { [IO.File]::WriteAllText($path, ($data | ConvertTo-Json -Depth 25), [Text.UTF8Encoding]::new($false)) }
Assert-GameExited
$taskGate = Get-Content -LiteralPath (Join-Path $taskWork 'verification.json') -Raw | ConvertFrom-Json
$taskMount = Get-Content -LiteralPath (Join-Path $taskWork 'mount-verification.json') -Raw | ConvertFrom-Json
$taskSurface = Get-Content -LiteralPath (Join-Path $taskWork 'surface-verification.json') -Raw | ConvertFrom-Json
$taskVisual = Get-Content -LiteralPath (Join-Path $taskWork 'visual-review.json') -Raw | ConvertFrom-Json
if ($taskGate.status -ne 'independent-atlas-container-verified-runtime-pending' -or $taskGate.package_count -ne 3 -or !$taskGate.original_shared_atlas_not_overridden -or !$taskGate.geometry_and_physics_not_overridden) { throw 'Unexpected candidate scope' }
if (!$taskMount.passed -or !$taskMount.directory_order_independent -or !$taskSurface.passed -or !$taskVisual.reviewed) { throw 'Missing final verification or visual review' }
if ($taskMount.source_atlas_sha256 -ne $taskGate.source_atlas_sha256 -or $taskSurface.output_atlas_sha256 -ne $taskGate.source_atlas_sha256 -or $taskVisual.source_atlas_sha256 -ne $taskGate.source_atlas_sha256) { throw 'Stale face verification' }
foreach ($item in $taskVisual.images.PSObject.Properties) { Assert-Hash $item.Name $item.Value }
$taskExpected = @($taskMount.installed_mod_snapshot)
$taskBefore = Snapshot
if ($taskBefore.Count -ne $taskExpected.Count) { throw 'Installed MOD set changed; rerun verify_mount.py' }
foreach ($item in $taskExpected) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
$taskNew = @('pak','ucas','utoc' | ForEach-Object { 'zzz_Sui_JiraiFace2_1_P.' + $_ })
if (@($taskGate.container_files).Count -ne 3) { throw 'Expected patch triple' }
foreach ($item in $taskGate.container_files) {
    if ($item.name -notin $taskNew) { throw 'Unexpected candidate filename' }
    Assert-Hash (Join-Path (Join-Path $taskWork 'container') $item.name) $item.sha256
    if (Test-Path -LiteralPath (Join-Path $taskMods $item.name)) { throw 'Face patch already installed' }
}
$taskTime = [DateTimeOffset]::UtcNow.ToOffset([TimeSpan]::FromHours(8))
$taskRecord = Join-Path $taskWork ('installation-' + $taskTime.ToString('yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $taskRecord | Out-Null
Write-Json (Join-Path $taskRecord 'before.json') $taskBefore
Assert-GameExited
try {
    foreach ($item in $taskGate.container_files) {
        Assert-GameExited
        [IO.File]::Copy((Join-Path (Join-Path $taskWork 'container') $item.name), (Join-Path $taskMods $item.name), $false)
        Assert-Hash (Join-Path $taskMods $item.name) $item.sha256
    }
    foreach ($item in $taskExpected) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
    $taskAfter = Snapshot
    $taskAllowed = $taskNew + @($taskExpected | ForEach-Object name)
    if (@(Compare-Object $taskAllowed @($taskAfter | ForEach-Object name)).Count) { throw 'Unexpected final MOD set' }
    $taskReceipt = [ordered]@{status='installed-hash-verified-runtime-pending';installed_at=$taskTime.ToString('o');target=$taskMods;record=$taskRecord;before=$taskBefore;after=$taskAfter;only_added_files=$taskNew;all_existing_model_and_voice_files_unchanged=$true;source_atlas_sha256=$taskGate.source_atlas_sha256;game_runtime_tested=$false}
    Write-Json (Join-Path $taskWork 'installation-receipt.json') $taskReceipt
    Write-Json (Join-Path $taskRecord 'installation-receipt.json') $taskReceipt
    Write-Output ('FACE_PATCH_INSTALLED_HASH_VERIFIED; record=' + $taskRecord)
} catch {
    $taskFailure = $_.Exception.Message
    foreach ($item in $taskGate.container_files) {
        $path = Join-Path $taskMods $item.name
        if (Test-Path -LiteralPath $path) {
            Assert-Hash $path $item.sha256
            Move-Item -LiteralPath $path -Destination (Join-Path $taskRecord $item.name)
        }
    }
    Write-Json (Join-Path $taskRecord 'failed.json') @{status='face-patch-removed';reason=$taskFailure;other_mods_untouched=$true}
    throw "Face installation failed; patch removed: $taskFailure"
}
