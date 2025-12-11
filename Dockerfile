# 🚨 CHANGE: Use a base image with PyTorch and CUDA pre-installed 🚨
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies (FFmpeg is still required for moviepy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /home/user/app

# Install remaining Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt # Build Timestamp: 2025-12-11-Final-Attempt-3

# Create user for security
RUN useradd -m user
USER user

# Create necessary directories
RUN mkdir -p downloads clips

# Copy the rest of the application code
COPY --chown=user:user . .

# Run the application
CMD ["python", "bot.py"]