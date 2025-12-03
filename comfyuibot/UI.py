from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from constant import *


# UI helpers
def back_to_main():
    kb = [[InlineKeyboardButton(text="◀️ Back", callback_data='back_to_main')]]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_to_settings():
    kb = [[InlineKeyboardButton(text="◀️ Back", callback_data='back_to_settings')]]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def main_menu():
    kb = [
        [InlineKeyboardButton(text="🎨 Generate", callback_data='generate'), InlineKeyboardButton(text="✏️ Change Prompt", callback_data='change_positive')],
        [InlineKeyboardButton(text="⚙️ Settings", callback_data='settings')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def settings_menu():
    kb = [
        [InlineKeyboardButton(text="⛔ Negative", callback_data='negative'), InlineKeyboardButton(text="🌱 Seed", callback_data='seed')],
        [InlineKeyboardButton(text="📐 Extension", callback_data='extension'), InlineKeyboardButton(text="🔢 Steps", callback_data='steps')],
        [InlineKeyboardButton(text="⚙️ CFG", callback_data='cfg'), InlineKeyboardButton(text="🔄 Shift", callback_data='shift')],
        [InlineKeyboardButton(text="🎨 Sampler", callback_data='sampler_name'), InlineKeyboardButton(text="📅 Scheduler", callback_data='scheduler')],
        [InlineKeyboardButton(text="◀️ Back", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def image_keyboard():
    kb = [[InlineKeyboardButton(text="🔄 Repeat", callback_data='repeat'), InlineKeyboardButton(text="✏️ Change", callback_data='change')]]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def cancel_keyboard():
    kb = [[InlineKeyboardButton(text="❌ Cancel Generation", callback_data='cancel_generation')]]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def extension_keyboard():
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки
    builder.button(text="⬜ 1:1 (1024x1024)", callback_data="1024x1024")     
    builder.button(text="🔲 3:4 (896x1152)", callback_data="896x1152")      
    builder.button(text="📱 5:8 (832x1216)", callback_data="832x1216")       
    builder.button(text="📲 9:16 (768x1344)", callback_data="768x1344")       
    builder.button(text="📏 9:21 (640x1536)", callback_data="640x1536")       
    builder.button(text="▭ 4:3 (1152x896)", callback_data="1152x896")         
    builder.button(text="🖼️ 3:2 (1216x832)", callback_data="1216x832")        
    builder.button(text="🖥️ 16:9 (1344x768)", callback_data="1344x768")       
    builder.button(text="📺 21:9 (1536x640)", callback_data="1536x640")   
    builder.button(text="◀️ Back", callback_data='back_to_settings')
    
    # По 2 кнопки в ряд
    builder.adjust(3)
    
    return builder.as_markup()
def scheduler_keyboard():
    builder = InlineKeyboardBuilder()
    scheduler_names = {
    'simple': '🟢 Simple',
    'sgm_uniform': '🟦 SGM Uniform',
    'karras': '🟠 Karras',
    'exponential': '📈 Exponential',
    'ddim_uniform': '🎯 DDIM Uniform',
    'beta': '🔷 Beta',
    'normal': '📊 Normal',
    'linear_quadratic': '📐 Linear Quadratic',
    'kl_optimal': '⚡ KL Optimal'
}
    for scheduler in SCHEDULERS:
        # Используем красивое название если есть, иначе форматируем стандартно
        if scheduler in scheduler_names:
            display_name = scheduler_names[scheduler]
        
        builder.button(text=display_name, callback_data=f"{scheduler}")
    
    # По 1 кнопке в ряд для лучшей читаемости
    builder.adjust(2)
    
    # Добавляем кнопку "Назад"
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data='back_to_settings'))
    
    return builder.as_markup()
def samplers_keyboard():
    builder = InlineKeyboardBuilder()
    
    # Словарь для красивых названий
    sampler_names = {
    'euler': '🔹 Euler',
    'euler_ancestral': '🔹 Euler Ancestral',
    'euler_cfg_pp': '🔹 Euler CFG++',
    'euler_ancestral_cfg_pp': '🔹 Euler Ancestral CFG++',
    'heun': '🔸 Heun',
    'heunpp2': '🔸 Heun++ 2',
    'dpm_2': '⚡ DPM 2',
    'dpm_2_ancestral': '⚡ DPM 2 Ancestral',
    'lms': '🔷 LMS',
    'dpm_fast': '⚡ DPM Fast',
    'dpm_adaptive': '⚡ DPM Adaptive',
    'dpmpp_2s_ancestral': '⚡ DPM++ 2S Ancestral',
    'dpmpp_2s_ancestral_cfg_pp': '⚡ DPM++ 2S Ancestral CFG++',
    'dpmpp_sde': '⚡ DPM++ SDE',
    'dpmpp_sde_gpu': '⚡ DPM++ SDE GPU',
    'dpmpp_2m': '⚡ DPM++ 2M',
    'dpmpp_2m_cfg_pp': '⚡ DPM++ 2M CFG++',
    'dpmpp_2m_sde': '⚡ DPM++ 2M SDE',
    'dpmpp_2m_sde_gpu': '⚡ DPM++ 2M SDE GPU',
    'dpmpp_2m_sde_heun': '⚡ DPM++ 2M SDE Heun',
    'dpmpp_2m_sde_heun_gpu': '⚡ DPM++ 2M SDE Heun GPU',
    'dpmpp_3m_sde': '⚡ DPM++ 3M SDE',
    'dpmpp_3m_sde_gpu': '⚡ DPM++ 3M SDE GPU',
    'ddpm': '🎯 DDPM',
    'lcm': '⚡ LCM',
    'ipndm': '🔶 IPNDM',
    'ipndm_v': '🔶 IPNDM V',
    'deis': '🔵 DEIS',
    'res_multistep': '🟣 Res Multistep',
    'res_multistep_cfg_pp': '🟣 Res Multistep CFG++',
    'res_multistep_ancestral': '🟣 Res Multistep Ancestral',
    'res_multistep_ancestral_cfg_pp': '🟣 Res Multistep Ancestral CFG++',
    'gradient_estimation': '📊 Gradient Estimation',
    'gradient_estimation_cfg_pp': '📊 Gradient Estimation CFG++',
    'er_sde': '🌊 ER SDE',
    'seeds_2': '🌱 SEEDS 2',
    'seeds_3': '🌱 SEEDS 3',
    'sa_solver': '🔧 SA Solver',
    'sa_solver_pece': '🔧 SA Solver PECE',
    'ddim': '🎯 DDIM',
    'uni_pc': '🚀 UniPC',
    'uni_pc_bh2': '🚀 UniPC BH2'
}
    # Добавляем кнопки
    for sampler in SAMPLERS:
        # Используем красивое название если есть, иначе форматируем стандартно
        if sampler in sampler_names:
            display_name = sampler_names[sampler]
        else:
            display_name = sampler.replace('_', ' ').title()
        
        builder.button(text=display_name, callback_data=f"{sampler}")
    
    # По 1 кнопке в ряд для лучшей читаемости
    builder.adjust(2)
    
    # Добавляем кнопку "Назад"
    builder.row(InlineKeyboardButton(text="◀️ Back", callback_data='back_to_settings'))
    
    return builder.as_markup()