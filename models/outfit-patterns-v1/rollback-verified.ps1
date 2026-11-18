$ErrorActionPreference='Stop'
$taskRepo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskWork=[IO.Path]::GetFullPath((Join-Path $taskRepo 'private/outfit-patterns-v1'))
$taskReceipt=Get-Content -LiteralPath (Join-Path $taskWork 'installation-receipt.json') -Raw | ConvertFrom-Json
$taskMods='F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods'
if($taskReceipt.target -ne $taskMods){throw 'Unexpected MOD directory'}
$taskRecord=[IO.Path]::GetFullPath($taskReceipt.record)
if(!$taskRecord.StartsWith($taskWork+[IO.Path]::DirectorySeparatorChar)){throw 'Record outside patterns workspace'}
function Assert-Exited {if(@(Get-Process | Where-Object {$_.ProcessName -match '(?i)PBZ|PhantomBlade'}).Count){throw 'PBZ is running; exit before rollback.'}}
function Assert-Hash($path,$hash){if(!(Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hash){throw "Missing or changed file: $path"}}
Assert-Exited
if(@(Get-ChildItem -LiteralPath $taskMods -File).Count -ne @($taskReceipt.after).Count){throw 'MOD set changed since installation'}
foreach($taskItem in $taskReceipt.after){Assert-Hash (Join-Path $taskMods $taskItem.name) $taskItem.sha256}
$taskNames=@('pak','ucas','utoc' | ForEach-Object {'zzzzz_Sui_OutfitPatterns1_4_P.'+$_})
if(@(Compare-Object $taskNames @($taskReceipt.added)).Count){throw 'Unexpected rollback scope'}
$taskRetired=Join-Path $taskRecord 'patterns-rolled-back'
if(Test-Path -LiteralPath $taskRetired){throw 'Rollback already recorded'}
New-Item -ItemType Directory -Path $taskRetired | Out-Null
try {
 foreach($taskName in $taskNames){Assert-Exited;Move-Item -LiteralPath (Join-Path $taskMods $taskName) -Destination (Join-Path $taskRetired $taskName)}
 foreach($taskItem in $taskReceipt.before){Assert-Hash (Join-Path $taskMods $taskItem.name) $taskItem.sha256}
 Write-Output 'HAIRPIN_FACE3_R8_RESTORED_HASH_VERIFIED'
} catch {
 foreach($taskName in $taskNames){$taskPath=Join-Path $taskRetired $taskName;if(Test-Path -LiteralPath $taskPath){Move-Item -LiteralPath $taskPath -Destination (Join-Path $taskMods $taskName)}}
 throw
}
