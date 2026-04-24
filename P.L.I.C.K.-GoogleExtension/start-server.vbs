' Start server in background (hidden)
Set objFSO = CreateObject("Scripting.FileSystemObject")
strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
Set objShell = CreateObject("WScript.Shell")

' Run setup.bat hidden
objShell.Run "cmd /c cd /d " & strPath & " && python Backend/server.py", 0, False

' Show message
objShell.Popup "Server started in background!" & vbCrLf & "Running at: http://localhost:8000", 2, "P.L.I.C.K. Setting", 64
