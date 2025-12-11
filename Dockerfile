# 1. BASE IMAGE: Use a stable and supported Python image (3.12 on Debian Bookworm).
FROM python:3.12-slim-bookworm

# 2. INSTALL SYSTEM DEPENDENCIES: Install necessary libraries (ffmpeg, MoviePy dependencies, tini).
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
        tini && \
    rm -rf /var/lib/apt/lists/*

# 3. SETUP USER AND DIRECTORY: Create the non-root user and app directory.
# CRITICAL FIX: Added -m (create home directory) flag to useradd.
RUN groupadd -r user && useradd -r -g user -m user && \
    mkdir /home/user/app && chown -R user:user /home/user/app
WORKDIR /home/user/app

# 4. COPY CODE
COPY . .

# 5. SWITCH USER: Ensure subsequent commands run as non-root.
USER user

# 6. INSTALL PYTHON DEPENDENCIES: Installed as the non-root 'user'.
RUN pip install --no-cache-dir -r requirements.txt

# 7. CREATE WORKING DIRECTORIES: Created as the non-root 'user'.
RUN mkdir -p downloads clips

# 8. EXPOSE PORT (Optional, if your bot uses webhooks)
EXPOSE 8080

# 9. RUN BOT: Use tini for proper signal handling.
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python3", "bot.py"]