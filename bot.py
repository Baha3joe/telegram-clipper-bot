import os
import sys
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from video_utils import process_video_clip

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configuration ---
# ⚠️ WARNING: Hardcoding the token is strongly discouraged for security reasons.
# Use Hugging Face Secrets instead.
# If you must hardcode it, replace the line below with the token you provided:
# TOKEN = "8575159633:AAHt8KYNKLrWKID8FOyZipEcPAxZ_zdjgg4" 
#
# If you are using Hugging Face Secrets (RECOMMENDED):
TOKEN = os.getenv("BOT_TOKEN") 

# Ensure the token is available
if not TOKEN:
    logger.error("FATAL: BOT_TOKEN is missing. Please set it as a Hugging Face Secret.")
    sys.exit(1)

# Ensure necessary directories exist
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
    
    # 1. Simple check for a link and time format
    if "youtu" not in user_message and "0:" not in user_message and "1:" not in user_message:
        logger.info(f"User {user_id} sent non-link message: {user_message[:20]}...")
        return
        
    try:
        # Separate link and time frame
        parts = user_message.split()
        url = parts[0]
        time_range = parts[1] if len(parts) > 1 else None

        if not time_range:
            await update.message.reply_text(
                "Please specify the clip range (e.g., `1:30-2:00`) after the link."
            )
            return

        logger.info(f"User {user_id} requested clip: {url} from {time_range}")
        await update.message.reply_text(f"Processing your request for: {time_range}...")
        
        # 2. Call the core processing function
        final_clip_path = await process_video_clip(
            url, 
            time_range, 
            DOWNLOAD_DIR, 
            CLIP_DIR, 
            user_id,
            logger # Pass logger for better tracking
        )

        if final_clip_path:
            # 3. Send the final video back
            logger.info(f"Sending final clip to user {user_id}: {final_clip_path}")
            await update.message.reply_video(
                video=open(final_clip_path, 'rb'),
                caption=f"✅ Your clip from {time_range} is ready!",
                supports_streaming=True
            )
            
        else:
            await update.message.reply_text(
                "❌ Error processing your clip. Please check the URL and time format (e.g., 0:30-1:00) and ensure the video is available."
            )

    except Exception as e:
        logger.error(f"An unexpected error occurred during processing for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text("An unexpected error occurred. Please check the format and try again.")
        
    finally:
        # 4. Clean up files after processing
        # Ensure your video_utils handles cleanup of temporary files (Crucial for free tier)
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