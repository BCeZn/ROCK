# FastMCP HelloWorld Docker Image
# A simple MCP server built with FastMCP framework

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies using Aliyun mirror
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# Copy server code
COPY server.py .

# Expose port for streamable-http transport
EXPOSE 8080

# Set the entrypoint to run the MCP server
ENTRYPOINT ["python", "server.py"]
