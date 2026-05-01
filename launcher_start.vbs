' Запуск GUI-лаунчера без окна консоли (вызывается из launcher.bat).
Option Explicit
Dim sh, fso, dir, py
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
py = dir & "\launcher.py"
sh.CurrentDirectory = dir
sh.Run "pyw -3 " & Chr(34) & py & Chr(34), 0, False
