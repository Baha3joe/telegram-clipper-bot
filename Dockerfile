# Use a robust base image with Python 3.11 for AI tasks
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

ENV PYTHONUNBUFFERED=1
ENV PATH="/home/user/.local/bin:$PATH" # Set PATH to find locally installed binaries

# Install system dependencies (FFmpeg is required for moviepy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/user/app

# 1. Create the user
RUN useradd -m user

# 2. INSTALL DEPENDENCIES (using the safe --user flag and targeting the user's home)
# This prevents permission issues and ensures modules are accessible
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 3. CREATE DIRECTORIES AND SET PERMISSIONS (as root)
# The RUN commands run as root by default, so we create and change ownership
RUN mkdir -p downloads clips && chown -R user:user /home/user/app /home/user/.local

# 4. SWITCH TO THE LIMITED USER
USER user

# 5. COPY THE CODE
COPY --chown=user:user . .

# 6. Run the application
CMD ["python3", "bot.py"]
