import pandas as pd
import numpy as np
from pathlib import Path
import json

INPUT  = "cleaned_data_1.xlsx"
OUTPUT = "summary.xlsx"

# ───────────────── 1. 對應欄位 ─────────────────
col_map = {
    "user"   : "user_id",
    "age"    : "age",
    "gender" : "gender",
    "meme"   : "resp_meme_name",
    "post"   : "resp_post_id",
    "rt"     : "resp_response_time_ms",
    "emo"    : "resp_english_label",
    "status" : "status",
    "email_provided" : "email_provided",
    "attention_passed" : "attention_passed",
    "participation" : "participation",
    "game_duration" : "game_duration"
}

# ───────────────── 2. 讀檔 & 基本轉換 ─────────────────
print("📊 正在讀取資料...")
df = pd.read_excel(INPUT)
df[col_map["rt"]] = pd.to_numeric(df[col_map["rt"]], errors="coerce") / 1000.0  # ms → 秒

print(f"✅ 資料讀取完成：{len(df)} 筆記錄，{df[col_map['user']].nunique()} 位使用者")

# ───────────────── 3. 建立情緒次數函數 ─────────────────
def emotion_counts(group_key: str) -> pd.DataFrame:
    """回傳 group_key × emotion 四類次數的 wide 表"""
    emo_tbl = (
        df.groupby([group_key, col_map["emo"]])
          .size()
          .unstack(col_map["emo"], fill_value=0)
          .reset_index()
    )
    # 重新命名情緒欄位
    emo_cols = {}
    for col in emo_tbl.columns:
        if col in ["anger", "contempt", "disgust", "others"]:
            emo_cols[col] = f"cnt_{col}"
    emo_tbl = emo_tbl.rename(columns=emo_cols)
    return emo_tbl

# ───────────────── 4. 使用者層級的詳細分析 ─────────────────
def user_detailed_analysis():
    """使用者層級的詳細統計"""
    user_stats = df.groupby(col_map["user"]).agg({
        col_map["age"]: "first",
        col_map["gender"]: "first", 
        col_map["status"]: "first",
        col_map["email_provided"]: "first",
        col_map["participation"]: "first",
        col_map["game_duration"]: "first",
        col_map["rt"]: ["count", "mean", "median", "std", "min", "max"],
        col_map["emo"]: lambda x: x.value_counts().to_dict()
    }).reset_index()
    
    # 平整化多層級欄位名稱
    user_stats.columns = [
        col_map["user"], "age", "gender", "status", "email_provided", 
        "participation", "game_duration_sec",
        "total_responses", "avg_response_time", "median_response_time", 
        "std_response_time", "min_response_time", "max_response_time",
        "emotion_breakdown"
    ]
    
    # 展開情緒統計
    emotion_df = pd.json_normalize(user_stats['emotion_breakdown'])
    emotion_df = emotion_df.fillna(0).astype(int)
    emotion_df.columns = [f"cnt_{col}" for col in emotion_df.columns]
    
    user_stats = pd.concat([user_stats.drop('emotion_breakdown', axis=1), emotion_df], axis=1)
    
    return user_stats

# ───────────────── 5. 年齡×性別的詳細交叉分析 ─────────────────
def age_gender_detailed():
    """年齡×性別的詳細交叉分析"""
    # 基本人數統計
    demo_crosstab = pd.crosstab(
        df[col_map["age"]], 
        df[col_map["gender"]], 
        aggfunc='nunique', 
        values=df[col_map["user"]]
    ).fillna(0).reset_index()
    
    # 平均反應時間
    rt_crosstab = df.groupby([col_map["age"], col_map["gender"]])[col_map["rt"]].mean().unstack(fill_value=0).reset_index()
    rt_crosstab.columns = [col_map["age"]] + [f"avg_rt_{col}" for col in rt_crosstab.columns[1:]]
    
    # 平均遊戲時長
    duration_crosstab = df.groupby([col_map["age"], col_map["gender"]])[col_map["game_duration"]].mean().unstack(fill_value=0).reset_index()
    duration_crosstab.columns = [col_map["age"]] + [f"avg_game_duration_{col}" for col in duration_crosstab.columns[1:]]
    
    # 合併所有統計
    age_gender_summary = demo_crosstab.merge(rt_crosstab, on=col_map["age"]).merge(duration_crosstab, on=col_map["age"])
    
    return age_gender_summary

# ───────────────── 6. 情緒分佈的詳細分析 ─────────────────
def emotion_detailed_analysis():
    """各群體的情緒分佈詳細分析"""
    
    # 年齡層的情緒分佈
    age_emotion = df.groupby([col_map["age"], col_map["emo"]]).size().unstack(fill_value=0)
    age_emotion_pct = age_emotion.div(age_emotion.sum(axis=1), axis=0).round(3)
    age_emotion_pct.columns = [f"pct_{col}" for col in age_emotion_pct.columns]
    age_emotion_combined = pd.concat([age_emotion, age_emotion_pct], axis=1).reset_index()
    
    # 性別的情緒分佈
    gender_emotion = df.groupby([col_map["gender"], col_map["emo"]]).size().unstack(fill_value=0)
    gender_emotion_pct = gender_emotion.div(gender_emotion.sum(axis=1), axis=0).round(3)
    gender_emotion_pct.columns = [f"pct_{col}" for col in gender_emotion_pct.columns]
    gender_emotion_combined = pd.concat([gender_emotion, gender_emotion_pct], axis=1).reset_index()
    
    return age_emotion_combined, gender_emotion_combined

# ───────────────── 7. 反應時間分析 ─────────────────
def response_time_analysis():
    """反應時間的詳細分析"""
    
    # 各年齡層的反應時間統計
    age_rt_stats = df.groupby(col_map["age"])[col_map["rt"]].agg([
        'count', 'mean', 'median', 'std', 'min', 'max',
        lambda x: x.quantile(0.25),
        lambda x: x.quantile(0.75)
    ]).round(3).reset_index()
    age_rt_stats.columns = [col_map["age"], 'count', 'mean_rt', 'median_rt', 'std_rt', 
                           'min_rt', 'max_rt', 'q25_rt', 'q75_rt']
    
    # 各性別的反應時間統計
    gender_rt_stats = df.groupby(col_map["gender"])[col_map["rt"]].agg([
        'count', 'mean', 'median', 'std', 'min', 'max',
        lambda x: x.quantile(0.25),
        lambda x: x.quantile(0.75)
    ]).round(3).reset_index()
    gender_rt_stats.columns = [col_map["gender"], 'count', 'mean_rt', 'median_rt', 'std_rt',
                              'min_rt', 'max_rt', 'q25_rt', 'q75_rt']
    
    # 各情緒的反應時間統計
    emotion_rt_stats = df.groupby(col_map["emo"])[col_map["rt"]].agg([
        'count', 'mean', 'median', 'std', 'min', 'max'
    ]).round(3).reset_index()
    emotion_rt_stats.columns = [col_map["emo"], 'count', 'mean_rt', 'median_rt', 'std_rt',
                               'min_rt', 'max_rt']
    
    return age_rt_stats, gender_rt_stats, emotion_rt_stats

# ───────────────── 8. Meme 表現分析 ─────────────────
def meme_performance_analysis():
    """各 Meme 的詳細表現分析"""
    
    meme_stats = df.groupby(col_map["meme"]).agg({
        col_map["user"]: "nunique",
        col_map["rt"]: ["count", "mean", "median", "std"],
        col_map["emo"]: lambda x: x.value_counts().to_dict()
    }).reset_index()
    
    # 平整化欄位名稱
    meme_stats.columns = [col_map["meme"], "unique_users", "total_responses", 
                         "avg_rt", "median_rt", "std_rt", "emotion_breakdown"]
    
    # 展開情緒分佈
    emotion_df = pd.json_normalize(meme_stats['emotion_breakdown'])
    emotion_df = emotion_df.fillna(0).astype(int)
    emotion_df.columns = [f"cnt_{col}" for col in emotion_df.columns]
    
    meme_detailed = pd.concat([meme_stats.drop('emotion_breakdown', axis=1), emotion_df], axis=1)
    
    # 計算情緒比例
    emotion_cols = [col for col in emotion_df.columns]
    total_responses = meme_detailed['total_responses']
    for col in emotion_cols:
        pct_col = col.replace('cnt_', 'pct_')
        meme_detailed[pct_col] = (meme_detailed[col] / total_responses).round(3)
    
    return meme_detailed

# ───────────────── 9. 完成度分析 ─────────────────
def completion_analysis():
    """使用者完成度和參與度分析"""
    
    completion_stats = df.groupby([col_map["status"], col_map["email_provided"], col_map["participation"]]).agg({
        col_map["user"]: "nunique",
        col_map["game_duration"]: ["mean", "median", "std"]
    }).reset_index()
    
    completion_stats.columns = ["status", "email_provided", "participation", 
                               "user_count", "avg_game_duration", "median_game_duration", "std_game_duration"]
    
    return completion_stats

# ───────────────── 10. 執行所有分析並輸出 ─────────────────
print("🔄 開始執行詳細分析...")

# 原始的基本分析（保留）
def build_demo_summary(group_key: str) -> pd.DataFrame:
    basic = (
        df.groupby(group_key)
          .agg(users        = (col_map["user"], "nunique"),
               avg_resp_sec = (col_map["rt"],   "mean"))
          .reset_index()
    )
    age_gender = (
        df.groupby([group_key, col_map["age"], col_map["gender"]])
          .size()
          .unstack([col_map["age"], col_map["gender"]], fill_value=0)
          .reset_index()
    )
    return basic.merge(age_gender, on=group_key)

# 執行各種分析
print("📈 分析使用者詳細資料...")
user_detailed = user_detailed_analysis()

print("📊 分析年齡性別交叉統計...")
age_gender_detailed = age_gender_detailed()

print("😊 分析情緒分佈...")
age_emotion, gender_emotion = emotion_detailed_analysis()

print("⏱️ 分析反應時間...")
age_rt, gender_rt, emotion_rt = response_time_analysis()

print("🎭 分析 Meme 表現...")
meme_detailed = meme_performance_analysis()

print("✅ 分析完成度...")
completion_stats = completion_analysis()

# 原始分析（保持相容性）
meme_demo = build_demo_summary(col_map["meme"])
meme_emo = emotion_counts(col_map["meme"])
meme_sum = meme_demo.merge(meme_emo, on=col_map["meme"])

post_demo = build_demo_summary(col_map["post"])
post_emo = emotion_counts(col_map["post"])
post_sum = post_demo.merge(post_emo, on=col_map["post"])

age_break = (df.groupby([col_map["age"], col_map["meme"]])
               .size().unstack(col_map["meme"], fill_value=0).reset_index())
gender_break = (df.groupby([col_map["gender"], col_map["meme"]])
                  .size().unstack(col_map["meme"], fill_value=0).reset_index())

# ───────────────── 11. 輸出到 Excel ─────────────────
print("💾 正在輸出結果...")

with pd.ExcelWriter(OUTPUT, engine="xlsxwriter") as w:
    # === 原始表格（向後相容） ===
    meme_sum.to_excel(w, index=False, sheet_name="meme_summary")
    post_sum.to_excel(w, index=False, sheet_name="post_summary")
    age_break.to_excel(w, index=False, sheet_name="age_breakdown")
    gender_break.to_excel(w, index=False, sheet_name="gender_breakdown")
    
    # === 新增的詳細分析表格 ===
    # 使用者詳細分析
    user_detailed.to_excel(w, index=False, sheet_name="user_detailed_stats")
    
    # 人口統計詳細交叉分析
    age_gender_detailed.to_excel(w, index=False, sheet_name="age_gender_detailed")
    
    # 情緒分佈分析
    age_emotion.to_excel(w, index=False, sheet_name="age_emotion_distribution")
    gender_emotion.to_excel(w, index=False, sheet_name="gender_emotion_distribution")
    
    # 反應時間分析
    age_rt.to_excel(w, index=False, sheet_name="age_response_time")
    gender_rt.to_excel(w, index=False, sheet_name="gender_response_time")
    emotion_rt.to_excel(w, index=False, sheet_name="emotion_response_time")
    
    # Meme 詳細表現分析
    meme_detailed.to_excel(w, index=False, sheet_name="meme_detailed_performance")
    
    # 完成度分析
    completion_stats.to_excel(w, index=False, sheet_name="completion_analysis")
    
    # === 額外的深度分析 ===
    # 年齡層內的性別分佈細節
    age_gender_count = pd.crosstab(
        df[col_map["age"]], 
        df[col_map["gender"]], 
        values=df[col_map["user"]], 
        aggfunc='nunique'
    ).fillna(0).reset_index()
    age_gender_count.to_excel(w, index=False, sheet_name="age_gender_user_count")
    
    # 每個使用者的情緒標註總結
    user_emotion_summary = df.groupby(col_map["user"])[col_map["emo"]].value_counts().unstack(fill_value=0).reset_index()
    user_emotion_summary.to_excel(w, index=False, sheet_name="user_emotion_summary")
    
    # 反應時間區間分析
    df['rt_bin'] = pd.cut(df[col_map["rt"]], bins=[0, 1, 2, 5, 10, float('inf')], 
                         labels=['<1s', '1-2s', '2-5s', '5-10s', '>10s'])
    rt_bin_analysis = pd.crosstab(df['rt_bin'], df[col_map["emo"]]).reset_index()
    rt_bin_analysis.to_excel(w, index=False, sheet_name="response_time_bins")

print(f"✅ 完成！已輸出詳細分析到 {Path(OUTPUT).resolve()}")
print(f"📋 總共包含 {len(pd.ExcelFile(OUTPUT).sheet_names)} 個工作表：")

# 列出所有工作表
sheet_descriptions = {
    "meme_summary": "Meme 基本統計（原始）",
    "post_summary": "Post 基本統計（原始）", 
    "age_breakdown": "年齡分佈（原始）",
    "gender_breakdown": "性別分佈（原始）",
    "user_detailed_stats": "使用者詳細統計（新）",
    "age_gender_detailed": "年齡×性別詳細交叉分析（新）",
    "age_emotion_distribution": "年齡層情緒分佈（新）",
    "gender_emotion_distribution": "性別情緒分佈（新）",
    "age_response_time": "年齡層反應時間統計（新）",
    "gender_response_time": "性別反應時間統計（新）",
    "emotion_response_time": "各情緒反應時間統計（新）",
    "meme_detailed_performance": "Meme 詳細表現分析（新）",
    "completion_analysis": "完成度和參與度分析（新）",
    "age_gender_user_count": "年齡×性別使用者人數統計（新）",
    "user_emotion_summary": "每位使用者情緒標註統計（新）",
    "response_time_bins": "反應時間區間分析（新）"
}

for sheet, desc in sheet_descriptions.items():
    print(f"  📄 {sheet}: {desc}")

print("\n🎉 所有分析完成！")