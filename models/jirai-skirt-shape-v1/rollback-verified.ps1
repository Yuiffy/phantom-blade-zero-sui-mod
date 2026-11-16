param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskWork = Join-Path $taskRepo 'private/jirai-skirt-shape-v1/dual'
$taskMods = 'F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods'
$taskReceipt = Get-Content -LiteralPath (Join-Path $taskWork 'installation-receipt.json') -Raw | ConvertFrom-Json
if ([IO.Path]::GetFullPath($taskReceipt.target) -ne [IO.Path]::GetFullPath($taskMods)) { throw 'Receipt target differs' }
$taskBackup = [IO.Path]::GetFullPath($taskReceipt.backup)
if (!$taskBackup.StartsWith(([IO.Path]::GetFullPath($taskWork) + [IO.Path]::DirectorySeparatorChar),[StringComparison]::OrdinalIgnoreCase)) { throw 'Backup outside candidate workspace' }
function Assert-File($root,$entry) {
 if ([IO.Path]::GetFileName($entry.name) -ne $entry.name) { throw 'Invalid receipt filename' }
 $path = Join-Path $root $entry.name
 if (!(Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw "File changed: $path" }
}
function Assert-Set($entries) {
 $names = @(Get-ChildItem -LiteralPath $taskMods -File | ForEach-Object Name)
 if (@(Compare-Object @($entries | ForEach-Object name) $names).Count) { throw 'Installed file set differs' }
 foreach ($entry in $entries) { Assert-File $taskMods $entry }
}
$taskOld = @($taskReceipt.before | Where-Object name -like 'z_Sui_DualOutfit_JK5_JiraiR7Recovery1_P.*')
$taskNew = @($taskReceipt.after | Where-Object name -like 'z_Sui_DualOutfit_JK5_JiraiR8Shape1_P.*')
foreach ($triple in @(@{files=$taskOld;stem='z_Sui_DualOutfit_JK5_JiraiR7Recovery1_P'},@{files=$taskNew;stem='z_Sui_DualOutfit_JK5_JiraiR8Shape1_P'})) {
 $expected = @('pak','ucas','utoc' | ForEach-Object { $triple.stem + '.' + $_ })
 if (@($triple.files).Count -ne 3 -or @(Compare-Object $expected @($triple.files | ForEach-Object name)).Count) { throw 'Invalid model triple' }
}
foreach ($entry in $taskOld) { Assert-File $taskBackup $entry }
$taskNames = @(Get-ChildItem -LiteralPath $taskMods -File | ForEach-Object Name)
if (@($taskOld | Where-Object { $_.name -in $taskNames }).Count -eq 3) {
 Assert-Set $taskReceipt.before
 Write-Output 'ALREADY_RESTORED_HASH_VERIFIED'
 return
}
Assert-Set $taskReceipt.after
if (!$Apply) { Write-Output 'ROLLBACK_READY_HASH_VERIFIED; no files changed'; return }
if (@(Get-Process | Where-Object ProcessName -match '(?i)PBZ|PhantomBlade').Count) { throw 'Exit PBZ before rollback' }
$taskQuarantine = Join-Path $taskWork ('rolled-back-' + [DateTimeOffset]::UtcNow.ToString('yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $taskQuarantine | Out-Null
try {
 foreach ($entry in $taskNew) { Move-Item -LiteralPath (Join-Path $taskMods $entry.name) -Destination (Join-Path $taskQuarantine $entry.name) }
 foreach ($entry in $taskOld) { Copy-Item -LiteralPath (Join-Path $taskBackup $entry.name) -Destination (Join-Path $taskMods $entry.name) }
 Assert-Set $taskReceipt.before
 Write-Output 'RECOVERY1_RESTORED_HASH_VERIFIED; Face2 and voice preserved'
} catch {
 $taskFailure = $_.Exception.Message
 foreach ($entry in $taskOld) {
  $path = Join-Path $taskMods $entry.name
  if (Test-Path -LiteralPath $path) { Move-Item -LiteralPath $path -Destination (Join-Path $taskQuarantine $entry.name) }
 }
 foreach ($entry in $taskNew) {
  $path = Join-Path $taskQuarantine $entry.name
  if (Test-Path -LiteralPath $path) { Copy-Item -LiteralPath $path -Destination (Join-Path $taskMods $entry.name) }
 }
 Assert-Set $taskReceipt.after
 throw "Rollback failed; R8 restored: $taskFailure"
}
