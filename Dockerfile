FROM python:3.12-slim

WORKDIR /app

COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

COPY server/ server/
COPY client/ client/

WORKDIR /app/server
ENV PORT=8000
EXPOSE 8000

# --workers se deja fijo en 1 a proposito: el estado de las partidas vive en
# memoria del proceso (ver DEPLOY.md). Mas de un worker significaria que dos
# jugadores emparejados podrian terminar cada uno hablando con un proceso
# distinto que no sabe nada del otro.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
