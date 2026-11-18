$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskWork = [IO.Path]::GetFullPath((Join-Path $taskRepo 'private/jirai-hairpin-v1'))
$taskMods = 'F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods'
function Assert-GameExited {
    if (@(Get-Process | Where-Object { $_.ProcessName -match '(?i)PBZ|PhantomBlade' }).Count) { throw 'PBZ is running; exit it before installation.' }
}
function Assert-Hash($path,$expected) {
    if (!(Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected.ToLowerInvariant()) { throw "Missing or changed file: $path" }
}
function Snapshot {
    @(Get-ChildItem -LiteralPath $taskMods -File | Sort-Object Name | ForEach-Object { [ordered]@{name=$_.Name;bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()} })
}
function Write-Json($path,$data) { [IO.File]::WriteAllText($path,($data | ConvertTo-Json -Depth 25),[Text.UTF8Encoding]::new($false)) }
Assert-GameExited
$taskGate = Get-Content -LiteralPath (Join-Path $taskWork 'verification.json') -Raw | ConvertFrom-Json
$taskGeometry = Get-Content -LiteralPath (Join-Path $taskWork 'geometry-verification.json') -Raw | ConvertFrom-Json
$taskMount = Get-Content -LiteralPath (Join-Path $taskWork 'mount-verification.json') -Raw | ConvertFrom-Json
$taskVisual = Get-Content -LiteralPath (Join-Path $taskWork 'visual-review.json') -Raw | ConvertFrom-Json
if (!$taskGate.passed -or $taskGate.package_count -ne 3 -or !$taskGate.all_non_accessory_bytes_exact -or !$taskGate.face3_geometry_frames_uv_exact -or !$taskGate.uv1_weights_skeleton_cloth_physics_exact) { throw 'Unexpected patch scope' }
if (!$taskGeometry.passed -or !$taskGeometry.final_container_readback -or !$taskMount.passed -or !$taskMount.directory_order_independent -or !$taskVisual.reviewed) { throw 'Missing final verification or visual review' }
if ($taskGeometry.source_atlas_sha256 -ne $taskGate.source_atlas_sha256 -or $taskVisual.source_atlas_sha256 -ne $taskGate.source_atlas_sha256 -or $taskMount.source_atlas_sha256 -ne $taskGate.source_atlas_sha256 -or $taskGeometry.native_render_sha256 -ne $taskGate.native_render_sha256 -or $taskVisual.native_render_sha256 -ne $taskGate.native_render_sha256 -or $taskMount.native_render_sha256 -ne $taskGate.native_render_sha256) { throw 'Stale verification' }
Assert-Hash (Join-Path $taskWork 'T_Jirai_Base.png') $taskGate.source_atlas_sha256
Assert-Hash (Join-Path $taskWork 'authored-geometry.npz') $taskGate.authored_geometry_sha256
Assert-Hash (Join-Path $taskWork 'final-render.npz') $taskGate.native_render_sha256
foreach ($image in $taskVisual.images.PSObject.Properties) { Assert-Hash $image.Name $image.Value }
$taskBefore = Snapshot
$taskExpected = @($taskMount.installed_mod_snapshot)
if ($taskBefore.Count -ne $taskExpected.Count) { throw 'Installed MOD set changed' }
foreach ($item in $taskExpected) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
$taskAllowed = @('pak','ucas','utoc' | ForEach-Object { 'zzzz_Sui_JiraiHairpin1_3_P.' + $_ })
if (@($taskGate.container_files).Count -ne 3) { throw 'Unexpected candidate file count' }
foreach ($item in $taskGate.container_files) {
    if ($item.name -notin $taskAllowed) { throw 'Unexpected candidate filename' }
    Assert-Hash (Join-Path (Join-Path $taskWork 'container') $item.name) $item.sha256
    if (Test-Path -LiteralPath (Join-Path $taskMods $item.name)) { throw 'Hairpin overlay already installed' }
}
$taskTime = [DateTimeOffset]::UtcNow.ToOffset([TimeSpan]::FromHours(8))
$taskRecord = Join-Path $taskWork ('installation-' + $taskTime.ToString('yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $taskRecord | Out-Null
Write-Json (Join-Path $taskRecord 'before.json') $taskBefore
try {
    foreach ($item in $taskGate.container_files) {
        Assert-GameExited
        [IO.File]::Copy((Join-Path (Join-Path $taskWork 'container') $item.name),(Join-Path $taskMods $item.name),$false)
        Assert-Hash (Join-Path $taskMods $item.name) $item.sha256
    }
    foreach ($item in $taskBefore) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
    $taskAfter = Snapshot
    if (@(Compare-Object @($taskExpected.name + $taskAllowed) @($taskAfter.name)).Count) { throw 'Unexpected final MOD set' }
    $taskReceipt = [ordered]@{status='installed-hash-verified-runtime-pending';installed_at=$taskTime.ToString('o');target=$taskMods;record=$taskRecord;before=$taskBefore;after=$taskAfter;added=$taskAllowed;previous_face3_r8_voice_files_exact=$true;source_atlas_sha256=$taskGate.source_atlas_sha256;native_render_sha256=$taskGate.native_render_sha256;game_runtime_tested=$false}
    Write-Json (Join-Path $taskWork 'installation-receipt.json') $taskReceipt
    Write-Json (Join-Path $taskRecord 'installation-receipt.json') $taskReceipt
    Write-Output ('HAIRPIN_INSTALLED_HASH_VERIFIED; record=' + $taskRecord)
} catch {
    $taskFailure = $_.Exception.Message
    foreach ($item in $taskGate.container_files) {
        $path = Join-Path $taskMods $item.name
        if (Test-Path -LiteralPath $path) {
            Assert-Hash $path $item.sha256
            Move-Item -LiteralPath $path -Destination (Join-Path $taskRecord $item.name)
        }
    }
    foreach ($item in $taskBefore) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
    Write-Json (Join-Path $taskRecord 'failed.json') @{reason=$taskFailure;status='Face3+R8 retained'}
    throw "Hairpin installation failed; original Face3 + R8 retained: $taskFailure"
}
