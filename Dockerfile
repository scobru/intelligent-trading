FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONUTF8=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg build-essential git sqlite3 dos2unix \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# SynFutures services differ between perp and neutral: build both
COPY agents/perp/synfutures-service/package*.json agents/perp/synfutures-service/tsconfig.json agents/perp/synfutures-service/
RUN cd agents/perp/synfutures-service && npm install --include=dev
COPY agents/neutral/synfutures-service/package*.json agents/neutral/synfutures-service/tsconfig.json agents/neutral/synfutures-service/
RUN cd agents/neutral/synfutures-service && npm install --include=dev
COPY . .
# one volume at /data, one subdir per agent (persistent_path() uses <agent>/data)
RUN cd agents/perp/synfutures-service && npm run build \
    && cd /app/agents/neutral/synfutures-service && npm run build \
    && cd /app \
    && find agents -name start.sh -exec dos2unix {} \; \
    && for a in coordinator perp yield neutral lp dca degen; do \
         mkdir -p /data/$a && rm -rf agents/$a/data && ln -s /data/$a agents/$a/data; \
       done
VOLUME /data
EXPOSE 3000
CMD ["python", "-u", "run.py"]
