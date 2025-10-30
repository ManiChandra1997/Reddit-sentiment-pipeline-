# Use a small, up-to-date Python base
FROM python:3.11-slim

# Build-time args for optional pip index or extra packages
ARG PIP_INDEX_URL=
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/app/.local/bin:${PATH}"
ENV STREAMLIT_SERVER_RUN_ON_SAVE=false
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLECORS=false

# Create a non-root user and working directory
RUN useradd --create-home --shell /bin/bash app
WORKDIR /app
USER app
COPY --chown=app:app requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
# Install dependencies as the non-root user into user site packages
RUN pip install --upgrade pip && \
    if [ -n "$PIP_INDEX_URL" ]; then pip config set global.index-url "$PIP_INDEX_URL"; fi && \
    pip install --user --no-cache-dir -r /app/requirements.txt

# Copy application sources
COPY --chown=app:app . /app

# Expose Streamlit port
EXPOSE 8501

# Default command to run the dashboard
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]