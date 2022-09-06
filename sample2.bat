@powershell -NoProfile -ExecutionPolicy Unrestricted "$s=[scriptblock]::create((gc \"%~f0\"|?{$_.readcount -gt 1})-join\"`n\");&$s" %*&goto:eof

# GET-WinEvent -ListProvider *
$csv=GET-Date -UFormat "W_%Y%m%d_%H%M%S.csv"

$a=GET-WinEvent -FilterHashtable @{
   LogName='System'
   ProviderName='*Kernel-Power', '*Kernel-Boot', '*Windows-Winlogon'
} | Where-Object{$_.Id -ne 566}
# $a.count

$b=GET-WinEvent -FilterHashtable @{
   LogName='System'
   Id=6005,6006,6008
}
# $b.count

$a + $b | `
Select-Object TimeCreated,ProviderName,Id,LevelDisplayName,Message | `
Sort-Object -Property TimeCreated | `
Export-CSV $csv -NoTypeInformation -Encoding UTF8
