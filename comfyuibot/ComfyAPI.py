import uuid
import threading
from typing import Callable, Optional, Tuple
import websocket
import random
import json
import requests
import time
import asyncio
from constant import *

class ComfyUIGenerator:
    def __init__(self):
        self.progress_data = {'current': 0, 'max': 0, 'node': ''}
        self.ws = None
        self.ws_thread = None
        self.progress_callback = None  # coroutine function or regular callable
        self.loop = None
        self.last_percent = -1
        self.current_prompt_id = None
        self.cancel_requested = False
        self.cancel_event = threading.Event()

    def generate_client_id(self) -> str:
        return str(uuid.uuid4())

    def create_workflow(self, positive_prompt, negative_prompt=DEFAULT_NEGATIVE, seed=DEFAULT_SEED, steps=DEFAULT_STEPS, width=int(DEFAULT_EXTENSION.split('x')[0]), height=int(DEFAULT_EXTENSION.split('x')[1]), cfg=DEFAULT_CFG, sampler_name=DEFAULT_SAMPLER_NAME, scheduler=DEFAULT_SCHEDULER, shift=DEFAULT_SHIFT, style=DEFAULT_STYLE):
        actual_seed = random.randint(0, 2**32 - 1) if seed == -1 else seed
        with open(WORKFLOW_JSON_PATH, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        try:
            workflow.get('3')['inputs']['steps'] = steps
            workflow.get('48')['inputs']['text'] = positive_prompt
            workflow.get('50')['inputs']['text'] = negative_prompt
            workflow.get('13')['inputs']['width'] = width
            workflow.get('13')['inputs']['height'] = height
            workflow.get('3')['inputs']['seed'] = seed
            workflow.get('11')['inputs']['shift'] = shift
            workflow.get('45')['inputs'].get("select_styles")["__value__"] = style
        except Exception:
            pass

        return workflow, actual_seed

    def submit_workflow(self, workflow, client_id: str) -> str:
        payload = {"prompt": workflow, "client_id": client_id}
        response = requests.post(f"{COMFYUI_URL}/prompt", json=payload)
        if response.status_code != 200:
            raise Exception(f"Error submitting prompt: {response.status_code} - {response.text}")
        data = response.json()
        prompt_id = data.get('prompt_id')
        self.current_prompt_id = prompt_id
        return prompt_id

    def cancel_current_generation(self):
        self.cancel_requested = True
        self.cancel_event.set()
        try:
            requests.post(f"{COMFYUI_URL}/interrupt")
        except Exception as e:
            print("Error sending interrupt:", e)

    def wait_for_completion(self, prompt_id: str) -> Tuple[dict, float]:
        start_time = time.time()
        while True:
            if self.cancel_event.is_set():
                raise Exception("Generation cancelled by user")

            time.sleep(0.5)
            try:
                status_response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
            except Exception:
                continue

            if status_response.status_code != 200:
                continue

            try:
                status_data = status_response.json()
            except Exception:
                continue

            # status_data expected to be mapping prompt_id -> execution data
            if prompt_id in status_data:
                execution_data = status_data[prompt_id]
                if isinstance(execution_data, dict) and "outputs" in execution_data:
                    end_time = time.time()
                    return status_data, end_time - start_time

                # Check errors
                if isinstance(execution_data, dict) and "status" in execution_data and isinstance(execution_data['status'], dict) and "error" in execution_data['status']:
                    raise Exception(f"Generation error: {execution_data['status']['error']}")

    def get_image_content(self, status_data: dict, prompt_id: str) -> bytes:
        if prompt_id not in status_data:
            raise Exception('No such prompt in status')
        node_outputs = status_data[prompt_id].get('outputs', {})

        for node_id, node_output in node_outputs.items():
            if isinstance(node_output, dict) and 'images' in node_output:
                for image_info in node_output['images']:
                    filename = image_info.get('filename')
                    if not filename:
                        continue
                    view_params = {"filename": filename, "type": "output"}
                    subfolder = image_info.get('subfolder')
                    if subfolder:
                        view_params['subfolder'] = subfolder
                    r = requests.get(f"{COMFYUI_URL}/view", params=view_params)
                    if r.status_code == 200:
                        return r.content
                    else:
                        raise Exception(f"Error downloading image: {r.status_code}")

        raise Exception('No images found in outputs')

    # WebSocket callbacks
    def on_message(self, ws, message):
        if self.cancel_event.is_set():
            return
        try:
            data = json.loads(message)
        except Exception:
            return

        try:
            if data.get('type') == 'progress':
                val = data['data'].get('value', 0)
                mx = data['data'].get('max', 0)
                self.progress_data['current'] = val
                self.progress_data['max'] = mx
                if mx > 0:
                    percent = (val / mx) * 100
                    rounded = round(percent, 1)
                    if rounded != self.last_percent:
                        self.last_percent = rounded
                        if self.progress_callback:
                            # Support sync and async callbacks
                            try:
                                if asyncio.iscoroutinefunction(self.progress_callback):
                                    asyncio.run_coroutine_threadsafe(self.progress_callback(val, mx, percent), self.loop)
                                else:
                                    # sync callback
                                    asyncio.run_coroutine_threadsafe(self._call_sync_callback(val, mx, percent), self.loop)
                            except Exception as e:
                                pass

            elif data.get('type') == 'executing':
                node = data['data'].get('node')
                if node:
                    self.progress_data['node'] = node
        except Exception:
            pass

    async def _call_sync_callback(self, val, mx, percent):
        self.progress_callback(val, mx, percent)

    def on_error(self, ws, error):
        pass

    def on_close(self, ws, code, msg):
        pass

    def on_open(self, ws):
        pass

    def start_websocket(self, client_id: str, progress_callback: Optional[Callable] = None, loop=None):
        self.progress_callback = progress_callback
        self.loop = loop or asyncio.get_event_loop()
        ws_url = f"{WS_URL}?clientId={client_id}"
        self.ws = websocket.WebSocketApp(ws_url, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close, on_open=self.on_open)
        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()

    def stop_websocket(self):
        try:
            if self.ws:
                self.ws.close()
        except Exception:
            pass
        try:
            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=1)
        except Exception:
            pass

    def generate_image(self, positive_prompt, negative_prompt=DEFAULT_NEGATIVE, seed=DEFAULT_SEED, steps=DEFAULT_STEPS, width=int(DEFAULT_EXTENSION.split('x')[0]), height=int(DEFAULT_EXTENSION.split('x')[1]), cfg=DEFAULT_CFG, sampler_name=DEFAULT_SAMPLER_NAME, scheduler=DEFAULT_SCHEDULER, shift=DEFAULT_SHIFT, style=DEFAULT_STYLE, progress_callback: Optional[Callable] = None, loop=None):
        client_id = self.generate_client_id()
        self.start_websocket(client_id, progress_callback, loop or asyncio.new_event_loop())
        time.sleep(0.2)

        try:
            workflow, actual_seed = self.create_workflow(positive_prompt, negative_prompt, seed, steps, width, height, cfg, sampler_name, scheduler, shift, style)
            prompt_id = self.submit_workflow(workflow, client_id)
            status_data, gen_time = self.wait_for_completion(prompt_id)
            image_content = self.get_image_content(status_data, prompt_id)
            return image_content, actual_seed, gen_time
        finally:
            self.stop_websocket()
            self.current_prompt_id = None
            self.cancel_requested = False
            self.cancel_event.clear()
