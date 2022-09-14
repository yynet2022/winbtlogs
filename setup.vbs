Option Explicit
Dim fsys, fdir, shell, startupPath, fn, sc

Set fsys = CreateObject("Scripting.FileSystemObject")
fdir = fsys.GetParentFolderName(WScript.ScriptFullName)

Set shell = WScript.CreateObject("WScript.Shell")
startupPath = shell.SpecialFolders("Startup")

fn = startupPath + "\pconoff - ÇµÇÂÅ`Ç∆Ç©Ç¡Ç∆.lnk"
if fsys.FileExists(fn) then
   fsys.DeleteFile fn
end if

Set sc = shell.CreateShortcut(fn)
sc.TargetPath = fdir + "\pconoff.exe"
sc.WorkingDirectory = fdir
sc.save
