FROM ghcr.io/livebook-dev/livebook:latest-cuda12

ENV LIVEBOOK_APP_SERVICE_NAME="🐳 Hugging Face - $SPACE_TITLE"
ENV LIVEBOOK_APP_SERVICE_URL="https://huggingface.co/spaces/$SPACE_AUTHOR_NAME/$SPACE_REPO_NAME"
ENV LIVEBOOK_UPDATE_INSTRUCTIONS_URL="https://livebook.dev"
ENV LIVEBOOK_WITHIN_IFRAME="true"
ENV LIVEBOOK_APPS_PATH="/public-apps"
ENV LIVEBOOK_APPS_PATH_WARMUP="manual"
ENV LIVEBOOK_DATA_PATH="/data"
ENV LIVEBOOK_PORT="7860"

EXPOSE 7860

RUN mkdir -p /data
RUN chmod 777 /data

# The Space container runs with user ID 1000, which corresponds to
# ubuntu in the Livebook image.
ENV HOME="/home/ubuntu"

USER ubuntu

COPY --chown=ubuntu public-apps/ /public-apps
RUN /app/bin/warmup_apps
