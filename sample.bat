@powershell -NoProfile -ExecutionPolicy Unrestricted "$s=[scriptblock]::create((gc \"%~f0\"|?{$_.readcount -gt 1})-join\"`n\");&$s" %*&goto:eof

# GET-WinEvent -ListProvider *
$csv=GET-Date -UFormat "W_%Y%m%d_%H%M%S.csv"
GET-WinEvent -FilterHashtable @{
   LogName='System'
   ProviderName='*Kernel-Power', '*Kernel-Boot', '*Windows-Winlogon'
} | Where-Object{$_.Id -ne 566} | `
Select-Object TimeCreated,ProviderName,Id,LevelDisplayName,Message | `
Sort-Object -Property TimeCreated | `
Export-CSV $csv -Encoding UTF8
