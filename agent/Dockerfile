FROM espressif/idf:latest

WORKDIR /workspace

# Copiar aplicación del agente
COPY app /agent

# Instalar dependencias Python para el agente
RUN python3 -m pip install --upgrade pip && \
    pip install langchain langchain-community openai rich

# Comando por defecto para ejecutar el agente
CMD ["bash", "-lc", "python3 /agent/agent.py"]
