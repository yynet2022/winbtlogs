Option Explicit
Dim fsys, fdir, shell, startupPath, sc

Set fsys = CreateObject("Scripting.FileSystemObject")
fdir = fsys.GetParentFolderName(WScript.ScriptFullName)

Set shell = WScript.CreateObject("WScript.Shell")
startupPath = shell.SpecialFolders("Startup")

Set sc = shell.CreateShortcut(startupPath + "\pconoff - ÇµÇÂÅ`Ç∆Ç©Ç¡Ç∆.lnk")
sc.TargetPath = fdir + "\pconoff.exe"
sc.WorkingDirectory = fdir
sc.save

