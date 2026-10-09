' Lancador Silencioso para Sollaris Nova (Zero Console Window)
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
ProjectRoot = FSO.GetParentFolderName(ScriptDir)
VenvPythonw = ProjectRoot & "\.venv\Scripts\pythonw.exe"
MainPy = ProjectRoot & "\main.py"
RunBat = ScriptDir & "\run.bat"

' Se o ambiente virtual nao existir, executa o setup automatico via run.bat
If Not FSO.FileExists(VenvPythonw) Then
    WshShell.Run Chr(34) & RunBat & Chr(34), 1, True
End If

' Executa a aplicacao com pythonw.exe sem nenhuma janela de console preta (modo 0)
If FSO.FileExists(VenvPythonw) Then
    WshShell.CurrentDirectory = ProjectRoot
    WshShell.Run Chr(34) & VenvPythonw & Chr(34) & " " & Chr(34) & MainPy & Chr(34), 0, False
End If

Set WshShell = Nothing
Set FSO = Nothing
