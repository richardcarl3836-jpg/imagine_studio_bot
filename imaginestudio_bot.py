"""
🎨 ImagineStudio Bot - Professional AI Image Generator
Generate REAL AI images from text prompts with multiple styles
Powered by Pollinations.ai - FREE, No API Key Needed!
"""

import os
import io
import re
import json
import logging
import random
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from PIL import Image, ImageEnhance

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ==================== LOGGING ====================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================

# Try multiple possible token variable names
BOT_TOKEN = (
    os.environ.get("TELEGRAM_TOKEN") or
    os.environ.get("TELEGRAM_BOT_TOKEN") or
    os.environ.get("BOT_TOKEN")
)

# If token is not set, try reading from .env file
if not BOT_TOKEN:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        BOT_TOKEN = (
            os.environ.get("TELEGRAM_TOKEN") or
            os.environ.get("TELEGRAM_BOT_TOKEN") or
            os.environ.get("BOT_TOKEN")
        )
    except:
        pass

# If still no token, show error
if not BOT_TOKEN:
    logger.error("=" * 60)
    logger.error("❌ ERROR: No Telegram Bot Token found!")
    logger.error("=" * 60)
    raise ValueError("❌ No Telegram Bot Token found in environment variables!")

BOT_NAME = "ImagineStudio Bot"
BOT_USERNAME = "imaginestudio_bot"
BOT_VERSION = "1.0.0"

# ==================== CONSTANTS ====================

# Image Sizes
IMAGE_SIZES = {
    "square": {"width": 512, "height": 512, "label": "🟦 Square (512x512)"},
    "portrait": {"width": 384, "height": 512, "label": "📱 Portrait (384x512)"},
    "landscape": {"width": 512, "height": 384, "label": "🖥️ Landscape (512x384)"},
    "wide": {"width": 768, "height": 512, "label": "🖼️ Wide (768x512)"},
    "hd": {"width": 1024, "height": 768, "label": "📷 HD (1024x768)"},
}

# Art Styles with enhanced prompts
ART_STYLES = {
    "realistic": {
        "label": "📷 Realistic",
        "prompt": "photorealistic, highly detailed, 8k, sharp focus, professional photography",
        "description": "Realistic photography style"
    },
    "anime": {
        "label": "🎨 Anime",
        "prompt": "anime style, vibrant colors, cel shaded, beautiful illustration, manga",
        "description": "Japanese animation style"
    },
    "digital": {
        "label": "💻 Digital Art",
        "prompt": "digital art, concept art, smooth rendering, detailed illustration, trending on artstation",
        "description": "Modern digital illustration"
    },
    "cartoon": {
        "label": "✏️ Cartoon",
        "prompt": "cartoon style, colorful, vector art, flat design, cute, playful",
        "description": "Cartoon and animation style"
    },
    "oil": {
        "label": "🖌️ Oil Painting",
        "prompt": "oil painting, canvas texture, artistic, brush strokes, renaissance style, masterpiece",
        "description": "Classic oil painting"
    },
    "watercolor": {
        "label": "💧 Watercolor",
        "prompt": "watercolor painting, soft colors, artistic, wet paint, fluid, beautiful",
        "description": "Soft watercolor art"
    },
    "cyberpunk": {
        "label": "💜 Cyberpunk",
        "prompt": "cyberpunk, neon lights, futuristic, dark city, vibrant colors, sci-fi",
        "description": "Cyberpunk futuristic style"
    },
    "fantasy": {
        "label": "🧙 Fantasy",
        "prompt": "fantasy art, magical, epic scene, vivid colors, detailed world, mythical",
        "description": "Fantasy and magical art"
    },
    "sketch": {
        "label": "✒️ Sketch",
        "prompt": "pencil sketch, monochrome, drawing, artistic, detailed linework",
        "description": "Pencil sketch style"
    },
    "cinematic": {
        "label": "🎬 Cinematic",
        "prompt": "cinematic, movie scene, dramatic lighting, film grain, epic, blockbuster",
        "description": "Movie poster style"
    },
    "3d": {
        "label": "🎮 3D Render",
        "prompt": "3D render, octane render, C4D, realistic textures, cinematic lighting, high quality",
        "description": "3D rendered style"
    },
    "pixel": {
        "label": "📟 Pixel Art",
        "prompt": "pixel art, retro, 8-bit, pixelated, video game style, nostalgic",
        "description": "Retro pixel art"
    },
}

# Color Themes for prompt enhancement
COLOR_THEMES = {
    "vibrant": "vibrant, colorful, saturated, bold",
    "pastel": "pastel colors, soft, gentle, delicate",
    "dark": "dark colors, moody, shadowy, noir",
    "warm": "warm colors, golden, sunset, cozy",
    "cool": "cool colors, blue, cyan, silver, fresh",
    "neon": "neon colors, glowing, vibrant, electric",
    "monochrome": "monochrome, black and white, grayscale",
    "cinematic": "cinematic colors, film grade, dramatic",
}

# Scene detection keywords
SCENE_KEYWORDS = {
    "portrait": ["portrait", "face", "person", "people", "model", "woman", "man", "girl", "boy", "headshot"],
    "landscape": ["landscape", "scenery", "mountain", "ocean", "beach", "forest", "nature", "river", "lake"],
    "character": ["character", "figure", "avatar", "warrior", "mage", "knight", "hero", "person"],
    "product": ["product", "item", "object", "device", "gadget", "phone", "laptop", "camera"],
    "architecture": ["building", "architecture", "house", "castle", "tower", "city", "skyscraper"],
    "fantasy": ["fantasy", "magic", "dragon", "wizard", "elf", "creature", "mythical"],
    "abstract": ["abstract", "pattern", "texture", "geometric", "shape", "modern"],
    "technology": ["tech", "cyber", "robot", "digital", "future", "ai", "space", "cyberpunk"],
    "nature": ["nature", "flower", "tree", "garden", "animal", "bird", "butterfly"],
}

# Scene enhancements
SCENE_ENHANCEMENTS = {
    "portrait": "professional portrait photography, studio lighting, sharp focus, detailed face",
    "landscape": "breathtaking landscape, panoramic view, golden hour, dramatic sky",
    "character": "character design, fantasy artwork, detailed illustration, dynamic pose",
    "product": "product photography, studio lighting, 3D render, perfect composition",
    "architecture": "architectural photography, stunning building, geometric lines, modern design",
    "fantasy": "fantasy art, magical atmosphere, epic scene, vivid colors, detailed world",
    "abstract": "abstract art, creative composition, modern design, artistic expression",
    "technology": "futuristic technology, cyberpunk style, sleek design, digital art",
    "nature": "beautiful nature, vibrant colors, peaceful scene, detailed flora"
}

# ==================== USER DATA ====================

user_data: Dict[int, Dict] = {}

def get_user_data(user_id: int) -> Dict:
    """Get or create user data"""
    if user_id not in user_data:
        user_data[user_id] = {
            "settings": {
                "style": "realistic",
                "size": "square",
                "theme": "vibrant",
            },
            "history": [],
            "total_generated": 0,
            "last_prompt": "",
            "last_image": None,
        }
    return user_data[user_id]

# ==================== KEYBOARDS ====================

def get_main_keyboard():
    """Create main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("🎨 Generate Image", callback_data="generate")],
        [InlineKeyboardButton("🎭 Art Styles", callback_data="styles")],
        [InlineKeyboardButton("📐 Image Sizes", callback_data="sizes")],
        [InlineKeyboardButton("🌈 Color Themes", callback_data="themes")],
        [InlineKeyboardButton("💡 Prompt Ideas", callback_data="ideas")],
        [InlineKeyboardButton("🔄 Regenerate", callback_data="regenerate")],
        [InlineKeyboardButton("📊 My Stats", callback_data="stats")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_style_keyboard(selected: str = None):
    """Create style selection keyboard"""
    builder = []
    styles = list(ART_STYLES.items())
    for i in range(0, len(styles), 2):
        row = []
        for j in range(2):
            if i + j < len(styles):
                style_id, style_data = styles[i + j]
                is_selected = (style_id == selected)
                text = f"{'✅ ' if is_selected else ''}{style_data['label']}"
                row.append(InlineKeyboardButton(
                    text,
                    callback_data=f"style_{style_id}"
                ))
        builder.append(row)
    builder.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    return InlineKeyboardMarkup(builder)

def get_size_keyboard(selected: str = None):
    """Create size selection keyboard"""
    builder = []
    sizes = list(IMAGE_SIZES.items())
    for i in range(0, len(sizes), 2):
        row = []
        for j in range(2):
            if i + j < len(sizes):
                size_id, size_data = sizes[i + j]
                is_selected = (size_id == selected)
                text = f"{'✅ ' if is_selected else ''}{size_data['label']}"
                row.append(InlineKeyboardButton(
                    text,
                    callback_data=f"size_{size_id}"
                ))
        builder.append(row)
    builder.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    return InlineKeyboardMarkup(builder)

def get_theme_keyboard(selected: str = None):
    """Create theme selection keyboard"""
    builder = []
    themes = list(COLOR_THEMES.items())
    for i in range(0, len(themes), 2):
        row = []
        for j in range(2):
            if i + j < len(themes):
                theme_id, theme_data = themes[i + j]
                is_selected = (theme_id == selected)
                text = f"{'✅ ' if is_selected else ''}{theme_id.capitalize()}"
                row.append(InlineKeyboardButton(
                    text,
                    callback_data=f"theme_{theme_id}"
                ))
        builder.append(row)
    builder.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
    return InlineKeyboardMarkup(builder)

def get_ideas_keyboard():
    """Create prompt ideas keyboard"""
    keyboard = [
        [InlineKeyboardButton("🌅 Cinematic Sunset", callback_data="idea_sunset")],
        [InlineKeyboardButton("🐱 Cute Anime Cat", callback_data="idea_cat")],
        [InlineKeyboardButton("🚀 Futuristic City", callback_data="idea_city")],
        [InlineKeyboardButton("🏰 Fantasy Castle", callback_data="idea_castle")],
        [InlineKeyboardButton("🌌 Cosmic Galaxy", callback_data="idea_galaxy")],
        [InlineKeyboardButton("🌸 Japanese Garden", callback_data="idea_garden")],
        [InlineKeyboardButton("🧙 Dark Wizard", callback_data="idea_wizard")],
        [InlineKeyboardButton("🐉 Epic Dragon", callback_data="idea_dragon")],
        [InlineKeyboardButton("🌊 Ocean Wave", callback_data="idea_ocean")],
        [InlineKeyboardButton("🏔️ Mountain Peak", callback_data="idea_mountain")],
        [InlineKeyboardButton("🤖 AI Robot", callback_data="idea_robot")],
        [InlineKeyboardButton("🌺 Tropical Paradise", callback_data="idea_paradise")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_generate_keyboard():
    """Create generate options keyboard"""
    keyboard = [
        [InlineKeyboardButton("🔄 Regenerate", callback_data="regenerate")],
        [InlineKeyboardButton("🎭 Change Style", callback_data="styles")],
        [InlineKeyboardButton("📐 Change Size", callback_data="sizes")],
        [InlineKeyboardButton("🌈 Change Theme", callback_data="themes")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== AI IMAGE GENERATION ====================

async def generate_image(prompt: str, width: int = 512, height: int = 512, style: str = "realistic", theme: str = "vibrant") -> Optional[bytes]:
    """
    Generate REAL AI image using Pollinations.ai (FREE, No API Key needed)
    """
    try:
        # Get style prompt
        style_prompt = ART_STYLES.get(style, ART_STYLES["realistic"])["prompt"]
        
        # Get theme prompt
        theme_prompt = COLOR_THEMES.get(theme, COLOR_THEMES["vibrant"])
        
        # Detect scene and enhance
        scene = detect_scene(prompt)
        scene_enhancement = SCENE_ENHANCEMENTS.get(scene, "")
        
        # Build enhanced prompt
        enhanced_prompt = f"{prompt}, {style_prompt}, {theme_prompt}, {scene_enhancement}, high quality, detailed, beautiful"
        
        # Clean prompt for URL
        clean_prompt = enhanced_prompt.strip().replace(" ", "%20").replace(",", "%2C")
        
        # Pollinations.ai URL (Free, No API Key)
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width={width}&height={height}&nologo=true&seed={int(datetime.now().timestamp())}&enhance=true"
        
        logger.info(f"🎨 Generating: {enhanced_prompt[:100]}...")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=60) as response:
                if response.status == 200:
                    image_data = await response.read()
                    
                    # Enhance image quality
                    try:
                        img = Image.open(io.BytesIO(image_data))
                        enhancer = ImageEnhance.Contrast(img)
                        img = enhancer.enhance(1.1)
                        enhancer = ImageEnhance.Color(img)
                        img = enhancer.enhance(1.05)
                        output = io.BytesIO()
                        img.save(output, format='PNG', optimize=True)
                        output.seek(0)
                        return output.getvalue()
                    except:
                        return image_data
                else:
                    logger.error(f"API Error: {response.status}")
                    return None
                    
    except asyncio.TimeoutError:
        logger.error("Generation timeout")
        return None
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return None

def detect_scene(prompt: str) -> str:
    """Detect scene from prompt"""
    prompt_lower = prompt.lower()
    scores = {}
    
    for scene, keywords in SCENE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in prompt_lower)
        if score > 0:
            scores[scene] = score
    
    if not scores:
        return "landscape"
    
    return max(scores, key=scores.get)

def format_size(bytes_count: int) -> str:
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB']:
        if bytes_count < 1024:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f} GB"

# ==================== COMMAND HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = str(user.id)
    data = get_user_data(user_id)
    
    welcome = (
        f"🎨 **Welcome to {BOT_NAME}!**\n\n"
        f"👋 Hello @{user.username or user.first_name}!\n\n"
        f"Your professional AI image generator.\n"
        f"⚡ Powered by **Pollinations.ai** (FREE!)\n\n"
        f"✨ **Features:**\n"
        f"• 🎨 12 Art Styles\n"
        f"• 📐 5 Image Sizes\n"
        f"• 🌈 8 Color Themes\n"
        f"• 🔍 Smart Scene Detection\n"
        f"• 💡 12+ Prompt Ideas\n"
        f"• 🔄 Regenerate Images\n\n"
        f"📊 **Your Stats:**\n"
        f"• Images generated: {data['total_generated']}\n\n"
        f"⬇️ Send me a prompt or use the buttons below!"
    )
    
    await update.message.reply_text(
        welcome,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        f"📖 **{BOT_NAME} User Guide**\n\n"
        "**🎨 How to Generate Images:**\n"
        "1. Click 'Generate Image'\n"
        "2. Type your prompt\n"
        "3. Wait 10-20 seconds\n"
        "4. Get your AI-generated image!\n\n"
        "**🎯 Tips for Best Results:**\n"
        "• Be specific and detailed\n"
        "• Describe colors, mood, lighting\n"
        "• Mention style preference\n"
        "• Use 5-20 words\n\n"
        "**⚙️ Customization:**\n"
        "• 12 Art Styles\n"
        "• 5 Image Sizes\n"
        "• 8 Color Themes\n\n"
        "**📌 Commands:**\n"
        "/start - Main menu\n"
        "/help - This help\n"
        "/stats - Your statistics\n"
        "/generate - Generate image"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    
    # Calculate style usage
    style_counts = {}
    for entry in data.get("history", []):
        style = entry.get("style", "unknown")
        style_counts[style] = style_counts.get(style, 0) + 1
    
    most_used = max(style_counts.items(), key=lambda x: x[1])[0] if style_counts else "None"
    most_used_label = ART_STYLES.get(most_used, {}).get("label", most_used)
    
    stats_text = (
        f"📊 **Your Statistics**\n\n"
        f"🖼️ Total images: {data['total_generated']}\n"
        f"🎨 Most used style: {most_used_label}\n"
        f"📅 Account active since: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        f"📈 **Style Usage:**\n"
    )
    
    for style, count in sorted(style_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        label = ART_STYLES.get(style, {}).get("label", style)
        stats_text += f"• {label}: {count}\n"
    
    await update.message.reply_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /generate command"""
    await update.message.reply_text(
        "🎨 **Describe your image!**\n\n"
        "Be creative! I'll generate a unique image based on your words.\n\n"
        "📝 **Examples:**\n"
        "• \"A beautiful sunset over the ocean with golden clouds\"\n"
        "• \"A cute cat sitting in a magical forest with glowing flowers\"\n"
        "• \"A futuristic cyberpunk city with neon lights and flying cars\"\n"
        "• \"A majestic dragon flying over a fantasy castle at dawn\"\n\n"
        "Send /cancel to cancel.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💡 Prompt Ideas", callback_data="ideas")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
        ])
    )
    context.user_data["action"] = "generate_waiting"

# ==================== GENERATION FUNCTION ====================

async def generate_and_send_image(message, prompt: str, data: Dict, query: Optional[CallbackQuery] = None):
    """Generate and send image"""
    settings = data["settings"]
    
    size = IMAGE_SIZES.get(settings.get("size", "square"), IMAGE_SIZES["square"])
    style = ART_STYLES.get(settings.get("style", "realistic"), ART_STYLES["realistic"])
    theme = settings.get("theme", "vibrant")
    
    # Send processing message
    if query:
        processing = await query.edit_message_text(
            f"🎨 **Generating your image...**\n\n"
            f"📝 Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}\n"
            f"🎨 Style: {style['label']}\n"
            f"📐 Size: {size['label']}\n"
            f"🌈 Theme: {theme.capitalize()}\n\n"
            f"⏳ Please wait 10-20 seconds...",
            parse_mode="Markdown"
        )
    else:
        processing = await message.reply_text(
            f"🎨 **Generating your image...**\n\n"
            f"📝 Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}\n"
            f"🎨 Style: {style['label']}\n"
            f"📐 Size: {size['label']}\n"
            f"🌈 Theme: {theme.capitalize()}\n\n"
            f"⏳ Please wait 10-20 seconds...",
            parse_mode="Markdown"
        )
    
    try:
        # Generate image
        image_data = await generate_image(
            prompt=prompt,
            width=size["width"],
            height=size["height"],
            style=settings.get("style", "realistic"),
            theme=settings.get("theme", "vibrant")
        )
        
        if image_data and len(image_data) > 1000:
            # Update stats
            data["total_generated"] += 1
            data["history"].append({
                "prompt": prompt,
                "style": settings.get("style", "realistic"),
                "size": settings.get("size", "square"),
                "theme": settings.get("theme", "vibrant"),
                "timestamp": datetime.now().isoformat()
            })
            data["last_prompt"] = prompt
            
            # Send image
            await message.reply_photo(
                photo=io.BytesIO(image_data),
                caption=(
                    f"🎨 **Image Generated!**\n\n"
                    f"📝 Prompt: {prompt[:150]}{'...' if len(prompt) > 150 else ''}\n"
                    f"🎨 Style: {style['label']}\n"
                    f"📐 Size: {size['label']}\n"
                    f"🌈 Theme: {theme.capitalize()}\n"
                    f"📊 Size: {len(image_data) // 1024} KB\n\n"
                    f"🔄 Send a new prompt to create another!"
                ),
                parse_mode="Markdown",
                reply_markup=get_generate_keyboard()
            )
            
            await processing.delete()
            
        else:
            await processing.edit_text(
                "⚠️ **Generation Failed**\n\n"
                "I couldn't create an image right now.\n\n"
                "💡 **Tips:**\n"
                "• Try a different prompt\n"
                "• Use simpler words\n"
                "• Try again in a moment",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await processing.edit_text(
            f"❌ **Error**\n\n"
            f"Something went wrong. Please try again.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ==================== CALLBACK HANDLERS ====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = get_user_data(user_id)
    settings = data["settings"]
    action = query.data
    
    # ===== MAIN ACTIONS =====
    
    if action == "generate":
        await query.edit_message_text(
            "🎨 **Describe your image!**\n\n"
            "Be creative! I'll generate a unique image based on your words.\n\n"
            "📝 **Examples:**\n"
            "• \"A beautiful sunset over the ocean with golden clouds\"\n"
            "• \"A cute cat sitting in a magical forest with glowing flowers\"\n"
            "• \"A futuristic cyberpunk city with neon lights and flying cars\"\n\n"
            "Send /cancel to cancel.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💡 Prompt Ideas", callback_data="ideas")],
                [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
            ])
        )
        context.user_data["action"] = "generate_waiting"
        
    elif action == "styles":
        await query.edit_message_text(
            "🎭 **Select Art Style**\n\n"
            "Choose your preferred art style:",
            parse_mode="Markdown",
            reply_markup=get_style_keyboard(settings.get("style", "realistic"))
        )
        
    elif action == "sizes":
        await query.edit_message_text(
            "📐 **Select Image Size**\n\n"
            "Choose your preferred image size:",
            parse_mode="Markdown",
            reply_markup=get_size_keyboard(settings.get("size", "square"))
        )
        
    elif action == "themes":
        await query.edit_message_text(
            "🌈 **Select Color Theme**\n\n"
            "Choose your preferred color theme:",
            parse_mode="Markdown",
            reply_markup=get_theme_keyboard(settings.get("theme", "vibrant"))
        )
        
    elif action == "ideas":
        await query.edit_message_text(
            "💡 **Prompt Ideas**\n\n"
            "Click any idea below to generate an image instantly:",
            parse_mode="Markdown",
            reply_markup=get_ideas_keyboard()
        )
        
    elif action == "regenerate":
        if data.get("last_prompt"):
            await generate_and_send_image(query.message, data["last_prompt"], data, query)
        else:
            await query.edit_message_text(
                "❌ No previous image to regenerate.\n\n"
                "Generate a new image with /generate",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            
    elif action == "stats":
        # Calculate style usage
        style_counts = {}
        for entry in data.get("history", []):
            style = entry.get("style", "unknown")
            style_counts[style] = style_counts.get(style, 0) + 1
        
        most_used = max(style_counts.items(), key=lambda x: x[1])[0] if style_counts else "None"
        most_used_label = ART_STYLES.get(most_used, {}).get("label", most_used)
        
        stats_text = (
            f"📊 **Your Statistics**\n\n"
            f"🖼️ Total images: {data['total_generated']}\n"
            f"🎨 Most used style: {most_used_label}\n"
            f"📅 Account active since: {datetime.now().strftime('%Y-%m-%d')}\n\n"
            f"📈 **Style Usage:**\n"
        )
        
        for style, count in sorted(style_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            label = ART_STYLES.get(style, {}).get("label", style)
            stats_text += f"• {label}: {count}\n"
        
        await query.edit_message_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
    elif action == "help":
        help_text = (
            f"📖 **{BOT_NAME} User Guide**\n\n"
            "**🎨 How to Generate Images:**\n"
            "1. Click 'Generate Image'\n"
            "2. Type your prompt\n"
            "3. Wait 10-20 seconds\n"
            "4. Get your AI-generated image!\n\n"
            "**🎯 Tips for Best Results:**\n"
            "• Be specific and detailed\n"
            "• Describe colors, mood, lighting\n"
            "• Mention style preference\n"
            "• Use 5-20 words\n\n"
            "**⚙️ Customization:**\n"
            "• 12 Art Styles\n"
            "• 5 Image Sizes\n"
            "• 8 Color Themes\n\n"
            "**📌 Commands:**\n"
            "/start - Main menu\n"
            "/help - This help\n"
            "/stats - Your statistics\n"
            "/generate - Generate image"
        )
        await query.edit_message_text(
            help_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        
    elif action == "back":
        await query.edit_message_text(
            "🎨 **Main Menu**\n\n"
            "What would you like to do?",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        context.user_data["action"] = None
        
    elif action == "settings":
        settings_text = (
            f"⚙️ **Current Settings**\n\n"
            f"🎨 Style: {ART_STYLES.get(settings.get('style', 'realistic'), {}).get('label', 'Realistic')}\n"
            f"📐 Size: {IMAGE_SIZES.get(settings.get('size', 'square'), {}).get('label', 'Square')}\n"
            f"🌈 Theme: {settings.get('theme', 'vibrant').capitalize()}\n\n"
            "Select what to customize:"
        )
        await query.edit_message_text(
            settings_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎭 Art Style", callback_data="styles")],
                [InlineKeyboardButton("📐 Image Size", callback_data="sizes")],
                [InlineKeyboardButton("🌈 Color Theme", callback_data="themes")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ])
        )
    
    # ===== STYLE SELECTION =====
    
    elif action.startswith("style_"):
        style_id = action.replace("style_", "")
        if style_id in ART_STYLES:
            settings["style"] = style_id
            await query.edit_message_text(
                f"✅ **Style Updated!**\n\n"
                f"New style: {ART_STYLES[style_id]['label']}\n\n"
                f"Generate a new image to see the change!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎨 Generate Image", callback_data="generate")],
                    [InlineKeyboardButton("🔙 Back", callback_data="settings")]
                ])
            )
    
    # ===== SIZE SELECTION =====
    
    elif action.startswith("size_"):
        size_id = action.replace("size_", "")
        if size_id in IMAGE_SIZES:
            settings["size"] = size_id
            await query.edit_message_text(
                f"✅ **Size Updated!**\n\n"
                f"New size: {IMAGE_SIZES[size_id]['label']}\n\n"
                f"Generate a new image to see the change!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎨 Generate Image", callback_data="generate")],
                    [InlineKeyboardButton("🔙 Back", callback_data="settings")]
                ])
            )
    
    # ===== THEME SELECTION =====
    
    elif action.startswith("theme_"):
        theme_id = action.replace("theme_", "")
        if theme_id in COLOR_THEMES:
            settings["theme"] = theme_id
            await query.edit_message_text(
                f"✅ **Theme Updated!**\n\n"
                f"New theme: {theme_id.capitalize()}\n\n"
                f"Generate a new image to see the change!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎨 Generate Image", callback_data="generate")],
                    [InlineKeyboardButton("🔙 Back", callback_data="settings")]
                ])
            )
    
    # ===== IDEAS =====
    
    elif action.startswith("idea_"):
        idea_map = {
            "idea_sunset": "A beautiful sunset over the ocean with golden clouds and palm trees",
            "idea_cat": "A cute anime cat sitting in a magical garden with glowing flowers and butterflies",
            "idea_city": "A futuristic cyberpunk city with neon lights and flying cars at night",
            "idea_castle": "A magnificent fantasy castle on a mountain peak with magical clouds",
            "idea_galaxy": "A beautiful cosmic galaxy with vibrant nebula, stars, and colorful planets",
            "idea_garden": "A peaceful Japanese garden with cherry blossoms, koi pond, and pagoda",
            "idea_wizard": "A dark wizard casting powerful magic with dramatic lighting in a fantasy setting",
            "idea_dragon": "An epic dragon flying over mountains with fire and magic in fantasy art",
            "idea_ocean": "A massive ocean wave with dramatic lighting and watercolor art style",
            "idea_mountain": "A snowy mountain peak at sunrise with golden hour lighting and majestic landscape",
            "idea_robot": "A futuristic AI robot with sleek design and cyberpunk style with glowing neon",
            "idea_paradise": "A tropical paradise with palm trees and crystal clear water at sunset"
        }
        
        prompt = idea_map.get(action, "A beautiful scene")
        
        # Generate image from idea
        await generate_and_send_image(query.message, prompt, data, query)

# ==================== MESSAGE HANDLERS ====================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user_id = str(update.effective_user.id)
    data = get_user_data(user_id)
    text = update.message.text.strip()
    action = context.user_data.get("action", "")
    
    if not text:
        await update.message.reply_text(
            "❌ Please send some text!",
            reply_markup=get_main_keyboard()
        )
        return
    
    # ===== CANCEL =====
    
    if text.lower() == "/cancel":
        context.user_data["action"] = None
        await update.message.reply_text(
            "✅ Cancelled!",
            reply_markup=get_main_keyboard()
        )
        return
    
    # ===== GENERATE IMAGE =====
    
    if action == "generate_waiting":
        # Generate image from prompt
        await generate_and_send_image(update.message, text, data)
        context.user_data["action"] = None
        
    else:
        await update.message.reply_text(
            "👋 **Use the buttons below!**\n\n"
            "Click 'Generate Image' to create AI art 🎨\n"
            "Or send a prompt directly!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ==================== MAIN ====================

async def post_init(application):
    """Post initialization"""
    logger.info("=" * 60)
    logger.info(f"🎨 {BOT_NAME} Started Successfully!")
    logger.info(f"🤖 Username: @{BOT_USERNAME}")
    logger.info(f"📦 Version: {BOT_VERSION}")
    logger.info(f"🎭 Art Styles: {len(ART_STYLES)}")
    logger.info(f"📐 Image Sizes: {len(IMAGE_SIZES)}")
    logger.info(f"🌈 Color Themes: {len(COLOR_THEMES)}")
    logger.info("=" * 60)
    logger.info("✅ Bot is ready to generate images!")
    logger.info("=" * 60)

def main():
    """Main entry point"""
    logger.info(f"🚀 Starting {BOT_NAME}...")
    logger.info(f"📡 Using token: {BOT_TOKEN[:15]}...{BOT_TOKEN[-5:]}")
    
    application = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .post_init(post_init) \
        .build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("generate", generate_command))
    
    # Callback handler
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("✅ Bot is polling for updates...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
