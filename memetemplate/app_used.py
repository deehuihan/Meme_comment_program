# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, make_response
import os
from datetime import datetime, timedelta
from uuid import uuid4
import random
import re
from config import config
from waitress import serve
import time
import json
import threading
from typing import Dict, List, Any, Optional
import traceback
import gc
import psutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.join(BASE_DIR, 'data', 'user')
ACTIVE_SESSIONS_FILE = os.path.join(BASE_DIR, 'data', 'active_sessions.json')
JSON_LOCK = threading.Lock()

app = Flask(__name__, template_folder='static/html')
app.jinja_env.globals.update(enumerate=enumerate)
app.permanent_session_lifetime = timedelta(minutes=30)
app.secret_key = config.SECRET_KEY

# 圖片路徑保持不變
IMAGE_FOLDER = os.path.join(BASE_DIR, 'static', 'socialmedia+meme')
IMAGE_FOLDER_practice = os.path.join(BASE_DIR, 'static', 'socialmedia+meme_practice')
SOURCE_FOLDERS_PATH = os.path.join(BASE_DIR, 'static', 'used')

JSON_LOCK = threading.RLock()
SESSIONS_LOCK = threading.RLock()
CACHE_LOCK = threading.RLock()

# 限制緩存大小
_normalize_cache = {}
CACHE_MAX_SIZE = 1000
CACHE_CLEANUP_INTERVAL = 3600  # 1小時清理一次

def cleanup_normalize_cache():
    """定期清理標準化緩存"""
    global _normalize_cache
    with CACHE_LOCK:
        if len(_normalize_cache) > CACHE_MAX_SIZE:
            # 只保留最近使用的一半
            items = list(_normalize_cache.items())
            _normalize_cache = dict(items[-CACHE_MAX_SIZE//2:])
            print(f"[CACHE] 清理緩存，保留 {len(_normalize_cache)} 項")

def cleanup_old_sessions():
    """清理過期的活躍會話記錄"""
    try:
        with SESSIONS_LOCK:
            if not os.path.exists(ACTIVE_SESSIONS_FILE):
                return
                
            with open(ACTIVE_SESSIONS_FILE, 'r', encoding='utf-8') as f:
                active_sessions = json.load(f)
            
            current_time = datetime.now()
            cleaned_sessions = {}
            
            for session_id, session_data in active_sessions.items():
                try:
                    # 解析最後活動時間
                    last_seen = session_data.get('last_seen')
                    if last_seen:
                        last_seen_dt = datetime.strptime(last_seen, '%Y-%m-%d %H:%M:%S.%f')
                        # 保留最近24小時內的會話
                        if current_time - last_seen_dt < timedelta(hours=24):
                            cleaned_sessions[session_id] = session_data
                except Exception as e:
                    print(f"[WARNING] 清理會話時出錯: {e}")
                    # 出錯時保留會話
                    cleaned_sessions[session_id] = session_data
            
            # 如果有清理，保存文件
            if len(cleaned_sessions) < len(active_sessions):
                with open(ACTIVE_SESSIONS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_sessions, f, ensure_ascii=False, indent=2)
                print(f"[SESSION] 清理會話：{len(active_sessions)} → {len(cleaned_sessions)}")
                
    except Exception as e:
        print(f"[ERROR] 清理會話失敗: {e}")

def periodic_cleanup():
    """定期清理任務"""
    print("[CLEANUP] 開始定期清理任務")
    while True:
        try:
            time.sleep(CACHE_CLEANUP_INTERVAL)  # 每小時執行一次
            
            # 清理緩存
            cleanup_normalize_cache()
            
            # 清理過期會話
            cleanup_old_sessions()
            
            # 強制垃圾回收
            gc.collect()
            
            print(f"[CLEANUP] 完成定期清理 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            print(f"[ERROR] 定期清理失敗: {e}")

def ensure_user_data_directory():
    """確保用戶資料目錄存在"""
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)
        print(f"[USER] 創建用戶資料目錄: {USER_DATA_DIR}")

def get_user_data_filename(player_name: str) -> str:
    """獲取用戶資料檔案路徑"""
    return os.path.join(USER_DATA_DIR, f"{player_name}.json")

def init_user_data_file(player_name: str, age: str, gender: str, user_agent: str) -> bool:
    """
    🚀 初始化用戶資料檔案（修復版 - 使用固定user_id格式和Unix時間）
    """
    try:
        with JSON_LOCK:
            ensure_user_data_directory()
            
            # 🚀 使用簡單的 user_ssid 格式作為固定ID
            user_id = player_name  # player_name 就是 user_ssid 格式
            unix_start_time = int(time.time())  # Unix timestamp (秒)
            
            user_file = get_user_data_filename(player_name)
            current_time_readable = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            current_timestamp_ms = int(time.time() * 1000)  # Unix 毫秒
            
            user_data = {
                # === 基本用戶資訊 ===
                'user_id': user_id,  # 🚀 固定不變的 user_ssid
                'file_name': player_name,  # 目前的檔案名（會變化）
                'unix_start_time': unix_start_time,  # Unix 開始時間（秒）
                'unix_start_time_ms': current_timestamp_ms,  # Unix 開始時間（毫秒）
                'unix_end_time': None,  # Unix 結束時間（秒，完成時設定）
                'unix_end_time_ms': None,  # Unix 結束時間（毫秒，完成時設定）
                'age': age,
                'gender': gender,
                'user_agent': user_agent,
                'user_ip': get_user_ip(),
                'status': 'incomplete',
                'email_provided': 'incomplete',
                'attention_passed': None,
                
                # 🚀 保留可讀時間（用於顯示）
                'start_time_readable': current_time_readable,
                'end_time_readable': None,
                
                'total_labels': 0,
                'emotion_summary': {'anger': 0, 'contempt': 0, 'disgust': 0, 'others': 0},
                'email': None,
                'participation': None,

                'total_responses': 0,
                'responses': [],
                
                'session_start_unix': unix_start_time,
                'session_status': 'active',
                'last_updated_unix': unix_start_time,
                'image_order': [],
                'completion_status': {
                    'practice_completed': False,
                    'game_started': False,
                    'game_completed': False,
                    'summary_viewed': False,
                    'email_submitted': False
                },
                
                # 🚀 Unix 時間戳（秒）
                'timestamps_unix': {
                    'registration_completed': unix_start_time,
                    'practice_started': None,
                    'practice_completed': None,
                    'game_started': None,
                    'first_label': None,
                    'last_label': None,
                    'game_completed': None,
                    'summary_viewed': None,
                    'email_submitted': None,
                    'session_end': None,
                    'last_updated': unix_start_time,
                },
                
                # 🚀 Unix 毫秒時間戳（用於精確計算）
                'timestamps_unix_ms': {
                    'registration_completed_ms': current_timestamp_ms,
                    'practice_started_ms': None,
                    'practice_completed_ms': None,
                    'game_started_ms': None,
                    'first_label_ms': None,
                    'last_label_ms': None,
                    'game_completed_ms': None,
                    'summary_viewed_ms': None,
                    'email_submitted_ms': None,
                    'session_end_ms': None,
                    'last_updated_ms': current_timestamp_ms,
                },
                
                # 🚀 時長統計（毫秒）
                'duration_stats_ms': {
                    'total_session_duration_ms': None,
                    'practice_duration_ms': None,
                    'game_duration_ms': None,
                    'labeling_duration_ms': None,
                    'email_submission_duration_ms': None,
                }
            }
            
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
            
            # 🚀 在 active_sessions 中使用固定的 user_id
            update_active_sessions(user_id, 'user_initialized')
            
            print(f"[USER] ✅ 用戶檔案已初始化: ID={user_id}, Unix時間={unix_start_time}")
            return True
            
    except Exception as e:
        print(f"[USER] ❌ 初始化用戶資料檔案失敗: {e}")
        return False


def get_user_ip() -> str:
    """獲取用戶真實 IP 地址"""
    try:
        # 檢查常見的代理頭部
        forwarded_ips = request.headers.getlist("X-Forwarded-For")
        if forwarded_ips:
            return forwarded_ips[0].split(',')[0].strip()
        
        # 檢查其他常見的IP頭部
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip.strip()
            
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
            
        return request.remote_addr or 'Unknown'
        
    except Exception as e:
        print(f"[IP] 獲取IP失敗: {e}")
        return 'Unknown'
    
def update_user_data_file(player_name: str, update_type: str, data: Dict = None) -> bool:
    """
    🚀 簡化版：使用Unix時間戳
    """
    try:
        with JSON_LOCK:
            user_file = get_user_data_filename(player_name)
            
            if not os.path.exists(user_file):
                print(f"[ERROR] 用戶檔案不存在: {player_name}")
                return False
            
            # 讀取現有資料
            with open(user_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            # Unix 時間戳處理
            current_unix = int(time.time())  # Unix 秒
            current_unix_ms = int(time.time() * 1000)  # Unix 毫秒
            current_time_readable = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            user_data['last_updated_unix'] = current_unix
            user_data['timestamps_unix']['last_updated'] = current_unix
            user_data['timestamps_unix_ms']['last_updated_ms'] = current_unix_ms
            
            # 🎯 根據動作更新狀態
            if update_type == 'practice_started':
                user_data['timestamps_unix']['practice_started'] = current_unix
                user_data['timestamps_unix_ms']['practice_started_ms'] = current_unix_ms
                print(f"[USER] {player_name} 開始練習")
                
            elif update_type == 'practice_completed':
                user_data['completion_status']['practice_completed'] = True
                user_data['timestamps_unix']['practice_completed'] = current_unix
                user_data['timestamps_unix_ms']['practice_completed_ms'] = current_unix_ms
                
                # 計算練習耗時
                start_ms = user_data['timestamps_unix_ms'].get('practice_started_ms')
                if start_ms:
                    user_data['duration_stats_ms']['practice_duration_ms'] = current_unix_ms - int(start_ms)
                
                print(f"[USER] {player_name} 完成練習")
                
            elif update_type == 'game_started':
                if not user_data.get('completion_status', {}).get('practice_completed', False):
                    user_data['completion_status']['practice_completed'] = True
                    user_data['timestamps_unix']['practice_completed'] = current_unix
                    user_data['timestamps_unix_ms']['practice_completed_ms'] = current_unix_ms
                    print(f"[AUTO] {player_name} 自動標記練習完成")
                
                user_data['completion_status']['game_started'] = True
                user_data['timestamps_unix']['game_started'] = current_unix
                user_data['timestamps_unix_ms']['game_started_ms'] = current_unix_ms
                
                if data and 'image_order' in data:
                    user_data['image_order'] = data['image_order']
                    
                print(f"[USER] {player_name} 開始遊戲")
                
            elif update_type == 'image_labeled':
                if data:
                    # 記錄第一次和最後一次標記
                    if not user_data['timestamps_unix'].get('first_label'):
                        user_data['timestamps_unix']['first_label'] = current_unix
                        user_data['timestamps_unix_ms']['first_label_ms'] = current_unix_ms
                    
                    user_data['timestamps_unix']['last_label'] = current_unix
                    user_data['timestamps_unix_ms']['last_label_ms'] = current_unix_ms
                    
                    # 添加響應記錄
                    response_item = {
                        'image_path': data.get('image_path'),
                        'label': data.get('label'),
                        'response_time': data.get('response_time'),
                        'timestamp_unix': current_unix,
                        'timestamp_unix_ms': current_unix_ms,
                        'timestamp_readable': current_time_readable,
                        'normalized_name': normalize_image_name(data.get('image_path', '')),
                        'meme_name': extract_meme_name(data.get('image_path', '')),
                        'post_id': extract_post_id(data.get('image_path', '')),
                        'english_label': get_english_label(data.get('label', ''))
                    }
                    user_data['responses'].append(response_item)
                    user_data['total_responses'] = len(user_data['responses'])
                    user_data['total_labels'] = len(user_data['responses'])

                    response_time_str = data.get('response_time', '')
                    response_time_ms = parse_response_time_to_ms(response_time_str)
                    response_item['response_time_ms'] = response_time_ms
                    
                    # 更新情緒統計
                    english_label = get_english_label(data.get('label', ''))
                    if english_label in user_data['emotion_summary']:
                        user_data['emotion_summary'][english_label] += 1
                    
            elif update_type == 'game_completed':
                user_data['completion_status']['game_completed'] = True
                user_data['status'] = 'complete'
                user_data['timestamps_unix']['game_completed'] = current_unix
                user_data['timestamps_unix_ms']['game_completed_ms'] = current_unix_ms
                
                # 重新計算統計
                user_data['total_labels'] = len(user_data.get('responses', []))
                user_data['total_responses'] = len(user_data.get('responses', []))
                
                # 重新計算情緒統計
                emotion_counts = {'anger': 0, 'contempt': 0, 'disgust': 0, 'others': 0}
                for response in user_data.get('responses', []):
                    english_label = response.get('english_label', 'others')
                    if english_label in emotion_counts:
                        emotion_counts[english_label] += 1
                user_data['emotion_summary'] = emotion_counts
                
                # 計算遊戲耗時
                game_start_ms = user_data['timestamps_unix_ms'].get('game_started_ms')
                if game_start_ms:
                    user_data['duration_stats_ms']['game_duration_ms'] = current_unix_ms - int(game_start_ms)
                
                # 計算標記耗時
                first_label_ms = user_data['timestamps_unix_ms'].get('first_label_ms')
                last_label_ms = user_data['timestamps_unix_ms'].get('last_label_ms')
                if first_label_ms and last_label_ms:
                    user_data['duration_stats_ms']['labeling_duration_ms'] = int(last_label_ms) - int(first_label_ms)
                
                if data:
                    user_data['attention_passed'] = data.get('attention_passed')
                    
                print(f"[USER] {player_name} 完成遊戲")
                
            elif update_type == 'summary_viewed':
                user_data['completion_status']['summary_viewed'] = True
                user_data['timestamps_unix']['summary_viewed'] = current_unix
                user_data['timestamps_unix_ms']['summary_viewed_ms'] = current_unix_ms
                print(f"[USER] {player_name} 查看摘要")
                
            elif update_type == 'email_submitted':
                user_data['completion_status']['email_submitted'] = True
                user_data['email_provided'] = 'complete'
                user_data['session_status'] = 'completed'
                user_data['timestamps_unix']['email_submitted'] = current_unix
                user_data['timestamps_unix']['session_end'] = current_unix
                user_data['timestamps_unix_ms']['email_submitted_ms'] = current_unix_ms
                user_data['timestamps_unix_ms']['session_end_ms'] = current_unix_ms
                
                # 🚀 設置結束時間
                user_data['unix_end_time'] = current_unix
                user_data['unix_end_time_ms'] = current_unix_ms
                user_data['end_time_readable'] = current_time_readable
                
                # 計算總耗時
                start_ms = user_data['timestamps_unix_ms'].get('registration_completed_ms')
                if start_ms:
                    user_data['duration_stats_ms']['total_session_duration_ms'] = current_unix_ms - int(start_ms)
                
                # 計算 email 提交耗時
                summary_viewed_ms = user_data['timestamps_unix_ms'].get('summary_viewed_ms')
                if summary_viewed_ms:
                    user_data['duration_stats_ms']['email_submission_duration_ms'] = current_unix_ms - int(summary_viewed_ms)
                
                if data:
                    user_data['email'] = data.get('email')
                    user_data['participation'] = data.get('participation')
                    
                print(f"[USER] {player_name} 提交 email，Unix結束時間: {current_unix}")
            
            # 保存檔案
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
            
            # 更新活躍會話
            update_active_sessions(player_name, update_type)
            
            return True
            
    except Exception as e:
        print(f"[USER] ❌ 更新失敗: {e}")
        return False

def parse_response_time_to_ms(response_time_str: str) -> int:
    """將響應時間字符串轉換為毫秒"""
    try:
        # 格式: "00:00:02.304"
        parts = response_time_str.split(':')
        if len(parts) >= 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_parts = parts[2].split('.')
            seconds = int(seconds_parts[0])
            milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            
            total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds
            return total_ms
        return 0
    except Exception as e:
        print(f"[ERROR] 解析響應時間失敗: {response_time_str}, {e}")
        return 0

def format_timestamp_from_ms(timestamp_ms: int) -> str:
    """將毫秒時間戳轉換為可讀格式"""
    try:
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # 2025-06-09 21:42:00.166
    except Exception as e:
        print(f"[ERROR] 格式化時間戳失敗: {timestamp_ms}, {e}")
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


def load_all_users_for_comparison(exclude_user: str = None) -> Dict[str, List[str]]:
    """
    🚀 從 user/ 資料夾載入所有用戶的比對資料
    """
    try:
        comparison_data = {}
        
        if not os.path.exists(USER_DATA_DIR):
            return comparison_data
        
        user_files = [f for f in os.listdir(USER_DATA_DIR) if f.endswith('.json')]
        processed_users = 0
        
        for user_file in user_files:
            user_name = user_file.replace('.json', '')
            
            if exclude_user and user_name == exclude_user:
                continue
                
            try:
                user_path = os.path.join(USER_DATA_DIR, user_file)
                with open(user_path, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                
                # 只處理已完成遊戲的用戶
                if not user_data.get('completion_status', {}).get('game_completed', False):
                    continue
                
                # 處理 responses 資料（users_cache 格式）
                for response in user_data.get('responses', []):
                    normalized_name = response.get('normalized_name')
                    label = response.get('label')
                    
                    if normalized_name and label:
                        if normalized_name not in comparison_data:
                            comparison_data[normalized_name] = []
                        comparison_data[normalized_name].append(label)
                
                processed_users += 1
                
            except Exception as e:
                print(f"[USER] ⚠️  讀取用戶檔案失敗 {user_file}: {e}")
                continue
        
        print(f"[USER] 比對資料載入完成，基於 {processed_users} 個用戶，涵蓋 {len(comparison_data)} 張圖片")
        return comparison_data
        
    except Exception as e:
        print(f"[USER] ❌ 載入比對資料失敗: {e}")
        return {}

def extract_meme_name(image_path: str) -> str:
    """從圖片路徑提取 meme 名稱"""
    if '/' in image_path:
        return image_path.split('/', 1)[0]
    return image_path.rsplit('.', 1)[0]

def extract_post_id(image_path: str) -> Optional[int]:
    """從圖片路徑提取 post ID"""
    import re
    match = re.search(r'_(\d+)\.', image_path)
    return int(match.group(1)) if match else None

def get_english_label(chinese_label: str) -> str:
    """轉換中文標籤為英文"""
    mapping = {'憤怒': 'anger', '輕蔑': 'contempt', '厭惡': 'disgust', '其他': 'others'}
    return mapping.get(chinese_label, 'others')

def update_active_sessions(user_identifier: str, action: str) -> bool:
    """改進的活躍會話更新，減少檔案鎖定時間"""
    try:
        now = datetime.now()
        current_time = now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        current_timestamp_ms = int(now.timestamp() * 1000)
        
        # 快速準備數據，減少檔案操作時間
        session_key = user_identifier
        
        # 提取 user_id 邏輯保持不變...
        if '_' in user_identifier and ('noemail' in user_identifier or 'fullycomplete' in user_identifier):
            try:
                parts = user_identifier.split('_')
                if len(parts) >= 2 and parts[0] == 'user':
                    session_key = f"{parts[0]}_{parts[1]}"
            except Exception:
                pass
        
        # 最小化鎖定時間
        with SESSIONS_LOCK:
            active_sessions = {}
            if os.path.exists(ACTIVE_SESSIONS_FILE):
                try:
                    with open(ACTIVE_SESSIONS_FILE, 'r', encoding='utf-8') as f:
                        active_sessions = json.load(f)
                except Exception as e:
                    print(f"[WARNING] 讀取會話失敗: {e}")
            
            # 快速更新數據
            if session_key not in active_sessions:
                active_sessions[session_key] = {
                    'first_seen': current_time,
                    'first_seen_ms': current_timestamp_ms,
                    'actions': []
                }
            
            # 處理動作記錄
            should_record = True
            if action == 'image_labeled':
                existing_actions = [a.get('action') for a in active_sessions[session_key]['actions']]
                if 'first_image_labeled' not in existing_actions:
                    action = 'first_image_labeled'
                else:
                    should_record = False
            
            if should_record:
                active_sessions[session_key]['last_seen'] = current_time
                active_sessions[session_key]['last_seen_ms'] = current_timestamp_ms
                
                action_record = {
                    'action': action,
                    'timestamp': current_time,
                    'timestamp_ms': current_timestamp_ms,
                    'sequence_number': len(active_sessions[session_key]['actions']) + 1
                }
                
                active_sessions[session_key]['actions'].append(action_record)
                
                # 限制動作記錄數量
                if len(active_sessions[session_key]['actions']) > 50:
                    active_sessions[session_key]['actions'] = active_sessions[session_key]['actions'][-25:]
            
            # 原子性寫入
            temp_file = ACTIVE_SESSIONS_FILE + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(active_sessions, f, ensure_ascii=False, indent=2)
            
            # Windows 兼容的原子性重命名
            if os.name == 'nt':  # Windows
                if os.path.exists(ACTIVE_SESSIONS_FILE):
                    backup_file = ACTIVE_SESSIONS_FILE + '.bak'
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
                    os.rename(ACTIVE_SESSIONS_FILE, backup_file)
                os.rename(temp_file, ACTIVE_SESSIONS_FILE)
                if os.path.exists(backup_file):
                    os.remove(backup_file)
            else:  # Linux/Mac
                os.rename(temp_file, ACTIVE_SESSIONS_FILE)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 更新活躍會話失敗: {e}")
        return False

def format_duration_ms(duration_ms: int) -> str:
    """將毫秒轉換為可讀的時間格式"""
    try:
        if duration_ms < 0:
            return "00:00.000"
            
        total_seconds = duration_ms // 1000
        milliseconds = duration_ms % 1000
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        else:
            return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    except Exception as e:
        print(f"[ERROR] 格式化時間失敗: {e}")
        return "00:00.000"
    
def get_images(folder):
    try:
        images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        images.sort()
        return images
    except Exception as e:
        print(f"Error retrieving images: {e}")
        return []

def select_random_images_from_folders(player_name=None):
    selected_images = []
    used_indices = set()
    
    try:
        subfolders = [f for f in os.listdir(SOURCE_FOLDERS_PATH) 
                    if os.path.isdir(os.path.join(SOURCE_FOLDERS_PATH, f))]
        
        folder_images_count = {}
        max_images = 0
        
        for folder in subfolders:
            folder_path = os.path.join(SOURCE_FOLDERS_PATH, folder)
            images = [f for f in os.listdir(folder_path) 
                     if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            folder_images_count[folder] = len(images)
            max_images = max(max_images, len(images))
        
        for folder in subfolders:
            folder_path = os.path.join(SOURCE_FOLDERS_PATH, folder)
            images = [f for f in os.listdir(folder_path) 
                     if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            if images:
                images.sort()
                available_indices = [i for i in range(len(images)) if i not in used_indices]
                
                if not available_indices:
                    selected_index = random.randrange(len(images))
                else:
                    selected_index = random.choice(available_indices)
                
                used_indices.add(selected_index)
                
                selected_image = images[selected_index]
                selected_images.append(f"{folder}/{selected_image}")
        
        return selected_images
    except Exception as e:
        print(f"Error selecting random images: {e}")
        import traceback
        traceback.print_exc()
        return []

def select_random_images_with_attention_checks(player_name=None):
    regular_images = select_random_images_from_folders(player_name)
    
    attention_check_folder = os.path.join(BASE_DIR, 'static', 'attention_check')
    attention_check_images = []
    if os.path.exists(attention_check_folder):
        attention_check_images = [f for f in os.listdir(attention_check_folder) 
                                 if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    else:
        return regular_images
    
    if not attention_check_images:
        return regular_images
    
    total_images = len(regular_images)
    max_attention_checks = 2
    
    if total_images < max_attention_checks:
        return regular_images
    
    selected_check_images = random.sample(attention_check_images, max_attention_checks)
        
    insert_positions = []
    current_position = 0
    for _ in range(max_attention_checks):
        random_offset = random.randint(20, 25)
        current_position += random_offset
        if current_position >= total_images:
            current_position = total_images - 1
        insert_positions.append(current_position)
        current_position += 1
        
    final_image_list = []
    check_index = 0
    
    for i, img in enumerate(regular_images):
        final_image_list.append(img)
        
        if check_index < len(insert_positions) and i + 1 == insert_positions[check_index]:
            attention_image = selected_check_images[check_index]
            
            final_image_list.append(f"attention_check/{attention_image}")            
            check_index += 1
    
    print(f"最終圖片列表長度: {len(final_image_list)}")
    
    return final_image_list

def check_attention_passed(player_data):
    try:
        attention_data = None
        
        if 'attention' in player_data:
            attention_data = player_data['attention']
        elif 'images' in player_data:
            attention_data = {}
            for img_name, img_data in player_data['images'].items():
                if 'attention_check/' in img_name:
                    filename = img_name.split('/')[-1]
                    attention_data[filename] = img_data
        else:
            attention_data = {}
            for key, value in player_data.items():
                if isinstance(value, dict) and 'image_path' in value:
                    if 'attention_check/' in value['image_path']:
                        filename = value['image_path'].split('/')[-1]
                        attention_data[filename] = value
        
        if not attention_data:
            print(f"[DEBUG] 用戶沒有注意力檢查數據")
            return True 
        
        if not isinstance(attention_data, dict):
            return True
        
        total_checks = 0
        passed_checks = 0
        
        print(f"[DEBUG] 開始檢查注意力測試，共有 {len(attention_data)} 個檢查項目")
        
        for check_key, check_data in attention_data.items():
            if isinstance(check_data, dict) and 'label' in check_data:
                total_checks += 1
                user_label = check_data['label']
                
                expected_emotion = None
                check_key_lower = check_key.lower()
                
                if 'anger' in check_key_lower:
                    expected_emotion = '憤怒'
                elif 'disgust' in check_key_lower:
                    expected_emotion = '厭惡'
                elif 'contempt' in check_key_lower:
                    expected_emotion = '輕蔑'
                elif 'others' in check_key_lower or 'other' in check_key_lower:
                    expected_emotion = '其他'
                
                if expected_emotion:
                    attention_passed = (user_label == expected_emotion)
                    if attention_passed:
                        passed_checks += 1
                    
                    print(f"[DEBUG] 注意力檢查 {check_key}: 期望={expected_emotion}, 實際={user_label}, 結果={'通過' if attention_passed else '失敗'}")
                else:
                    print(f"[WARNING] 無法從檔名 {check_key} 判斷期望情緒，跳過此檢查")
        
        print(f"[DEBUG] 注意力檢查總結果: {passed_checks}/{total_checks} 通過")
        
        return total_checks > 0 and passed_checks == total_checks
        
    except Exception as e:
        print(f"[ERROR] 檢查注意力測試時出錯: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_current_user_matches_with_order(player_data, other_players_data, image_order):
    """
    修復版：處理比對結果並按照用戶實際看圖順序排列
    """
    matches = []
    user_choices = []
    
    # 🚀 修復順序映射：只映射非注意力檢查的圖片，避免重複
    order_mapping = {}
    regular_order = []
    
    if image_order:
        regular_index = 0  # 用於追蹤實際的正常圖片順序
        for img in image_order:
            if 'attention_check/' not in img:
                # 只為正常圖片建立映射
                order_mapping[img] = regular_index
                regular_order.append(img)
                
                # 🚀 同時為不含路徑的檔名建立映射
                if '/' in img:
                    filename_only = img.split('/')[-1]
                    # 只有當檔名不重複時才映射
                    if filename_only not in order_mapping:
                        order_mapping[filename_only] = regular_index
                
                regular_index += 1
    
    
    # 處理用戶的圖片響應
    for image_name, image_data in player_data.get('images', {}).items():
        if 'attention_check/' in image_name:
            continue
            
        if 'label' in image_data:
            player_choice = image_data['label']
            image_path = image_data.get('image_path', image_name)
            user_choices.append(player_choice)
            
            normalized_name = normalize_image_name(image_path)
            other_choices = other_players_data.get(normalized_name, [])
            total_others = len(other_choices)
            
            if total_others > 0:
                percentages = {
                    '輕蔑': sum(1 for choice in other_choices if choice == '輕蔑') / total_others * 100,
                    '憤怒': sum(1 for choice in other_choices if choice == '憤怒') / total_others * 100,
                    '厭惡': sum(1 for choice in other_choices if choice == '厭惡') / total_others * 100,
                    '其他': sum(1 for choice in other_choices if choice == '其他') / total_others * 100
                }
            else:
                percentages = {
                    '輕蔑': 100 if player_choice == '輕蔑' else 0,
                    '憤怒': 100 if player_choice == '憤怒' else 0,
                    '厭惡': 100 if player_choice == '厭惡' else 0,
                    '其他': 100 if player_choice == '其他' else 0
                }

            # 🚀 更精確的順序查找
            display_order = 999999  # 默認放在最後
            
            # 優先使用完整路徑匹配
            if image_path in order_mapping:
                display_order = order_mapping[image_path]
            elif image_name in order_mapping:
                display_order = order_mapping[image_name]
            elif '/' in image_path:
                # 嘗試檔名匹配
                filename_only = image_path.split('/')[-1]
                if filename_only in order_mapping:
                    display_order = order_mapping[filename_only]
                        
            matches.append({
                'image': image_path,
                'image_url': f"/summary/images/{image_path}",
                'choice': player_choice,
                'percentages': percentages,
                'normalized_name': normalized_name,
                'comparison_count': total_others,
                'display_order': display_order
            })

    # 🚀 按照實際看圖順序排序
    sorted_matches = sorted(matches, key=lambda x: x['display_order'])
    
    return sorted_matches, user_choices

def get_personality_type(user_percentages, matches=None):
    """
    計算用戶的人格類型 (從app.py複製過來)
    """
    result = get_response_pattern(user_percentages, matches)
    result["animal"] = ""
    return result

def get_response_pattern(emotion_percentages, matches):
    """
    優化版：減少調試輸出
    """
    if not matches or len(matches) == 0:
        return {
            "type": "no_data",
            "description": "沒有足夠的數據進行分析", 
            "animal": ""
        }
    
    total_agreement = 0
    total_images = len(matches)
    
    for match in matches:
        user_choice = match['choice']
        user_agreement_percentage = match['percentages'].get(user_choice, 0)
        total_agreement += user_agreement_percentage
    
    if total_images > 0:
        agreement_percentage = total_agreement / total_images
    else:
        agreement_percentage = 0
        
    if agreement_percentage >= 50:
        return {
            "type": "high_agreement",  
            "description": "大多數人與您有相同的選擇", 
            "animal": ""
        }
    elif agreement_percentage >= 20:
        return {
            "type": "medium_agreement", 
            "description": "您的部分選擇與大多數人相同，但也展現了自己的觀點", 
            "animal": ""
        }
    else:
        return {
            "type": "low_agreement",
            "description": "您的選擇與大多數人不同，為結果帶來了更多的多樣性", 
            "animal": ""
        }     
        
def calculate_uniqueness_score(matches):
    """
    優化版：減少調試輸出
    """
    if not matches:
        return 0
    uniqueness_sum = sum(1 - m['percentages'][m['choice']]/100 for m in matches)
    uniqueness_score = round(uniqueness_sum / len(matches) * 100, 2)
        
    return uniqueness_score

def normalize_image_name(image_path):
    """改進的線程安全緩存"""
    with CACHE_LOCK:
        if image_path in _normalize_cache:
            return _normalize_cache[image_path]
        
        try:
            if '/' in image_path:
                folder, filename = image_path.split('/', 1)
                base_name = re.sub(r'_\d+(?:\.png|_png)$', '', filename)
                normalized = f"{folder}/{base_name}"
            else:
                normalized = re.sub(r'_\d+(?:\.png|_png)$', '', image_path)
            
            # 檢查緩存大小並清理
            if len(_normalize_cache) >= CACHE_MAX_SIZE:
                cleanup_normalize_cache()
            
            _normalize_cache[image_path] = normalized
            return normalized
            
        except Exception as e:
            print(f"[ERROR] Failed to normalize {image_path}: {e}")
            return image_path

def generate_new_username():
    """
    🚀 生成簡單的用戶ID格式：user_ssid
    """
    import secrets
    # 生成6位隨機字符串作為session ID
    ssid = secrets.token_hex(3)  # 產生6個字符的hex字串
    user_id = f"user_{ssid}"
    
    print(f"[USER] 生成用戶ID: {user_id}")
    return user_id


def update_username_by_completion_status(old_filename: str, completion_type: str) -> str:
    """
    🚀 根據完成狀態更新檔案名稱（使用Unix時間）
    格式：user_ssid_unixstarttime_unixendtime_fullycomplete
    """
    try:
        print(f"[DEBUG] 更新檔案名: {old_filename}, 類型: {completion_type}")
        
        # 檢查是否是從 noemail 轉換為 fullycomplete
        if completion_type == 'email_submitted' and 'noemail' in old_filename:
            unix_end_time = int(time.time())
            new_filename = old_filename.replace('_noemail', f'_{unix_end_time}_fullycomplete')
            
            old_file = get_user_data_filename(old_filename)
            new_file = get_user_data_filename(new_filename)
            
            if os.path.exists(old_file):
                with JSON_LOCK:
                    with open(old_file, 'r', encoding='utf-8') as f:
                        user_data = json.load(f)
                    
                    # 只更新檔案名稱和結束時間，user_id 保持不變
                    user_data['file_name'] = new_filename
                    user_data['unix_end_time'] = unix_end_time
                    user_data['unix_end_time_ms'] = int(time.time() * 1000)
                    user_data['end_time_readable'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    user_data['completion_status_in_filename'] = 'email_submitted'
                    
                    with open(new_file, 'w', encoding='utf-8') as f:
                        json.dump(user_data, f, ensure_ascii=False, indent=2)
                    
                    os.remove(old_file)
                    
                    print(f"[USER] ✅ 檔案重命名: {old_filename} → {new_filename}, ID保持: {user_data['user_id']}")
                    return new_filename
            else:
                print(f"[ERROR] 原始檔案不存在: {old_file}")
                return old_filename
        
        # 處理原始檔案名的轉換邏輯
        if 'noemail' in old_filename or 'fullycomplete' in old_filename:
            print(f"[INFO] 檔案名已包含完成狀態: {old_filename}")
            return old_filename
        
        # 讀取用戶數據以獲取 unix_start_time
        old_file = get_user_data_filename(old_filename)
        if not os.path.exists(old_file):
            print(f"[ERROR] 檔案不存在: {old_file}")
            return old_filename
            
        with open(old_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        user_id = user_data.get('user_id', old_filename)  # user_ssid
        unix_start_time = user_data.get('unix_start_time', int(time.time()))
        unix_end_time = int(time.time())
        
        # 根據完成類型生成新檔案名
        if completion_type == 'summary_viewed':
            # 到達摘要但未提供email：user_ssid_starttime_noemail
            new_filename = f"{user_id}_{unix_start_time}_noemail"
        elif completion_type == 'email_submitted':
            # 完全完成：user_ssid_starttime_endtime_fullycomplete
            new_filename = f"{user_id}_{unix_start_time}_{unix_end_time}_fullycomplete"
        else:
            print(f"[ERROR] 未知的完成類型: {completion_type}")
            return old_filename
        
        # 檢查新檔案名是否重複
        new_file = get_user_data_filename(new_filename)
        attempt = 0
        while os.path.exists(new_file) and attempt < 100:
            attempt += 1
            if completion_type == 'summary_viewed':
                new_filename = f"{user_id}_{unix_start_time}_noemail_{attempt:02d}"
            else:
                new_filename = f"{user_id}_{unix_start_time}_{unix_end_time}_fullycomplete_{attempt:02d}"
            new_file = get_user_data_filename(new_filename)
        
        # 重新命名檔案
        if os.path.exists(old_file):
            with JSON_LOCK:
                # 更新數據中的檔案名和結束時間
                user_data['file_name'] = new_filename
                user_data['unix_end_time'] = unix_end_time if completion_type == 'email_submitted' else None
                user_data['unix_end_time_ms'] = int(time.time() * 1000) if completion_type == 'email_submitted' else None
                user_data['filename_updated_unix'] = int(time.time())
                user_data['original_filename'] = old_filename
                user_data['completion_status_in_filename'] = completion_type
                
                if completion_type == 'email_submitted':
                    user_data['end_time_readable'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                
                with open(new_file, 'w', encoding='utf-8') as f:
                   json.dump(user_data, f, ensure_ascii=False, indent=2)
                
                os.remove(old_file)
                
                print(f"[USER] ✅ 檔案重命名: {old_filename} → {new_filename}, ID保持: {user_data['user_id']}")
                return new_filename
        else:
            print(f"[ERROR] 原始檔案不存在: {old_file}")
            return old_filename
            
    except Exception as e:
        print(f"[ERROR] 重命名檔案失敗: {e}")
        import traceback
        traceback.print_exc()
        return old_filename  
def get_username_completion_info(username: str) -> dict:
    """
    🚀 從用戶名解析完成狀態資訊
    """
    try:
        if 'fully_completed' in username:
            status = 'fully_completed'
            description = '完全完成'
        elif 'partially_completed' in username:
            status = 'partially_completed'
            description = '部分完成（未提供email）'
        else:
            status = 'abandoned'
            description = '未完成或中途離開'
        
        # 解析時間資訊
        parts = username.split('_')
        if len(parts) >= 3:
            date_part = parts[1]  # YYYYMMDD
            start_time = parts[2]  # HHMMSSmmm
            end_time = parts[3] if len(parts) >= 4 and not parts[3].endswith('completed') else None
            
            return {
                'status': status,
                'description': description,
                'date': date_part,
                'start_time': start_time,
                'end_time': end_time,
                'has_end_time': end_time is not None
            }
    except Exception as e:
        print(f"[ERROR] 解析用戶名失敗: {username}, {e}")
    
    return {
        'status': 'unknown',
        'description': '無法解析',
        'date': None,
        'start_time': None,
        'end_time': None,
        'has_end_time': False
    }
def get_user_statistics_by_completion():
    """
    按完成狀態統計用戶
    """
    try:
        stats = {
            'fully_completed': 0,      # _fully_completed
            'partially_completed': 0,  # _partially_completed  
            'abandoned': 0,            # 只有起始時間
            'total_users': 0,
            'details': {
                'fully_completed': [],
                'partially_completed': [],
                'abandoned': []
            }
        }
        
        if not os.path.exists(USER_DATA_DIR):
            return stats
        
        user_files = [f for f in os.listdir(USER_DATA_DIR) if f.endswith('.json')]
        
        for user_file in user_files:
            username = user_file.replace('.json', '')
            completion_info = get_username_completion_info(username)
            
            stats['total_users'] += 1
            
            if completion_info['status'] == 'fully_completed':
                stats['fully_completed'] += 1
                stats['details']['fully_completed'].append(username)
            elif completion_info['status'] == 'partially_completed':
                stats['partially_completed'] += 1
                stats['details']['partially_completed'].append(username)
            else:  # abandoned
                stats['abandoned'] += 1
                stats['details']['abandoned'].append(username)
        
        # 計算完成率
        if stats['total_users'] > 0:
            stats['full_completion_rate'] = round(stats['fully_completed'] / stats['total_users'] * 100, 2)
            stats['partial_completion_rate'] = round(stats['partially_completed'] / stats['total_users'] * 100, 2)
            stats['abandonment_rate'] = round(stats['abandoned'] / stats['total_users'] * 100, 2)
        
        return stats
        
    except Exception as e:
        print(f"[ERROR] 統計用戶完成狀態失敗: {e}")
        return {'error': str(e)}   

    
def get_or_create_session_user_id():
    """
    🚀 生成簡單的 user_ssid 格式
    """
    if 'temp_user_id' not in session:
        import secrets
        ssid = secrets.token_hex(3)  # 生成6位hex字串
        temp_user_id = f"user_{ssid}"
        session['temp_user_id'] = temp_user_id
        print(f"[SESSION] 生成用戶ID: {temp_user_id}")
    
    return session['temp_user_id']

def update_session_tracking(action: str):
    """
    統一的會話追蹤函數 - 始終使用真實用戶名格式
    """
    # 🚀 優先使用已註冊的用戶名，否則使用預生成的用戶ID
    user_id = session.get('player_name') or get_or_create_session_user_id()
    update_active_sessions(user_id, action)
    print(f"[SESSION] 追蹤 {user_id}: {action}")

def finalize_user_registration(final_player_name: str):
    """
    用戶註冊完成時，如果用戶名不同，需要合併會話記錄
    """
    temp_id = session.get('temp_user_id')
    
    if temp_id and temp_id != final_player_name:
        # 合併 active_sessions 記錄
        try:
            if os.path.exists(ACTIVE_SESSIONS_FILE):
                with open(ACTIVE_SESSIONS_FILE, 'r', encoding='utf-8') as f:
                    active_sessions = json.load(f)
                
                if temp_id in active_sessions:
                    temp_data = active_sessions[temp_id]
                    
                    # 如果最終用戶名已存在，合併動作記錄
                    if final_player_name in active_sessions:
                        # 將臨時記錄的動作添加到正式記錄前面
                        temp_actions = temp_data.get('actions', [])
                        final_actions = active_sessions[final_player_name].get('actions', [])
                        
                        # 更新序列號
                        for i, action in enumerate(final_actions):
                            action['sequence_number'] = len(temp_actions) + i + 1
                        
                        # 合併動作列表
                        active_sessions[final_player_name]['actions'] = temp_actions + final_actions
                        
                        # 保持最早的首次時間
                        if temp_data.get('first_seen_ms', 0) < active_sessions[final_player_name].get('first_seen_ms', float('inf')):
                            active_sessions[final_player_name]['first_seen'] = temp_data['first_seen']
                            active_sessions[final_player_name]['first_seen_time'] = temp_data['first_seen_time']
                            active_sessions[final_player_name]['first_seen_ms'] = temp_data['first_seen_ms']
                    else:
                        # 直接重命名
                        active_sessions[final_player_name] = temp_data
                    
                    # 刪除臨時記錄
                    del active_sessions[temp_id]
                    
                    # 保存更新
                    with open(ACTIVE_SESSIONS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(active_sessions, f, ensure_ascii=False, indent=2)
                    
                    print(f"[SESSION] ✅ 合併會話記錄: {temp_id} → {final_player_name}")
                
        except Exception as e:
            print(f"[SESSION] ❌ 合併會話記錄失敗: {e}")
        
        # 清理 session 中的臨時ID
        if 'temp_user_id' in session:
            del session['temp_user_id']

def check_task_completion_cookie():
    """
    Check if user has already completed the task based on cookies
    """
    return request.cookies.get('game_completed') == 'true'

def create_completion_cookie(response):
    """
    Add completion cookie to response
    """
    response.set_cookie(
        'game_completed', 
        'true', 
        max_age=60*60*24*365,  
        httponly=True,  
        secure=False,   
        samesite='Lax' 
    )
    return response

@app.route('/', methods=['GET', 'POST'])
def introduction():
    session.clear()
    session['has_viewed_introduction'] = True
    
    # 🚀 使用統一的真實用戶名格式追蹤
    update_session_tracking('visited_introduction')
    
    if request.method == 'POST':
        return redirect(url_for('consentform'))
    return render_template('introduction.html')

@app.route('/consentform', methods=['GET', 'POST'])
def consentform():
    if check_task_completion_cookie():
        return render_template('error.html')
        
    if 'has_viewed_introduction' not in session:
        return redirect(url_for('introduction'))
    
    # 🚀 使用統一追蹤
    update_session_tracking('visited_consentform')
    
    session['has_viewed_consentform'] = True
    if request.method == 'POST':
        return redirect(url_for('terms'))
    return render_template('consentform.html')

@app.route('/terms', methods=['GET', 'POST'])
def terms():
    if check_task_completion_cookie():
        return render_template('error.html')
    
    if 'has_viewed_consentform' not in session:
        return redirect(url_for('consentform'))
    
    # 🚀 使用統一追蹤
    update_session_tracking('visited_terms')
    
    session['has_viewed_terms'] = True
    
    if request.method == 'POST' and 'accept_terms' in request.form:
        return redirect(url_for('instruction_1'))
    return render_template('terms.html')

@app.route('/instruction1', methods=['GET', 'POST'])
def instruction_1():
    if check_task_completion_cookie():
        return render_template('error.html')
    
    if 'has_viewed_terms' not in session:
        return redirect(url_for('terms'))
    
    # 🚀 使用統一追蹤
    update_session_tracking('visited_instruction1')
    
    session['has_viewed_instruction_1'] = True
    return render_template('instruction_1.html')


@app.route('/instruction2', methods=['GET', 'POST'])
def instruction_2():
    if check_task_completion_cookie():
        return render_template('error.html')
    
    if 'has_viewed_instruction_1' not in session:
        return redirect(url_for('instruction_1'))
    
    update_session_tracking('visited_instruction2')
    session['has_viewed_instruction_2'] = True

    if request.method == 'POST':
        # 🚀 使用預生成的 user_ssid 格式
        player_name = get_or_create_session_user_id()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        custom_gender = request.form.get('custom_gender', '').strip()

        if gender == 'custom' and custom_gender:
            gender = custom_gender

        if not age or not gender:
            return render_template('instruction_2.html', error="Please enter age and gender information")

        session_id = str(uuid4())
        session['session_id'] = session_id
        session['player_name'] = player_name
        session['age'] = age
        session['gender'] = gender
        session.permanent = True

        finalize_user_registration(player_name)

        user_agent = request.headers.get('User-Agent', 'Unknown')
        json_success = init_user_data_file(player_name, age, gender, user_agent)
        
        if json_success:
            print(f"[JSON] ✅ 用戶 {player_name} 完整會話已初始化")
        else:
            print(f"[JSON] ❌ 用戶 {player_name} 會話初始化失敗")

        selected_images = select_random_images_with_attention_checks(player_name)
        session['image_order'] = selected_images

        return redirect(url_for('practice'))

    # 🚀 顯示預生成的 user_ssid
    default_player_name = get_or_create_session_user_id()
    return render_template('instruction_2.html', player_name=default_player_name)


@app.route('/practice')
def practice():
    if check_task_completion_cookie():
        return render_template('error.html')
    
    if 'has_viewed_instruction_2' not in session:
        return redirect(url_for('instruction_2'))
    
    if 'player_name' not in session:
        return redirect(url_for('instruction_2'))
    
    session['has_viewed_practice'] = True
    practice_images = get_images(IMAGE_FOLDER_practice)
    
    # 🚀 追蹤練習頁面訪問
    if session.get('player_name'):
        update_user_data_file(session['player_name'], 'practice_started')
        update_session_tracking('practice_page_visited')  # 🚀 使用統一追蹤
        
    return render_template('practice.html', player_name=session['player_name'], images=practice_images)


@app.route('/game/<player_name>')
def game(player_name):
    if check_task_completion_cookie():
        return render_template('error.html')
    
    if 'has_viewed_practice' not in session:
        return redirect(url_for('practice'))
    
    session['has_viewed_game'] = True
    if session.get('player_name') != player_name:
        return jsonify({"error": "Unauthorized"}), 403

    # 🚀 自動標記練習完成（如果還沒標記的話）
    try:
        user_file = get_user_data_filename(player_name)
        if os.path.exists(user_file):
            with open(user_file, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
            
            # 檢查練習是否已完成，如果沒有就自動標記
            if not user_data.get('completion_status', {}).get('practice_completed', False):
                update_user_data_file(player_name, 'practice_completed')
                print(f"[AUTO] {player_name} 自動標記練習完成")
    except Exception as e:
        print(f"[WARNING] 自動標記練習完成失敗: {e}")

    if 'image_order' in session and session['image_order']:
        all_images = session['image_order']
        
        # 如果 session 中沒有 player_data，創建新的
        if 'player_data' not in session:
            session['player_data'] = {
                'status': 'incomplete',
                'image_order': all_images,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'images': {}
            }
    else:
        # 🚀 如果沒有 image_order，重新生成（不讀取 Firebase）
        all_images = select_random_images_with_attention_checks(player_name)
        session['image_order'] = all_images
        session['player_data'] = {
            'status': 'incomplete',
            'image_order': all_images,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'images': {}
        }

    update_user_data_file(player_name, 'game_started', {'image_order': all_images})
    
    # 🚀 處理圖片順序（保持原邏輯）
    attention_check_images = [img for img in all_images if 'attention_check/' in img]
    regular_images = [img for img in all_images if 'attention_check/' not in img]
    random.shuffle(regular_images)

    final_images = []
    attention_index = 0
    for i in range(len(regular_images) + len(attention_check_images)):
        if attention_index < len(attention_check_images) and i == session['image_order'].index(attention_check_images[attention_index]):
            final_images.append(attention_check_images[attention_index])
            attention_index += 1
        else:
            final_images.append(regular_images.pop(0))

    return render_template('index.html', player_name=player_name, images=final_images)
@app.route('/label/<player_name>', methods=['POST'])
def label(player_name):
    if 'session_id' not in session or session['player_name'] != player_name:
        return jsonify({'error': 'Unauthorized access'}), 403

    try:
        data = request.get_json() or {}
        image_name = data.get('image_name')
        label_text = data.get('label')
        response_time = data.get('response_time')
        

        if not all([image_name, label_text, response_time is not None]):
            return jsonify({'error': 'Missing parameters'}), 400

        # Session 存儲（保持原有邏輯）
        if 'player_data' not in session:
            session['player_data'] = {'images': {}}
        
        session['player_data']['images'][image_name] = {
            'label': label_text,
            'response_time': response_time,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'image_path': image_name
        }

        # 🚀 JSON 檔案更新
        update_success = update_user_data_file(player_name, 'image_labeled', {
            'image_path': image_name,
            'label': label_text,
            'response_time': response_time,
        })

        return jsonify({
            'success': True, 
            'message': 'Label saved successfully',
            'json_updated': update_success
        }), 200

    except Exception as e:
        print(f"Error in /label/{player_name}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/summary/<player_name>')
def summary(player_name):
    if 'has_viewed_practice' not in session:
        return redirect(url_for('practice'))
    session['has_viewed_game'] = True
    if session.get('player_name') != player_name:
        return jsonify({"error": "Unauthorized"}), 403

    # 🚀 追蹤 summary 頁面訪問
    update_session_tracking('visited_summary')

    try:
        player_data = session.get('player_data', {})
        if not player_data:
            return render_template('summary.html', player_name=player_name, error_message="No data found for this player")

        print(f"[SUMMARY] 處理用戶 {player_name}")
        
        # 檢查注意力測試（保持原邏輯）
        attention_images = {}
        regular_images = {}
        
        for image_name, image_data in player_data.get('images', {}).items():
            if 'attention_check/' in image_name:
                attention_images[image_name] = image_data
            else:
                regular_images[image_name] = image_data
        
        if attention_images:
            attention_check_data = {'images': attention_images}
            attention_passed = check_attention_passed(attention_check_data)
        else:
            attention_passed = True

        print(f"[SUMMARY] 注意力檢查: {'通過' if attention_passed else '失敗'}")
        update_user_data_file(player_name, 'game_completed', {'attention_passed': attention_passed})
        update_user_data_file(player_name, 'summary_viewed')

        # 🚀 重要：到達摘要頁面時，立即標記為 partially_completed
        # 因為用戶已經完成了遊戲但還沒提交email
        try:
            new_username = update_username_by_completion_status(player_name, 'summary_viewed')
            if new_username != player_name:
                session['player_name'] = new_username
                session['original_player_name'] = player_name
                print(f"[USER] ✅ 摘要頁面標記為 noemail: {player_name} → {new_username}")
                current_player_name = new_username
            else:
                current_player_name = player_name
                if 'original_player_name' not in session:
                    session['original_player_name'] = player_name
        except Exception as e:
            print(f"[ERROR] 更新用戶名失敗: {e}")
            current_player_name = player_name
            if 'original_player_name' not in session:
                session['original_player_name'] = player_name

        # 準備數據處理
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        age = session.get('age', '未提供')
        gender = session.get('gender', '未提供')
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # 準備響應數據陣列
        image_responses = []
        emotion_counts = {'anger': 0, 'contempt': 0, 'disgust': 0, 'others': 0}
        label_mapping = {'憤怒': 'anger', '輕蔑': 'contempt', '厭惡': 'disgust', '其他': 'others'}
        
        # 處理每個圖片響應
        for image_name, image_data in regular_images.items():
            if 'label' not in image_data:
                continue
                
            label = image_data['label']
            response_time = image_data.get('response_time', 0)
            image_path = image_data.get('image_path', image_name)
            
            english_label = label_mapping.get(label, 'others')
            emotion_counts[english_label] += 1
            
            # 添加到響應陣列
            response_item = {
                'image_path': image_path,
                'label': label,
                'response_time': response_time,
                'timestamp': image_data.get('timestamp'),
                'normalized_name': normalize_image_name(image_path),
                'meme_name': extract_meme_name(image_path),
                'post_id': extract_post_id(image_path),
                'english_label': english_label
            }
            image_responses.append(response_item)
                  
        # 🚀 使用本地比對數據（排除當前用戶的原始用戶名）
        exclude_user = session.get('original_player_name', player_name)
        other_players_data = load_all_users_for_comparison(exclude_user=exclude_user)
        print(f"[SUMMARY] 使用本地 JSON 比對數據，涵蓋 {len(other_players_data)} 張圖片，排除用戶: {exclude_user}")
        
        # 處理比對結果
        image_order = session.get('image_order', [])
        matches, user_choices = process_current_user_matches_with_order(player_data, other_players_data, image_order)

        # 計算結果統計
        total_choices = len(user_choices)
        if total_choices > 0:
            user_percentages = {
                '輕蔑': round(user_choices.count('輕蔑') / total_choices * 100, 2),
                '憤怒': round(user_choices.count('憤怒') / total_choices * 100, 2),
                '厭惡': round(user_choices.count('厭惡') / total_choices * 100, 2),
                '其他': round(user_choices.count('其他') / total_choices * 100, 2)
            }
        else:
            user_percentages = {'輕蔑': 0, '憤怒': 0, '厭惡': 0, '其他': 0}

        # 計算獨特性分數和人格類型
        uniqueness_score = calculate_uniqueness_score(matches)
        personality_result = get_personality_type(user_percentages, matches)

        print(f"[SUMMARY] 完成：{total_choices} 個選擇，獨特性 {uniqueness_score}%")
        print(f"[SUMMARY] 最終使用的用戶名: {current_player_name}")

        # 🚀 創建響應，使用更新後的用戶名
        response = make_response(render_template(
            'summary.html',
            player_name=current_player_name,  # 使用可能更新後的用戶名（partially_completed）
            uniqueness_score=uniqueness_score,
            all_items=matches,
            image_order=image_order,
            user_percentages=user_percentages,
            personality_type=personality_result.get("type", ""),
            personality_description=personality_result.get("description", ""),
            personality_animal=personality_result.get("animal", ""),
            matches=matches,
            attention_passed=attention_passed,
            # 🚀 新增：提供原始用戶名給模板使用（如果需要）
            original_player_name=session.get('original_player_name', player_name)
        ))
        
        # 設置完成 cookie
        response.set_cookie('game_completed', 'true', max_age=60*60*24*30)
        return response

    except Exception as e:
        print(f"[ERROR] summary 路由錯誤: {e}")
        import traceback
        traceback.print_exc()
        
        # 錯誤處理：使用原始用戶名
        error_player_name = session.get('original_player_name', player_name)
        return render_template('summary.html', 
                              player_name=error_player_name, 
                              error_message="An error occurred",
                              user_percentages={'輕蔑': 0, '憤怒': 0, '厭惡': 0, '其他': 0},
                              all_items=[], image_order=[], uniqueness_score=0,
                              personality_type="", personality_description="", personality_animal="",
                              matches=[], attention_passed=True)
        
@app.route('/save_email/<player_name>', methods=['POST'])
def save_email(player_name):
    if 'session_id' not in session:
        print(f"[ERROR] 沒有有效的 session_id")
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # 🚀 檢查用戶名匹配（支持原始用戶名和當前用戶名）
    current_session_name = session.get('player_name', '')
    original_session_name = session.get('original_player_name', '')
    
    # 靈活匹配：URL中的用戶名可能是原始的或者是partially_completed的
    valid_user = False
    target_username = None
    
    if current_session_name == player_name:
        # URL用戶名與當前session用戶名匹配
        valid_user = True
        target_username = current_session_name
    elif original_session_name == player_name:
        # URL用戶名與原始用戶名匹配
        valid_user = True
        target_username = current_session_name  # 使用當前的（可能是partially_completed）
    elif current_session_name and ('noemail' in current_session_name):
        # 當前是noemail狀態，檢查原始用戶名
        if original_session_name == player_name:
            valid_user = True
            target_username = current_session_name
    
    if not valid_user:
        print(f"[ERROR] 用戶名驗證失敗: URL={player_name}, Session={current_session_name}, Original={original_session_name}")
        return jsonify({'error': 'Unauthorized access'}), 403

    email = request.form.get('email', '').strip()
    participation = request.form.get('participation', 'no')
    
    print(f"[DEBUG] save_email 開始: player_name={player_name}, target_username={target_username}, email={email}")
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    # 🚀 追蹤 email 保存動作
    update_session_tracking('saved_email')

    try:
        # 🚀 先更新用戶數據
        json_success = update_user_data_file(target_username, 'email_submitted', {
            'email': email,
            'participation': participation
        })
        
        print(f"[DEBUG] JSON 更新結果: {json_success}")
        
        if json_success:
            print(f"[JSON] ✅ 用戶 {target_username} email 已更新到個人檔案")
            
            # 🚀 Email 提交成功後，從 partially_completed 更新為 fully_completed
            try:
                print(f"[DEBUG] 準備更新用戶名為 fully_completed: {target_username}")
                
                new_username = update_username_by_completion_status(target_username, 'email_submitted')
                print(f"[DEBUG] 用戶名更新結果: {target_username} → {new_username}")
                
                if new_username != target_username:
                    session['player_name'] = new_username
                    session['final_player_name'] = new_username
                    print(f"[USER] ✅ 最終用戶名已更新為 fully_completed: {target_username} → {new_username}")
                else:
                    print(f"[WARNING] 用戶名沒有更新，可能已經是正確狀態: {target_username}")
                    
            except Exception as e:
                print(f"[ERROR] 更新用戶名時出錯: {e}")
                import traceback
                traceback.print_exc()
            
            # 🚀 創建成功響應
            response = make_response(jsonify({
                'success': True, 
                'message': 'Email and participation saved successfully',
                'final_username': session.get('player_name', target_username)
            }))
            response = create_completion_cookie(response)
            return response, 200
        else:
            print(f"[JSON] ❌ 個人檔案 email 更新失敗")
            return jsonify({'error': 'Failed to save email'}), 500
            
    except Exception as e:
        print(f"[JSON] ❌ 個人檔案異常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500
@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

@app.route('/practice_images/<path:filename>')
def serve_practice_image(filename):
    return send_from_directory(IMAGE_FOLDER_practice, filename)

@app.route('/selected_images/<path:filename>')
def serve_selected_image(filename):
    """
    Serve images directly from source folders instead of a copied folder
    """
    if '/' in filename:
        folder, image = filename.split('/', 1)
        if folder == 'attention_check':
            attention_check_folder = os.path.join(BASE_DIR, 'static', 'attention_check')
            return send_from_directory(attention_check_folder, image)
        folder_path = os.path.join(SOURCE_FOLDERS_PATH, folder)
        if os.path.exists(os.path.join(folder_path, image)):
            return send_from_directory(folder_path, image)
    return send_from_directory(SOURCE_FOLDERS_PATH, filename)

@app.route('/summary/images/<path:filename>')
def serve_summary_image(filename):
    """
    Serve images for summary page directly from source folders
    """
    if '/' in filename:
        folder, image = filename.split('/', 1)
        if folder == 'attention_check':
            attention_check_folder = os.path.join(BASE_DIR, 'static', 'attention_check')
            return send_from_directory(attention_check_folder, image)
        
        folder_path = os.path.join(SOURCE_FOLDERS_PATH, folder)
        if os.path.exists(os.path.join(folder_path, image)):
            return send_from_directory(folder_path, image)
    for folder in os.listdir(SOURCE_FOLDERS_PATH):
        folder_path = os.path.join(SOURCE_FOLDERS_PATH, folder)
        if os.path.isdir(folder_path):
            if os.path.exists(os.path.join(folder_path, filename)):
                return send_from_directory(folder_path, filename)
    
    return send_from_directory(IMAGE_FOLDER, filename)

@app.route('/health')
def health_check():
    """改進的健康檢查端點"""
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 檢查用戶目錄
        user_dir_exists = os.path.exists(USER_DATA_DIR)
        user_files_count = len([f for f in os.listdir(USER_DATA_DIR) if f.endswith('.json')]) if user_dir_exists else 0
        
        # 檢查緩存狀態
        cache_size = len(_normalize_cache)
        
        # 檢查會話文件
        sessions_exists = os.path.exists(ACTIVE_SESSIONS_FILE)
        sessions_count = 0
        if sessions_exists:
            try:
                with open(ACTIVE_SESSIONS_FILE, 'r', encoding='utf-8') as f:
                    sessions_data = json.load(f)
                    sessions_count = len(sessions_data)
            except:
                sessions_count = -1  # 表示檔案損壞
        
        # 🚀 記憶體使用情況
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': current_time,
            'user_directory': user_dir_exists,
            'user_files_count': user_files_count,
            'cache_size': cache_size,
            'cache_max_size': CACHE_MAX_SIZE,
            'sessions_file': sessions_exists,
            'active_sessions_count': sessions_count,
            'memory_usage_mb': round(memory_info.rss / 1024 / 1024, 2),
            'cleanup_interval_hours': CACHE_CLEANUP_INTERVAL / 3600
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 500

@app.template_filter('emotion_class')
def emotion_class(emotion):
    mapping = {
        '輕蔑': 'contempt',
        '憤怒': 'anger',
        '厭惡': 'disgust',
        '其他': 'others'
    }
    return mapping.get(emotion, 'others')

if __name__ == '__main__':
    ensure_user_data_directory()
    
    # 啟動清理線程
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    print("[STARTUP] 定期清理線程已啟動")
    
    # 增加線程數和連接限制
    serve(app, host='0.0.0.0', port=5000, threads=16, connection_limit=200)
