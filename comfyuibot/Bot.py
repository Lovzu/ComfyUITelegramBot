import asyncio
import random
import ComfyAPI  # Assuming this is your custom module
import UI  # Assuming this is your custom UI module
from constant import *  # Assuming this contains your constants
from concurrent.futures import ThreadPoolExecutor
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, BufferedInputFile, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
import logging

# Configure logging with detailed format for debugging and monitoring
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

# Thread pool for blocking operations to prevent blocking the event loop
executor = ThreadPoolExecutor(max_workers=3)

# Telegram bot configuration


class Form(StatesGroup):
    """State group for handling user input in different contexts"""
    wait_negative = State()      # Waiting for negative prompt
    wait_seed = State()          # Waiting for seed value
    wait_steps = State()         # Waiting for steps count
    wait_cfg = State()           # Waiting for CFG scale
    wait_shift = State()         # Waiting for shift value
    wait_positive = State()      # Waiting for positive prompt

# Initialize bot and dispatcher
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# Dictionary to track active generation tasks for each chat
# Format: {chat_id: {task: asyncio.Task, generator: ComfyUIGenerator, progress_msg_id: int}}
generation_tasks = {}

async def update_main_message(chat_id: int, message_id: int, state: FSMContext):
    """
    Update the main message with current generation parameters.
    
    Args:
        chat_id: Unique identifier for the chat
        message_id: ID of the message to update
        state: FSM context containing current parameters
    """
    data_state = await state.get_data()
    positive = data_state.get('positive', 'Not set')
    negative = data_state.get('negative', 'Not set')
    seed = data_state.get('seed')
    width, height = data_state.get('extension').split('x')
    # Construct the message text with all parameters
    text = "<b>🎨 IMAGE GENERATOR</b>\n\n"
    text += f"✨ <b>Prompt:</b> <code>{positive}</code>\n"
    if negative:
        text += f"⛔ <b>Negative:</b> <code>{negative}</code>\n\n"
    else:
        text += f"⛔ <b>Negative:</b> <code>-</code>\n\n"
    text += "<b>Base Parameters:</b>\n"
    text += f"🌱 <b>Seed</b>: <code>{seed if seed else 'random'}</code>\n"
    text += f"📏 <b>Size</b>: <code>{width}x{height}</code>\n"

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=UI.main_menu(),
            parse_mode="HTML"
        )
    except Exception:
        # Fail silently to avoid breaking the flow if message edit fails
        pass

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Handle the /start command to welcome the user and initialize the bot.
    
    Args:
        message: The incoming message object
        state: FSM context for the user
    """
    name = message.from_user.full_name
    user_id = message.from_user.id
    logging.info(f"👤 User: {name} (ID: {user_id}) started the bot.")
    
    await message.answer(
        f"👋 <b>Hello, {name}!</b>\n\n"
        "✨ I'm your <i>personal AI image generator</i>.\n\n"
        "🎨 <b>What would you like to see? (Any language)</b>\n"
        "💡 <i>Just describe your idea — and I'll bring it to life!</i>\n"
        "🔞 <i><b>No censors.</b> Full creative freedom.</i>\n\n"
        "<blockquote>Example: A cup of coffee</blockquote>",
        parse_mode='HTML'
    )

@dp.message(Form.wait_negative)
async def process_negative(message: Message, state: FSMContext):
    """
    Process the negative prompt input from the user.
    
    Args:
        message: The message containing the negative prompt
        state: FSM context for the user
    """
    name = message.from_user.full_name
    user_id = message.from_user.id
    negative = message.text
    logging.info(f"👤 User: {name} (ID: {user_id}) set custom ⛔ Negative prompt: {negative[:50]}...")

    data_state = await state.get_data()
    main_message_id = data_state.get('main_message_id')

    # Attempt to delete the user's message for cleaner interface
    try:
        await message.delete()
    except Exception:
        pass

    # Clear state and update with new negative prompt
    await state.clear()
    await state.update_data(
        main_message_id=main_message_id,
        positive=data_state.get('positive'),
        negative=negative,
        seed=data_state.get('seed'),
        steps=data_state.get('steps'),
        extension=data_state.get('extension'),
        cfg=data_state.get('cfg'),
        shift=data_state.get('shift'),
        sampler_name=data_state.get('sampler_name'),
        scheduler=data_state.get('scheduler'),
        style=data_state.get('style')
    )

    if main_message_id:
        await update_main_message(message.chat.id, main_message_id, state)

@dp.message(Form.wait_seed)
async def process_seed(message: Message, state: FSMContext):
    """
    Process the seed value input from the user with validation.
    
    Args:
        message: The message containing the seed value
        state: FSM context for the user
    """
    seed_str = message.text.strip()
    data_state = await state.get_data()
    main_message_id = data_state.get('main_message_id')
    name = message.from_user.full_name
    user_id = message.from_user.id
    chat_id = message.chat.id
    logging.info(f"👤 User: {name} (ID: {user_id}) set custom 🌱 Seed: {seed_str}.")

    await message.delete()

    # Validate seed input
    if seed_str == "":
        seed = None  # Use random seed
    else:
        try:
            seed = int(seed_str)
            if seed < 0:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=main_message_id,
                    text="❌ Seed must be a positive number or leave empty for random.",
                    reply_markup=UI.back_to_settings()
                )
                return
        except ValueError:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=main_message_id,
                text="❌ Seed must be a positive number or leave empty for random.",
                reply_markup=UI.back_to_settings()
            )
            return

    # Update state with validated seed
    await state.clear()
    await state.update_data(
        main_message_id=main_message_id,
        positive=data_state.get('positive'),
        negative=data_state.get('negative'),
        seed=seed,
        steps=data_state.get('steps'),
        extension=data_state.get('extension'),
        cfg=data_state.get('cfg'),
        shift=data_state.get('shift'),
        sampler_name=data_state.get('sampler_name'),
        scheduler=data_state.get('scheduler'),
        style=data_state.get('style')
    )

    if main_message_id:
        await update_main_message(message.chat.id, main_message_id, state)

@dp.message(Form.wait_steps)
async def process_steps(message: Message, state: FSMContext):
    """
    Process the steps count input from the user with validation.
    
    Args:
        message: The message containing the steps count
        state: FSM context for the user
    """
    steps_str = message.text.strip()
    data_state = await state.get_data()
    main_message_id = data_state.get('main_message_id')
    name = message.from_user.full_name
    user_id = message.from_user.id
    chat_id = message.chat.id
    logging.info(f"👤 User: {name} (ID: {user_id}) set custom 🚀 Steps: {steps_str}.")

    try:
        await message.delete()
    except Exception:
        pass

    # Validate steps input
    try:
        steps = int(steps_str)
        if steps <= 0:
            await bot.edit_message_text(
                message_id=main_message_id,
                chat_id=chat_id,
                text="❌ Steps must be a positive integer.",
                reply_markup=UI.back_to_settings()
            )
            return
    except ValueError:
        await bot.edit_message_text(
            message_id=main_message_id,
            chat_id=chat_id,
            text="❌ Steps must be a positive integer.",
            reply_markup=UI.back_to_settings()
        )
        return

    # Update state with validated steps
    await state.clear()
    await state.update_data(
        main_message_id=main_message_id,
        positive=data_state.get('positive'),
        negative=data_state.get('negative'),
        seed=data_state.get('seed'),
        style=data_state.get('style'),
        steps=steps,
        extension=data_state.get('extension'),
        cfg=data_state.get('cfg'),
        shift=data_state.get('shift'),
        sampler_name=data_state.get('sampler_name'),
        scheduler=data_state.get('scheduler')
    )

    if main_message_id:
        await update_main_message(message.chat.id, main_message_id, state)

@dp.message(Form.wait_cfg)
async def process_cfg(message: Message, state: FSMContext):
    """
    Process the CFG scale input from the user with validation.
    
    Args:
        message: The message containing the CFG scale
        state: FSM context for the user
    """
    cfg_str = message.text.strip()
    data_state = await state.get_data()
    main_message_id = data_state.get('main_message_id')
    name = message.from_user.full_name
    user_id = message.from_user.id
    logging.info(f"👤 User: {name} (ID: {user_id}) set custom ⚙️ CFG: {cfg_str}.")

    chat_id = message.chat.id
    try:
        await message.delete()
    except Exception:
        pass

    # Validate CFG input
    try:
        cfg = float(cfg_str)
        if cfg <= 0.0:
            await bot.edit_message_text(
                message_id=main_message_id,
                chat_id=chat_id,
                text="❌ CFG must be greater than 0.0.",
                reply_markup=UI.back_to_settings()
            )
            return
    except ValueError:
        await bot.edit_message_text(
            message_id=main_message_id,
            chat_id=chat_id,
            text="❌ CFG must be greater than 0.0.",
            reply_markup=UI.back_to_settings()
        )
        return

    # Update state with validated CFG
    await state.clear()
    await state.update_data(
        main_message_id=main_message_id,
        positive=data_state.get('positive'),
        negative=data_state.get('negative'),
        seed=data_state.get('seed'),
        steps=data_state.get('steps'),
        style=data_state.get('style'),
        extension=data_state.get('extension'),
        cfg=cfg,
        shift=data_state.get('shift'),
        sampler_name=data_state.get('sampler_name'),
        scheduler=data_state.get('scheduler')
    )

    if main_message_id:
        await update_main_message(message.chat.id, main_message_id, state)

@dp.message(Form.wait_shift)
async def process_shift(message: Message, state: FSMContext):
    """
    Process the shift value input from the user with validation.
    
    Args:
        message: The message containing the shift value
        state: FSM context for the user
    """
    shift_str = message.text.strip()
    data_state = await state.get_data()
    main_message_id = data_state.get('main_message_id')
    name = message.from_user.full_name
    user_id = message.from_user.id
    chat_id = message.chat.id
    logging.info(f"👤 User: {name} (ID: {user_id}) set custom 🔄 Shift: {shift_str}.")

    try:
        await message.delete()
    except Exception:
        pass

    # Validate shift input
    try:
        shift = float(shift_str)
        if shift <= 0.0:
            await bot.edit_message_text(
                message_id=main_message_id,
                chat_id=chat_id,
                text="❌ Shift must be greater than 0.0.",
                reply_markup=UI.back_to_settings()
            )
            return
    except ValueError:
        await bot.edit_message_text(
            message_id=main_message_id,
            chat_id=chat_id,
            text="❌ Shift must be greater than 0.0.",
            reply_markup=UI.back_to_settings()
        )
        return

    # Update state with validated shift
    await state.clear()
    await state.update_data(
        main_message_id=main_message_id,
        positive=data_state.get('positive'),
        negative=data_state.get('negative'),
        seed=data_state.get('seed'),
        steps=data_state.get('steps'),
        style=data_state.get('style'),
        extension=data_state.get('extension'),
        cfg=data_state.get('cfg'),
        shift=shift,
        sampler_name=data_state.get('sampler_name'),
        scheduler=data_state.get('scheduler')
    )

    if main_message_id:
        await update_main_message(message.chat.id, main_message_id, state)

@dp.message(Form.wait_positive)
async def process_positive(message: Message, state: FSMContext):
    """
    Process the positive prompt input from the user.
    
    Args:
        message: The message containing the positive prompt
        state: FSM context for the user
    """
    positive = message.text
    data_state = await state.get_data()
    main_message_id = data_state.get('main_message_id')
    name = message.from_user.full_name
    user_id = message.from_user.id
    chat_id = message.chat.id
    logging.info(f"👤 User: {name} (ID: {user_id}) set ✏️ New Prompt: {positive[:50]}...")

    try:
        await message.delete()
    except Exception:
        pass

    # Update state with new positive prompt
    await state.clear()
    await state.update_data(
        main_message_id=main_message_id,
        positive=positive,
        negative=data_state.get('negative'),
        seed=data_state.get('seed'),
        steps=data_state.get('steps'),
        style=data_state.get('style'),
        extension=data_state.get('extension'),
        cfg=data_state.get('cfg'),
        shift=data_state.get('shift'),
        sampler_name=data_state.get('sampler_name'),
        scheduler=data_state.get('scheduler')
    )

    if main_message_id:
        await update_main_message(message.chat.id, main_message_id, state)

@dp.message(F.text)
async def process_positive_text(message: Message, state: FSMContext):
    """
    Process initial positive prompt when user sends plain text.
    This is the default handler for text messages outside of specific states.
    
    Args:
        message: The incoming message object
        state: FSM context for the user
    """
    positive = message.text
    name = message.from_user.full_name
    user_id = message.from_user.id
    chat_id = message.chat.id
    logging.info(f"👤 User: {name} (ID: {user_id}) set 🎨 Initial prompt: {positive[:50]}...")

    # Initialize state with default values and the provided prompt
    await state.clear()
    await state.update_data(
        seed=DEFAULT_SEED,
        steps=DEFAULT_STEPS,
        style=DEFAULT_STYLE,
        extension=DEFAULT_EXTENSION,
        cfg=DEFAULT_CFG,
        shift=DEFAULT_SHIFT,
        sampler_name=DEFAULT_SAMPLER_NAME,
        scheduler=DEFAULT_SCHEDULER,
        negative=DEFAULT_NEGATIVE,
        positive=positive
    )

    # Send the main menu with initial parameters
    text = "🎨 <b>IMAGE GENERATOR</b>\n\nSend a text prompt or configure settings below:"
    msg = await message.answer(text, reply_markup=UI.main_menu(), parse_mode="HTML")
    await state.update_data(main_message_id=msg.message_id)
    await update_main_message(message.chat.id, msg.message_id, state)

async def run_generation(chat_id: int, progress_msg_id: int, state: FSMContext, generator: ComfyAPI.ComfyUIGenerator):
    """
    Execute the image generation process in a separate thread.
    
    Args:
        chat_id: Unique identifier for the chat
        progress_msg_id: ID of the progress message to update
        state: FSM context containing generation parameters
        generator: ComfyUI generator instance
    """
    # Retrieve all parameters from state
    data = await state.get_data()
    positive = data.get('positive', 'A beautiful landscape')
    negative = data.get('negative', DEFAULT_NEGATIVE)
    seed = data.get('seed', -1)
    steps = int(data.get('steps', DEFAULT_STEPS))
    width, height = data.get('extension', DEFAULT_EXTENSION).split('x')
    cfg = data.get('cfg', DEFAULT_CFG)
    shift = data.get('shift', DEFAULT_SHIFT)
    sampler_name = data.get('sampler_name', DEFAULT_SAMPLER_NAME)
    scheduler = data.get('scheduler', DEFAULT_SCHEDULER)
    style = data.get('style', DEFAULT_STYLE)

    # Estimate generation time based on steps
    estimated_time = steps * 4.8

    async def progress_cb(current, total, percent):
        """Callback function to update progress during generation"""
        try:
            await bot.edit_message_text(
                f"🎨 <b>Generating image...</b>\n"
                f"⏱️ <b>Estimated time:</b> <blockquote>~{estimated_time:.1f}s</blockquote>\n"
                f"🔁 Progress: <code>{percent:.1f}%</code>",
                chat_id=chat_id,
                message_id=progress_msg_id,
                reply_markup=UI.cancel_keyboard(),
                parse_mode="HTML"
            )
        except Exception:
            # Fail silently to avoid breaking the generation process
            pass

    try:
        # Run the blocking generation in a separate thread
        loop = asyncio.get_event_loop()
        gen_task = loop.run_in_executor(
            executor,
            lambda: generator.generate_image(
                positive,
                negative,
                -1 if seed in (None, '', 'random') else int(seed),
                steps,
                width,
                height,
                cfg,
                sampler_name,
                scheduler,
                shift,
                style,
                progress_cb,
                loop
            )
        )

        # Wait for generation to complete
        image_content, final_seed, gen_time = await gen_task

        # Create caption with all generation parameters
        caption = f"🏁 <b>Generation completed!</b>\n⏱️ <b>Time:</b> {gen_time:.1f}s\n\n"
        caption += f"🌱 Seed: <code>{final_seed}</code>\n"
        caption += f"🔢 Steps: <code>{steps}</code>\n"
        caption += f"📐 Size: <code>{width}x{height}</code>\n"
        caption += f"⚙️ CFG: <code>{cfg}</code>\n"
        caption += f"🔄 Shift: <code>{shift}</code>\n"
        caption += f"🎨 Sampler: <code>{sampler_name}</code>\n"
        caption += f"📅 Scheduler: <code>{scheduler}</code>\n"
        caption += f"🖼️ Style: <code>{', '.join(style)}</code>\n\n"
        caption += f"✨ <blockquote>{positive[:MAX_POSITIVE] + '...' if len(positive) > MAX_POSITIVE else positive}</blockquote>\n"
        if bool(negative):
            caption += f"\n⛔ <blockquote>{negative[:MAX_NEGATIVE] + '...' if len(negative) > MAX_NEGATIVE else negative}</blockquote>"

        # Send the generated image with parameters
        try:
            reply_to_id = data.get('reply_to_message_id')
            await bot.delete_message(chat_id=chat_id, message_id=progress_msg_id)
            
            await bot.send_document(
                chat_id,
                BufferedInputFile(image_content, filename="generated_image.png"),
                caption=caption,
                reply_markup=UI.image_keyboard(),
                parse_mode="HTML",
                reply_to_message_id=reply_to_id
            )
        except Exception:
            reply_to_id = data.get('reply_to_message_id')
            await bot.send_document(
                chat_id,
                BufferedInputFile(image_content, filename="generated_image.png"),
                caption=caption,
                reply_markup=UI.image_keyboard(),
                parse_mode="HTML",
                reply_to_message_id=reply_to_id
            )

    except Exception as e:
        error_msg = str(e)
        if 'cancel' in error_msg.lower() or 'cancelled' in error_msg.lower():
            try:
                await bot.edit_message_text(
                    "❌ <b>Generation cancelled!</b>",
                    chat_id=chat_id,
                    message_id=progress_msg_id,
                    parse_mode="HTML"
                )
            except Exception:
                pass
        else:
            try:
                await bot.edit_message_text(
                    f"❌ Error during generation: {error_msg}",
                    chat_id=chat_id,
                    message_id=progress_msg_id,
                    parse_mode="HTML"
                )
            except Exception:
                pass
    finally:
        # Remove the task from active tasks
        generation_tasks.pop(chat_id, None)

@dp.callback_query(F.data)
async def callback(call: CallbackQuery, state: FSMContext):
    """
    Handle all callback queries from inline keyboards.
    
    Args:
        call: The callback query object
        state: FSM context for the user
    """
    call_data = call.data
    print(call_data)

    # Handle generation cancellation
    if call_data == 'cancel_generation':
        chat_id = call.message.chat.id
        info = generation_tasks.get(chat_id)
        if info:
            task = info.get('task')
            generator = info.get('generator')
            
            # Request cancellation from ComfyUI
            generator.cancel_current_generation()
            # Cancel the asyncio task
            try:
                task.cancel()
            except Exception:
                pass
            # Remove from active tasks
            generation_tasks.pop(chat_id, None)
            
            try:
                await call.message.edit_text("❌ <b>Generation cancelled!</b>", parse_mode="HTML")
            except Exception:
                pass
            await call.answer("Generation cancelled")
        else:
            await call.answer("No active generation")
        return

    # Handle settings navigation and input requests
    if call_data == 'negative':
        msg = await call.message.edit_text(
            '⛔ <b>Send Negative Prompt</b>',
            reply_markup=UI.back_to_settings(),
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=msg.message_id)
        await state.set_state(Form.wait_negative)
        await call.answer()
        return

    if call_data == 'seed':
        msg = await call.message.edit_text(
            '🌱 <b>Send Seed (number or leave empty for random)</b>',
            reply_markup=UI.back_to_settings(),
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=msg.message_id)
        await state.set_state(Form.wait_seed)
        await call.answer()
        return

    if call_data == 'steps':
        msg = await call.message.edit_text(
            '🔢 <b>Send Steps count</b>',
            reply_markup=UI.back_to_settings(),
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=msg.message_id)
        await state.set_state(Form.wait_steps)
        await call.answer()
        return

    if call_data == 'extension':
        msg = await call.message.edit_text(
            '📏 <b>Select extension</b>',
            reply_markup=UI.extension_keyboard(),
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=msg.message_id)
        await call.answer()
        return

    if call_data == 'cfg':
        msg = await call.message.edit_text(
            '⚙️ <b>Send CFG Scale</b>',
            reply_markup=UI.back_to_settings(),
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=msg.message_id)
        await state.set_state(Form.wait_cfg)
        await call.answer()
        return

    if call_data == 'sampler_name':
        msg = await call.message.edit_text(
            f"🎨 <b>Select Sampler</b>\n\n",
            reply_markup=UI.samplers_keyboard(),
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=msg.message_id)
        await call.answer()
        return

    if call_data == 'scheduler':
        msg = await call.message.edit_text(
            f"📅 <b>Select Scheduler</b>",
            reply_markup=UI.scheduler_keyboard(),
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=msg.message_id)
        await call.answer()
        return

    if call_data == 'shift':
        msg = await call.message.edit_text(
            '🔄 <b>Send Shift value</b>',
            reply_markup=UI.back_to_settings(),
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=msg.message_id)
        await state.set_state(Form.wait_shift)
        await call.answer()
        return
    if call_data == "style":
        msg = await call.message.edit_text(
            '⚠️ <b>Select style, but be careful</b>\n💥 <b>Some styles can <ins>break</ins> your image</b>',
            reply_markup=UI.style_keyboard(),
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=msg.message_id)
        await call.answer()
        return
        


    # Handle image generation
    if call_data == 'generate':
        data_state = await state.get_data()
        steps = int(data_state.get('steps', DEFAULT_STEPS))
        estimated_time = steps * 4.8
        await state.update_data(seed=random.randint(0, 2**32 - 1))
        await call.answer("🎨 Generation started...")

        await call.message.edit_text(
            f"🎨 <b>Start Generate...</b>\n"
            f"⏱️ <b>Estimated time:</b> <blockquote>~{estimated_time:.1f}s</blockquote>",
            reply_markup=UI.cancel_keyboard(),
            parse_mode="HTML"
        )

        generator = ComfyAPI.ComfyUIGenerator()
        task = asyncio.create_task(run_generation(call.message.chat.id, call.message.message_id, state, generator))
        generation_tasks[call.message.chat.id] = {
            'task': task,
            'generator': generator,
            'progress_msg_id': call.message.message_id
        }
        return

    # Handle re-generation with new random seed
    if call_data == 'repeat':
        data_state = await state.get_data()
        await state.update_data(seed=random.randint(0, 2**32 - 1))
        
        previous_image_id = call.message.message_id
        await state.update_data(reply_to_message_id=previous_image_id)
        await call.answer("🎨 Re-generation started...")

        steps = int(data_state.get('steps', DEFAULT_STEPS))
        estimated_time = steps * 4.8

        progress_msg = await call.message.reply(
            f"🎨 <b>Re-generate image...</b>\n"
            f"⏱️ <b>Estimated time:</b> <blockquote>~{estimated_time:.1f}s</blockquote>",
            reply_markup=UI.cancel_keyboard(),
            parse_mode="HTML"
        )

        generator = ComfyAPI.ComfyUIGenerator()
        task = asyncio.create_task(run_generation(call.message.chat.id, progress_msg.message_id, state, generator))
        generation_tasks[call.message.chat.id] = {
            'task': task,
            'generator': generator,
            'progress_msg_id': progress_msg.message_id
        }
        return

    # Handle image change with new random seed
    if call_data == 'change':
        data_state = await state.get_data()
        positive = data_state.get('positive', 'A beautiful landscape')
        negative = data_state.get('negative', DEFAULT_NEGATIVE)
        steps = data_state.get('steps', DEFAULT_STEPS)
        extension = data_state.get('extension', DEFAULT_EXTENSION)
        width, height = extension.split('x')
        cfg = data_state.get('cfg', DEFAULT_CFG)
        shift = data_state.get('shift', DEFAULT_SHIFT)
        sampler_name = data_state.get('sampler_name', DEFAULT_SAMPLER_NAME)
        scheduler = data_state.get('scheduler', DEFAULT_SCHEDULER)
        style = data_state.get('style', DEFAULT_STYLE)
        await state.clear()
        await state.update_data(
            seed=random.randint(0, 2**32 - 1),  # New random seed
            steps=steps,
            extension=extension,
            cfg=cfg,
            shift=shift,
            sampler_name=sampler_name,
            scheduler=scheduler,
            style=style,
            negative=negative,
            positive=positive
        )

        width, height = extension.split('x')
        text = "<b>🎨 Change image</b>\n\n"
        text += f"✨ <b>Prompt:</b> <code>{positive}</code>\n"
        if bool(negative):
            text += f"⛔ <b>Negative:</b> <code>{negative}</code>\n\n"
        text += "<b>Full Parameters:</b>\n"
        text += f"🌱 Seed: <code>random</code>\n"
        text += f"🔢 Steps: <code>{steps}</code>\n"
        text += f"📐 Size: <code>{width}x{height}</code>\n"
        text += f"⚙️ CFG: <code>{cfg}</code>\n"
        text += f"🔄 Shift: <code>{shift}</code>\n"
        text += f"🎨 Sampler: <code>{sampler_name}</code>\n"
        text += f"📅 Scheduler: <code>{scheduler}</code>\n"
        text += f"🖼️ Style: <code>{', '.join(style)}</code>"

        msg = await call.message.reply(text, reply_markup=UI.main_menu(), parse_mode="HTML")
        await state.update_data(main_message_id=msg.message_id)
        await call.answer("Ready for new generation!")
        return

    # Handle prompt change
    if call_data == 'change_positive':
        msg = await call.message.edit_text(
            '✏️ <b>Send new prompt</b>',
            reply_markup=UI.back_to_main(),
            parse_mode="HTML"
        )
        await state.update_data(bot_message_id=msg.message_id)
        await state.set_state(Form.wait_positive)
        await call.answer()
        return

    # Handle selection of specific values
    if call_data in SAMPLERS:
        await state.update_data(sampler_name=call_data)
        await call.answer()

    if call_data in EXTENSIONS:
        await state.update_data(extension=call_data)
        await call.answer()

    if call_data in SCHEDULERS:
        await state.update_data(scheduler=call_data)
        await call.answer()

    if call_data in STYLES:
        data_state = await state.get_data()
        style = data_state.get('style')
        print(call_data in style)
        if call_data in style:
            
            try:
                style.remove(call_data)
                print(style)
                if bool(style) is False:
                    style = ['Not set']
            except:
                pass
        else:
            try:
                style.append(call_data)
                style.remove('Not set')
            except:
                pass
        await state.update_data(style=style)
        await call.answer()
        

    

    # Handle navigation between menus
    if call_data == 'settings' or call_data == 'back_to_settings' or call_data in SAMPLERS or call_data in EXTENSIONS or call_data in SCHEDULERS or call_data in STYLES:
        data_state = await state.get_data()
        main_message_id = data_state.get('main_message_id', call.message.message_id)
        
        await state.clear()
        await state.update_data(
            main_message_id=main_message_id,
            positive=data_state.get('positive'),
            negative=data_state.get('negative'),
            seed=data_state.get('seed'),
            steps=data_state.get('steps'),
            extension=data_state.get('extension'),
            cfg=data_state.get('cfg'),
            shift=data_state.get('shift'),
            sampler_name=data_state.get('sampler_name'),
            scheduler=data_state.get('scheduler'),
            style=data_state.get('style')
        )

        positive = data_state.get('positive', 'Not set')
        negative = data_state.get('negative', 'Not set')
        seed = data_state.get('seed')
        steps = data_state.get('steps')
        width, height = data_state.get('extension').split('x')  
        cfg = data_state.get('cfg')
        shift = data_state.get('shift')
        sampler_name = data_state.get('sampler_name')
        scheduler = data_state.get('scheduler')
        style = data_state.get('style')

        text = "<b>🎨 IMAGE GENERATOR</b>\n\n"
        text += f"✨ <b>Prompt:</b> <code>{positive}</code>\n"
        if bool(negative):
            text += f"⛔ <b>Negative:</b> <code>{negative}</code>\n\n"
        text += "<b>Full Parameters:</b>\n"
        text += f"🌱 Seed: <code>{seed if seed else 'random'}</code>\n"
        text += f"🔢 Steps: <code>{steps}</code>\n"
        text += f"📏 Size: <code>{width}x{height}</code>\n"
        text += f"⚙️ CFG: <code>{cfg}</code>\n"
        text += f"🔄 Shift: <code>{shift}</code>\n"
        text += f"🎨 Sampler: <code>{sampler_name}</code>\n"
        text += f"📅 Scheduler: <code>{scheduler}</code>\n"
        text += f"🖼️ Style: <code>{', '.join(style)}</code>"


        try:
            await call.message.edit_text(text, reply_markup=UI.settings_menu(), parse_mode="HTML")
        except Exception:
            pass
        await call.answer()
        return

    if call_data == 'back_to_main':
        data_state = await state.get_data()
        main_message_id = data_state.get('main_message_id', call.message.message_id)
        
        await state.clear()
        await state.update_data(
            main_message_id=main_message_id,
            positive=data_state.get('positive'),
            negative=data_state.get('negative'),
            seed=data_state.get('seed'),
            steps=data_state.get('steps'),
            extension=data_state.get('extension'),
            cfg=data_state.get('cfg'),
            shift=data_state.get('shift'),
            sampler_name=data_state.get('sampler_name'),
            scheduler=data_state.get('scheduler'),
            style=data_state.get('style')
        )
        
        await update_main_message(call.message.chat.id, main_message_id, state)
        await call.answer()
        return

if __name__ == '__main__':
    print('Starting bot...')
    try:
        dp.run_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        print('Shutting down...')
