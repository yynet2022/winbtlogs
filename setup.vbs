Set shell = WScript.CreateObject("WScript.Shell")
startupPath = shell.SpecialFolders("Startup")

Set scf = shell.CreateShortcut(startupPath + "\pconoff - ÇµÇÂÅ`Ç∆Ç©Ç¡Ç∆.lnk")
scf.TargetPath = shell.CurrentDirectory + "\pconoff.exe"
scf.WorkingDirectory = shell.CurrentDirectory
scf.save

