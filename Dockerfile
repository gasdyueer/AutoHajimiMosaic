FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Install dependencies
ENV DEBIAN_FRONTEND=noninteractive
COPY packages.txt /app/packages.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends $(cat /app/packages.txt) && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
ENV VIRTUAL_ENV=/opt/venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv $VIRTUAL_ENV && \
    uv pip install --extra-index-url https://download.pytorch.org/whl/cpu torch torchvision && \
    uv pip install -r /app/requirements.txt

# Copy application code
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY . /app
WORKDIR /app
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "app.py"]
CMD ["--server.enableCORS=false", "--server.enableXsrfProtection=false", "--server.port=8501"]