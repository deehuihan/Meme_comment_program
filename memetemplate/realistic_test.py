# -*- coding: utf-8 -*-
"""
🔥 終極版壓力測試腳本 - 涵蓋所有 Edge Cases 和 Worse Cases
- 適配新的 user_ssid 格式和 Unix 時間戳系統
- 模擬各種異常用戶行為和邊界情況
- 測試服務器極限承受能力
"""

import requests
import time
import random
import threading
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
import uuid
import signal
import sys
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🚀 測試目標配置

# 🔥 全面的用戶行為類型
USER_BEHAVIOR_TYPES = {
    'perfect_user': {
        'description': '完美用戶 - 正常完成所有流程',
        'probability': 0.20,
        'completion_time': (120, 300),  # 2-5分鐘
        'label_interval': (0.5, 2.0),
        'behavior': 'normal'
    },
    'fast_clicker': {
        'description': '快速點擊用戶 - 極快完成',
        'probability': 0.15,
        'completion_time': (30, 90),   # 0.5-1.5分鐘
        'label_interval': (0.1, 0.5),
        'behavior': 'fast'
    },
    'slow_reader': {
        'description': '慢速閱讀用戶 - 仔細閱讀每個頁面',
        'probability': 0.15,
        'completion_time': (600, 1200), # 10-20分鐘
        'label_interval': (2.0, 8.0),
        'behavior': 'slow'
    },
    'partial_abandoner': {
        'description': '部分完成用戶 - 在隨機階段離開',
        'probability': 0.15,
        'completion_time': (60, 180),
        'label_interval': (1.0, 3.0),
        'behavior': 'abandon_partial'
    },
    'game_abandoner': {
        'description': '遊戲中途離開用戶 - 標記部分圖片後離開',
        'probability': 0.10,
        'completion_time': (90, 240),
        'label_interval': (0.8, 2.5),
        'behavior': 'abandon_game'
    },
    'summary_abandoner': {
        'description': '摘要頁面離開用戶 - 看到摘要但不提交email',
        'probability': 0.10,
        'completion_time': (150, 350),
        'label_interval': (1.0, 3.0),
        'behavior': 'abandon_summary'
    },
    'refresher': {
        'description': '頁面刷新用戶 - 隨機刷新頁面',
        'probability': 0.05,
        'completion_time': (180, 400),
        'label_interval': (1.0, 4.0),
        'behavior': 'refresh_pages'
    },
    'duplicate_clicker': {
        'description': '重複點擊用戶 - 重複提交相同請求',
        'probability': 0.05,
        'completion_time': (120, 300),
        'label_interval': (0.5, 2.0),
        'behavior': 'duplicate_requests'
    },
    'network_unstable': {
        'description': '網路不穩定用戶 - 模擬連線中斷',
        'probability': 0.03,
        'completion_time': (200, 500),
        'label_interval': (1.0, 5.0),
        'behavior': 'network_issues'
    },
    'malicious_user': {
        'description': '惡意用戶 - 嘗試非法操作',
        'probability': 0.02,
        'completion_time': (60, 180),
        'label_interval': (0.1, 1.0),
        'behavior': 'malicious'
    }
}

# 🔥 極限測試參數
EXTREME_TEST_CONFIG = {
    'concurrent_users': 50,      # 同時用戶數
    'total_users': 200,          # 總用戶數
    'batch_sizes': [1, 3, 5, 10, 15],  # 批次大小
    'min_batch_interval': 5,     # 最小批次間隔
    'max_batch_interval': 30,
    'stress_duration': 3600,     # 1小時壓力測試
}

# 🔥 異常測試配置
MALICIOUS_PAYLOADS = [
    "'; DROP TABLE users; --",
    "<script>alert('XSS')</script>",
    "../../../etc/passwd",
    "A" * 10000,  # 超長字串
    {"malicious": "json_injection"},
    None,
    "",
    " ",
]

# 🚀 壓力測試配置 - 生產環境
BASE_URL = "http://140.113.214.158:5000/"

USER_COMPLETION_TIMES = {
    'fast': (60, 120),       # 1-2分鐘
    'normal': (180, 240),    # 3-4分鐘  
    'slow': (300, 360)       # 5-6分鐘
}

USER_TYPE_DISTRIBUTION = {
    'fast': 0.3,     # 30% 快速用戶 (降低以減少服務器負載)
    'normal': 0.5,   # 50% 標準用戶
    'slow': 0.2      # 20% 慢速用戶
}

# 🚀 生產環境建議較小的測試規模
TOTAL_USERS = 20  # 預設降低為20個用戶
BATCH_SIZES = [1, 2, 3]  # 較小的批次大小
MIN_BATCH_INTERVAL = 15   # 增加間隔時間
MAX_BATCH_INTERVAL = 45

USED_POST_IDS = {}  # {folder_name: set(used_post_ids)}
POST_ID_LOCK = threading.Lock()

EMOTION_LABELS = ['輕蔑', '憤怒', '厭惡', '其他']
GENDERS = ['男', '女', '其他']
AGES = ['18', '20', '25', '30', '35', '40', '45', '50']

# 🚀 基於你提供的真實圖片文件夾結構（完整50個文件夾）
REAL_MEME_FOLDERS = {
    'Afraid-To-Ask-Andy': None,
    'Always-Has-Been': None,
    'Always-you-three': None,
    'Angry-Baby': None,
    'Archer': None,
    'Arthur-Fist': None,
    'Batman-Slapping-Robin': None,
    'Black-guy-hiding-behind-tree': None,
    'Charlie-Day': None,
    'Chill-guy': None,
    'Confused-Gandalf': None,
    'dave-chapelle': None,
    'Dinkleberg': None,
    'Disappointed-Man': None,
    'Disaster-Girl': None,
    'DJ-Pauly-D': None,
    'Drake-NoYes': None,
    'For-the-better-right-blank': None,
    'Futurama-Fry': None,
    'Gru-Gun': None,
    'Happy--Shock': None,
    'Hide-the-Pain-Harold': None,
    'Hold-fart': None,
    'I-am-once-again-asking': None,
    'Ill-Have-You-Know-Spongebob': None,
    'Im-The-Captain-Now': None,
    'Kevin-Hart': None,
    'Khan': None,
    'Laughing-wolf': None,
    'Leonardo-Dicaprio-Wolf-Of-Wall-Street': None,
    'Math-ladyConfused-lady': None,
    'Mocking-Spongebob': None,
    'Moe-throws-Barney': None,
    'Monkey-Puppet': None,
    'Mr-incredible-mad': None,
    'Mr-McMahon-reaction': None,
    'Nuclear-Explosion': None,
    'Obi-Wan-Kenobi': None,
    'Persian-Cat-Room-Guardian': None,
    'Picard-Wtf': None,
    'Put-It-Somewhere-Else-Patrick': None,
    'Scooby-doo-mask-reveal': None,
    'Smudge-the-cat': None,
    'Spiderman-Hospital': None,
    'Spongebob-Yelling': None,
    'Surprised-Pikachu': None,
    'Table-Flip-Guy': None,
    'Thats-a-paddlin': None,
    'Well-Yes-But-Actually-No': None,
    'You-The-Real-MVP': None
}

def generate_complete_meme_folders():
    """
    動態生成每個文件夾的完整圖片列表（1-50張）
    """
    complete_folders = {}
    
    for folder_name in REAL_MEME_FOLDERS.keys():
        # 🚀 為每個文件夾生成 1-50 的完整圖片列表
        images = []
        for i in range(1, 51):  # 1 到 50
            image_name = f"{folder_name}_{i}.png"
            images.append(image_name)
        
        complete_folders[folder_name] = images
    
    return complete_folders

REAL_MEME_FOLDERS = generate_complete_meme_folders()

# 注意力檢查圖片（只有2張）
ATTENTION_CHECK_IMAGES = [
    'attention_check_Contempt.png',
    'attention_check_Disgust.png'
]

def initialize_post_id_tracking():
    """初始化post_id追蹤"""
    global USED_POST_IDS
    USED_POST_IDS = {}
    for folder in REAL_MEME_FOLDERS.keys():
        USED_POST_IDS[folder] = set()

def get_available_post_id(folder_name, images_in_folder):
    """獲取該文件夾中可用的post_id"""
    with POST_ID_LOCK:
        # 提取所有可能的post_id
        available_post_ids = []
        for img in images_in_folder:
            try:
                post_id = int(img.split('_')[-1].replace('.png', ''))
                if post_id not in USED_POST_IDS[folder_name]:
                    available_post_ids.append((post_id, img))
            except:
                continue
        
        if not available_post_ids:
            # 如果沒有可用的，重置該文件夾（或返回隨機一張）
            print(f"[WARNING] 文件夾 {folder_name} 的post_id已用完，重置")
            USED_POST_IDS[folder_name] = set()
            available_post_ids = [(int(img.split('_')[-1].replace('.png', '')), img) 
                                for img in images_in_folder]
        
        # 隨機選擇一個可用的post_id
        selected_post_id, selected_image = random.choice(available_post_ids)
        USED_POST_IDS[folder_name].add(selected_post_id)
        
        return selected_image

def get_user_type():
    """隨機選擇用戶類型"""
    rand = random.random()
    cumulative = 0
    for user_type, probability in USER_TYPE_DISTRIBUTION.items():
        cumulative += probability
        if rand <= cumulative:
            return user_type
    return 'normal'

def calculate_user_completion_time(user_type):
    """計算用戶完成時間"""
    min_time, max_time = USER_COMPLETION_TIMES[user_type]
    return random.uniform(min_time, max_time)

class AdvancedTestUser:
    def __init__(self, user_id, behavior_type, behavior_config, batch_id):
        self.user_id = user_id
        self.behavior_type = behavior_type # e.g., 'perfect_user', 'fast_clicker'
        self.behavior_config = behavior_config # The dictionary for this behavior_type
        self.batch_id = batch_id
        self.session = requests.Session()
        self.session.verify = False # As per previous discussions for IP address usage

        self.player_name = None
        self.age = random.choice(AGES)
        self.gender = random.choice(GENDERS)
        self.images = []
        self.start_time = None
        self.success = False
        self.abandon_stage = None # For partial_abandoner
        self.labels_completed = 0
        self.errors_encountered = []
        self.abandon_after_labels = 0 # For game_abandoner
        self.view_summary_time = 0 # For summary_abandoner
        self.malicious_payloads = [] # For malicious_user

        self.setup_behavior_specific_config()

        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Android 13; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0',
        ]
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8,ja;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin', # Changed from none to same-origin for more realism after first request
            'Cache-Control': 'max-age=0'
        })

        # Behavior-specific timeout
        # The 'behavior' key in behavior_config corresponds to 'normal', 'fast', 'slow', etc.
        behavior_category = self.behavior_config.get('behavior', 'normal')
        if behavior_category == 'network_issues':
            self.current_timeout = (5, 10)  # Short timeout for network issues
        elif behavior_category == 'slow':
            self.current_timeout = (60, 120) # Long timeout for slow users
        elif behavior_category == 'fast':
            self.current_timeout = (15, 30) # Shorter for fast users
        else:
            self.current_timeout = (30, 60) # Default
        self.session.timeout = self.current_timeout


    def setup_behavior_specific_config(self):
        """根據用戶行為類型設定特定配置"""
        behavior = self.behavior_config['behavior'] # This is 'normal', 'fast', 'abandon_partial', etc.
        
        if behavior == 'abandon_partial':
            self.abandon_stage = random.choice([
                'introduction', 'consentform', 'terms', 'instruction1', 'instruction2'
            ])
        elif behavior == 'abandon_game':
            self.abandon_after_labels = random.randint(5, 30)
        elif behavior == 'abandon_summary':
            self.view_summary_time = random.uniform(10, 30) # Shorter than original, as it's just viewing
        elif behavior == 'malicious':
            self.malicious_payloads = random.sample(MALICIOUS_PAYLOADS, k=min(len(MALICIOUS_PAYLOADS), 3))


    def _make_request(self, method, url_path, data=None, json_payload=None, expected_statuses=None, step_name="Request"):
        if expected_statuses is None:
            expected_statuses = [200, 302] # Common success statuses (200 OK, 302 Redirect)
        
        full_url = f"{BASE_URL}{url_path.lstrip('/')}"
        try:
            if method.upper() == 'GET':
                response = self.session.get(full_url, timeout=self.current_timeout)
            elif method.upper() == 'POST':
                if json_payload is not None:
                    response = self.session.post(full_url, json=json_payload, timeout=self.current_timeout, headers={'Content-Type': 'application/json'})
                else:
                    response = self.session.post(full_url, data=data, timeout=self.current_timeout)
            else:
                self.errors_encountered.append(f"{step_name} error: Unsupported method {method}")
                return None, False

            if response.status_code not in expected_statuses:
                error_msg = f"{step_name} failed: Status {response.status_code}, URL: {full_url}, Expected: {expected_statuses}, Response: {response.text[:100]}"
                self.errors_encountered.append(error_msg)
                print(f"[用戶{self.user_id}] ❌ {error_msg}")
                return response, False
            
            # Update Sec-Fetch-Site after the first successful navigation
            if self.session.headers.get('Sec-Fetch-Site') == 'none':
                 self.session.headers['Sec-Fetch-Site'] = 'same-origin'

            return response, True
        except requests.exceptions.Timeout:
            error_msg = f"{step_name} TIMEOUT: URL: {full_url}"
            self.errors_encountered.append(error_msg)
            print(f"[用戶{self.user_id}] ❌ {error_msg}")
            return None, False
        except requests.exceptions.RequestException as e:
            error_msg = f"{step_name} navigation error: {e}, URL: {full_url}"
            self.errors_encountered.append(error_msg)
            print(f"[用戶{self.user_id}] ❌ {error_msg}")
            return None, False
        except Exception as e:
            error_msg = f"Unexpected error in {step_name}: {e}, URL: {full_url}"
            self.errors_encountered.append(error_msg)
            print(f"[用戶{self.user_id}] ❌ {error_msg}")
            return None, False

    def _simulate_think_time(self, scale_factor=1.0):
        min_t, max_t = self.behavior_config['label_interval']
        time.sleep(random.uniform(min_t * scale_factor, max_t * scale_factor))

    # --- Navigation Methods ---
    def navigate_introduction(self):
        self.session.headers['Sec-Fetch-Site'] = 'none' # First request
        response, success = self._make_request('GET', '/', step_name="Introduction GET")
        if not success: return False
        self._simulate_think_time()
        # Assuming clicking "start" is a POST to the same URL or a specific "start" endpoint
        response, success = self._make_request('POST', '/', data={}, step_name="Introduction POST")
        if success: print(f"[用戶{self.user_id}] ✅ Navigated introduction")
        return success

    def navigate_consentform(self):
        response, success = self._make_request('GET', '/consentform', step_name="Consent GET")
        if not success: return False
        self._simulate_think_time()
        response, success = self._make_request('POST', '/consentform', data={'consent_given': 'yes'}, step_name="Consent POST")
        if success: print(f"[用戶{self.user_id}] ✅ Navigated consentform")
        return success

    def navigate_terms(self):
        response, success = self._make_request('GET', '/terms', step_name="Terms GET")
        if not success: return False
        self._simulate_think_time()
        response, success = self._make_request('POST', '/terms', data={'terms_accepted': 'yes'}, step_name="Terms POST")
        if success: print(f"[用戶{self.user_id}] ✅ Navigated terms")
        return success

    def navigate_instruction1(self):
        response, success = self._make_request('GET', '/instruction1', step_name="Instruction1 GET")
        if not success: return False
        self._simulate_think_time()
        response, success = self._make_request('POST', '/instruction1', data={}, step_name="Instruction1 POST")
        if success: print(f"[用戶{self.user_id}] ✅ Navigated instruction1")
        return success

    def navigate_instruction2(self):
        response, success = self._make_request('GET', '/instruction2', step_name="Instruction2 GET")
        if not success: return False
        self._simulate_think_time()
        form_data = {'age': self.age, 'gender': self.gender}
        response, success = self._make_request('POST', '/instruction2', data=form_data, step_name="Instruction2 POST")
        if not success: return False
        
        if response: # Extract player_name if POST was successful
            extracted_name = self.extract_player_name_from_page(response.text)
            if extracted_name:
                self.player_name = extracted_name
                print(f"[用戶{self.user_id}] ✅ Navigated instruction2, player_name: {self.player_name}")
            else:
                # This could be an error if player_name is critical for next steps
                print(f"[用戶{self.user_id}] ⚠️ Navigated instruction2, but player_name not extracted.")
                # self.errors_encountered.append("Instruction2: player_name not extracted")
                # return False # Decide if this is a critical failure
        return True


    def navigate_practice(self):
        # Practice URL might depend on player_name or be generic
        practice_url_path = "/practice"
        if self.player_name: # Assuming player_name might be part of the URL
             # practice_url_path = f"/practice/{self.player_name}" # Uncomment and adjust if needed
             pass

        response, success = self._make_request('GET', practice_url_path, step_name="Practice GET")
        if not success: return False
        self._simulate_think_time(scale_factor=1.5) # Longer for practice
        # Assuming practice is just viewing, no POST to "finish" unless specified by app_used.py
        if success: print(f"[用戶{self.user_id}] ✅ Navigated practice")
        return success

    def navigate_game(self):
        if not self.player_name:
            # Attempt to get player_name if not set, e.g., by visiting a generic game page
            # This is a fallback, ideally player_name is set reliably earlier
            print(f"[用戶{self.user_id}] ⚠️ player_name not set before game, attempting to GET /game to find it.")
            response_game_generic, success_generic = self._make_request('GET', '/game', step_name="Game Generic GET for PlayerName")
            if success_generic and response_game_generic:
                extracted = self.extract_player_name_from_page(response_game_generic.text)
                if extracted:
                    self.player_name = extracted
                    print(f"[用戶{self.user_id}] Player_name extracted from /game: {self.player_name}")
                else:
                    self.errors_encountered.append("Game: player_name not set and could not be extracted from /game.")
                    return False
            elif not success_generic:
                 self.errors_encountered.append("Game: player_name not set and failed to GET /game to find it.")
                 return False


        game_url_path = f"/game/{self.player_name}" if self.player_name else "/game" # Fallback if still no player_name
        
        response, success = self._make_request('GET', game_url_path, step_name="Game GET")
        if not success: return False

        if not self.images: # Generate images if not already done
            self.images = self.generate_52_realistic_images()
        
        if success: print(f"[用戶{self.user_id}] ✅ Navigated game. Player: {self.player_name}")
        return success

    def navigate_summary(self):
        summary_url_path = f"/summary/{self.player_name}" if self.player_name else "/summary"
        response, success = self._make_request('GET', summary_url_path, step_name="Summary GET")
        if success: print(f"[用戶{self.user_id}] ✅ Navigated summary")
        return success

    # --- Action Methods ---
    def label_image_realistic(self, image_path):
        if not self.player_name:
            self.errors_encountered.append(f"Labeling {image_path}: player_name not set.")
            return False

        label = ""
        is_attention_check = 'attention_check/' in image_path

        if self.behavior_config['behavior'] == 'attention_fail' and is_attention_check: # For attention_saboteur
            correct_label = self.get_attention_check_label(image_path)
            possible_wrong_labels = [l for l in EMOTION_LABELS if l != correct_label]
            label = random.choice(possible_wrong_labels) if possible_wrong_labels else EMOTION_LABELS[0]
            print(f"[用戶{self.user_id}] 😈 Attention check: Chose wrong '{label}' for {image_path} (Correct: {correct_label})")
        elif is_attention_check:
            label = self.get_attention_check_label(image_path)
        else:
            label = random.choice(EMOTION_LABELS)

        # Determine response time based on behavior category ('fast', 'slow', 'normal')
        behavior_category = self.behavior_config.get('behavior', 'normal')
        if 'fast' in behavior_category: # Covers 'fast' and 'fast_clicker'
            response_time_ms = random.randint(300, 1000) # milliseconds
        elif 'slow' in behavior_category: # Covers 'slow' and 'slow_reader'
            response_time_ms = random.randint(2000, 8000)
        else: # normal, abandoners, refreshers, etc.
            response_time_ms = random.randint(800, 3000)
        
        # Add jitter based on label_interval from specific behavior_type config
        min_interval, max_interval = self.behavior_config['label_interval']
        response_time_ms += random.uniform(min_interval * 100, max_interval * 100) # Add small portion of interval
        response_time_ms = max(100, int(response_time_ms)) # Ensure positive and reasonable

        # Convert response_time to string format to match server expectations
        response_time_str = str(response_time_ms)
        
        payload = {'image_name': image_path, 'label': label, 'response_time': response_time_str}
        
        # Network issue simulation for labeling
        if self.behavior_config['behavior'] == 'network_issues' and random.random() < 0.15: # 15% chance of issue per label
            print(f"[用戶{self.user_id}] 📶 Simulating network issue during label for {image_path}")
            if random.random() < 0.5: # 50% of those are timeouts
                self.errors_encountered.append(f"Labeling {image_path}: Simulated network timeout.")
                time.sleep(random.uniform(self.current_timeout[0], self.current_timeout[1])) # Simulate timeout duration
                return False
            else: # Simulate delay
                time.sleep(random.uniform(3,7))

        _r, success = self._make_request('POST', f"/label/{self.player_name}", json_payload=payload, step_name=f"Label {image_path.split('/')[-1]}", expected_statuses=[200])
        return success

    def complete_all_labels(self, label_method_override=None):
        if not self.player_name:
            self.errors_encountered.append("Labeling: player_name not set.")
            return False
        if not self.images:
            self.images = self.generate_52_realistic_images()

        label_method = label_method_override if callable(label_method_override) else self.label_image_realistic

        for i, image_path in enumerate(self.images):
            if not label_method(image_path):
                print(f"[用戶{self.user_id}] 🛑 Failed to label image {i+1}/{len(self.images)}: {image_path}. Aborting labeling.")
                return False
            self.labels_completed += 1
            self._simulate_think_time() # Standard think time between labels
            if (i + 1) % 10 == 0:
                print(f"[用戶{self.user_id}] 📝 Labeled {self.labels_completed}/{len(self.images)} images...")
        print(f"[用戶{self.user_id}] ✅ Completed all {len(self.images)} labels.")
        return True

    def complete_all_labels_fast(self):
        original_interval = self.behavior_config['label_interval']
        self.behavior_config['label_interval'] = (0.1, 0.3) # Override for fast clicks
        success = self.complete_all_labels()
        self.behavior_config['label_interval'] = original_interval # Restore
        if success: print(f"[用戶{self.user_id}] ✅ Completed all labels (fast).")
        return success

    def complete_all_labels_slow(self):
        original_interval = self.behavior_config['label_interval']
        self.behavior_config['label_interval'] = (3.0, 10.0) # Override for slow clicks
        success = self.complete_all_labels()
        self.behavior_config['label_interval'] = original_interval # Restore
        if success: print(f"[用戶{self.user_id}] ✅ Completed all labels (slow).")
        return success

    def complete_partial_labels(self, num_to_label):
        if not self.player_name:
            self.errors_encountered.append(f"Labeling (partial): player_name not set.")
            return False
        if not self.images:
            self.images = self.generate_52_realistic_images()

        for i in range(min(num_to_label, len(self.images))):
            image_path = self.images[i]
            if not self.label_image_realistic(image_path):
                return False
            self.labels_completed += 1
            self._simulate_think_time()
        print(f"[用戶{self.user_id}] ✅ Completed {self.labels_completed} partial labels.")
        return True

    def submit_email(self):
        if not self.player_name:
            self.errors_encountered.append("Email submission: player_name not set.")
            return False
        email_address = f"user{self.user_id}_{int(time.time())}@example.com"
        participation = random.choice(['yes', 'no'])
        payload = {'email': email_address, 'participation': participation}
        
        response, success = self._make_request('POST', f"/save_email/{self.player_name}", data=payload, step_name="Submit Email", expected_statuses=[200])
        
        if success and response:
            try:
                json_response = response.json()
                if json_response.get('success'):
                    print(f"[用戶{self.user_id}] ✅ Email submitted: {email_address}")
                    return True
                else:
                    self.errors_encountered.append(f"Email submission failed: Server responded success=false. Data: {payload}, Response: {response.text[:100]}")
                    return False
            except json.JSONDecodeError:
                self.errors_encountered.append(f"Email submission failed: Not valid JSON. Data: {payload}, Status: {response.status_code}, Response: {response.text[:100]}")
                return False
        return False

    # --- Variant Methods ---
    def _navigate_with_refresh(self, base_nav_method, step_name_prefix):
        # Initial navigation
        if not base_nav_method():
            return False # Base navigation failed
        
        # Random refreshes
        for i in range(random.randint(1, 2)): # 1 to 2 refreshes
            self._simulate_think_time(scale_factor=0.5)
            print(f"[用戶{self.user_id}] 🔄 Refreshing {step_name_prefix} page (attempt {i+1})")
            # Assuming refresh is a GET to the same effective URL as the base_nav_method's GET part
            # This is a simplification; true refresh might need specific URL from base_nav_method
            current_url_path = self.session.url.replace(BASE_URL, "") # Get current relative path
            if not current_url_path: current_url_path = "/" # Default to root if parse fails

            _resp, refresh_success = self._make_request('GET', current_url_path, step_name=f"{step_name_prefix} Refresh {i+1}")
            if not refresh_success:
                print(f"[用戶{self.user_id}] ⚠️ {step_name_prefix} Refresh {i+1} failed, continuing flow if possible.")
                # Decide if a failed refresh should abort. For now, it continues.
        return True

    def navigate_introduction_with_refresh(self):
        return self._navigate_with_refresh(self.navigate_introduction, "Introduction")
        # The POST part of navigate_introduction will happen after refreshes if self.navigate_introduction is structured with GET then POST

    def navigate_consentform_with_refresh(self):
        return self._navigate_with_refresh(self.navigate_consentform, "Consentform")
    
    def navigate_practice_with_refresh(self):
        return self._navigate_with_refresh(self.navigate_practice, "Practice")

    def navigate_game_with_refresh(self):
         return self._navigate_with_refresh(self.navigate_game, "Game")

    def _navigate_with_duplicates(self, base_get_url, base_post_url, post_data, step_name_prefix):
        response_get, success_get = self._make_request('GET', base_get_url, step_name=f"{step_name_prefix} (Dup) GET")
        if not success_get: return False
        self._simulate_think_time()

        num_duplicates = random.randint(1, 2) # 1-2 extra POSTs
        last_post_success = False
        for i in range(num_duplicates + 1): # Original + duplicates
            print(f"[用戶{self.user_id}] 🔁 Duplicative POST to {step_name_prefix} ({i+1}/{num_duplicates+1})")
            _resp, post_success_current = self._make_request('POST', base_post_url, data=post_data, step_name=f"{step_name_prefix} (Dup) POST {i+1}", expected_statuses=[200,302,400,409]) # Allow errors for duplicates
            if i == num_duplicates: # Check success of the last attempt (or the one that should proceed)
                last_post_success = post_success_current and (_resp.status_code in [200,302]) if _resp else False
            if i < num_duplicates: time.sleep(random.uniform(0.1, 0.5)) # Small delay
        
        if last_post_success: print(f"[用戶{self.user_id}] ✅ Navigated {step_name_prefix} (with duplicates)")
        else: self.errors_encountered.append(f"{step_name_prefix} (Dup) final POST failed or had unexpected status.")
        return last_post_success

    def navigate_introduction_with_duplicates(self):
        return self._navigate_with_duplicates('/', '/', {}, "Introduction")

    def navigate_consentform_with_duplicates(self):
        return self._navigate_with_duplicates('/consentform', '/consentform', {'consent_given': 'yes'}, "Consentform")

    def complete_all_labels_with_duplicates(self):
        if not self.player_name:
            self.errors_encountered.append("Labeling (Dup): player_name not set.")
            return False
        if not self.images:
            self.images = self.generate_52_realistic_images()

        for i, image_path in enumerate(self.images):
            num_duplicates = random.randint(0, 1) # 0 or 1 extra attempt
            last_label_attempt_successful = False
            for attempt in range(num_duplicates + 1):
                if attempt > 0:
                    print(f"[用戶{self.user_id}] 🔁 Duplicate label attempt {attempt+1} for {image_path}")
                    self._simulate_think_time(scale_factor=0.2) # Very short delay
                
                current_attempt_success = self.label_image_realistic(image_path)
                if attempt == num_duplicates: # This is the "final" attempt for this image
                    last_label_attempt_successful = current_attempt_success
            
            if not last_label_attempt_successful:
                print(f"[用戶{self.user_id}] 🛑 Failed to label image {i+1}/{len(self.images)}: {image_path} after duplicate attempts. Aborting.")
                return False
            
            self.labels_completed += 1 # Count one success per image
            self._simulate_think_time() # Normal think time after an image is "done"
            if (i + 1) % 10 == 0:
                print(f"[用戶{self.user_id}] 📝 Labeled {self.labels_completed}/{len(self.images)} images (with duplicates)...")
        print(f"[用戶{self.user_id}] ✅ Completed all {len(self.images)} labels (with duplicates).")
        return True

    def submit_email_with_duplicates(self):
        if not self.player_name:
            self.errors_encountered.append("Email (Dup): player_name not set.")
            return False
        email_address = f"user{self.user_id}_{int(time.time())}_dup@example.com"
        participation = random.choice(['yes', 'no'])
        payload = {'email': email_address, 'participation': participation}
        
        num_duplicates = random.randint(1, 2)
        last_submit_successful = False

        for i in range(num_duplicates + 1):
            print(f"[用戶{self.user_id}] 🔁 Duplicative Email Submit ({i+1}/{num_duplicates+1})")
            response, success = self._make_request('POST', f"/save_email/{self.player_name}", data=payload, step_name=f"Submit Email (Dup) {i+1}", expected_statuses=[200, 400, 409])
            
            current_attempt_truly_successful = False
            if success and response:
                try:
                    json_data = response.json()
                    if response.status_code == 200 and json_data.get('success'):
                        current_attempt_truly_successful = True
                except json.JSONDecodeError:
                    pass # Not a JSON success response
            
            if i == num_duplicates: # This is the "final" attempt
                last_submit_successful = current_attempt_truly_successful
            
            if i < num_duplicates: time.sleep(random.uniform(0.1, 0.5))

        if last_submit_successful: print(f"[用戶{self.user_id}] ✅ Email submitted (with duplicates): {email_address}")
        else: self.errors_encountered.append(f"Email (Dup) final submission failed or was not successful. Payload: {payload}")
        return last_submit_successful

    def _simulate_network_glitch(self, step_name):
        if random.random() < 0.25: # 25% chance of a glitch
            glitch_type = random.choice(['delay', 'timeout_exception', 'status_error'])
            print(f"[用戶{self.user_id}] 📶 Simulating network {glitch_type} for {step_name}")
            if glitch_type == 'delay':
                time.sleep(random.uniform(self.current_timeout[0] * 0.5, self.current_timeout[1] * 1.5)) # Significant delay
                return True # Glitch happened, but didn't stop the request from eventually proceeding (simulated)
            elif glitch_type == 'timeout_exception':
                self.errors_encountered.append(f"{step_name}: Simulated network timeout exception.")
                return False # Glitch causes failure
            elif glitch_type == 'status_error':
                self.errors_encountered.append(f"{step_name}: Simulated network status error (e.g., 503).")
                # In a real _make_request, this would be a non-200/302 status. Here we just mark error.
                return False # Glitch causes failure
        return True # No glitch simulated for this call

    def navigate_introduction_with_network_issues(self):
        if not self._simulate_network_glitch("Intro GET (NI)"): return False
        return self.navigate_introduction() # Base method will use the session's already short timeout

    def navigate_instruction2_with_network_issues(self):
        if not self._simulate_network_glitch("Instruction2 GET (NI)"): return False
        return self.navigate_instruction2()

    def complete_all_labels_with_network_issues(self):
        # Network issues are already partly handled in label_image_realistic for 'network_issues' behavior.
        # This method can ensure the overall flow is more susceptible.
        print(f"[用戶{self.user_id}] 📶 Starting label completion with general network instability.")
        return self.complete_all_labels() # label_image_realistic will apply per-label issues

    # --- Malicious Methods ---
    def navigate_instruction2_malicious(self):
        response_get, success_get = self._make_request('GET', '/instruction2', step_name="Instruction2 (Malicious) GET")
        if not success_get: return False
        self._simulate_think_time(scale_factor=0.3)

        chosen_payload = {}
        if self.malicious_payloads: # Ensure list is not empty
            payload_parts = {
                'age': random.choice([self.age, random.choice(self.malicious_payloads)]),
                'gender': random.choice([self.gender, random.choice(self.malicious_payloads)]),
            }
            if random.random() < 0.5: # Add an extra field sometimes
                payload_parts[random.choice(self.malicious_payloads) if isinstance(random.choice(self.malicious_payloads), str) else 'extra_evil'] = random.choice(self.malicious_payloads)
            
            # Filter out None keys that might come from malicious_payloads if it contains None
            chosen_payload = {k:v for k,v in payload_parts.items() if k is not None}


        print(f"[用戶{self.user_id}] 🦹 Instruction2 (Malicious) - Attempting payload: {str(chosen_payload)[:200]}")
        _resp_mal, success_mal = self._make_request('POST', '/instruction2', data=chosen_payload, step_name="Instruction2 (Malicious) POST", expected_statuses=[200,302,400,403,500])

        if success_mal and _resp_mal and _resp_mal.status_code in [200,302]:
            print(f"[用戶{self.user_id}] ⚠️ Instruction2 (Malicious) - Server accepted malicious payload! Status: {_resp_mal.status_code}")
            # Try to extract player name if it went through
            extracted_name = self.extract_player_name_from_page(_resp_mal.text)
            if extracted_name: self.player_name = extracted_name
            return True # Count as "success" for malicious user if server accepted it
        elif success_mal and _resp_mal and _resp_mal.status_code in [400,403]:
             print(f"[用戶{self.user_id}] ✅ Instruction2 (Malicious) - Server correctly rejected payload with status: {_resp_mal.status_code}")
        # else: an error was already logged by _make_request or it was a 500

        # Malicious user might try a normal submission if the malicious one "failed" (was rejected)
        if random.random() < 0.7 or not self.player_name: # Higher chance if no player_name yet
            print(f"[用戶{self.user_id}] 🦹 Instruction2 (Malicious) - Attempting normal submission after malicious try.")
            self._simulate_think_time(scale_factor=0.5)
            return self.navigate_instruction2() # Call the normal version
        
        return True # Malicious step is "done" even if payload rejected, unless it tries normal and fails

    def complete_all_labels_malicious(self):
        if not self.player_name:
            print(f"[用戶{self.user_id}] 🦹 Labeling (Malicious) - No player_name, faking one: user_evil_{self.user_id}")
            self.player_name = f"user_evil_{self.user_id}" 
            # Server should ideally reject this if player_name isn't valid
        
        if not self.images: self.images = self.generate_52_realistic_images()

        for i, image_path in enumerate(self.images):
            label = random.choice(EMOTION_LABELS)
            response_time_ms = random.randint(50, 800) # Quick, erratic
            payload = {'image_name': image_path, 'label': label, 'response_time': response_time_ms}

            if self.malicious_payloads and random.random() < 0.25: # 25% chance to inject something
                field_to_poison = random.choice(['image_name', 'label', 'response_time', 'extra_param'])
                poison = random.choice(self.malicious_payloads)
                if field_to_poison == 'extra_param':
                    payload[random.choice(self.malicious_payloads) if isinstance(random.choice(self.malicious_payloads), str) else 'evil_field'] = poison
                else:
                    payload[field_to_poison] = poison
                print(f"[用戶{self.user_id}] 🦹 Labeling (Malicious) - Poisoning field '{field_to_poison}' for {image_path}")
            
            _resp, _success = self._make_request('POST', f"/label/{self.player_name}", json_payload=payload, step_name=f"Label Malicious {image_path.split('/')[-1]}", expected_statuses=[200,400,403,404,500])
            # Malicious user continues regardless of individual label success
            self.labels_completed +=1
            self._simulate_think_time(scale_factor=0.1) # Very fast
        
        print(f"[用戶{self.user_id}] ✅ Completed all {len(self.images)} labels (maliciously).")
        return True # Malicious flow "succeeds" by attempting all labels

    def submit_email_malicious(self):
        if not self.player_name:
            self.player_name = f"user_evil_email_{self.user_id}"

        email_address = f"user{self.user_id}_{int(time.time())}@example.com"
        participation = 'yes'
        payload = {'email': email_address, 'participation': participation}

        if self.malicious_payloads and random.random() < 0.5: # 50% chance to poison email submission
            field_to_poison = random.choice(['email', 'participation', 'extra_field'])
            poison = random.choice(self.malicious_payloads)
            if field_to_poison == 'extra_field':
                 payload[random.choice(self.malicious_payloads) if isinstance(random.choice(self.malicious_payloads), str) else 'evil_submit_field'] = poison
            else:
                payload[field_to_poison] = poison
            print(f"[用戶{self.user_id}] 🦹 Email (Malicious) - Poisoning field '{field_to_poison}' for submission.")
        
        _resp, _success = self._make_request('POST', f"/save_email/{self.player_name}", data=payload, step_name="Submit Email (Malicious)", expected_statuses=[200,400,403,404,500])
        
        if _success and _resp and _resp.status_code == 200:
            try:
                if _resp.json().get('success'):
                    print(f"[用戶{self.user_id}] ⚠️ Email (Malicious) - Server accepted malicious email payload: {str(payload)[:100]}")
            except json.JSONDecodeError: pass # Not a concern for malicious user if it's not JSON

        return True # Malicious flow "succeeds" by attempting

    # --- Helper methods from original script ---
    def extract_player_name_from_page(self, page_html):
        if not page_html: return None
        try:
            soup = BeautifulSoup(page_html, 'html.parser')
            patterns = [
                r'player_name["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'"player_name"\s*:\s*"([^"]+)"',
                r'var\s+player_name\s*=\s*["\']([^"\']+)["\'];',
                r'const\s+player_name\s*=\s*["\']([^"\']+)["\'];',
                r'let\s+player_name\s*=\s*["\']([^"\']+)["\'];',
            ]
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string:
                    for pattern in patterns:
                        match = re.search(pattern, script.string)
                        if match: return match.group(1)
            
            player_input = soup.find('input', {'name': 'player_name', 'value': True})
            if player_input: return player_input['value']
            
            player_input_id = soup.find('input', {'id': 'player_name', 'value': True})
            if player_input_id: return player_input_id['value']

            # Search for user_xxxxxx pattern in URLs or text
            user_id_pattern = re.compile(r'user_[a-f0-9]{6,}') # More flexible user_ssid
            
            # Check common places like form actions or links
            forms = soup.find_all('form', action=True)
            for form in forms:
                match = user_id_pattern.search(form['action'])
                if match: return match.group(0)
            
            links = soup.find_all('a', href=True)
            for link in links:
                match = user_id_pattern.search(link['href'])
                if match: return match.group(0)

            # Fallback: search in the whole text
            match_in_text = user_id_pattern.search(page_html)
            if match_in_text: return match_in_text.group(0)

            return None
        except Exception as e:
            print(f"[用戶{self.user_id}] Error extracting player_name: {e}")
            self.errors_encountered.append(f"Player name extraction error: {e}")
            return None

    def generate_52_realistic_images(self):
        selected_images = []
        available_folders = list(REAL_MEME_FOLDERS.keys())
        random.shuffle(available_folders) # Shuffle to get variety if less than 50 folders are used
        
        # Ensure USED_POST_IDS is initialized for folders we might use
        for folder_name in available_folders:
            with POST_ID_LOCK:
                if folder_name not in USED_POST_IDS:
                    USED_POST_IDS[folder_name] = set()

        # Select 50 normal images
        for i in range(50):
            folder_name = available_folders[i % len(available_folders)] # Cycle through folders
            images_in_folder = REAL_MEME_FOLDERS.get(folder_name, [])
            if not images_in_folder:
                # This case should ideally not happen if REAL_MEME_FOLDERS is populated
                self.errors_encountered.append(f"Image generation: Folder {folder_name} has no images.")
                # Add a placeholder or skip, for now, let's try to add a placeholder to keep count
                selected_images.append(f"{folder_name}/placeholder_error_1.png") 
                continue

            selected_image_name = get_available_post_id(folder_name, images_in_folder) # This returns just the image name
            if selected_image_name:
                full_path = f"{folder_name}/{selected_image_name}"
                selected_images.append(full_path)
            else:
                # Fallback if get_available_post_id returns None (e.g., all used and reset failed)
                self.errors_encountered.append(f"Image generation: Could not get image for {folder_name}.")
                selected_images.append(f"{folder_name}/placeholder_error_2.png")


        # Add 2 attention check images
        if len(ATTENTION_CHECK_IMAGES) >= 2:
            attention_sample = random.sample(ATTENTION_CHECK_IMAGES, 2)
        elif ATTENTION_CHECK_IMAGES: # if only 1 is available
             attention_sample = ATTENTION_CHECK_IMAGES * 2 
        else: # if no attention images defined
            attention_sample = ["attention_check/dummy_check1.png", "attention_check/dummy_check2.png"]


        # Insert attention checks at random valid positions (e.g., not first or last, reasonable spread)
        # Ensure positions are valid for a list of 50 images before insertion
        pos1 = random.randint(10, 25) 
        pos2 = random.randint(26, 45)
        if pos1 == pos2: pos2 = pos1 + 1 # Ensure distinct
        insert_positions = sorted([pos1, pos2], reverse=True) # Insert from end to keep indices valid

        for i, attention_img_name in enumerate(attention_sample):
            # The ATTENTION_CHECK_IMAGES should already contain the "attention_check/" prefix if that's how they are stored/named
            # If not, add it here:
            if not attention_img_name.startswith("attention_check/"):
                 attention_path = f"attention_check/{attention_img_name}"
            else:
                 attention_path = attention_img_name
            
            # Use the pre-calculated insert positions
            # The positions were for a list of 50. After first insertion, list is 51.
            # Correct logic is to insert at specific indices into the list of 50.
            # Example: insert at index 20 and index 40 of the original 50.
            # If inserting into selected_images (which is already 50 long):
            # selected_images.insert(insert_positions[i], attention_path) # This is if positions are for the growing list
            # Simpler:
            if i == 0: selected_images.insert(pos2, attention_path) # Insert later one first
            if i == 1: selected_images.insert(pos1, attention_path)


        return selected_images


    def get_attention_check_label(self, image_path):
        filename = image_path.lower()
        if 'contempt' in filename: return '輕蔑'
        if 'disgust' in filename: return '厭惡'
        # Add other attention check keywords if any
        # if 'anger' in filename: return '憤怒' # Example if you add an anger check image
        return random.choice(EMOTION_LABELS) # Fallback if no keyword matches

    # --- Flow Execution Methods (Copied from provided context, ensure they call implemented methods) ---
    def execute_comprehensive_test(self):
        try:
            self.start_time = time.time()
            behavior_desc = self.behavior_config['description']
            print(f"[批次{self.batch_id}|用戶{self.user_id}] 🚀 開始測試: {behavior_desc}")
            
            # The 'behavior' key in behavior_config is e.g. 'normal', 'fast', 'abandon_partial'
            flow_behavior = self.behavior_config['behavior'] 
            
            success = False
            if flow_behavior == 'normal': success = self.execute_normal_flow()
            elif flow_behavior == 'fast': success = self.execute_fast_flow()
            elif flow_behavior == 'slow': success = self.execute_slow_flow()
            elif flow_behavior == 'abandon_partial': success = self.execute_partial_abandon_flow()
            elif flow_behavior == 'abandon_game': success = self.execute_game_abandon_flow()
            elif flow_behavior == 'abandon_summary': success = self.execute_summary_abandon_flow()
            elif flow_behavior == 'refresh_pages': success = self.execute_refresh_flow()
            elif flow_behavior == 'duplicate_requests': success = self.execute_duplicate_flow()
            elif flow_behavior == 'network_issues': success = self.execute_network_issue_flow()
            elif flow_behavior == 'malicious': success = self.execute_malicious_flow()
            elif flow_behavior == 'attention_fail': # If you add this behavior type
                # This user type will intentionally fail attention checks in label_image_realistic
                success = self.execute_normal_flow() # Or a specific flow
            else: # Default to normal flow for any undefined behavior string
                print(f"[用戶{self.user_id}] ⚠️ Unknown behavior string '{flow_behavior}', defaulting to normal flow.")
                success = self.execute_normal_flow()
            
            actual_time = time.time() - self.start_time
            status_icon = "✅ 成功" if success else "❌ 失敗"
            error_detail = f" (First error: {self.errors_encountered[0]})" if self.errors_encountered else ""
            print(f"[批次{self.batch_id}|用戶{self.user_id}] {status_icon} - {actual_time/60:.1f}分鐘, 錯誤: {len(self.errors_encountered)}{error_detail}")
            
            self.success = success
            return success
            
        except Exception as e:
            # This top-level exception is a safety net. Errors should ideally be caught in specific methods.
            error_msg = f"執行異常 (Outer): {e}"
            print(f"[批次{self.batch_id}|用戶{self.user_id}] ❌ {error_msg}")
            self.errors_encountered.append(error_msg)
            self.success = False # Ensure success is false if we reach here
            # To provide more context for debugging the test script itself:
            import traceback
            traceback.print_exc()
            return False

    def execute_normal_flow(self):
        try:
            if not self.navigate_introduction(): return False
            if not self.navigate_consentform(): return False
            if not self.navigate_terms(): return False
            if not self.navigate_instruction1(): return False
            if not self.navigate_instruction2(): return False
            if not self.navigate_practice(): return False
            if not self.navigate_game(): return False
            if not self.complete_all_labels(): return False
            if not self.navigate_summary(): return False
            if not self.submit_email(): return False
            return True
        except Exception as e: # Catch-all for unexpected issues in this flow
            self.errors_encountered.append(f"Normal flow unexpected error: {e}")
            return False

    def execute_fast_flow(self):
        try:
            # Fast flow implies quicker _simulate_think_time and label_image_realistic uses 'fast' behavior
            if not self.navigate_introduction(): return False
            if not self.navigate_consentform(): return False
            if not self.navigate_terms(): return False
            if not self.navigate_instruction1(): return False
            if not self.navigate_instruction2(): return False
            if not self.navigate_practice(): return False
            if not self.navigate_game(): return False
            if not self.complete_all_labels_fast(): return False # Uses specific fast labeling logic
            if not self.navigate_summary(): return False
            self._simulate_think_time(scale_factor=0.2) # Very quick look at summary
            if not self.submit_email(): return False
            return True
        except Exception as e:
            self.errors_encountered.append(f"Fast flow unexpected error: {e}")
            return False

    def execute_slow_flow(self):
        try:
            # Slow flow implies longer _simulate_think_time and label_image_realistic uses 'slow' behavior
            if not self.navigate_introduction(): return False
            if not self.navigate_consentform(): return False
            if not self.navigate_terms(): return False
            if not self.navigate_instruction1(): return False
            if not self.navigate_instruction2(): return False
            if not self.navigate_practice(): return False
            if not self.navigate_game(): return False
            if not self.complete_all_labels_slow(): return False # Uses specific slow labeling
            if not self.navigate_summary(): return False
            self._simulate_think_time(scale_factor=3.0) # Long look at summary
            if not self.submit_email(): return False
            return True
        except Exception as e:
            self.errors_encountered.append(f"Slow flow unexpected error: {e}")
            return False

    def execute_partial_abandon_flow(self):
        try:
            if not self.navigate_introduction(): return False
            if self.abandon_stage == 'introduction': 
                print(f"[用戶{self.user_id}] 🏃 Abandoned after introduction.")
                return True # Abandonment is a "successful" scenario for this user type
            
            if not self.navigate_consentform(): return False
            if self.abandon_stage == 'consentform':
                print(f"[用戶{self.user_id}] 🏃 Abandoned after consent form.")
                return True
            
            if not self.navigate_terms(): return False
            if self.abandon_stage == 'terms':
                print(f"[用戶{self.user_id}] 🏃 Abandoned after terms.")
                return True
            
            if not self.navigate_instruction1(): return False
            if self.abandon_stage == 'instruction1':
                print(f"[用戶{self.user_id}] 🏃 Abandoned after instruction1.")
                return True
            
            if not self.navigate_instruction2(): return False
            if self.abandon_stage == 'instruction2':
                print(f"[用戶{self.user_id}] 🏃 Abandoned after instruction2.")
                return True
            
            # If abandon_stage was not hit, it means it was set to something after instruction2
            # or the logic in setup_behavior_specific_config needs review for this case.
            # For now, consider it a successful abandonment if it reaches here without specific stage.
            print(f"[用戶{self.user_id}] 🏃 Partial abandon flow completed (default abandon point or end of defined stages).")
            return True 
        except Exception as e:
            self.errors_encountered.append(f"Partial abandon flow unexpected error: {e}")
            return False

    def execute_game_abandon_flow(self):
        try:
            if not self.navigate_introduction(): return False
            if not self.navigate_consentform(): return False
            if not self.navigate_terms(): return False
            if not self.navigate_instruction1(): return False
            if not self.navigate_instruction2(): return False
            if not self.navigate_practice(): return False
            if not self.navigate_game(): return False
            
            if not self.complete_partial_labels(self.abandon_after_labels): 
                # If labeling itself fails before abandonment count, it's a script/app error
                return False 
            
            print(f"[用戶{self.user_id}] 🏃 Game abandoned after {self.labels_completed} labels.")
            return True # Successful abandonment
        except Exception as e:
            self.errors_encountered.append(f"Game abandon flow unexpected error: {e}")
            return False

    def execute_summary_abandon_flow(self):
        try:
            if not self.navigate_introduction(): return False
            if not self.navigate_consentform(): return False
            if not self.navigate_terms(): return False
            if not self.navigate_instruction1(): return False
            if not self.navigate_instruction2(): return False
            if not self.navigate_practice(): return False
            if not self.navigate_game(): return False
            if not self.complete_all_labels(): return False
            if not self.navigate_summary(): return False
            
            print(f"[用戶{self.user_id}] 📊 Viewing summary for {self.view_summary_time:.1f}s then abandoning.")
            time.sleep(self.view_summary_time)
            print(f"[用戶{self.user_id}] 🏃 Abandoned at summary page, did not submit email.")
            return True # Successful abandonment
        except Exception as e:
            self.errors_encountered.append(f"Summary abandon flow unexpected error: {e}")
            return False

    def execute_refresh_flow(self):
        try:
            if not self.navigate_introduction_with_refresh(): return False
            if not self.navigate_consentform_with_refresh(): return False
            if not self.navigate_terms(): return False # No refresh variant for terms in example
            if not self.navigate_instruction1(): return False
            if not self.navigate_instruction2(): return False
            if not self.navigate_practice_with_refresh(): return False
            if not self.navigate_game_with_refresh(): return False
            if not self.complete_all_labels(): return False # No refresh during labeling in this flow
            if not self.navigate_summary(): return False
            if not self.submit_email(): return False
            return True
        except Exception as e:
            self.errors_encountered.append(f"Refresh flow unexpected error: {e}")
            return False

    def execute_duplicate_flow(self):
        try:
            if not self.navigate_introduction_with_duplicates(): return False
            if not self.navigate_consentform_with_duplicates(): return False
            if not self.navigate_terms(): return False # No duplicate variant for terms
            if not self.navigate_instruction1(): return False
            if not self.navigate_instruction2(): return False # No duplicate for user info submission
            if not self.navigate_practice(): return False
            if not self.navigate_game(): return False
            if not self.complete_all_labels_with_duplicates(): return False
            if not self.navigate_summary(): return False
            if not self.submit_email_with_duplicates(): return False
            return True
        except Exception as e:
            self.errors_encountered.append(f"Duplicate flow unexpected error: {e}")
            return False

    def execute_network_issue_flow(self):
        try:
            # For this flow, the session timeout is already short.
            # Specific methods with _network_issues add more explicit glitches.
            if not self.navigate_introduction_with_network_issues(): return False
            if not self.navigate_consentform(): return False # Standard navigation here
            if not self.navigate_terms(): return False
            if not self.navigate_instruction1(): return False
            if not self.navigate_instruction2_with_network_issues(): return False
            if not self.navigate_practice(): return False
            if not self.navigate_game(): return False
            if not self.complete_all_labels_with_network_issues(): return False # Labeling handles its own network issues
            if not self.navigate_summary(): return False
            if not self.submit_email(): return False # Standard email submission
            return True
        except Exception as e:
            self.errors_encountered.append(f"Network issue flow unexpected error: {e}")
            return False

    def execute_malicious_flow(self):
        try:
            # Malicious flows often "succeed" by just attempting their actions.
            # Failure here means the script itself broke, not that the server correctly handled malice.
            if not self.navigate_introduction(): return False # Standard intro
            if not self.navigate_consentform(): return False # Standard consent
            if not self.navigate_terms(): return False # Standard terms
            if not self.navigate_instruction1(): return False # Standard instruction1
            if not self.navigate_instruction2_malicious(): return False # Malicious user info
            if not self.navigate_practice(): return False # Standard practice
            if not self.navigate_game(): return False # Standard game nav
            if not self.complete_all_labels_malicious(): return False # Malicious labeling
            if not self.navigate_summary(): return False # Standard summary nav
            if not self.submit_email_malicious(): return False # Malicious email
            return True
        except Exception as e:
            self.errors_encountered.append(f"Malicious flow unexpected error: {e}")
            return False
        
def execute_user_batch(batch_id, user_list):
    """執行一批用戶測試 - 生產環境版本"""
    batch_size = len(user_list)
    print(f"\n🔥 [批次 {batch_id}] 啟動 {batch_size} 個生產環境用戶，每人52張真實圖片（50正常+2檢查）")
    print(f"🌐 [批次 {batch_id}] 目標服務器: {BASE_URL}")
    print(f"🆔 [批次 {batch_id}] 使用新的 user_ssid 格式和 Unix 時間戳系統")
    
    # 🚀 生產環境：降低並發數
    max_workers = min(batch_size, 3)  # 最多同時3個用戶
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        
        for user_data in user_list:
            user_id, user_type, completion_time = user_data
            user = AdvancedTestUser(user_id, user_type, completion_time, batch_id)
            future = executor.submit(user.execute_comprehensive_test)
            futures.append((future, user))
            
            # 🚀 生產環境：用戶啟動間隔
            time.sleep(random.uniform(2, 5))
        
        success_count = 0
        for future, user in futures:
            try:
                if future.result():
                    success_count += 1
                    print(f"[批次{batch_id}] ✅ 用戶{user.user_id} 成功，檔案: {user.player_name}_unix_unix_fullycomplete.json")
            except Exception as e:
                print(f"[批次{batch_id}|用戶{user.user_id}] 執行異常: {e}")
        
        print(f"🏁 [批次 {batch_id}] 完成：{success_count}/{batch_size} 成功")
        return success_count, batch_size

def get_health_stats():
    """獲取健康狀態統計 - 生產環境版本"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10, verify=True)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def monitor_system_status():
    """監控系統狀態 - 生產環境版本"""
    print("\n📊 生產環境系統監控已啟動...")
    
    while True:
        try:
            stats = get_health_stats()
            if stats:
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"[{current_time}] 📈 生產環境狀態 - 用戶檔案: {stats.get('user_files_count', 0)}, "
                      f"活躍會話: {stats.get('active_sessions_count', 0)}, "
                      f"記憶體: {stats.get('memory_usage_mb', 0)}MB, "
                      f"狀態: {stats.get('status', 'unknown')}")
            else:
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"[{current_time}] ⚠️  無法獲取生產環境健康狀態")
            
            time.sleep(60)  # 生產環境：增加監控間隔
            
        except KeyboardInterrupt:
            break
        except:
            time.sleep(60)

def run_firebase_stress_test():
    """運行生產環境測試"""
    print("🔥 生產環境真實圖片壓力測試 - 適配新的 user_ssid 系統")
    print("="*80)
    print(f"🎯 目標: {TOTAL_USERS} 個用戶，每人52張真實圖片（50正常+2檢查）")
    print(f"🆔 用戶ID格式: user_ssid (例如: user_a1b2c3)")
    print(f"📁 檔案命名: user_ssid_unixstart_unixend_fullycomplete.json")
    print(f"⏰ 時間系統: Unix timestamp (秒和毫秒)")
    print(f"📁 使用 {len(REAL_MEME_FOLDERS)} 個真實meme文件夾")
    print(f"🖼️  總計 {sum(len(images) for images in REAL_MEME_FOLDERS.values())} 張真實圖片可選")
    print(f"✅ 每用戶: 50張正常圖片 + 2張attention check = 52張")
    print(f"🌐 生產服務器: {BASE_URL}")
    print(f"⚠️  生產環境測試 - 請謹慎使用")
    print("="*80)
    
    # 🚀 檢查生產服務器
    try:
        print("🔍 檢查生產服務器連接...")
        response = requests.get(BASE_URL, timeout=15, verify=True)
        print(f"✅ 生產服務器狀態: {response.status_code}")
        
        # 檢查健康狀態
        health = get_health_stats()
        if health:
            print(f"💚 生產環境健康狀態: {health.get('status')}")
            print(f"📊 當前用戶檔案: {health.get('user_files_count', 0)}")
            print(f"💾 記憶體使用: {health.get('memory_usage_mb', 0)}MB")
        else:
            print("⚠️  無法獲取生產環境健康狀態")
        
    except Exception as e:
        print(f"❌ 生產服務器連接失敗: {e}")
        print("請檢查網路連接或服務器狀態")
        return
    
    # 🚀 生產環境警告
    print("\n" + "⚠️ " * 20)
    print("🚨 警告：這是生產環境測試！")
    print("🚨 請確保你有權限在生產環境進行測試")
    print("🚨 建議在低峰時段進行測試")
    print("⚠️ " * 20)
    
    confirm_prod = input("\n確認要在生產環境進行測試嗎？(輸入 'YES' 確認): ").strip()
    if confirm_prod != 'YES':
        print("❌ 生產環境測試已取消")
        return
    
    # 啟動監控
    monitor_thread = threading.Thread(target=monitor_system_status, daemon=True)
    monitor_thread.start()
    
    # 準備用戶
    all_users = []
    for user_id in range(1, TOTAL_USERS + 1):
        user_type = get_user_type()
        completion_time = calculate_user_completion_time(user_type)
        all_users.append((user_id, user_type, completion_time))
    
    # 分批執行
    batch_id = 1
    current_index = 0
    total_success = 0
    start_time = time.time()
    
    while current_index < len(all_users):
        batch_size = random.choice(BATCH_SIZES)
        end_index = min(current_index + batch_size, len(all_users))
        
        user_batch = all_users[current_index:end_index]
        current_index = end_index
        
        success_count, batch_size = execute_user_batch(batch_id, user_batch)
        total_success += success_count
        
        if current_index < len(all_users):
            interval = random.uniform(MIN_BATCH_INTERVAL, MAX_BATCH_INTERVAL)
            print(f"⏳ 等待 {interval:.1f} 秒後啟動下一批次...")
            time.sleep(interval)
        
        batch_id += 1
    
    # 最終統計
    end_time = time.time()
    total_duration = end_time - start_time
    
    print("\n" + "="*80)
    print("🎉 生產環境真實圖片壓力測試完成！- 新 user_ssid 系統")
    print("="*80)
    print(f"⏱️  總測試時間: {total_duration/60:.1f} 分鐘")
    print(f"👥 成功用戶: {total_success}/{TOTAL_USERS}")
    print(f"📊 成功率: {total_success/TOTAL_USERS*100:.1f}%")
    print(f"🖼️  每用戶處理52張真實圖片（50正常+2檢查）")
    print(f"📈 總計處理: {total_success * 52} 張圖片標記")
    print(f"🆔 檔案格式: user_ssid_unixstart_noemail.json → user_ssid_unixstart_unixend_fullycomplete.json")
    print(f"⏰ 時間格式: Unix timestamp (秒和毫秒)")
    print(f"🌐 生產服務器: {BASE_URL}")
    
    # 最終健康檢查
    try:
        final_health = get_health_stats()
        if final_health:
            print(f"\n📊 最終生產環境狀態:")
            print(f"   用戶檔案: {final_health.get('user_files_count', 0)}")
            print(f"   活躍會話: {final_health.get('active_sessions_count', 0)}")
            print(f"   記憶體使用: {final_health.get('memory_usage_mb', 0)}MB")
    except:
        pass

def get_user_behavior_type():
    """根據機率分佈選擇用戶行為類型"""
    rand = random.random()
    cumulative = 0
    
    for behavior_type, config in USER_BEHAVIOR_TYPES.items():
        cumulative += config['probability']
        if rand <= cumulative:
            return behavior_type, config
    
    return 'perfect_user', USER_BEHAVIOR_TYPES['perfect_user']

def execute_extreme_user_batch(batch_id, user_list):
    """執行極限用戶批次測試"""
    batch_size = len(user_list)
    print(f"\n🔥 [批次 {batch_id}] 啟動 {batch_size} 個極限測試用戶")
    
    # 🔥 高並發測試
    max_workers = min(batch_size, 15)  # 最多同時15個用戶
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        
        for user_data in user_list:
            user_id, behavior_type, behavior_config = user_data
            user = AdvancedTestUser(user_id, behavior_type, behavior_config, batch_id)
            future = executor.submit(user.execute_comprehensive_test)
            futures.append((future, user))
            
            # 極快的用戶啟動間隔
            time.sleep(random.uniform(0.1, 1.0))
        
        success_count = 0
        total_errors = 0
        behavior_stats = {}
        
        for future, user in futures:
            try:
                if future.result():
                    success_count += 1
                
                # 統計行為類型
                behavior = user.behavior_type
                if behavior not in behavior_stats:
                    behavior_stats[behavior] = {'success': 0, 'total': 0, 'errors': 0}
                
                behavior_stats[behavior]['total'] += 1
                if user.success:
                    behavior_stats[behavior]['success'] += 1
                behavior_stats[behavior]['errors'] += len(user.errors_encountered)
                total_errors += len(user.errors_encountered)
                
            except Exception as e:
                total_errors += 1
                print(f"[批次{batch_id}] 執行異常: {e}")
        
        # 詳細統計報告
        print(f"🏁 [批次 {batch_id}] 完成：{success_count}/{batch_size} 成功，總錯誤: {total_errors}")
        print(f"📊 [批次 {batch_id}] 行為統計:")
        for behavior, stats in behavior_stats.items():
            success_rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"   {behavior}: {stats['success']}/{stats['total']} ({success_rate:.1f}%) 錯誤:{stats['errors']}")
        
        return success_count, batch_size, total_errors, behavior_stats

def run_ultimate_stress_test():
    """運行終極壓力測試"""
    print("🔥 終極版壓力測試 - 涵蓋所有 Edge Cases 和 Worse Cases")
    print("="*80)
    print(f"🎯 目標: 全面測試各種用戶行為和異常情況")
    print(f"🔧 支援的行為類型: {len(USER_BEHAVIOR_TYPES)} 種")
    for behavior, config in USER_BEHAVIOR_TYPES.items():
        print(f"   - {behavior}: {config['description']} ({config['probability']*100:.1f}%)")
    print("="*80)
    
    # 檢查服務器狀態
    try:
        print("🔍 檢查本地服務器連接...")
        response = requests.get(BASE_URL, timeout=10)
        print(f"✅ 服務器狀態: {response.status_code}")
        
        health = get_health_stats()
        if health:
            print(f"💚 服務器健康狀態: {health.get('status')}")
    except Exception as e:
        print(f"❌ 服務器連接失敗: {e}")
        return
    
    total_users = EXTREME_TEST_CONFIG['total_users']
    print(f"\n📊 極限測試配置:")
    print(f"   總用戶數: {total_users}")
    print(f"   同時用戶數: {EXTREME_TEST_CONFIG['concurrent_users']}")
    print(f"   預估測試時間: {EXTREME_TEST_CONFIG['stress_duration']/60:.0f} 分鐘")
    
    confirm = input(f"\n確定開始極限壓力測試？ (輸入 'YES' 確認): ").strip()
    if confirm != 'YES':
        print("❌ 測試已取消")
        return
    
    # 啟動監控
    monitor_thread = threading.Thread(target=monitor_system_status, daemon=True)
    monitor_thread.start()
    
    # 準備用戶
    all_users = []
    for user_id in range(1, total_users + 1):
        behavior_type, behavior_config = get_user_behavior_type()
        all_users.append((user_id, behavior_type, behavior_config))
    
    # 分批執行
    batch_id = 1
    current_index = 0
    total_success = 0
    total_errors = 0
    overall_behavior_stats = {}
    start_time = time.time()
    
    try:
        while current_index < len(all_users):
            batch_size = random.choice(EXTREME_TEST_CONFIG['batch_sizes'])
            end_index = min(current_index + batch_size, len(all_users))
            
            user_batch = all_users[current_index:end_index]
            current_index = end_index
            
            success_count, batch_size, errors, behavior_stats = execute_extreme_user_batch(batch_id, user_batch)
            total_success += success_count
            total_errors += errors
            
            # 合併行為統計
            for behavior, stats in behavior_stats.items():
                if behavior not in overall_behavior_stats:
                    overall_behavior_stats[behavior] = {'success': 0, 'total': 0, 'errors': 0}
                overall_behavior_stats[behavior]['success'] += stats['success']
                overall_behavior_stats[behavior]['total'] += stats['total']
                overall_behavior_stats[behavior]['errors'] += stats['errors']
            
            if current_index < len(all_users):
                interval = random.uniform(
                    EXTREME_TEST_CONFIG['min_batch_interval'], 
                    EXTREME_TEST_CONFIG['max_batch_interval']
                )
                print(f"⏳ 等待 {interval:.1f} 秒後啟動下一批次...")
                time.sleep(interval)
            
            batch_id += 1
    
    except KeyboardInterrupt:
        print("\n🛑 測試被用戶中斷")
    
    # 最終統計
    end_time = time.time()
    total_duration = end_time - start_time
    
    print("\n" + "="*80)
    print("🎉 終極版壓力測試完成！")
    print("="*80)
    print(f"⏱️  總測試時間: {total_duration/60:.1f} 分鐘")
    print(f"👥 成功用戶: {total_success}/{total_users}")
    print(f"📊 成功率: {total_success/total_users*100:.1f}%")
    print(f"❌ 總錯誤數: {total_errors}")
    print(f"📈 每分鐘處理用戶: {total_users/(total_duration/60):.1f}")
    
    print(f"\n📊 詳細行為統計:")
    for behavior, stats in overall_behavior_stats.items():
        success_rate = stats['success'] / stats['total'] * 100 if stats['total'] > 0 else 0
        config = USER_BEHAVIOR_TYPES.get(behavior, {})
        description = config.get('description', behavior)
        print(f"  {behavior}:")
        print(f"    描述: {description}")
        print(f"    成功率: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        print(f"    錯誤數: {stats['errors']}")
    
    # 最終健康檢查
    try:
        final_health = get_health_stats()
        if final_health:
            print(f"\n📊 最終服務器狀態:")
            print(f"   用戶檔案: {final_health.get('user_files_count', 0)}")
            print(f"   活躍會話: {final_health.get('active_sessions_count', 0)}")
            print(f"   記憶體使用: {final_health.get('memory_usage_mb', 0)}MB")
            print(f"   狀態: {final_health.get('status', 'unknown')}")
    except:
        print("⚠️  無法獲取最終健康狀態")

def main():
    """主函數 - 終極版"""
    print("🔥 終極版壓力測試腳本")
    print("="*60)
    print("測試類型:")
    print("1. 標準壓力測試 (原有功能)")
    print("2. 終極壓力測試 (涵蓋所有Edge Cases)")
    print("3. 自定義測試配置")
    
    choice = input("選擇測試類型 (1/2/3): ").strip()
    
    if choice == "2":
        run_ultimate_stress_test()
    elif choice == "3":
        # 自定義配置
        global EXTREME_TEST_CONFIG
        try:
            users = int(input("總用戶數 (預設200): ") or "200")
            concurrent = int(input("同時用戶數 (預設50): ") or "50")
            EXTREME_TEST_CONFIG['total_users'] = users
            EXTREME_TEST_CONFIG['concurrent_users'] = concurrent
            run_ultimate_stress_test()
        except ValueError:
            print("無效輸入，使用預設值")
            run_ultimate_stress_test()
    else:
        # 保留原有的標準測試
        run_firebase_stress_test()

if __name__ == "__main__":
    main()