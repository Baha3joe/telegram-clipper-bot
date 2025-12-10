import os
import shutil
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters
from video_utils import download_video, create_clips, generate_tags

# Load env variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# States for Conversation
URL, NUM_CLIPS, DURATION, PROCESSING = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Welcome to the AI Clipper Bot!**\n\n"
        "I can download YouTube videos, create clips, add captions, and generate tags.\n"
        "Send /cancel at any time to stop.\n\n"
        "Please send me the **YouTube URL** to get started."
    )
    return URL

async def receive_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ That doesn't look like a valid YouTube URL. Please try again.")
        return URL
    
    context.user_data['url'] = url
    await update.message.reply_text("✅ URL received!\n\nHow many clips would you like to generate? (e.g., 3)")
    return NUM_CLIPS

async def receive_num_clips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text)
        if count > 10:
            await update.message.reply_text("⚠️ Let's keep it under 10 clips for performance. Try again.")
            return NUM_CLIPS
        
        context.user_data['num_clips'] = count
        await update.message.reply_text("Got it. How long should each clip be (in seconds)? (e.g., 30)")
        return DURATION
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return NUM_CLIPS

async def receive_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        duration = int(update.message.text)
        context.user_data['duration'] = duration
        
        await update.message.reply_text(
            f"🎬 **Processing Started!**\n"
            f"Video: {context.user_data['url']}\n"
            f"Clips: {context.user_data['num_clips']}\n"
            f"Duration: {duration}s\n\n"
            "This will take a few minutes depending on your PC speed. I'll send the clips when ready!"
        )
        
        # Trigger the processing function asynchronously
        # We use create_task so the bot doesn't freeze
        context.application.create_task(process_video(update, context))
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number for seconds.")
        return DURATION

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = context.user_data
    
    try:
        # 1. Download
        video_path, title, _ = download_video(data['url'])
        
        # 2. Generate Tags
        tags = generate_tags(title)
        
        # 3. Process Clips
        clips = create_clips(video_path, data['num_clips'], data['duration'])
        
        # 4. Send Clips
        for clip_path in clips:
            await context.bot.send_video(
                chat_id=user_id,
                video=open(clip_path, 'rb'),
                caption=f"🎥 **{title}**\n\n{tags}",
                read_timeout=60
            )
            # Clean up individual clip after sending
            os.remove(clip_path)

        # Cleanup original video
        os.remove(video_path)
        
        await context.bot.send_message(chat_id=user_id, text="✅ All clips sent! Send /start to process another.")
        
    except Exception as e:
        await context.bot.send_message(chat_id=user_id, text=f"❌ An error occurred: {str(e)}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Operation cancelled. Send /start to begin again.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_url)],
            NUM_CLIPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_num_clips)],
            DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_duration)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()