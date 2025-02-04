import logging
import asyncio
from typing import Dict, List, Set
from collections import defaultdict
from telegram import Update, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio
from telegram.ext import ContextTypes
from telegram.error import RetryAfter
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

# Constants
MEDIA_GROUP_TIMEOUT = 2  # Seconds to wait before processing media group
MAX_RETRIES = 3  # Maximum number of retry attempts for failed operations
RETRY_DELAY = 1  # Delay between retry attempts in seconds
MAX_MEDIA_GROUP_SIZE = 10  # Maximum media items per group

class MessageForwarder:
    """
    Handles message forwarding logic with support for:
    - Single messages
    - Media groups (photos, videos, documents, audio)
    - Rate limiting handling
    - Retry mechanism
    """
    def __init__(self):
        # Store media group messages until ready to forward
        self.media_groups: Dict[str, List] = defaultdict(list)
        # Track message counts
        self.media_group_counts: Dict[str, int] = defaultdict(int)
        # Track scheduled media group processing jobs
        self.scheduled_media_groups: Set[str] = set()
        self.config_manager = ConfigManager()

    async def retry_operation(self, operation, *args, **kwargs):
        """
        Enhanced retry mechanism with:
        - Exponential backoff
        - Error type tracking
        - Context-aware delays
        """
        retry_errors = defaultdict(int)
        base_delay = RETRY_DELAY
        
        for attempt in range(MAX_RETRIES):
            try:
                timeout = 30 + (10 * attempt)  # Progressive timeout
                return await asyncio.wait_for(operation(*args, **kwargs), timeout=timeout)
            except RetryAfter as err:
                retry_errors['rate_limit'] += 1
                await asyncio.sleep(err.retry_after * (attempt + 1))
            except asyncio.TimeoutError:
                retry_errors['timeout'] += 1
                await asyncio.sleep(base_delay * (2 ** attempt))
            except Exception as e:
                error_name = type(e).__name__
                retry_errors[error_name] += 1
                await asyncio.sleep(base_delay * (2 ** attempt))
            finally:
                if attempt == MAX_RETRIES - 1 and retry_errors:
                    logger.error(f"Failed after {MAX_RETRIES} attempts. Errors: {dict(retry_errors)}")
                    raise

    def get_media_input(self, message):
        """
        Convert a message to appropriate InputMedia type
        Returns None if message type is not supported
        """
        caption = message.caption
        
        if message.photo:
            return InputMediaPhoto(
                media=message.photo[-1].file_id,
                caption=caption
            )
        elif message.video:
            return InputMediaVideo(
                media=message.video.file_id,
                caption=caption,
                duration=message.video.duration,
                width=message.video.width,
                height=message.video.height
            )
        elif message.document:
            return InputMediaDocument(
                media=message.document.file_id,
                caption=caption,
                filename=message.document.file_name
            )
        elif message.audio:
            return InputMediaAudio(
                media=message.audio.file_id,
                caption=caption,
                duration=message.audio.duration,
                performer=message.audio.performer,
                title=message.audio.title
            )
        return None

    def get_media_type(self, msg):
        """Returns the media type string or None"""
        if msg.photo: return 'photo'
        if msg.video: return 'video'
        if msg.document: return 'document'
        if msg.audio: return 'audio'
        return None

    async def process_media_group(self, context: ContextTypes.DEFAULT_TYPE, media_group_id: str = None):
        """
        Process collected media group messages with:
        - Precise message ordering using server-side timestamps
        - Duplicate detection
        - Media type consistency checks
        """
        if media_group_id is None:
            # If called from job queue
            job = context.job
            media_group_id = job.data

        messages = self.media_groups.pop(media_group_id, [])
        self.scheduled_media_groups.discard(media_group_id)
        self.media_group_counts.pop(media_group_id, None)  # Clean up count tracking

        if not messages:
            return

        # Order by server-side timestamp and message_id
        messages.sort(key=lambda msg: (msg.date.timestamp(), msg.message_id))
        
        # Check media type consistency
        media_types = {self.get_media_type(msg) for msg in messages}
        media_types.discard(None)
        
        if len(media_types) > 1:
            logger.warning(f"Mixed media types in group {media_group_id}: {media_types}")
        
        # Remove duplicates based on file_id
        seen = set()
        unique_messages = []
        for msg in messages:
            media_type = self.get_media_type(msg)
            if media_type:
                if msg.photo:
                    file_id = msg.photo[-1].file_id
                elif msg.video:
                    file_id = msg.video.file_id
                elif msg.document:
                    file_id = msg.document.file_id
                elif msg.audio:
                    file_id = msg.audio.file_id
                else:
                    continue
                if file_id not in seen:
                    seen.add(file_id)
                    unique_messages.append(msg)
        
        # Get the caption from the first message that has one
        group_caption = next((msg.caption for msg in unique_messages if msg.caption), None)
        
        # Convert messages to appropriate InputMedia types
        media = []
        for i, msg in enumerate(unique_messages):
            # Only include caption for the first media item
            caption = group_caption if i == 0 else None
            
            if msg.photo:
                media.append(InputMediaPhoto(
                    media=msg.photo[-1].file_id,
                    caption=caption,
                    caption_entities=msg.caption_entities if caption else None
                ))
            elif msg.video:
                media.append(InputMediaVideo(
                    media=msg.video.file_id,
                    caption=caption,
                    caption_entities=msg.caption_entities if caption else None,
                    duration=msg.video.duration,
                    width=msg.video.width,
                    height=msg.video.height
                ))
            elif msg.document:
                media.append(InputMediaDocument(
                    media=msg.document.file_id,
                    caption=caption,
                    caption_entities=msg.caption_entities if caption else None,
                    filename=msg.document.file_name
                ))
            elif msg.audio:
                media.append(InputMediaAudio(
                    media=msg.audio.file_id,
                    caption=caption,
                    caption_entities=msg.caption_entities if caption else None,
                    duration=msg.audio.duration,
                    performer=msg.audio.performer,
                    title=msg.audio.title
                ))

        if media:
            for attempt in range(MAX_RETRIES):
                try:
                    await context.bot.send_media_group(
                        chat_id=self.config_manager.config['destination_id'],
                        media=media,
                        read_timeout=30,
                    )
                    logger.info(f"Successfully forwarded media group {media_group_id} with {len(media)} items")
                    break
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1}/{MAX_RETRIES} failed in send_media_group: {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        delay = RETRY_DELAY * (2 ** attempt)
                        if "Timed out" in str(e):
                            delay *= 2
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Failed to forward media group {media_group_id} after {MAX_RETRIES} attempts")

    async def forward_single_message(self, message, context: ContextTypes.DEFAULT_TYPE):
        """
        Forward a single message with retry logic
        Handles all message types including:
        - Text messages
        - Single media items
        - Stickers
        - Location
        - Contacts
        - Polls
        """
        try:
            # For media messages that might have captions
            if any([message.photo, message.video, message.document, 
                   message.audio, message.animation]):
                # Forward as media group of 1 to preserve caption formatting
                input_media = self.get_media_input(message)
                if input_media:
                    await self.retry_operation(
                        context.bot.send_media_group,
                        chat_id=self.config_manager.config['destination_id'],
                        media=[input_media]
                    )
                    return

            # For other message types, use copy_message
            await self.retry_operation(
                context.bot.copy_message,
                chat_id=self.config_manager.config['destination_id'],
                from_chat_id=message.chat_id,
                message_id=message.message_id
            )
        except Exception as e:
            logger.error(f"Error forwarding message {message.message_id}: {str(e)}")

    async def forward_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Main message handling logic
        - Checks source channel
        - Handles both single messages and media groups
        - Implements delayed media group processing
        """
        # Security check
        if update.effective_chat.id != self.config_manager.config['source_id']:
            return

        # Configuration check
        if not self.config_manager.config['destination_id']:
            logger.warning("Destination channel not set. Skipping forwarding.")
            return

        try:
            self.config_manager.validate_config()
        except ValueError as e:
            logger.error(f"Invalid configuration: {str(e)}")
            return

        message = update.effective_message

        # Handle media groups
        if message.media_group_id:
            media_group_id = message.media_group_id
            # Always add the message to the group
            self.media_groups[media_group_id].append(message)
            self.media_group_counts[media_group_id] += 1
            
            # Cancel existing timer if any
            if media_group_id in self.scheduled_media_groups:
                current_jobs = context.job_queue.get_jobs_by_name(str(media_group_id))
                for job in current_jobs:
                    job.schedule_removal()
                    
            # Immediate processing if reached max size
            if self.media_group_counts[media_group_id] >= MAX_MEDIA_GROUP_SIZE:
                await self.process_media_group(context, media_group_id)
                logger.info(f"Processing media group {media_group_id} immediately - max size reached")
                return
            
            # Otherwise reset timer
            self.scheduled_media_groups.add(media_group_id)
            context.job_queue.run_once(
                lambda ctx: self.process_media_group(ctx, media_group_id),
                when=MEDIA_GROUP_TIMEOUT,
                name=str(media_group_id)
            )
            logger.info(f"Reset timer for media group {media_group_id}. Messages collected: {self.media_group_counts[media_group_id]}")
        else:
            # Handle single message
            await self.forward_single_message(message, context)
