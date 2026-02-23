# Use a minimal Python 3.12 image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Set the PYTHONPATH environment variable
ENV PYTHONPATH=/app

# Copy only the requirements file first (leveraging Docker cache)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --timeout=60 --prefer-binary -r requirements.txt

# Copy only the necessary directories
COPY src /app/src

# Run the database script at build time
RUN python src/db/populate_database.py || echo "Database script failed during build"

# Expose the application port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "src.app.app:app", "--host", "0.0.0.0", "--port", "8000"]