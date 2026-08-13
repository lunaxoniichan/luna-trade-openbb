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

# Overlay fork patch onto the PyPI openbb-cftc pulled by the umbrella package.
# Upstream CFTC catalog can return None subcategory/code; unguarded .strip()
# crashes FastAPI startup (build_choices) so port 6900 never binds.
COPY external_libs/luna-trade-openbb/openbb_platform/providers/cftc/openbb_cftc/cftc_router.py /tmp/cftc_router.py
RUN python -c "import pathlib, shutil; import openbb_cftc; shutil.copy('/tmp/cftc_router.py', pathlib.Path(openbb_cftc.__file__).parent / 'cftc_router.py')"

EXPOSE 6900

# Launch the OpenBB Platform API
CMD ["python", "-m", "openbb_platform.extensions.platform_api.openbb_platform_api.main"]


