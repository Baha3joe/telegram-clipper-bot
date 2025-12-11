FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies (FFmpeg is required for moviepy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /home/user/app

# Create user for security
RUN useradd -m user
USER user

# Install sensitive Python dependencies (Torch and NumPy first)
# This layer MUST be separate to guarantee correct dependency linking
RUN pip install --no-cache-dir numpy torch # Final binary dependency fix

# Install remaining Python dependencies
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt # Build Timestamp: 2025-12-11-Final-Attempt-2

# Create necessary directories
RUN mkdir -p downloads clips

# Copy the rest of the application code
COPY --chown=user:user . .

# Run the application
CMD ["python", "bot.py"]