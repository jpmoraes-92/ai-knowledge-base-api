# Usa uma versão leve e oficial do Python 3.11
FROM python:3.11-slim

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Instala bibliotecas do sistema (necessárias para o C++ do FAISS e do PyMuPDF funcionarem no Linux)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de requisitos e instala (isto usa o cache do Docker para ir mais rápido)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da sua aplicação para dentro do container
COPY . .

# Liberta a porta 8000
EXPOSE 8000

# O comando mestre que o container vai rodar quando nascer
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]