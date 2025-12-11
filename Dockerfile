# 1. Base Image: Uses PyTorch base to avoid installation failures for numpy/torch
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

# Environment Variables
ENV PYTHONUNBUFFERED=1
# Set PATH to find locally installed binaries (crucial for yt-dlp, whisper)
ENV PATH="/home/user/.local/bin:$PATH" 

# Install system dependencies (FFmpeg is required for moviepy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/user/app

# 2. Create the non-root user
RUN useradd -m user

# 3. Install remaining Python dependencies with --user flag
# This installs packages into the user's local directory, bypassing system conflicts.
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 4. Create directories and set full ownership/permissions
# This must run as root before switching to the limited user.
RUN mkdir -p downloads clips && chown -R user:user /home/user/app /home/user/.local

# 5. Switch to the limited user for security and runtime execution
USER user

# 6. Copy application code (owned by 'user')
COPY --chown=user:user . .

# 7. Run the application
CMD ["python3", "bot.py"]