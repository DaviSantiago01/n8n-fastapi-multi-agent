#!/bin/bash
# Script de startup para Railway
PORT=${PORT:-8000}
exec uvicorn main:app --host 0.0.0.0 --port $PORT
