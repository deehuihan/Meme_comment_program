import os
import pandas as pd
from datetime import datetime

class CommentManager:
    def __init__(self):
        self.news_directory = 'static/news'
        self.meme_directory = 'static/meme_50'
        self.excel_file = 'static/Comments_Meme_Similarity.xlsx'
        self.user_data_file = 'user_data.xlsx'
        
        # 手動定義每個帖文的留言
        self.comments = {
            'High_Intentional_1': '惡劣賤人、欺負幼兒、以其人之道還治其人之身',
            'High_Intentional_2': '這種垃圾還是安樂死吧，對小孩動手，活著也是浪費糧食',
            'High_Intentional_3': '我吐了，好噁的嘴臉！',
            'High_Intentional_4': '這是什麼噁心的老人，給我下地獄！！！',
            'High_Unintentional_1': '社會敗類，直接負二代，重投胎就還完了',
            'High_Unintentional_2': '每次看到這種新聞都很氣，當家長的可以都有點安全意識嗎，更何況這小孩才1歲，這位媽媽已經不是大意了，是無知！！！',
            'High_Unintentional_3': '這人太白目，會害死人的啊！',
            'High_Unintentional_4': '對這種無腦行為感到生氣，會犯這種錯的家長都是沒在照顧小孩的！',
            'Low_Intentional_1': '這種行為實在是弱智，幹狗屁倒灶的事情還錄影存證上傳網路，怕沒人知道，這種人不多見',
            'Low_Intentional_2': '這是教授還是野獸？噁心，該抓出來了吧？',
            'Low_Intentional_3': '完全沒有付出，就只是因為房子是她的就可以隨便抬價，除了無恥還是無恥，良心何在？',
            'Low_Intentional_4': '不意外，猴子生養出來的還是猴子啊！',
            'Low_Unintentional_1': '母女都能載到打架？打到不是親身似的..可悲的母女！',
            'Low_Unintentional_2': '有夠北七的，最近上班都遇到這種，一綠燈就直接騎，也不看看後面有沒有來車，真的三寶',
            'Low_Unintentional_3': '這位老闆的人格氣度不值40元，真的很悲哀',
            'Low_Unintentional_4': '這領隊也太隨便，只會領錢又不會做事？'
        }
        
    def get_news_posts_for_page(self, page_type):
        """Get news posts filtered by page type (sender or receiver)"""
        posts_data = []
        
        # Get all PNG files from the news directory
        if os.path.exists(self.news_directory):
            all_files = [f for f in os.listdir(self.news_directory) if f.endswith('.png')]
            
            # Filter based on page type
            if page_type == 'receiver':
                # For receiver: show images ending with _1.png and _2.png
                filtered_files = [f for f in all_files if f.endswith('_1.png') or f.endswith('_2.png')]
            elif page_type == 'sender':
                # For sender: show images ending with _3.png and _4.png
                filtered_files = [f for f in all_files if f.endswith('_3.png') or f.endswith('_4.png')]
            else:
                filtered_files = all_files
            
            # Create posts data with comments
            for i, filename in enumerate(filtered_files, 1):
                # 從文件名提取Post_ID (去掉.png擴展名)
                post_id_from_filename = filename.replace('.png', '')
                
                # 獲取對應的留言
                comment = self.comments.get(post_id_from_filename, "這篇新聞真有趣！")
                
                # 獲取對應的Meme推薦（sender和receiver頁面都需要）
                memes = []
                if page_type in ['sender', 'receiver']:
                    memes = self.get_memes_for_post_id(post_id_from_filename)
                
                posts_data.append({
                    'post_id': i,
                    'news_file': filename,
                    'time_description': f'{i}小時前',
                    'comment': comment,
                    'original_post_id': post_id_from_filename,
                    'recommended_memes': memes
                })
        
        return posts_data
        
    def get_memes_for_post_id(self, post_id):
        """根據Post_ID獲取對應的Meme圖片列表"""
        try:
            # 讀取Excel數據
            if not os.path.exists(self.excel_file):
                print(f"找不到Excel文件: {self.excel_file}")
                return []
                
            df = pd.read_excel(self.excel_file)
            
            # 找到對應的Post_ID
            row = df[df['Post_ID'] == post_id]
            if row.empty:
                print(f"找不到Post_ID: {post_id}")
                return []
            
            row = row.iloc[0]
            
            # 獲取三個級別的Meme名稱
            high_memes = str(row['Meme_High_Similarity']).split(', ') if pd.notna(row['Meme_High_Similarity']) else []
            medium_memes = str(row['Meme_Medium_Similarity']).split(', ') if pd.notna(row['Meme_Medium_Similarity']) else []
            low_memes = str(row['Meme_Low_Similarity']).split(', ') if pd.notna(row['Meme_Low_Similarity']) else []
            
            # 合併所有Meme名稱
            all_memes = high_memes + medium_memes + low_memes
            
            # 驗證圖片文件是否存在，並創建Meme數據結構
            existing_memes = []
            for meme_name in all_memes:
                if meme_name.strip():  # 確保不是空字符串
                    meme_name_clean = meme_name.strip()
                    meme_filename = f"{meme_name_clean}.jpg"
                    meme_path = os.path.join(self.meme_directory, meme_filename)
                    
                    if os.path.exists(meme_path):
                        existing_memes.append({
                            'name': meme_name_clean,
                            'filename': meme_filename,
                            'url': f"static/meme_50/{meme_filename}"
                        })
            
            # 如果少於6個，就返回現有的，如果多於6個，取前6個
            return existing_memes[:6]
            
        except Exception as e:
            print(f"處理Post_ID {post_id} 時出錯: {e}")
            return []
    
    def get_meme_similarity_category(self, meme_name, post_id):
        """判斷給定的meme屬於哪個相似度類別，返回完整格式"""
        try:
            if not os.path.exists(self.excel_file):
                return f"Unknown_{meme_name}"
                
            df = pd.read_excel(self.excel_file)
            row = df[df['Post_ID'] == post_id]
            if row.empty:
                return f"Unknown_{meme_name}"
            
            row = row.iloc[0]
            
            # 獲取三個級別的Meme名稱
            high_memes = str(row['Meme_High_Similarity']).split(', ') if pd.notna(row['Meme_High_Similarity']) else []
            medium_memes = str(row['Meme_Medium_Similarity']).split(', ') if pd.notna(row['Meme_Medium_Similarity']) else []
            low_memes = str(row['Meme_Low_Similarity']).split(', ') if pd.notna(row['Meme_Low_Similarity']) else []
            
            # 清理meme名稱並檢查屬於哪個類別
            meme_name_clean = meme_name.strip()
            
            if meme_name_clean in [m.strip() for m in high_memes]:
                return f"High_Similarity_{meme_name_clean}"
            elif meme_name_clean in [m.strip() for m in medium_memes]:
                return f"Medium_Similarity_{meme_name_clean}"
            elif meme_name_clean in [m.strip() for m in low_memes]:
                return f"Low_Similarity_{meme_name_clean}"
            else:
                return f"Unknown_{meme_name_clean}"
                
        except Exception as e:
            print(f"判斷meme相似度類別時出錯: {e}")
            return f"Unknown_{meme_name}"
    
    def record_user_data(self, user_id, category, post_id, original_comment, meme_used, questionnaire_scores):
        """記錄使用者資料到Excel檔案
        
        Args:
            user_id (str): 使用者ID
            category (str): 頁面類型 (receiver/sender)
            post_id (str): 帖文ID
            original_comment (str): 原始留言內容
            meme_used (str): 使用的迷因圖分類
            questionnaire_scores (dict): 問卷分數 {'Q1': score, 'Q2': score, ...}
        """
        try:
            # 創建新的資料記錄 - 基本欄位
            new_record = {
                'user_id': user_id,
                'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'category': category,
                'post_id': post_id,
                'original_comments': original_comment,
                'meme_used': meme_used
            }
            
            # 動態添加問卷分數欄位
            for question_key, score in questionnaire_scores.items():
                new_record[question_key] = score
            
            # 檢查檔案是否存在
            if os.path.exists(self.user_data_file):
                # 讀取現有資料
                df = pd.read_excel(self.user_data_file)
                # 添加新記錄
                df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
            else:
                # 創建新的DataFrame
                df = pd.DataFrame([new_record])
            
            # 保存到Excel檔案
            df.to_excel(self.user_data_file, index=False)
            print(f"已記錄使用者 {user_id} 在 {category} 頁面的資料")
            
        except Exception as e:
            print(f"記錄使用者資料時出錯: {e}")
    
    def record_receiver_data(self, user_id, post_id, displayed_meme_name, questionnaire_scores):
        """記錄receiver頁面的使用者資料
        
        Args:
            user_id (str): 使用者ID
            post_id (str): 帖文ID
            displayed_meme_name (str): 顯示給使用者的迷因圖名稱
            questionnaire_scores (dict): 問卷分數
        """
        original_comment = self.comments.get(post_id, "")
        # 動態查詢迷因圖的相似度分類，返回完整格式 (例如: High_Similarity_Arthur-Fist)
        meme_used = self.get_meme_similarity_category(displayed_meme_name, post_id)
        
        self.record_user_data(
            user_id=user_id,
            category="receiver",
            post_id=post_id,
            original_comment=original_comment,
            meme_used=meme_used,
            questionnaire_scores=questionnaire_scores
        )
    
    def record_sender_data(self, user_id, post_id, selected_meme_name, questionnaire_scores):
        """記錄sender頁面的使用者資料
        
        Args:
            user_id (str): 使用者ID
            post_id (str): 帖文ID
            selected_meme_name (str): 使用者選擇的迷因圖名稱
            questionnaire_scores (dict): 問卷分數
        """
        original_comment = self.comments.get(post_id, "")
        # 動態查詢迷因圖的相似度分類，返回完整格式 (例如: Medium_Similarity_Scooby-doo-mask-reveal)
        meme_used = self.get_meme_similarity_category(selected_meme_name, post_id)
        
        self.record_user_data(
            user_id=user_id,
            category="sender",
            post_id=post_id,
            original_comment=original_comment,
            meme_used=meme_used,
            questionnaire_scores=questionnaire_scores
        )
        
    def get_all_news_posts(self):
        """Get all news posts for backward compatibility"""
        return self.get_news_posts_for_page('all')
