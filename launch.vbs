Set shell = CreateObject("WScript.Shell")
root = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
pythonw = root & "\.venv\Scripts\pythonw.exe"
mainPy = root & "\main.py"
shell.Run """" & pythonw & """ """ & mainPy & """", 0, False
