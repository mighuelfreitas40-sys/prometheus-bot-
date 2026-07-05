FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends     lua5.1     luajit     git     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clona os deobfuscadores
RUN git clone https://github.com/0x251/Prometheus-Deobfuscator.git /app/deob-v1 &&     git clone https://github.com/0x251/Prometheus-DeobfuscatorV2.git /app/deob-v2 &&     git clone https://github.com/wcrddn/Prometheus.git /app/deob-v2/Prometheus

COPY . .

CMD ["python", "bot.py"]
