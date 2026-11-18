$ErrorActionPreference = 'Stop'
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$taskWork = [IO.Path]::GetFullPath((Join-Path $taskRepo 'private/jirai-hairpin-v1'))
$taskReceipt = Get-Content -LiteralPath (Join-Path $taskWork 'installation-receipt.json') -Raw | ConvertFrom-Json
$taskMods = 'F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods'
if ($taskReceipt.target -ne $taskMods) { throw 'Unexpected MOD directory' }
$taskRecord = [IO.Path]::GetFullPath($taskReceipt.record)
if (!$taskRecord.StartsWith($taskWork + [IO.Path]::DirectorySeparatorChar)) { throw 'Record outside hairpin workspace' }
function Assert-GameExited {
    if (@(Get-Process | Where-Object { $_.ProcessName -match '(?i)PBZ|PhantomBlade' }).Count) { throw 'PBZ is running; exit before rollback.' }
}
function Assert-Hash($path,$hash) {
    if (!(Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hash) { throw "Missing or changed file: $path" }
}
Assert-GameExited
if (@(Get-ChildItem -LiteralPath $taskMods -File).Count -ne @($taskReceipt.after).Count) { throw 'MOD set changed since installation' }
foreach ($item in $taskReceipt.after) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
$taskExpected = @('pak','ucas','utoc' | ForEach-Object { 'zzzz_Sui_JiraiHairpin1_3_P.' + $_ })
if (@(Compare-Object $taskExpected @($taskReceipt.added)).Count) { throw 'Unexpected rollback scope' }
$taskRetired = Join-Path $taskRecord 'hairpin-rolled-back'
if (Test-Path -LiteralPath $taskRetired) { throw 'Rollback already recorded' }
New-Item -ItemType Directory -Path $taskRetired | Out-Null
try {
    foreach ($name in $taskExpected) {
        Assert-GameExited
        Move-Item -LiteralPath (Join-Path $taskMods $name) -Destination (Join-Path $taskRetired $name)
    }
    foreach ($item in $taskReceipt.before) { Assert-Hash (Join-Path $taskMods $item.name) $item.sha256 }
    Write-Output 'FACE3_AND_R8_RESTORED_HASH_VERIFIED'
} catch {
    foreach ($name in $taskExpected) {
        $path = Join-Path $taskRetired $name
        if (Test-Path -LiteralPath $path) { Move-Item -LiteralPath $path -Destination (Join-Path $taskMods $name) }
    }
    throw
}
