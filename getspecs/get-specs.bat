@echo off
REM or enter your path to the powershell script
PowerShell -NoProfile -ExecutionPolicy Bypass -File "%USERPROFILE%\Documents\dotfiles\getspecs\Get-Specs.ps1"
REM Opens the text file of the device specs
start "" "%USERPROFILE%\Desktop\specs.txt"