# 1. Base Image
FROM python:3.11-slim

# 2. Install System Dependencies (FFmpeg, ImageMagick)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    imagemagick \
    # Clean up APT files to keep the image small
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Create and Switch to a Non-Root User
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user

# 4. Set Working Directory
WORKDIR $HOME/app

# 5. Install Python Dependencies
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy Application Code
COPY --chown=user:user . .

# 7. Create Temporary Folders
RUN mkdir -p downloads clips

# 8. Start the Bot
CMD ["python", "bot.py"]