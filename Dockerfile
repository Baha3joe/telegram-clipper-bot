# 1. BASE IMAGE: Use a stable and smaller Debian-based Python image
FROM python:3.10-slim-buster

# 2. INSTALL SYSTEM DEPENDENCIES: Install necessary libraries for FFmpeg/MoviePy and other tools.
# 'tini' is used as an init system for graceful shutdown on Railway.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
        tini && \
    rm -rf /var/lib/apt/lists/*

# 3. SETUP USER AND DIRECTORY: Create the non-root user and app directory.
RUN groupadd -r user && useradd -r -g user user && \
    mkdir /home/user/app && chown -R user:user /home/user/app
WORKDIR /home/user/app

# 4. COPY CODE
COPY . .

# 5. CRITICAL FIX: Switch to the non-root user *before* installing packages.
# This ensures all installed files and directories belong to 'user'.
USER user

# 6. INSTALL PYTHON DEPENDENCIES: This will automatically create /home/user/.local 
# and own it with 'user', resolving your previous permission error.
RUN pip install --no-cache-dir -r requirements.txt

# 7. CREATE WORKING DIRECTORIES: Create the folders the bot needs for processing.
# This runs as 'user', so no 'chown' is needed.
RUN mkdir -p downloads clips

# 8. EXPOSE PORT: Railway will automatically map a public port to this internal port.
# If your bot is a web-hook listener, it needs a port. If it's a long-polling bot, 
# this line is technically optional but good practice.
EXPOSE 8080

# 9. RUN BOT: Use tini as the entrypoint for proper signal handling (recommended for Docker).
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python3", "bot.py"]