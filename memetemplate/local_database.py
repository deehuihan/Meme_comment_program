import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class LocalDatabase:
    def __init__(self, db_path: str = None):
        """
        初始化 SQLite 數據庫
        
        Args:
            db_path: 數據庫文件路徑，默認為 './data/meme_local.sqlite'
        """
        if db_path is None:
            # 🗄️ SQLite 檔案會儲存在這裡
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, 'data')
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            db_path = os.path.join(data_dir, 'meme_local.sqlite')
        
        self.db_path = db_path
        self.init_database()
        print(f"[SQLITE] 數據庫初始化完成: {db_path}")
    
    def init_database(self):
        """初始化數據庫表結構"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 創建用戶表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        player_name TEXT PRIMARY KEY,
                        age TEXT,
                        gender TEXT,
                        user_agent TEXT,
                        attention_passed BOOLEAN,
                        timestamp TEXT,
                        email TEXT,
                        participation TEXT,
                        emotion_summary TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 創建圖片標記表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS image_labels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        player_name TEXT,
                        image_path TEXT,
                        label TEXT,
                        response_time REAL,
                        timestamp TEXT,
                        normalized_name TEXT,
                        meme_name TEXT,
                        post_id INTEGER,
                        english_label TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (player_name) REFERENCES users (player_name)
                    )
                ''')
                
                # 創建索引提高查詢效能
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_player_name ON image_labels (player_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_normalized_name ON image_labels (normalized_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_meme_name ON image_labels (meme_name)')
                
                conn.commit()
                
        except Exception as e:
            print(f"[SQLITE] 初始化數據庫失敗: {e}")
    
    def add_user_data(self, player_name: str, user_info: Dict[str, Any], image_responses: List[Dict[str, Any]]) -> bool:
        """
        添加用戶數據和圖片響應
        
        Args:
            player_name: 用戶名
            user_info: 用戶信息字典
            image_responses: 圖片響應列表
            
        Returns:
            bool: 是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 插入用戶信息
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (player_name, age, gender, user_agent, attention_passed, timestamp, emotion_summary, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    player_name,
                    user_info.get('age', ''),
                    user_info.get('gender', ''),
                    user_info.get('user_agent', ''),
                    user_info.get('attention_passed', True),
                    user_info.get('timestamp', ''),
                    json.dumps(user_info.get('emotion_summary', {})),
                    datetime.now().isoformat()
                ))
                
                # 刪除舊的圖片標記（如果存在）
                cursor.execute('DELETE FROM image_labels WHERE player_name = ?', (player_name,))
                
                # 插入圖片響應
                for response in image_responses:
                    cursor.execute('''
                        INSERT INTO image_labels 
                        (player_name, image_path, label, response_time, timestamp, normalized_name, 
                         meme_name, post_id, english_label)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        player_name,
                        response.get('image_path', ''),
                        response.get('label', ''),
                        response.get('response_time', 0),
                        response.get('timestamp', ''),
                        response.get('normalized_name', ''),
                        response.get('meme_name', ''),
                        response.get('post_id'),
                        response.get('english_label', '')
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"[SQLITE] 添加用戶數據失敗: {e}")
            return False
    
    def update_email(self, player_name: str, email: str, participation: str) -> bool:
        """
        更新用戶 email 和參與意願
        
        Args:
            player_name: 用戶名
            email: 電子郵件
            participation: 參與意願
            
        Returns:
            bool: 是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE users 
                    SET email = ?, participation = ?, updated_at = ?
                    WHERE player_name = ?
                ''', (email, participation, datetime.now().isoformat(), player_name))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"[SQLITE] 更新 email 失敗: {e}")
            return False
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """
        獲取數據庫統計摘要
        
        Returns:
            Dict: 統計信息
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 用戶統計
                cursor.execute('SELECT COUNT(*) FROM users')
                total_users = cursor.fetchone()[0]
                
                # 標記統計
                cursor.execute('SELECT COUNT(*) FROM image_labels')
                total_labels = cursor.fetchone()[0]
                
                # 注意力檢查通過率
                cursor.execute('SELECT COUNT(*) FROM users WHERE attention_passed = 1')
                attention_passed = cursor.fetchone()[0]
                
                # 有 email 的用戶
                cursor.execute('SELECT COUNT(*) FROM users WHERE email IS NOT NULL AND email != ""')
                users_with_email = cursor.fetchone()[0]
                
                # 數據庫文件大小
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                return {
                    'total_users': total_users,
                    'total_labels': total_labels,
                    'attention_passed_count': attention_passed,
                    'attention_pass_rate': round(attention_passed / total_users * 100, 2) if total_users > 0 else 0,
                    'users_with_email': users_with_email,
                    'email_completion_rate': round(users_with_email / total_users * 100, 2) if total_users > 0 else 0,
                    'database_size_mb': round(db_size / (1024*1024), 2),
                    'database_path': self.db_path,
                    'last_checked': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"[SQLITE] 獲取統計失敗: {e}")
            return {
                'total_users': 0,
                'total_labels': 0,
                'error': str(e)
            }
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """
        驗證數據完整性
        
        Returns:
            Dict: 完整性檢查結果
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 檢查孤立的圖片標記
                cursor.execute('''
                    SELECT COUNT(*) FROM image_labels 
                    WHERE player_name NOT IN (SELECT player_name FROM users)
                ''')
                orphaned_labels = cursor.fetchone()[0]
                
                # 檢查沒有標記的用戶
                cursor.execute('''
                    SELECT COUNT(*) FROM users 
                    WHERE player_name NOT IN (SELECT DISTINCT player_name FROM image_labels)
                ''')
                users_without_labels = cursor.fetchone()[0]
                
                # 檢查重複用戶
                cursor.execute('''
                    SELECT player_name, COUNT(*) FROM users 
                    GROUP BY player_name HAVING COUNT(*) > 1
                ''')
                duplicate_users = cursor.fetchall()
                
                return {
                    'orphaned_labels': orphaned_labels,
                    'users_without_labels': users_without_labels,
                    'duplicate_users_count': len(duplicate_users),
                    'duplicate_users': duplicate_users[:5],  # 只顯示前5個
                    'integrity_status': 'good' if orphaned_labels == 0 and len(duplicate_users) == 0 else 'issues_found',
                    'checked_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"[SQLITE] 完整性檢查失敗: {e}")
            return {
                'error': str(e),
                'integrity_status': 'error'
            }
    
    def get_user_data(self, player_name: str) -> Optional[Dict[str, Any]]:
        """
        獲取特定用戶的完整數據
        
        Args:
            player_name: 用戶名
            
        Returns:
            Dict or None: 用戶數據
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 獲取用戶信息
                cursor.execute('SELECT * FROM users WHERE player_name = ?', (player_name,))
                user_row = cursor.fetchone()
                
                if not user_row:
                    return None
                
                # 獲取列名
                user_columns = [description[0] for description in cursor.description]
                user_data = dict(zip(user_columns, user_row))
                
                # 解析 emotion_summary
                if user_data.get('emotion_summary'):
                    try:
                        user_data['emotion_summary'] = json.loads(user_data['emotion_summary'])
                    except:
                        pass
                
                # 獲取圖片標記
                cursor.execute('SELECT * FROM image_labels WHERE player_name = ?', (player_name,))
                label_rows = cursor.fetchall()
                label_columns = [description[0] for description in cursor.description]
                
                user_data['image_labels'] = [
                    dict(zip(label_columns, row)) for row in label_rows
                ]
                
                return user_data
                
        except Exception as e:
            print(f"[SQLITE] 獲取用戶數據失敗: {e}")
            return None
    
    def close(self):
        """關閉數據庫連接（SQLite 自動管理，通常不需要）"""
        pass