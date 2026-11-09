@echo off
title AgroTrap Monitor - División Agropecuaria
cd /d "%~dp0"
echo Iniciando servidor AgroTrap Monitor...
start http://127.0.0.1:8000
python -m uvicorn main:app --reload