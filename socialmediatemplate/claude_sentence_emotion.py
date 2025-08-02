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

def main():
    """主程式範例 - 自動處理 Excel 文件"""
    
    # 設定 API Key
    api_key = config.CLAUDE_API_KEY
    if not api_key:
        api_key = input("請輸入 Anthropic API Key: ")
    
    # 設定路徑
    excel_path = "C:/Users/deehu/Desktop/Program/socialmediatemplate/meme_analysis_complete_results.xlsx"
    input_excel_path = "C:/Users/deehu/Desktop/Program/socialmediatemplate/static/Comments_Meme_Similarity.xlsx"
    
    # 檢查檔案
    if not os.path.exists(excel_path):
        print(f"找不到檔案: {excel_path}")
        return
        
    if not os.path.exists(input_excel_path):
        print(f"找不到輸入檔案: {input_excel_path}")
        return
    
    # 初始化系統
    print("初始化推薦系統...")
    recommender = IntegratedMemeRecommender(api_key, excel_path)
    
    # 讀取輸入 Excel 檔案
    print("讀取留言數據...")
    try:
        df = pd.read_excel(input_excel_path)
        print(f"載入 {len(df)} 個留言")
    except Exception as e:
        print(f"讀取 Excel 檔案失敗: {e}")
        return
    
    # 檢查是否有 Comments 欄位
    if 'Comments' not in df.columns:
        print("Excel 檔案中找不到 'Comments' 欄位")
        print(f"可用欄位: {list(df.columns)}")
        return
    
    # 初始化結果欄位
    df['G'] = ""  # High similarity
    df['H'] = ""  # Medium similarity  
    df['I'] = ""  # Low similarity
    
    # 處理每個留言
    for index, row in df.iterrows():
        comment = row['Comments']
        if pd.isna(comment) or comment.strip() == "":
            print(f"第 {index + 1} 行留言為空，跳過")
            continue
            
        print(f"\n處理第 {index + 1} 行: {comment[:50]}...")
        
        try:
            emotion_result, recommendations = recommender.recommend_for_sentence(str(comment))
            
            if emotion_result is None:
                print("不是人身攻擊，跳過推薦")
                df.at[index, 'G'] = "非人身攻擊"
                df.at[index, 'H'] = "非人身攻擊"
                df.at[index, 'I'] = "非人身攻擊"
            else:
                # 提取推薦結果
                high_memes = recommendations['high_similarity']['meme_name'].tolist()
                medium_memes = recommendations['medium_similarity']['meme_name'].tolist()
                low_memes = recommendations['low_similarity']['meme_name'].tolist()
                
                # 寫入 Excel
                df.at[index, 'G'] = "; ".join(high_memes) if high_memes else ""
                df.at[index, 'H'] = "; ".join(medium_memes) if medium_memes else ""
                df.at[index, 'I'] = "; ".join(low_memes) if low_memes else ""
                
                print(f"推薦完成 - 高:{len(high_memes)}, 中:{len(medium_memes)}, 低:{len(low_memes)}")
                
        except Exception as e:
            print(f"處理第 {index + 1} 行時發生錯誤: {e}")
            df.at[index, 'G'] = f"錯誤: {str(e)}"
            df.at[index, 'H'] = f"錯誤: {str(e)}"
            df.at[index, 'I'] = f"錯誤: {str(e)}"
    
    # 保存結果
    output_path = "C:/Users/deehu/Desktop/Program/socialmediatemplate/static/Comments_Meme_Similarity_Results.xlsx"
    try:
        df.to_excel(output_path, index=False)
        print(f"\n結果已保存至: {output_path}")
    except Exception as e:
        print(f"保存檔案失敗: {e}")
    
    print("處理完成！")

if __name__ == "__main__":
    main()