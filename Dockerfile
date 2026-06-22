# syntax=docker/dockerfile:1
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        asymptote \
        ghostscript \
        texlive-latex-base \
        texlive-fonts-recommended \
        texlive-lang-cjk \
        texlive-lang-chinese \
        fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY asyagent/ /app/asyagent/

ENV ASYAGENT_HOST=0.0.0.0 \
    ASYAGENT_PORT=8787 \
    ASYAGENT_LOCAL_DIR=/data/storage \
    ASYAGENT_INSTALL_SKILLUTILS=true \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

RUN mkdir -p /data/storage && python3 -c "import asyagent; print('asyagent', asyagent.__version__)"

EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8787/healthz', timeout=3); sys.exit(0)" || exit 1

CMD ["python3", "-m", "asyagent"]
