"""
簡化版情緒分析系統 - 使用 Claude 3.5 Sonnet
分離職責：人身攻擊檢測 + 情緒分析
"""

import anthropic
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import time
import os
import random
from dataclasses import dataclass
from config import config
import re

@dataclass
class EmotionResult:
    """情緒分析結果"""
    contempt: float
    anger: float
    disgust: float
    raw_response: str
    reasoning: str = ""

@dataclass
class AttackDetectionResult:
    """人身攻擊檢測結果"""
    is_personal_attack: bool
    reasoning: str
    raw_response: str

class ClaudeEmotionAnalyzer:
    def __init__(self, api_key: str):
        """
        初始化 Claude 情緒分析器
        
        Args:
            api_key (str): Anthropic API key
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def detect_personal_attack(self, text: str, max_retries: int = 5) -> AttackDetectionResult:
        """
        檢測人身攻擊
        
        Args:
            text (str): 要分析的文本
            max_retries (int): 最大重試次數
            
        Returns:
            AttackDetectionResult: 人身攻擊檢測結果
        """
        
        prompt = f"""判斷這個留言是否含有人生攻擊的言論 

        句子：「{text}」

        人身攻擊定義： 指在溝通對話時，攻擊、批評對方個人因素相關之斷言或質疑；如人格、動機、態度、地位、階級、處境或是外貌等。

        請只用 JSON 格式回應：
        {{
        "is_personal_attack": true/false,
        "reasoning": "簡短理由"
        }}"""

        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=200,
                    temperature=0.1,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                content = response.content[0].text.strip()
                
                # 提取 JSON
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    result_dict = json.loads(json_str)
                    
                    return AttackDetectionResult(
                        is_personal_attack=result_dict.get('is_personal_attack', False),
                        reasoning=result_dict.get('reasoning', ''),
                        raw_response=content
                    )
                
            except Exception as e:
                print(f"人身攻擊檢測嘗試 {attempt + 1} 失敗: {e}")
                if attempt == max_retries - 1:
                    # 最後一次失敗時，記錄錯誤並返回False，表示無法檢測
                    print(f"人身攻擊檢測完全失敗: {e}")
                    return AttackDetectionResult(
                        is_personal_attack=False,  # 檢測失敗時預設為不是人身攻擊
                        reasoning=f'檢測失敗: {str(e)}',
                        raw_response=f"Error: {e}"
                    )
                
                # 根據錯誤類型調整等待時間
                if "overloaded" in str(e).lower() or "529" in str(e):
                    wait_time = (attempt + 1) * 5  # 5, 10, 15 秒
                    print(f"API 過載，等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                elif "rate_limit" in str(e).lower() or "429" in str(e):
                    wait_time = (attempt + 1) * 10  # 10, 20, 30 秒
                    print(f"達到速率限制，等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                else:
                    time.sleep(2)  # 其他錯誤等待 2 秒

    def analyze_emotion(self, text: str, max_retries: int = 5) -> EmotionResult:
        """
        分析句子情緒
        
        Args:
            text (str): 要分析的文本
            max_retries (int): 最大重試次數
            
        Returns:
            EmotionResult: 情緒分析結果
        """
        
        prompt = f"""     
        請分析以下句子各別傳達的語氣,判斷它們是表達何種情緒，
        1) anger, 2) contempt, 3) disgust. 
        寫出各個情緒類別的信心值。 
        
        句子：「{text}」
        
        使用JSON 格式回應: {{ "contempt": 0.xxx, "anger": 0.xxx, "disgust": 0.xxx, "reasoning": "簡短分析理由" }}
        """

        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=200,
                    temperature=0.1,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                content = response.content[0].text.strip()
                
                # 提取 JSON
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    result_dict = json.loads(json_str)
                    
                    # 驗證結果
                    contempt = float(result_dict.get('contempt', 0))
                    anger = float(result_dict.get('anger', 0))
                    disgust = float(result_dict.get('disgust', 0))
                    reasoning = result_dict.get('reasoning', '')
                    
                    
                    return EmotionResult(
                        contempt=contempt,
                        anger=anger,
                        disgust=disgust,
                        raw_response=content,
                        reasoning=reasoning
                    )
                
            except Exception as e:
                if attempt == max_retries - 1:
                    return EmotionResult(
                        contempt=0.33,
                        anger=0.33,
                        disgust=0.34,
                        raw_response=f"Error: {e}",
                        reasoning="分析失敗"
                    )
                
                print(f"情緒分析嘗試 {attempt + 1} 失敗: {e}")
                # 根據錯誤類型調整等待時間
                if "overloaded" in str(e).lower() or "529" in str(e):
                    wait_time = (attempt + 1) * 5
                    print(f"API 過載，等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                elif "rate_limit" in str(e).lower() or "429" in str(e):
                    wait_time = (attempt + 1) * 10
                    print(f"達到速率限制，等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                else:
                    time.sleep(2)

class IntegratedMemeRecommender:
    """整合情緒分析和 meme 推薦的完整系統"""
    
    def __init__(self, claude_api_key: str, excel_path: str):
        """
        初始化整合推薦系統
        
        Args:
            claude_api_key (str): Claude API key
            excel_path (str): meme 資料庫 Excel 路徑
        """
        self.emotion_analyzer = ClaudeEmotionAnalyzer(claude_api_key)
        self.excel_path = excel_path
        self.meme_database = None
        self.load_meme_database()
    
    def load_meme_database(self):
        """載入 meme 情緒資料庫"""
        try:
            self.meme_database = pd.read_excel(self.excel_path, sheet_name="Meme_Database_Stable")
            print(f"載入 {len(self.meme_database)} 個 memes")
        except Exception as e:
            try:
                self.meme_database = pd.read_excel(self.excel_path, sheet_name="Meme_Database_All")
                print(f"使用全部 {len(self.meme_database)} 個 memes")
            except:
                raise
    
    def recommend_for_sentence(self, sentence: str) -> Tuple[Optional[EmotionResult], Dict[str, pd.DataFrame]]:
        """
        完整流程：檢測人身攻擊 → 分析句子情緒 → 推薦 memes
        
        Args:
            sentence (str): 輸入句子
            
        Returns:
            Tuple[Optional[EmotionResult], Dict[str, pd.DataFrame]]: 情緒分析結果和推薦結果
        """
        print(f"句子：{sentence}")
        
        # 1. 人身攻擊檢測
        attack_result = self.emotion_analyzer.detect_personal_attack(sentence)
        
        if attack_result.is_personal_attack:
            print(f"人身攻擊：是 - {attack_result.reasoning}")
        else:
            print(f"人身攻擊：否 - {attack_result.reasoning}")
            print("此句子不構成人身攻擊，跳過情緒分析")
            return None, {"high_similarity": pd.DataFrame(), "medium_similarity": pd.DataFrame(), "low_similarity": pd.DataFrame()}
        
        # 2. 情緒分析
        emotion_result = self.emotion_analyzer.analyze_emotion(sentence)
        
        print(f"情緒：輕蔑 {emotion_result.contempt:.3f} | 憤怒 {emotion_result.anger:.3f} | 厭惡 {emotion_result.disgust:.3f}")
        
        if emotion_result.reasoning:
            print(f"理由：{emotion_result.reasoning}")
        
        # 3. 計算與所有 memes 的相似度
        user_emotion = np.array([emotion_result.contempt, emotion_result.anger, emotion_result.disgust])
        
        similarities = []
        for _, meme_row in self.meme_database.iterrows():
            meme_emotion = np.array([meme_row['contempt'], meme_row['anger'], meme_row['disgust']])
            
            # Cosine Similarity
            dot_product = np.dot(user_emotion, meme_emotion)
            norm_user = np.linalg.norm(user_emotion)
            norm_meme = np.linalg.norm(meme_emotion)
            
            similarity = dot_product / (norm_user * norm_meme)
            
            similarities.append({
                'meme_name': meme_row['meme_name'],
                'similarity': similarity,
                'contempt': meme_row['contempt'],
                'anger': meme_row['anger'],
                'disgust': meme_row['disgust']
            })
        
        # 4. 排序並選擇高中低三組
        recommendations_df = pd.DataFrame(similarities)
        recommendations_df = recommendations_df.sort_values('similarity', ascending=False)

        total_memes = len(recommendations_df)

        # 確保有足夠的 memes（至少48個）
        if total_memes < 48:
            print(f"警告：meme 數量不足 ({total_memes}個)，調整選擇策略")
            # 如果數量不足，按比例選擇
            high_indices = [0, 1] if total_memes > 1 else list(range(min(2, total_memes)))
            medium_start = max(2, total_memes // 3)
            medium_indices = [medium_start + i for i in range(2)] if total_memes > medium_start + 1 else []
            low_start = max(total_memes - 2, medium_start + 2) if total_memes > 4 else total_memes
            low_indices = [low_start + i for i in range(2)] if total_memes > low_start + 1 else []
        else:
            # 標準選擇：固定排名
            high_indices = [0, 1]  # 排名 1, 2
            medium_indices = [23, 24]  # 排名 24, 25
            low_indices = [46, 47]  # 排名 47, 48

        # 高分組：選擇排名 1, 2
        high_similarity = recommendations_df.iloc[high_indices] if high_indices else pd.DataFrame()

        # 中分組：選擇排名 24, 25
        medium_similarity = recommendations_df.iloc[medium_indices] if medium_indices and all(i < total_memes for i in medium_indices) else pd.DataFrame()

        # 低分組：選擇排名 47, 48
        low_similarity = recommendations_df.iloc[low_indices] if low_indices and all(i < total_memes for i in low_indices) else pd.DataFrame()
        
        # 顯示各組的選擇結果
        print(f"\n=== 推薦結果 ===")
        print(f"總共 {total_memes} 個 memes")
        
        print(f"\n高相似度組（固定選擇排名 1, 2）：")
        for i, (_, row) in enumerate(high_similarity.iterrows(), 1):
            rank = recommendations_df.index.get_loc(row.name) + 1
            print(f"{i}. {row['meme_name']} (排名: {rank}, 相似度: {row['similarity']:.3f})")
        
        print(f"\n中相似度組（固定選擇排名 24, 25）：")
        for i, (_, row) in enumerate(medium_similarity.iterrows(), 1):
            rank = recommendations_df.index.get_loc(row.name) + 1
            print(f"{i}. {row['meme_name']} (排名: {rank}, 相似度: {row['similarity']:.3f})")
        
        print(f"\n低相似度組（固定選擇排名 47, 48）：")
        for i, (_, row) in enumerate(low_similarity.iterrows(), 1):
            rank = recommendations_df.index.get_loc(row.name) + 1
            print(f"{i}. {row['meme_name']} (排名: {rank}, 相似度: {row['similarity']:.3f})")
        
        return emotion_result, {
            "high_similarity": high_similarity,
            "medium_similarity": medium_similarity,
            "low_similarity": low_similarity
        }

# ================================
# 使用範例
# ================================

def demo_mode():
    """演示模式 - 不需要 API Key 的測試功能"""
    
    print("\n=== 演示模式 ===")
    print("這是一個不需要 API Key 的演示版本")
    print("將模擬情緒分析和人身攻擊檢測的結果")
    print("=" * 50)
    
    # 設定 meme 資料庫路徑
    excel_path = "C:/Users/deehu/Desktop/Program/Meme_comment_program/socialmediatemplate/meme_analysis_complete_results.xlsx"
    
    # 檢查檔案
    if not os.path.exists(excel_path):
        print(f"找不到 meme 資料庫檔案: {excel_path}")
        return
    
    # 載入 meme 資料庫
    try:
        meme_database = pd.read_excel(excel_path, sheet_name="Meme_Database_Stable")
        print(f"載入 {len(meme_database)} 個 memes")
    except Exception as e:
        try:
            meme_database = pd.read_excel(excel_path, sheet_name="Meme_Database_All")
            print(f"使用全部 {len(meme_database)} 個 memes")
        except:
            print(f"無法載入 meme 資料庫: {e}")
            return
    
    print("輸入 'quit' 或 'exit' 結束程式")
    
    while True:
        try:
            # 取得使用者輸入
            user_input = input("\n請輸入要分析的句子: ").strip()
            
            # 檢查是否要結束程式
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("感謝使用，再見！")
                break
            
            # 檢查輸入是否為空
            if not user_input:
                print("請輸入有效的句子")
                continue
            
            print(f"\n正在分析: 「{user_input}」")
            print("-" * 50)
            
            # 模擬人身攻擊檢測
            attack_keywords = ['白痴', '死', '笨蛋', '垃圾', '廢物', '蠢', '智障']
            is_attack = any(keyword in user_input for keyword in attack_keywords)
            
            if not is_attack:
                print("人身攻擊：否 - 未檢測到人身攻擊相關詞彙")
                print("\n✅ 結論：此句子不構成人身攻擊，無需進行 meme 推薦")
            else:
                print("人身攻擊：是 - 檢測到攻擊性詞彙")
                
                # 模擬情緒分析結果
                import hashlib
                hash_val = int(hashlib.md5(user_input.encode()).hexdigest(), 16)
                np.random.seed(hash_val % 1000)
                
                contempt = np.random.uniform(0.1, 0.9)
                anger = np.random.uniform(0.1, 0.9)
                disgust = np.random.uniform(0.1, 0.9)
                
                # 正規化
                total = contempt + anger + disgust
                contempt /= total
                anger /= total
                disgust /= total
                
                print(f"\n📊 情緒分析結果（模擬）:")
                print(f"   輕蔑 (Contempt): {contempt:.3f}")
                print(f"   憤怒 (Anger): {anger:.3f}")
                print(f"   厭惡 (Disgust): {disgust:.3f}")
                print(f"   分析理由: 基於文本內容的模擬分析")
                
                # 計算與所有 memes 的相似度
                user_emotion = np.array([contempt, anger, disgust])
                
                similarities = []
                for _, meme_row in meme_database.iterrows():
                    meme_emotion = np.array([meme_row['contempt'], meme_row['anger'], meme_row['disgust']])
                    
                    # Cosine Similarity
                    dot_product = np.dot(user_emotion, meme_emotion)
                    norm_user = np.linalg.norm(user_emotion)
                    norm_meme = np.linalg.norm(meme_emotion)
                    
                    if norm_user > 0 and norm_meme > 0:
                        similarity = dot_product / (norm_user * norm_meme)
                    else:
                        similarity = 0
                    
                    similarities.append({
                        'meme_name': meme_row['meme_name'],
                        'similarity': similarity,
                        'contempt': meme_row['contempt'],
                        'anger': meme_row['anger'],
                        'disgust': meme_row['disgust']
                    })
                
                # 排序並選擇高中低三組
                recommendations_df = pd.DataFrame(similarities)
                recommendations_df = recommendations_df.sort_values('similarity', ascending=False)
                
                total_memes = len(recommendations_df)
                
                # 選擇推薦
                if total_memes >= 48:
                    high_indices = [0, 1]  # 排名 1, 2
                    medium_indices = [23, 24]  # 排名 24, 25
                    low_indices = [46, 47]  # 排名 47, 48
                else:
                    high_indices = [0, 1] if total_memes > 1 else [0]
                    medium_start = max(2, total_memes // 3)
                    medium_indices = [medium_start] if total_memes > medium_start else []
                    low_start = max(total_memes - 1, medium_start + 1) if total_memes > 4 else total_memes - 1
                    low_indices = [low_start] if total_memes > low_start else []
                
                print(f"\n🎭 推薦 Memes:")
                
                if high_indices:
                    high_memes = recommendations_df.iloc[high_indices]
                    print(f"\n   高相似度組:")
                    for i, (_, row) in enumerate(high_memes.iterrows(), 1):
                        rank = recommendations_df.index.get_loc(row.name) + 1
                        print(f"   {i}. {row['meme_name']} (排名: {rank}, 相似度: {row['similarity']:.3f})")
                
                if medium_indices and all(i < total_memes for i in medium_indices):
                    medium_memes = recommendations_df.iloc[medium_indices]
                    print(f"\n   中相似度組:")
                    for i, (_, row) in enumerate(medium_memes.iterrows(), 1):
                        rank = recommendations_df.index.get_loc(row.name) + 1
                        print(f"   {i}. {row['meme_name']} (排名: {rank}, 相似度: {row['similarity']:.3f})")
                
                if low_indices and all(i < total_memes for i in low_indices):
                    low_memes = recommendations_df.iloc[low_indices]
                    print(f"\n   低相似度組:")
                    for i, (_, row) in enumerate(low_memes.iterrows(), 1):
                        rank = recommendations_df.index.get_loc(row.name) + 1
                        print(f"   {i}. {row['meme_name']} (排名: {rank}, 相似度: {row['similarity']:.3f})")
            
            print("-" * 50)
                
        except KeyboardInterrupt:
            print("\n\n程式被使用者中斷")
            break
        except Exception as e:
            print(f"\n❌ 分析過程中發生錯誤: {e}")

def main():
    """主程式 - 終端機互動式輸入分析"""
    
    # 詢問使用者要使用哪種模式
    print("請選擇運行模式:")
    print("1. 正常模式 (需要有效的 Claude API Key)")
    print("2. 演示模式 (不需要 API Key，使用模擬結果)")
    
    mode = input("請輸入選擇 (1 或 2): ").strip()
    
    if mode == "2":
        demo_mode()
        return
    
    # 設定 API Key
    api_key = config.CLAUDE_API_KEY
    if not api_key or api_key == "your_claude_api_key_here":
        api_key = input("請輸入 Anthropic API Key: ")
    
    # 設定 meme 資料庫路徑
    excel_path = "C:/Users/deehu/Desktop/Program/Meme_comment_program/socialmediatemplate/meme_analysis_complete_results.xlsx"
    
    # 檢查檔案
    if not os.path.exists(excel_path):
        print(f"找不到 meme 資料庫檔案: {excel_path}")
        return
    
    # 初始化系統
    print("初始化推薦系統...")
    try:
        recommender = IntegratedMemeRecommender(api_key, excel_path)
        print("系統初始化完成！")
    except Exception as e:
        print(f"系統初始化失敗: {e}")
        return
    
    print("\n=== Claude 情緒分析與 Meme 推薦系統 ===")
    print("輸入文字進行人身攻擊檢測和情緒分析")
    print("輸入 'quit' 或 'exit' 結束程式")
    print("=" * 50)
    
    # 測試 API Key 是否有效
    print("\n正在測試 API 連線...")
    test_result = recommender.emotion_analyzer.detect_personal_attack("測試", max_retries=1)
    if "Error code: 401" in test_result.raw_response:
        print("❌ API Key 無效或已過期")
        api_key = input("請重新輸入有效的 Anthropic API Key: ")
        try:
            recommender = IntegratedMemeRecommender(api_key, excel_path)
            print("✅ API Key 更新成功！")
        except Exception as e:
            print(f"❌ 仍然無法連接: {e}")
            return
    else:
        print("✅ API 連線正常")
    
    while True:
        try:
            # 取得使用者輸入
            user_input = input("\n請輸入要分析的句子: ").strip()
            
            # 檢查是否要結束程式
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("感謝使用，再見！")
                break
            
            # 檢查輸入是否為空
            if not user_input:
                print("請輸入有效的句子")
                continue
            
            print(f"\n正在分析: 「{user_input}」")
            print("-" * 50)
            
            # 進行分析
            emotion_result, recommendations = recommender.recommend_for_sentence(user_input)
            
            # 顯示詳細結果
            if emotion_result is None:
                print("\n✅ 結論：此句子不構成人身攻擊，無需進行 meme 推薦")
            else:
                print(f"\n📊 情緒分析結果:")
                print(f"   輕蔑 (Contempt): {emotion_result.contempt:.3f}")
                print(f"   憤怒 (Anger): {emotion_result.anger:.3f}")
                print(f"   厭惡 (Disgust): {emotion_result.disgust:.3f}")
                
                if emotion_result.reasoning:
                    print(f"   分析理由: {emotion_result.reasoning}")
                
                # 顯示推薦的 memes
                print(f"\n🎭 推薦 Memes:")
                
                high_memes = recommendations['high_similarity']
                medium_memes = recommendations['medium_similarity']
                low_memes = recommendations['low_similarity']
                
                if not high_memes.empty:
                    print(f"\n   高相似度組:")
                    for i, (_, row) in enumerate(high_memes.iterrows(), 1):
                        print(f"   {i}. {row['meme_name']} (相似度: {row['similarity']:.3f})")
                
                if not medium_memes.empty:
                    print(f"\n   中相似度組:")
                    for i, (_, row) in enumerate(medium_memes.iterrows(), 1):
                        print(f"   {i}. {row['meme_name']} (相似度: {row['similarity']:.3f})")
                
                if not low_memes.empty:
                    print(f"\n   低相似度組:")
                    for i, (_, row) in enumerate(low_memes.iterrows(), 1):
                        print(f"   {i}. {row['meme_name']} (相似度: {row['similarity']:.3f})")
            
            print("-" * 50)
                
        except KeyboardInterrupt:
            print("\n\n程式被使用者中斷")
            break
        except Exception as e:
            print(f"\n❌ 分析過程中發生錯誤: {e}")
            print("請重新輸入或檢查網路連線")

if __name__ == "__main__":
    main()