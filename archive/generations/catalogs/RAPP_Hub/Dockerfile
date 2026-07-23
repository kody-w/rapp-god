# RAPPhub Server - Serves published RAPPverse worlds
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn[standard]

# Copy everything
COPY . .

# Expose port
EXPOSE 8888

# Run server
CMD ["python", "server.py", "8888"]
