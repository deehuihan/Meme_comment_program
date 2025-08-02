import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class EmotionAnalyzer:
    """
    動態情緒分析系統 - 可隨數據更新自動調整
    """
    
    def __init__(self, data_path: str):
        """
        初始化分析器
        
        Args:
            data_path: Excel檔案路徑
        """
        self.data_path = data_path
        self.data = None
        self.user_count = None
        self.post_count = None
        self.total_responses = None
        self.overall_proportions = {}
        self.post_analysis = {}
        self.recommended_posts = []
        
    def load_data(self) -> pd.DataFrame:
        """
        載入數據並自動檢測規模
        """
        print("🔄 載入數據中...")
        self.data = pd.read_excel(self.data_path)
        
        # 自動檢測數據規模
        self.user_count = self.data['user_id'].nunique()
        self.post_count = self.data['resp_post_id'].nunique()
        self.total_responses = len(self.data)
        
        print(f"✅ 數據載入完成:")
        print(f"   - 用戶數: {self.user_count}")
        print(f"   - Posts數: {self.post_count}")
        print(f"   - 總回應數: {self.total_responses}")
        print(f"   - 預期回應數: {self.user_count * self.post_count}")
        
        return self.data
    
    def calculate_overall_baseline(self) -> Dict[str, float]:
        """
        步驟1: 計算整體情緒分布基準
        方法: 先計算每個Post的情緒比例，再求所有Posts的平均
        """
        print("\n🔢 步驟1: 計算整體情緒分布基準...")
        
        # 按post_id分組計算每個post的情緒比例
        post_emotion_props = []
        
        for post_id in sorted(self.data['resp_post_id'].unique()):
            post_data = self.data[self.data['resp_post_id'] == post_id]
            post_size = len(post_data)
            
            # 計算該post的情緒比例
            emotion_counts = post_data['resp_english_label'].value_counts()
            emotion_props = {
                'anger': emotion_counts.get('anger', 0) / post_size,
                'contempt': emotion_counts.get('contempt', 0) / post_size,
                'disgust': emotion_counts.get('disgust', 0) / post_size,
                'others': emotion_counts.get('others', 0) / post_size
            }
            post_emotion_props.append(emotion_props)
        
        # 計算所有posts的平均比例
        self.overall_proportions = {
            'anger': np.mean([p['anger'] for p in post_emotion_props]),
            'contempt': np.mean([p['contempt'] for p in post_emotion_props]),
            'disgust': np.mean([p['disgust'] for p in post_emotion_props]),
            'others': np.mean([p['others'] for p in post_emotion_props])
        }
        
        print("✅ 整體情緒分布基準:")
        for emotion, prop in self.overall_proportions.items():
            print(f"   - {emotion.capitalize()}: {prop:.1%}")
        
        return self.overall_proportions
    
    def calculate_z_scores(self, threshold: float = 1.5) -> Dict:
        """
        步驟2: 計算每個Post的Z-scores並篩選
        
        Args:
            threshold: Z-score閾值，默認1.5
        """
        print(f"\n🧮 步驟2: 計算Z-scores (閾值 = {threshold})...")
        
        self.post_analysis = {}
        
        for post_id in sorted(self.data['resp_post_id'].unique()):
            post_data = self.data[self.data['resp_post_id'] == post_id]
            n = len(post_data)
            
            # 計算觀察比例
            emotion_counts = post_data['resp_english_label'].value_counts()
            observed_props = {
                'anger': emotion_counts.get('anger', 0) / n,
                'contempt': emotion_counts.get('contempt', 0) / n,
                'disgust': emotion_counts.get('disgust', 0) / n,
                'others': emotion_counts.get('others', 0) / n
            }
            
            # 計算Z-scores
            z_scores = {}
            for emotion in ['anger', 'contempt', 'disgust', 'others']:
                p_observed = observed_props[emotion]
                p_expected = self.overall_proportions[emotion]
                
                # 標準誤差
                se = np.sqrt(p_expected * (1 - p_expected) / n)
                
                # Z-score
                z_score = (p_observed - p_expected) / se
                z_scores[emotion] = z_score
            
            # 最大絕對Z-score
            max_abs_z = max(abs(z) for z in z_scores.values())
            
            # 儲存分析結果
            self.post_analysis[post_id] = {
                'sample_size': n,
                'observed_props': observed_props,
                'z_scores': z_scores,
                'max_abs_z': max_abs_z,
                'is_balanced': max_abs_z < threshold,
                'meme_name': post_data['resp_meme_name'].iloc[0] if 'resp_meme_name' in post_data.columns else f"Post-{post_id}"
            }
        
        # 篩選推薦posts
        self.recommended_posts = [
            post_id for post_id, analysis in self.post_analysis.items()
            if analysis['is_balanced']
        ]
        
        balanced_count = len(self.recommended_posts)
        total_count = len(self.post_analysis)
        
        print(f"✅ Z-score分析完成:")
        print(f"   - 總Posts數: {total_count}")
        print(f"   - 情緒平衡Posts: {balanced_count} ({balanced_count/total_count:.1%})")
        print(f"   - 推薦Posts: {sorted(self.recommended_posts)}")
        
        return self.post_analysis
    
    def analyze_recommended_posts(self) -> pd.DataFrame:
        """
        步驟3: 分析推薦Posts的詳細情緒分布
        """
        print(f"\n📊 步驟3: 分析推薦的{len(self.recommended_posts)}個Posts...")
        
        if not self.recommended_posts:
            print("⚠️ 沒有推薦的Posts可供分析")
            return pd.DataFrame()
        
        # 篩選推薦posts的數據
        recommended_data = self.data[
            self.data['resp_post_id'].isin(self.recommended_posts)
        ]
        
        # 創建詳細分析表
        analysis_results = []
        
        for post_id in sorted(self.recommended_posts):
            analysis = self.post_analysis[post_id]
            
            result = {
                'post_id': post_id,
                'meme_name': analysis['meme_name'],
                'sample_size': analysis['sample_size'],
                'max_abs_z': round(analysis['max_abs_z'], 2),
                'anger_pct': round(analysis['observed_props']['anger'] * 100, 1),
                'contempt_pct': round(analysis['observed_props']['contempt'] * 100, 1),
                'disgust_pct': round(analysis['observed_props']['disgust'] * 100, 1),
                'others_pct': round(analysis['observed_props']['others'] * 100, 1),
                'anger_z': round(analysis['z_scores']['anger'], 2),
                'contempt_z': round(analysis['z_scores']['contempt'], 2),
                'disgust_z': round(analysis['z_scores']['disgust'], 2),
                'others_z': round(analysis['z_scores']['others'], 2)
            }
            analysis_results.append(result)
        
        results_df = pd.DataFrame(analysis_results)
        
        print("✅ 推薦Posts分析:")
        print(results_df[['post_id', 'meme_name', 'max_abs_z', 'anger_pct', 'contempt_pct', 'disgust_pct', 'others_pct']].to_string(index=False))
        
        return results_df
    
    def create_visualization(self, save_path: str = None):
        """
        創建視覺化圖表
        """
        print("\n🎨 創建視覺化圖表...")
        
        if not self.recommended_posts:
            print("⚠️ 沒有推薦的Posts可供視覺化")
            return
        
        # 準備數據
        plot_data = []
        for post_id in sorted(self.recommended_posts):
            analysis = self.post_analysis[post_id]
            props = analysis['observed_props']
            
            plot_data.append({
                'Post_ID': f"Post {post_id}",
                'Meme': analysis['meme_name'][:15] + '...' if len(analysis['meme_name']) > 15 else analysis['meme_name'],
                'Anger': props['anger'] * 100,
                'Contempt': props['contempt'] * 100,
                'Disgust': props['disgust'] * 100,
                'Others': props['others'] * 100,
                'Max_Z': analysis['max_abs_z']
            })
        
        df_plot = pd.DataFrame(plot_data)
        
        # 創建圖表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
        
        # 圖1: 堆疊柱狀圖
        emotions = ['Contempt', 'Anger', 'Disgust', 'Others']
        colors = ['#16a34a', '#dc2626', '#9333ea', '#6b7280']
        
        bottom = np.zeros(len(df_plot))
        
        for emotion, color in zip(emotions, colors):
            ax1.bar(df_plot['Meme'], df_plot[emotion], bottom=bottom, 
                   label=emotion, color=color, alpha=0.8)
            bottom += df_plot[emotion]
        
        ax1.set_title(f'推薦的{len(self.recommended_posts)}個Posts情緒分布 (Z<1.5)\n'
                     f'基於{self.user_count}個用戶的{self.total_responses}個回應', 
                     fontsize=14, fontweight='bold')
        ax1.set_xlabel('Meme Posts')
        ax1.set_ylabel('Percentage (%)')
        ax1.legend()
        ax1.tick_params(axis='x', rotation=45)
        
        # 圖2: Z-score分布
        ax2.bar(df_plot['Meme'], df_plot['Max_Z'], color='lightblue', alpha=0.7)
        ax2.axhline(y=1.5, color='red', linestyle='--', label='閾值 = 1.5')
        ax2.set_title('各Posts的最大絕對Z-Score', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Meme Posts')
        ax2.set_ylabel('Max |Z-Score|')
        ax2.legend()
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ 圖表已儲存至: {save_path}")
        else:
            plt.show()
    
    def generate_summary_report(self) -> str:
        """
        生成總結報告
        """
        report = f"""
📋 情緒篩選分析報告
{'='*50}

📊 數據概況:
- 用戶數: {self.user_count}
- Posts數: {self.post_count}
- 總回應數: {self.total_responses}

🎯 整體情緒基準:
- Anger: {self.overall_proportions['anger']:.1%}
- Contempt: {self.overall_proportions['contempt']:.1%}
- Disgust: {self.overall_proportions['disgust']:.1%}
- Others: {self.overall_proportions['others']:.1%}

🔍 篩選結果 (Z < 1.5):
- 推薦Posts數: {len(self.recommended_posts)}
- 篩選比例: {len(self.recommended_posts)/len(self.post_analysis):.1%}
- 推薦Posts: {sorted(self.recommended_posts)}

💡 結論:
這{len(self.recommended_posts)}個Posts的情緒分布與整體平均沒有顯著差異,
適合用於需要控制情緒變項的研究。
"""
        return report
    
    def run_complete_analysis(self, z_threshold: float = 1.5, 
                            save_plot: str = None, 
                            save_results: str = None) -> pd.DataFrame:
        """
        執行完整分析流程
        
        Args:
            z_threshold: Z-score閾值
            save_plot: 圖表儲存路徑
            save_results: 結果儲存路徑
        
        Returns:
            推薦Posts的詳細分析結果
        """
        print("🚀 開始完整情緒篩選分析...")
        
        # 執行三個步驟
        self.load_data()
        self.calculate_overall_baseline()
        self.calculate_z_scores(z_threshold)
        results_df = self.analyze_recommended_posts()
        
        # 創建視覺化
        if len(self.recommended_posts) > 0:
            self.create_visualization(save_plot)
        
        # 生成報告
        report = self.generate_summary_report()
        print(report)
        
        # 儲存結果
        if save_results and not results_df.empty:
            results_df.to_excel(save_results, index=False)
            print(f"✅ 結果已儲存至: {save_results}")
        
        return results_df

# 使用範例
if __name__ == "__main__":
    # 初始化分析器
    analyzer = EmotionAnalyzer("your_data.xlsx")
    
    # 執行完整分析
    results = analyzer.run_complete_analysis(
        z_threshold=1.5,
        save_plot="emotion_analysis.png",
        save_results="recommended_posts.xlsx"
    )
    
    # 查看推薦Posts
    print("\n🎯 推薦使用的Posts:")
    print(results[['post_id', 'meme_name', 'max_abs_z']].to_string(index=False))