# 🎨 Z-Image Telegram Bot for ComfyUI

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-blueviolet?style=for-the-badge&logo=telegram)
![ComfyUI](https://img.shields.io/badge/Backend-ComfyUI-green?style=for-the-badge)

A powerful, high-performance Telegram bot interface for **ComfyUI**, designed to generate stunning images using the **Z-Image** architecture.

This project allows you to control a local ComfyUI instance remotely via Telegram, featuring real-time progress updates, advanced parameter controls (Seed, Steps, CFG, Shift), and support for multiple aspect ratios.

---

## ✨ Features

* **📱 Seamless Interface:** User-friendly inline keyboards for smooth navigation.
* **⚡ Real-Time Progress:** Live generation percentage and time estimation directly in the chat.
* **🛠️ Deep Configuration:** Full control over `Seed`, `Steps`, `CFG`, `Shift`, `Sampler`, and `Scheduler`.
* **📐 Multi-Ratio Support:** Generate images in 1:1, 16:9, 9:16, 4:3, and more.
* **🔄 Async Queue:** Robust threading system to handle multiple user requests simultaneously.
* **🔌 WebSocket Integration:** Direct, low-latency communication with the ComfyUI backend.

---

## 🛠️ Prerequisites & Installation

### Step 1: Install ComfyUI
If you don't have ComfyUI installed, download it from the official repository. You must have a working ComfyUI installation to run this bot.
* **📥 Repository:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)

### Step 2: Download Models (Crucial)
You must download the following specific Z-Image models and place them in the correct folders inside your **ComfyUI directory**.

| Component | Model Name | Download Link | Target ComfyUI Folder |
| :--- | :--- | :--- | :--- |
| **Diffusion (BF16)** | `z_image_turbo_bf16.safetensors` | [**Download Here**](https://huggingface.co/Comfy-Org/z_image_turbo/blob/main/split_files/diffusion_models/z_image_turbo_bf16.safetensors) | `ComfyUI/models/diffusion_models/` |
| **Diffusion (FP8)**<br>*(Low VRAM)* | `z-image-turbo_fp8_scaled_e4m3fn_KJ.safetensors` | [**Download Here**](https://huggingface.co/Kijai/Z-Image_comfy_fp8_scaled/resolve/main/z-image-turbo_fp8_scaled_e4m3fn_KJ.safetensors) | `ComfyUI/models/diffusion_models/` |
| **VAE** | `ae.safetensors` | [**Download Here**](https://huggingface.co/Comfy-Org/z_image_turbo/blob/main/split_files/vae/ae.safetensors) | `ComfyUI/models/vae/` |
| **Text Encoder** | `qwen_3_4b.safetensors` | [**Download Here**](https://huggingface.co/Comfy-Org/z_image_turbo/blob/main/split_files/text_encoders/qwen_3_4b.safetensors) | `ComfyUI/models/clip/` |

> **⚠️ Important:** The filenames must match those in the workflow exactly.

### Step 3: Bot Setup and Dependencies

1.  **Project Structure:** Download all the bot files (`Bot.py`, `UI.py`, `constant.py`, `ComfyAPI.py`, `workflow`) and place them into **one single folder**. All these files must reside together.
2.  Style File (`fooocus_styles.json`) place to [`ComfyUI\ComfyUI\custom_nodes\ComfyUI-Easy-Use\resources`].

3.  **Install Dependencies:** Open your terminal/command prompt in that folder and run the command to install the required Python libraries:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Workflow Setup:** The file `Z-image.json` is the default workflow. Ensure it is in the root directory of the bot project.

    > **ℹ️ Changing Workflow:** If you want to use a different workflow file or change its name, open `constant.py` and modify the `WORKFLOW_JSON_PATH`:
    > ```python
    > # constant.py
    > WORKFLOW_JSON_PATH = Path(__file__).with_name("YOUR_NEW_WORKFLOW.json")
    > ```

### Step 4: Configure the Bot

You need to set your Telegram Bot Token and verify the ComfyUI connection details.

1.  **Bot Token:** Open `constant.py` and replace the placeholder with your Telegram Bot Token:
    ```python
    # constant.py
    BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    ```

2.  **ComfyUI URL:** Verify the ComfyUI connection settings in `constant.py`. The default assumes ComfyUI is running on the same machine on port 8188.
    ```python
    # constant.py
    COMFYUI_URL = "[http://127.0.0.1:8188](http://127.0.0.1:8188)"
    WS_URL = "ws://127.0.0.1:8188/ws"
    ```

---

## 🎮 How to Run

1.  **Start ComfyUI:**
    Launch your ComfyUI backend (e.g., `run_nvidia_gpu.bat` or `python main.py`).
    * *Ensure it is running on port 8188 (default).*

2.  **Start the Bot:**
    Run the bot script in your terminal:
    ```bash
    python Bot.py
    ```

3.  **Start Generating:**
    Open the bot in Telegram and send `/start`.
    * Send any initial text to set the positive prompt.
    * Use the menu buttons to change settings or aspect ratios before generating.

---

## ⚙️ Usage Guide

### Main Menu
The initial menu after setting a prompt or using `/start`.
* **🎨 Generate:** Starts the image generation process using the current settings.
* **✏️ Change Prompt:** Allows you to enter a new positive description.
* **⚙️ Settings:** Opens the advanced configuration menu.

### Settings Menu
Here you can fine-tune all generation parameters.
* **⛔ Negative:** Set what you *don't* want in the image.
* **🌱 Seed:** Set a fixed seed for reproducibility.
* **📐 Extension:** Choose the image resolution (e.g., `1024x1024`, `1344x768`, etc.).
* **🔢 Steps / ⚙️ CFG / 🔄 Shift:** Fine-tune the generation parameters based on the specific model requirements.
* **🎨 Sampler / 📅 Scheduler:** Select the specific generation algorithms (Euler, DPM++, Karras, etc.).
* **🖼️ Style:** Select the specific Style for generation (Anime, Realistic, Simple Negative, Advanced Negative).

---

## 📝 License

This project is open-source. Feel free to modify and adapt the code for your personal use.
