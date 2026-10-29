#!/usr/bin/env python3
"""Launcher do MCP opencode-vision — corrige o modelo Gemini hardcoded.

O pacote opencode-vision usa GEMINI_MODEL="gemini-2.5-flash" (descontinuado).
Este launcher troca o modelo para GEMINI_MODEL (padrao gemini-3.8-flash)
antes de subir o servidor MCP em stdio.
"""
import os

from opencode_vision import gemini

model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
gemini.GEMINI_MODEL = model
gemini.GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{model}:generateContent"
)

from opencode_vision.server import main  # noqa: E402

main()