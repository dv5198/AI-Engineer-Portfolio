FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install native dependencies required by Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libxkbcommon0 \
    libgbm1 \
    libpangocairo-1.0-0 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
# Use the correct dependency list, falling back if pip complains about variants
RUN pip install --no-cache-dir -r requirements.txt

# Install explicitly required playwright browsers (Chromium for PDF)
RUN playwright install chromium
RUN playwright install-deps

# Copy backend source code
COPY . .

# Expose FastAPI listening port
EXPOSE 8000

# Start server using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
