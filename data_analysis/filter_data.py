import pandas as pd
import json
import matplotlib.pyplot as plt
import numpy as np

def extract_game_duration(row):
    """
    修正版：正確解析 duration_stats_ms JSON 字串
    """
    duration_str = str(row)
    
    # 如果已經是數字，直接返回
    if isinstance(row, (int, float)) and not pd.isna(row):
        return row
    
    # 如果是 JSON 字串，嘗試解析
    if isinstance(duration_str, str) and duration_str.strip():
        try:
            # 嘗試解析為 JSON
            if duration_str.startswith('{') and duration_str.endswith('}'):
                duration_dict = json.loads(duration_str)
                game_duration_ms = duration_dict.get('game_duration_ms')
                if game_duration_ms is not None:
                    return game_duration_ms / 1000  # ms 轉秒
            
            # 如果 JSON 解析失敗，嘗試正則表達式
            import re
            m = re.search(r'"game_duration_ms":\s*(\d+)', duration_str)
            if m:
                return int(m.group(1)) / 1000  # ms 轉秒
                
        except (json.JSONDecodeError, ValueError) as e:
            print(f"解析錯誤: {e}, 資料: {duration_str[:100]}...")
    
    return None

def extract_game_duration_from_direct_column(row):
    """
    如果 game_duration 欄位已經有值，直接使用
    """
    if pd.isna(row) or row == '' or row is None:
        return None
    
    try:
        return float(row)
    except (ValueError, TypeError):
        return None

def print_user_stats_by_user(df, stage_name=""):
    user_profile = df.groupby('user_id').first().reset_index()[['user_id', 'age', 'gender']]
    total = user_profile['user_id'].nunique()
    print(f"\n--- {stage_name} ---")
    print(f"總人數：{total}")
    print("年齡 x 性別分佈：")
    print(user_profile.groupby(['age', 'gender']).size().unstack(fill_value=0))
    print()

def clean_age_data(age_series):
    """
    清理年齡數據，保持原始區間格式，只做基本清理
    """
    def convert_age(age):
        if pd.isna(age):
            return 'Unknown'
        
        # 如果是字符串，進行基本清理
        if isinstance(age, str):
            age = age.strip()
            
            # 如果是空字符串
            if age == '':
                return 'Unknown'
            
            # 直接返回原始年齡區間，不做轉換
            return age
        
        # 如果是數字，轉為字符串
        if isinstance(age, (int, float)):
            return str(int(age))
        
        return 'Unknown'
    
    return age_series.apply(convert_age)

def clean_gender_data(gender_series):
    """
    清理性別數據，標準化格式
    """
    def convert_gender(gender):
        if pd.isna(gender):
            return 'Unknown'
        
        if isinstance(gender, str):
            gender = gender.strip().lower()
            
            # 標準化性別值
            if gender in ['male', 'm', '男', 'man']:
                return 'Male'
            elif gender in ['female', 'f', '女', 'woman']:
                return 'Female'
            elif gender in ['other', 'others', '其他']:
                return 'Other'
            elif gender in ['prefer not to respond', 'prefer not to say', 'no response', 'n/a']:
                return 'Prefer not to respond'
            else:
                return 'Unknown'
        
        return 'Unknown'
    
    return gender_series.apply(convert_gender)

def create_user_demographics_analysis(df):
    """
    創建用戶人口統計分析表格 - 使用原始年齡區間
    """
    print("📊 開始創建人口統計分析...")
    
    # 每個用戶只取一次基本資料
    user_profile = df.groupby('user_id').first().reset_index()
    print(f"   - 原始用戶數: {len(user_profile)}")
    
    # 顯示原始年齡數據的樣本
    print("📋 原始年齡數據樣本:")
    age_samples = user_profile['age'].value_counts().head(10)
    for age_val, count in age_samples.items():
        print(f"   '{age_val}': {count} 人")
    
    # 清理年齡和性別數據（保持原始格式）
    print("🧹 清理年齡和性別數據...")
    user_profile['age_cleaned'] = clean_age_data(user_profile['age'])
    user_profile['gender_cleaned'] = clean_gender_data(user_profile['gender'])
    
    # 檢查清理結果
    age_valid = (user_profile['age_cleaned'] != 'Unknown').sum()
    age_invalid = len(user_profile) - age_valid
    print(f"   - 有效年齡數據: {age_valid} 個")
    print(f"   - 無效年齡數據: {age_invalid} 個")
    
    gender_counts = user_profile['gender_cleaned'].value_counts()
    print(f"   - 性別分布: {dict(gender_counts)}")
    
    # 顯示清理後的年齡分布
    if age_valid > 0:
        print("📋 清理後年齡分布:")
        age_cleaned_counts = user_profile['age_cleaned'].value_counts()
        for age_val, count in age_cleaned_counts.items():
            print(f"   {age_val}: {count} 人")
    
    # 1. 基本統計摘要
    summary_stats = {
        'Metric': [
            'Total Users',
            'Users with Valid Age',
            'Total Responses',
            'Average Responses per User',
            'Unique Age Groups',
            'Unique Genders',
            'Most Common Age Group',
            'Most Common Gender'
        ],
        'Value': [
            len(user_profile),
            age_valid,
            len(df),
            f"{len(df) / len(user_profile):.1f}",
            user_profile['age_cleaned'].nunique(),
            user_profile['gender_cleaned'].nunique(),
            user_profile['age_cleaned'].mode().iloc[0] if not user_profile['age_cleaned'].mode().empty else 'N/A',
            user_profile['gender_cleaned'].mode().iloc[0] if not user_profile['gender_cleaned'].mode().empty else 'N/A'
        ]
    }
    summary_df = pd.DataFrame(summary_stats)
    
    # 2. 性別分布
    gender_stats = user_profile['gender_cleaned'].value_counts().reset_index()
    gender_stats.columns = ['Gender', 'Count']
    gender_stats['Percentage'] = (gender_stats['Count'] / len(user_profile) * 100).round(2)
    gender_stats['Percentage_Text'] = gender_stats['Percentage'].astype(str) + '%'
    
    # 3. 年齡分布（使用原始區間）
    age_stats = user_profile['age_cleaned'].value_counts().reset_index()
    age_stats.columns = ['Age_Group', 'Count']
    age_stats['Percentage'] = (age_stats['Count'] / len(user_profile) * 100).round(2)
    age_stats['Percentage_Text'] = age_stats['Percentage'].astype(str) + '%'
    
    # 按照年齡區間順序排序
    age_order = ['18-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55+', 'Unknown']
    age_stats['sort_order'] = age_stats['Age_Group'].apply(lambda x: age_order.index(x) if x in age_order else 999)
    age_stats = age_stats.sort_values('sort_order').drop('sort_order', axis=1).reset_index(drop=True)
    
    # 4. 年齡 x 性別交叉分析
    try:
        cross_tab = pd.crosstab(user_profile['age_cleaned'], user_profile['gender_cleaned'], margins=True)
        cross_tab_reset = cross_tab.reset_index()
        cross_tab_reset.columns.name = None  # 移除列名
    except Exception as e:
        print(f"❌ 年齡x性別交叉表錯誤: {e}")
        cross_tab_reset = pd.DataFrame()
    
    # 5. 修改詳細用戶列表 - 只包含需要的欄位
    print("📋 準備用戶詳細資料...")
    
    # 確定需要的欄位
    required_columns = ['user_id', 'age', 'gender', 'game_duration', 'attention_passed']
    
    # 檢查 email 欄位是否存在
    if 'email' in user_profile.columns:
        required_columns.append('email')
        print("   - 發現 email 欄位，將包含在輸出中")
    else:
        print("   - 未發現 email 欄位，跳過")
    
    # 建立 user_details，只包含需要的欄位
    available_columns = [col for col in required_columns if col in user_profile.columns]
    user_details = user_profile[available_columns].copy()
    
    # 如果缺少某些欄位，用空值填充
    for col in required_columns:
        if col not in user_details.columns:
            user_details[col] = None
            print(f"   - 欄位 '{col}' 不存在，已添加空值")
    
    # 按照指定順序重新排列欄位
    final_columns = ['user_id', 'age', 'gender', 'game_duration', 'attention_passed']
    if 'email' in user_details.columns and user_details['email'].notna().sum() > 0:
        final_columns.append('email')
    
    user_details = user_details[final_columns]
    
    # 按年齡區間和性別排序（如果有年齡數據的話）
    if 'age' in user_details.columns:
        age_order = ['18-24', '25-29', '30-34', '35-39', '40-44', '45-49', '50-54', '55+', 'Unknown']
        # 創建臨時排序欄位
        user_details['temp_age_clean'] = clean_age_data(user_details['age'])
        user_details['sort_order'] = user_details['temp_age_clean'].apply(lambda x: age_order.index(x) if x in age_order else 999)
        
        if 'gender' in user_details.columns:
            user_details = user_details.sort_values(['sort_order', 'gender', 'user_id'])
        else:
            user_details = user_details.sort_values(['sort_order', 'user_id'])
        
        # 移除臨時欄位
        user_details = user_details.drop(['temp_age_clean', 'sort_order'], axis=1)
    
    user_details = user_details.reset_index(drop=True)
    
    print(f"✅ 用戶詳細資料準備完成，包含 {len(user_details)} 位用戶")
    print(f"   - 欄位: {list(user_details.columns)}")
    
    print("✅ 人口統計分析完成")
    
    return {
        'summary': summary_df,
        'gender_distribution': gender_stats,
        'age_distribution': age_stats,
        'age_gender_crosstab': cross_tab_reset,
        'user_details': user_details
    }

def auto_filter_and_export(input_xlsx, output_xlsx):
    print(f"讀取檔案: {input_xlsx}")
    df = pd.read_excel(input_xlsx)
    
    print(f"原始資料: {len(df)} 筆記錄, {df['user_id'].nunique()} 位用戶")
    
    # 檢查 game_duration 欄位是否已經有值
    if 'game_duration' in df.columns:
        print("發現 game_duration 欄位，檢查是否有有效資料...")
        
        # 先嘗試使用現有的 game_duration 欄位
        df['game_duration_extracted'] = df['game_duration'].apply(extract_game_duration_from_direct_column)
        
        valid_game_duration_count = df['game_duration_extracted'].notna().sum()
        print(f"從 game_duration 欄位提取到 {valid_game_duration_count} 筆有效資料")
        
        # 如果 game_duration 欄位大部分是空的，則從 duration_stats_ms 提取
        if valid_game_duration_count < len(df) * 0.5:  # 如果少於50%有資料
            print("game_duration 欄位資料不足，從 duration_stats_ms 重新提取...")
            df['game_duration_from_stats'] = df['duration_stats_ms'].apply(extract_game_duration)
            
            # 合併兩個來源的資料
            df['game_duration'] = df['game_duration_extracted'].fillna(df['game_duration_from_stats'])
        else:
            df['game_duration'] = df['game_duration_extracted']
    else:
        print("未發現 game_duration 欄位，從 duration_stats_ms 提取...")
        df['game_duration'] = df['duration_stats_ms'].apply(extract_game_duration)
    
    # 檢查提取結果
    valid_duration_count = df['game_duration'].notna().sum()
    print(f"最終提取到 {valid_duration_count} 筆有效的 game_duration 資料")
    
    if valid_duration_count == 0:
        print("❌ 錯誤：沒有提取到任何有效的 game_duration 資料")
        print("請檢查 duration_stats_ms 欄位的格式")
        
        # 顯示幾個樣本供除錯
        print("\nduration_stats_ms 欄位樣本:")
        for i in range(min(3, len(df))):
            print(f"第 {i+1} 筆: {str(df.iloc[i]['duration_stats_ms'])[:200]}...")
        
        return
    
    # Step 1: 有效填寫者（扣除 attention 失敗和 responses≠52）
    print("\n開始篩選有效填寫者...")
    
    # 檢查 attention_passed 欄位
    if 'attention_passed' not in df.columns:
        print("⚠️ 警告：找不到 attention_passed 欄位，跳過 attention 檢查")
        df_valid = df.copy()
    else:
        df_valid = df[df['attention_passed'] == True]
        print(f"通過 attention 檢查: {len(df_valid)} 筆記錄")
    
    # 檢查每位用戶的 response 數量
    if 'resp_english_label' not in df.columns:
        print("⚠️ 警告：找不到 resp_english_label 欄位，跳過 response 數量檢查")
    else:
        counts = df_valid.groupby('user_id')['resp_english_label'].count()
        valid_users = counts[counts == 52].index
        df_valid = df_valid[df_valid['user_id'].isin(valid_users)]
        print(f"有 52 個 responses 的用戶: {len(valid_users)} 位")
    
    # 計算統計資料 - 每個用戶只取一個 game_duration
    print("計算每個用戶的 game_duration...")
    user_game_valid = df_valid.groupby('user_id')['game_duration'].first().dropna().sort_values()
    
    print(f"預期用戶數: {df_valid['user_id'].nunique()}")
    print(f"實際有 game_duration 的用戶數: {len(user_game_valid)}")
    print(f"每個用戶的 game_duration 範圍: {user_game_valid.min():.1f} - {user_game_valid.max():.1f} 秒")
    
    if len(user_game_valid) == 0:
        print("❌ 錯誤：沒有有效的用戶 game_duration 資料")
        return
    
    mean_v = user_game_valid.mean()
    std_v = user_game_valid.std()
    min_cut_v = mean_v - std_v
    max_cut_v = mean_v + std_v

    print_user_stats_by_user(df_valid, "有效填寫者（attention/response 過關）")
    print(f"game_duration (valid): 平均 = {mean_v:.2f} 秒，標準差 = {std_v:.2f} 秒，mean-std = {min_cut_v:.2f} 秒")
    print(f"有效用戶數: {len(user_game_valid)} (每個用戶1個 game_duration)")
    print(f"Game duration 統計: 最短 {user_game_valid.min():.1f}秒, 最長 {user_game_valid.max():.1f}秒")
    
    # 驗證：確保我們確實是每個用戶一個值
    if len(user_game_valid) != df_valid['user_id'].nunique():
        print(f"⚠️ 警告：用戶數量不匹配！預期 {df_valid['user_id'].nunique()}，實際 {len(user_game_valid)}")
    else:
        print(f"✅ 驗證通過：{len(user_game_valid)} 個用戶，每人一個 game_duration")
    print()

    # 1. 用戶個別遊戲時長圖
    plt.figure(figsize=(22,6), dpi=150)
    plt.bar(range(len(user_game_valid)), user_game_valid.values, color="deepskyblue", label=f"Valid users (N={user_game_valid.size})")
    plt.axhline(mean_v, color="orange", linestyle="-", label=f"Mean={mean_v:.1f}")
    plt.axhline(min_cut_v, color="green", linestyle="--", label=f"Mean-SD={min_cut_v:.1f}")
    plt.axhline(max_cut_v, color="red", linestyle="--", label=f"Mean+SD={max_cut_v:.1f}")
    plt.xticks(range(len(user_game_valid)), user_game_valid.index, rotation=90, fontsize=8)
    plt.ylabel("Game Duration (sec)")
    plt.title(f"Game Duration per User (Valid)\nmean={mean_v:.1f}, SD={std_v:.1f}, N={user_game_valid.size}")
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig("user_game_duration_valid.png", dpi=160)
    plt.close()
    print("✅ user_game_duration_valid.png（有效填寫者）已產生")

    # 2. 遊戲時長直方圖（含mean±SD線）
    plt.figure(figsize=(10,6), dpi=150)
    bin_width = 100
    bins = range(0, int(user_game_valid.max()) + bin_width, bin_width)
    plt.hist(user_game_valid.values, bins=bins, color="skyblue", edgecolor='black')
    plt.axvline(mean_v, color="orange", linestyle="-", label=f"Mean={mean_v:.1f}")
    plt.axvline(min_cut_v, color="green", linestyle="--", label=f"Mean-SD={min_cut_v:.1f}")
    plt.axvline(max_cut_v, color="red", linestyle="--", label=f"Mean+SD={max_cut_v:.1f}")
    plt.xlabel("Game Duration (sec)")
    plt.ylabel("User Count")
    plt.title(f"Distribution of Game Duration (Valid Users)\nmean={mean_v:.1f}, SD={std_v:.1f}, N={user_game_valid.size}")
    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig("user_game_duration_hist.png", dpi=160)
    plt.close()
    print("✅ user_game_duration_hist.png（分佈+標線）已產生")

    # 3. SD 篩選後的直方圖
    user_game_filt = user_game_valid[user_game_valid >= min_cut_v].sort_values()
    plt.figure(figsize=(10,6), dpi=150)
    bin_width = 100
    bins = range(0, int(user_game_filt.max()) + bin_width, bin_width)
    plt.hist(user_game_filt.values, bins=bins, color="royalblue", edgecolor='black')
    plt.xlabel("Game Duration (sec)")
    plt.ylabel("User Count")
    plt.title(f"Game Duration Distribution After SD Filter (N={user_game_filt.size})")
    plt.tight_layout()
    plt.savefig("user_game_duration_hist_filtered.png", dpi=160)
    plt.close()
    print("✅ user_game_duration_hist_filtered.png（SD 篩後分佈）已產生")

    # 創建人口統計分析
    print("\n🔍 生成用戶人口統計分析...")
    demographics = create_user_demographics_analysis(df_valid)
    
    if demographics is None:
        print("❌ 人口統計分析失敗，跳過相關工作表")
        # 只輸出主要數據
        with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
            df_valid.to_excel(writer, sheet_name='Cleaned_Data', index=False)
        print(f"✅ 主要數據已輸出至 {output_xlsx}")
        return
    
    # 輸出 Excel（含多個工作表）
    print(f"\n💾 準備輸出 Excel 檔案: {output_xlsx}")
    
    with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
        # 主要數據
        df_valid.to_excel(writer, sheet_name='Cleaned_Data', index=False)
        print(f"✅ 主要數據已寫入 'Cleaned_Data' 工作表")
        
        # 人口統計摘要
        demographics['summary'].to_excel(writer, sheet_name='Demographics_Summary', index=False)
        print(f"✅ 人口統計摘要已寫入 'Demographics_Summary' 工作表")
        
        # 性別分布
        demographics['gender_distribution'].to_excel(writer, sheet_name='Gender_Distribution', index=False)
        print(f"✅ 性別分布已寫入 'Gender_Distribution' 工作表")
        
        # 年齡分布（使用原始區間）
        demographics['age_distribution'].to_excel(writer, sheet_name='Age_Distribution', index=False)
        print(f"✅ 年齡分布已寫入 'Age_Distribution' 工作表")
        
        # 年齡 x 性別交叉表
        if not demographics['age_gender_crosstab'].empty:
            demographics['age_gender_crosstab'].to_excel(writer, sheet_name='Age_Gender_Crosstab', index=False)
            print(f"✅ 年齡x性別交叉表已寫入 'Age_Gender_Crosstab' 工作表")
        
        # 詳細用戶列表 - 只包含需要的欄位
        demographics['user_details'].to_excel(writer, sheet_name='User_Details', index=False)
        print(f"✅ 詳細用戶列表已寫入 'User_Details' 工作表")
        print(f"   - 包含欄位: {list(demographics['user_details'].columns)}")
    
    print(f"\n🎉 已完成資料清理和人口統計分析！")
    print(f"📊 輸出檔案：{output_xlsx}")
    print(f"📈 包含 {len(demographics['user_details'])} 位有效用戶，{len(df_valid)} 筆記錄")
    print(f"📋 Excel 工作表:")
    print(f"   - Cleaned_Data: 清理後的主要數據")
    print(f"   - Demographics_Summary: 人口統計摘要")
    print(f"   - Gender_Distribution: 性別分布")
    print(f"   - Age_Distribution: 年齡區間分布")
    print(f"   - Age_Gender_Crosstab: 年齡區間x性別交叉表")
    print(f"   - User_Details: 詳細用戶資料 (包含: {list(demographics['user_details'].columns)})")

if __name__ == "__main__":
    auto_filter_and_export(r"C:\Users\deehu\Desktop\Program\data_analysis\user_combined.xlsx", "cleaned_data_1.xlsx")