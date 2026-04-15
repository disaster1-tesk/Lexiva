@echo off
chcp 65001 >nul
title Lexiva AI 英语学习系统
python "%~dp0run.py" %*
