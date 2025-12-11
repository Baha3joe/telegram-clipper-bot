# Use a lighter PyTorch image to save space and time
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

ENV PYTHONUNBUFFERED=1

# Install system dependencies
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

# 2. INSTALL DEPENDENCIES FIRST (as root)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. CREATE DIRECTORIES AND SET PERMISSIONS (as root)
RUN mkdir -p downloads clips && chown -R user:user /home/user/app

# 4. NOW SWITCH TO THE USER
USER user

# 5. COPY THE CODE
COPY --chown=user:user . .

CMD ["python3", "bot.py"]