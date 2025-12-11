import os
import sys
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# CORRECT IMPORT: Ensure this function name exactly matches the definition in video_utils.py
from video_utils import process_youtube_clip

# --- Logging Configuration ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configuration ---
# 1. Fetch token securely from environment variable (Hugging Face Secret)
TOKEN = os.getenv("BOT_TOKEN") 

# 2. Safety check for the token
if not TOKEN:
    logger.error("FATAL: BOT_TOKEN is missing. Please set it as a Hugging Face Secret.")
    sys.exit(1)

# 3. Define local directories (Crucial for Docker environment)
DOWNLOAD_DIR = "downloads"
CLIP_DIR = "clips"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(CLIP_DIR, exist_ok=True)

# --- Command Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    logger.info(f"Received /start command from user {update.effective_user.id}")
    await update.message.reply_text(
        '👋 Welcome to the AI Telegram Video Clipper Bot!\n\n'
        'Send me a YouTube video link and specify the start and end times '
        '(e.g., `https://youtu.be/example 0:30-1:00`).\n\n'
        'I will generate the clip, transcribe the audio, and send the final video back!'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles messages containing a potential YouTube link."""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    # Simple check to filter out non-link/non-command messages
    if "youtu" not in user_message or "-" not in user_message:
        return
        
    try:
        # Separate link and time frame
        parts = user_message.split()
        url = parts[0]
        time_range = parts[1] if len(parts) > 1 else None

        if not time_range or len(parts) < 2:
            await update.message.reply_text(
                "Please specify the clip range (e.g., `1:30-2:00`) after the link."
            )
            return

        await update.message.reply_text(f"Processing your request for {time_range}. This might take a few minutes...")
        logger.info(f"User {user_id} requested clip: {url} from {time_range}")
        
        # 4. Call the core processing function (MUST MATCH THE IMPORT NAME)
        final_clip_path, caption = await process_youtube_clip(
            url, 
            time_range, 
            DOWNLOAD_DIR, 
            CLIP_DIR, 
            user_id,
            logger
        )

        if final_clip_path:
            # 5. Send the final video back
            logger.info(f"Sending final clip to user {user_id}: {final_clip_path}")
            
            # Create a caption that includes the transcription
            full_caption = f"✅ Clip ({time_range}) from video.\n\n"
            if caption:
                full_caption += f"Transcription:\n{caption}"
            
            await update.message.reply_video(
                video=open(final_clip_path, 'rb'),
                caption=full_caption,
                supports_streaming=True,
                read_timeout=600, # Allow longer timeout for large video uploads
                write_timeout=600,
                pool_timeout=600
            )
            
        else:
            await update.message.reply_text(
                "❌ Error processing your clip. Check the URL/time format (e.g., 0:30-1:00) or ensure the video is public."
            )

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        await update.message.reply_text("An unexpected error occurred. Check the format and try again.")
        
    finally:
        # NOTE: Cleanup should primarily happen inside process_youtube_clip
        pass


# --- Main Application Runner ---

def main() -> None:
    """Start the bot."""
    logger.info("Starting Telegram Application...")
    
    # 1. Build the application
    application = Application.builder().token(TOKEN).build()

    # 2. Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_message
    ))

    # 3. Start polling
    logger.info("Bot is ready. Starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Bot polling stopped.")

if __name__ == "__main__":
    main()