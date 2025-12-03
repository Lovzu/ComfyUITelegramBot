import random
from pathlib import Path

BOT_TOKEN = ""

# Constants
SAMPLERS = [
    "euler", "euler_ancestral", "euler_cfg_pp", "euler_ancestral_cfg_pp",
    "heun", "heunpp2", "dpm_2", "dpm_2_ancestral", "lms", "dpm_fast",
    "dpm_adaptive", "dpmpp_2s_ancestral", "dpmpp_2s_ancestral_cfg_pp",
    "dpmpp_sde", "dpmpp_sde_gpu", "dpmpp_2m", "dpmpp_2m_cfg_pp",
    "dpmpp_2m_sde", "dpmpp_2m_sde_gpu", "dpmpp_2m_sde_heun",
    "dpmpp_2m_sde_heun_gpu", "dpmpp_3m_sde", "dpmpp_3m_sde_gpu",
    "ddpm", "lcm", "ipndm", "ipndm_v", "deis", "res_multistep",
    "res_multistep_cfg_pp", "res_multistep_ancestral", "res_multistep_ancestral_cfg_pp",
    "gradient_estimation", "gradient_estimation_cfg_pp", "er_sde", "seeds_2",
    "seeds_3", "sa_solver", "sa_solver_pece", "ddim", "uni_pc", "uni_pc_bh2"
]

SCHEDULERS = [
    "simple", "sgm_uniform", "karras", "exponential", "ddim_uniform",
    "beta", "normal", "linear_quadratic", "kl_optimal"
]

EXTENSIONS = [
    '1024x1024',
    '896x1152',
    '832x1216',
    '768x1344',
    '640x1536',
    '1152x896',
    '1216x832',
    '1344x768',
    '1536x640'
]
# Defaults
COMFYUI_URL = "http://127.0.0.1:8188"
WS_URL = "ws://127.0.0.1:8188/ws"
DEFAULT_NEGATIVE = "(asian:1.2), simple background, poorly drawn face, doll, wax figure, (words, letters, symbols:1.25), uncanny valley, extra arms, amputation, extra legs, extra fingers, many fingers, bad anatomy, ugly"
WORKFLOW_JSON_PATH = Path(__file__).parent / 'workflow' / 'Z-image.json'  # Can change to custom path

DEFAULT_SEED = 0 
DEFAULT_STEPS = 9
DEFAULT_EXTENSION = '1024x1024'
DEFAULT_CFG = 1.0
DEFAULT_SAMPLER_NAME = "euler"
DEFAULT_SCHEDULER = "simple"
DEFAULT_SHIFT = 3.00


