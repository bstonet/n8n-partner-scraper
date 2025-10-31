# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependency list first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app code
COPY . .

# Environment variable for Railway
ENV PORT=8000

# Expose port (for clarity; not strictly required by Railway)
EXPOSE 8000

# Start FastAPI using the PORT env var that Railway provides
# The ${PORT:-8000} ensures it defaults to 8000 locally if PORT isn't set
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

