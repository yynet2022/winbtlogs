Set shell = WScript.CreateObject("WScript.Shell")
startupPath = shell.SpecialFolders("Startup")

Set scf = shell.CreateShortcut(startupPath + "\pconoff - しょ〜とかっと.lnk")
scf.TargetPath = shell.CurrentDirectory + "\pconoff.exe"
scf.WorkingDirectory = shell.CurrentDirectory
scf.save

