Set shell = WScript.CreateObject("WScript.Shell")
startupPath = shell.SpecialFolders("Startup")

Set scf = shell.CreateShortcut(startupPath + "\pconoff - ����`�Ƃ�����.lnk")
scf.TargetPath = shell.CurrentDirectory + "\pconoff.exe"
scf.WorkingDirectory = shell.CurrentDirectory
scf.save

