Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

base = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = base & "\venv\Scripts\pythonw.exe"
app = base & "\app.py"

If Not fso.FileExists(pythonw) Then
  MsgBox "Invoice Emailer setup is not complete. Run install.bat first.", vbExclamation, "Invoice Emailer"
  WScript.Quit 1
End If

shell.CurrentDirectory = base
shell.Run """" & pythonw & """ """ & app & """", 0, False
