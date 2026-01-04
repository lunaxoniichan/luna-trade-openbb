FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OPENBB_API_HOST=0.0.0.0 \
    OPENBB_API_PORT=6900

RUN pip install --no-cache-dir --upgrade pip

# Copy and install the OpenBB Platform (local fork subset)
COPY external_libs/luna-trade-openbb/openbb_platform /app/openbb_platform
RUN pip install --no-cache-dir /app/openbb_platform || true

EXPOSE 6900

# Launch the OpenBB Platform API
CMD ["python", "-m", "openbb_platform.extensions.platform_api.openbb_platform_api.main"]


