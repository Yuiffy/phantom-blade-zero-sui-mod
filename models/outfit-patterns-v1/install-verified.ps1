$ErrorActionPreference='Stop'
$taskRepo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskWork=Join-Path $taskRepo 'private/outfit-patterns-v1'
$taskMods='F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods'
function Assert-GameExited {
 if(@(Get-Process | Where-Object {$_.ProcessName -match '(?i)PBZ|PhantomBlade'}).Count){throw 'PBZ is running; exit before installation.'}
}
function Assert-Hash($path,$expected){
 if(!(Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected.ToLowerInvariant()){throw "Missing or changed file: $path"}
}
function Snapshot {
 @(Get-ChildItem -LiteralPath $taskMods -File | Sort-Object Name | ForEach-Object {[ordered]@{name=$_.Name;bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}})
}
function Write-Json($path,$data){[IO.File]::WriteAllText($path,($data | ConvertTo-Json -Depth 25),[Text.UTF8Encoding]::new($false))}
Assert-GameExited
$taskGate=Get-Content -LiteralPath (Join-Path $taskWork 'verification.json') -Raw | ConvertFrom-Json
$taskSurface=Get-Content -LiteralPath (Join-Path $taskWork 'surface-verification.json') -Raw | ConvertFrom-Json
$taskMount=Get-Content -LiteralPath (Join-Path $taskWork 'mount-verification.json') -Raw | ConvertFrom-Json
$taskVisual=Get-Content -LiteralPath (Join-Path $taskWork 'visual-review.json') -Raw | ConvertFrom-Json
if(!$taskGate.passed -or $taskGate.package_count -ne 2 -or !$taskGate.no_mesh_material_physics_or_gameplay_packages -or !$taskSurface.passed -or !$taskMount.passed -or !$taskMount.directory_order_independent -or !$taskVisual.reviewed){throw 'Missing final verification'}
foreach($taskTexture in $taskGate.textures){
 $taskOutfit=$taskTexture.outfit
 $taskHash=$taskTexture.source_sha256
 if($taskSurface.outfits.$taskOutfit.output_atlas_sha256 -ne $taskHash -or $taskMount.texture_hashes.$taskOutfit -ne $taskHash -or $taskVisual.texture_hashes.$taskOutfit -ne $taskHash){throw 'Stale verification'}
 Assert-Hash (Join-Path $taskWork ($taskOutfit+'-after.png')) $taskHash
 Assert-Hash (Join-Path $taskWork ($taskOutfit+'-native.npz')) $taskSurface.outfits.$taskOutfit.source_native_sha256
}
foreach($taskImage in $taskVisual.images.PSObject.Properties){Assert-Hash $taskImage.Name $taskImage.Value}
$taskBefore=Snapshot
$taskExpected=@($taskMount.installed_mod_snapshot)
if($taskBefore.Count -ne $taskExpected.Count){throw 'Installed MOD set changed'}
foreach($taskItem in $taskExpected){Assert-Hash (Join-Path $taskMods $taskItem.name) $taskItem.sha256}
$taskAllowed=@('pak','ucas','utoc' | ForEach-Object {'zzzzz_Sui_OutfitPatterns1_4_P.'+$_})
if(@($taskGate.container_files).Count -ne 3){throw 'Unexpected candidate file count'}
foreach($taskItem in $taskGate.container_files){
 if($taskItem.name -notin $taskAllowed){throw 'Unexpected candidate filename'}
 Assert-Hash (Join-Path (Join-Path $taskWork 'container') $taskItem.name) $taskItem.sha256
 if(Test-Path -LiteralPath (Join-Path $taskMods $taskItem.name)){throw 'Patterns overlay already installed'}
}
$taskTime=[DateTimeOffset]::UtcNow.ToOffset([TimeSpan]::FromHours(8))
$taskRecord=Join-Path $taskWork ('installation-'+$taskTime.ToString('yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $taskRecord | Out-Null
Write-Json (Join-Path $taskRecord 'before.json') $taskBefore
try {
 foreach($taskItem in $taskGate.container_files){
  Assert-GameExited
  [IO.File]::Copy((Join-Path (Join-Path $taskWork 'container') $taskItem.name),(Join-Path $taskMods $taskItem.name),$false)
  Assert-Hash (Join-Path $taskMods $taskItem.name) $taskItem.sha256
 }
 foreach($taskItem in $taskBefore){Assert-Hash (Join-Path $taskMods $taskItem.name) $taskItem.sha256}
 $taskAfter=Snapshot
 if(@(Compare-Object @($taskExpected.name+$taskAllowed) @($taskAfter.name)).Count){throw 'Unexpected final MOD set'}
 $taskReceipt=[ordered]@{status='installed-hash-verified-runtime-pending';installed_at=$taskTime.ToString('o');target=$taskMods;record=$taskRecord;before=$taskBefore;after=$taskAfter;added=$taskAllowed;previous_face3_r8_hairpin_voice_files_exact=$true;texture_hashes=$taskMount.texture_hashes;game_runtime_tested=$false}
 Write-Json (Join-Path $taskWork 'installation-receipt.json') $taskReceipt
 Write-Json (Join-Path $taskRecord 'installation-receipt.json') $taskReceipt
 Write-Output 'OUTFIT_PATTERNS_INSTALLED_HASH_VERIFIED'
} catch {
 $taskFailure=$_.Exception.Message
 foreach($taskItem in $taskGate.container_files){
  $taskPath=Join-Path $taskMods $taskItem.name
  if(Test-Path -LiteralPath $taskPath){Assert-Hash $taskPath $taskItem.sha256;Move-Item -LiteralPath $taskPath -Destination (Join-Path $taskRecord $taskItem.name)}
 }
 foreach($taskItem in $taskBefore){Assert-Hash (Join-Path $taskMods $taskItem.name) $taskItem.sha256}
 throw "Patterns installation failed; previous installation retained: $taskFailure"
}
