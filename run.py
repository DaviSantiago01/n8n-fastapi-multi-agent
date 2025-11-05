#!/usr/bin/env python3
"""
Startup script para Railway
Lê a variável PORT e inicia uvicorn programaticamente
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"🚀 Iniciando servidor na porta {port}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
