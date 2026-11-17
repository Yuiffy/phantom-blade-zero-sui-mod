$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskWork = Join-Path $taskRepo 'private/jirai-face-v3'
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
$taskGeometry = Get-Content -LiteralPath (Join-Path $taskWork 'geometry-verification.json') -Raw | ConvertFrom-Json
$taskSurface = Get-Content -LiteralPath (Join-Path $taskWork 'surface-verification.json') -Raw | ConvertFrom-Json
$taskVisual = Get-Content -LiteralPath (Join-Path $taskWork 'visual-review.json') -Raw | ConvertFrom-Json
if (!$taskGate.passed -or $taskGate.package_count -ne 7 -or !$taskGate.all_other_native_bytes_exact -or !$taskGate.skirt_weights_physics_skeleton_indices_exact) { throw 'Unexpected candidate scope' }
if (!$taskMount.passed -or !$taskMount.directory_order_independent -or !$taskGeometry.passed -or !$taskGeometry.final_container_readback -or !$taskSurface.passed -or !$taskVisual.reviewed) { throw 'Missing final verification or visual review' }
if ($taskMount.source_atlas_sha256 -ne $taskGate.source_atlas_sha256 -or $taskSurface.output_atlas_sha256 -ne $taskGate.source_atlas_sha256 -or $taskVisual.source_atlas_sha256 -ne $taskGate.source_atlas_sha256 -or $taskVisual.source_iris_sha256 -ne $taskGate.source_iris_sha256 -or $taskSurface.surface_sha256 -ne $taskGate.surface_sha256 -or $taskVisual.surface_sha256 -ne $taskGate.surface_sha256 -or $taskMount.surface_sha256 -ne $taskGate.surface_sha256) { throw 'Stale face verification' }
Assert-Hash (Join-Path $taskWork 'surface.npz') $taskGate.surface_sha256
Assert-Hash (Join-Path $taskWork 'T_Jirai_Base.png') $taskGate.source_atlas_sha256
Assert-Hash (Join-Path $taskWork 'T_Face3_Iris.png') $taskGate.source_iris_sha256
Assert-Hash (Join-Path $taskWork 'T_Face3_EyeMix.png') $taskGate.source_mix_sha256
Assert-Hash (Join-Path $taskWork 'native/final-render.npz') $taskGeometry.native_render_sha256
foreach ($item in $taskVisual.images.PSObject.Properties) { Assert-Hash $item.Name $item.Value }
$taskExpected = @($taskMount.installed_mod_snapshot)
$taskBefore = Snapshot
if ($taskBefore.Count -ne $taskExpected.Count) { throw 'Installed MOD set changed; rerun verify_mount.py' }
foreach ($item in $taskExpected) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
$taskOld = @('pak','ucas','utoc' | ForEach-Object { 'zzz_Sui_JiraiFace2_1_P.' + $_ })
$taskNew = @('pak','ucas','utoc' | ForEach-Object { 'zzz_Sui_JiraiFace3_2_P.' + $_ })
if (@($taskGate.container_files).Count -ne 3) { throw 'Expected patch triple' }
foreach ($item in $taskGate.container_files) {
    if ($item.name -notin $taskNew) { throw 'Unexpected candidate filename' }
    Assert-Hash (Join-Path (Join-Path $taskWork 'container') $item.name) $item.sha256
    if (Test-Path -LiteralPath (Join-Path $taskMods $item.name)) { throw 'Face3 already installed' }
}
foreach ($name in $taskOld) { if ($name -notin @($taskExpected | ForEach-Object name)) { throw 'Expected Face2 fallback missing' } }
$taskTime = [DateTimeOffset]::UtcNow.ToOffset([TimeSpan]::FromHours(8))
$taskRecord = Join-Path $taskWork ('installation-' + $taskTime.ToString('yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $taskRecord | Out-Null
$taskOldRecord = Join-Path $taskRecord 'face2'
New-Item -ItemType Directory -Path $taskOldRecord | Out-Null
Write-Json (Join-Path $taskRecord 'before.json') $taskBefore
Assert-GameExited
try {
    foreach ($item in $taskGate.container_files) {
        Assert-GameExited
        [IO.File]::Copy((Join-Path (Join-Path $taskWork 'container') $item.name), (Join-Path $taskMods $item.name), $false)
        Assert-Hash (Join-Path $taskMods $item.name) $item.sha256
    }
    foreach ($name in $taskOld) {
        Assert-GameExited
        Move-Item -LiteralPath (Join-Path $taskMods $name) -Destination (Join-Path $taskOldRecord $name)
    }
    foreach ($item in $taskExpected | Where-Object { $_.name -notin $taskOld }) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
    $taskAfter = Snapshot
    $taskAllowed = $taskNew + @($taskExpected | Where-Object { $_.name -notin $taskOld } | ForEach-Object name)
    if (@(Compare-Object $taskAllowed @($taskAfter | ForEach-Object name)).Count) { throw 'Unexpected final MOD set' }
    $taskReceipt = [ordered]@{status='installed-hash-verified-runtime-pending';installed_at=$taskTime.ToString('o');target=$taskMods;record=$taskRecord;before=$taskBefore;after=$taskAfter;removed_face2=$taskOld;added_face3=$taskNew;current_skirt_base_and_voice_files_exact=$true;source_atlas_sha256=$taskGate.source_atlas_sha256;source_iris_sha256=$taskGate.source_iris_sha256;surface_sha256=$taskGate.surface_sha256;game_runtime_tested=$false}
    Write-Json (Join-Path $taskWork 'installation-receipt.json') $taskReceipt
    Write-Json (Join-Path $taskRecord 'installation-receipt.json') $taskReceipt
    Write-Output ('FACE3_INSTALLED_HASH_VERIFIED; record=' + $taskRecord)
} catch {
    $taskFailure = $_.Exception.Message
    foreach ($item in $taskGate.container_files) {
        $path = Join-Path $taskMods $item.name
        if (Test-Path -LiteralPath $path) {
            Assert-Hash $path $item.sha256
            Move-Item -LiteralPath $path -Destination (Join-Path $taskRecord $item.name)
        }
    }
    foreach ($name in $taskOld) {
        $path = Join-Path $taskOldRecord $name
        if (Test-Path -LiteralPath $path) { Move-Item -LiteralPath $path -Destination (Join-Path $taskMods $name) }
    }
    Write-Json (Join-Path $taskRecord 'failed.json') @{status='face2-restored';reason=$taskFailure;other_mods_untouched=$true}
    throw "Face3 installation failed; Face2 restored: $taskFailure"
}
