# Meme 情緒分布比較分析 - 完整版
# 比較乾淨 post 與所有 post 下的 meme 情緒分布

# ================================
# 0. 清理環境並載入套件
# ================================
rm(list = ls())  # 清理環境

# 載入必要的套件
library(readxl)
library(dplyr)
library(ggplot2)
library(tidyr)
library(gridExtra)
library(openxlsx)  # 用於寫入 Excel 檔案

# 設定輸出目錄
output_dir <- "C:/Users/deehu/Desktop/Program/data_analysis/output_cleanedpostmeme_vs_allpostmeme"

# 檢查並創建輸出目錄
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
  cat("創建輸出目錄:", output_dir, "\n")
} else {
  cat("輸出目錄已存在:", output_dir, "\n")
}

# 設定工作目錄為輸出目錄
setwd(output_dir)
cat("當前工作目錄:", getwd(), "\n")

# 設定乾淨的 post IDs
clean_post_ids <- c(8, 13, 20, 25, 27, 40, 44, 47)

# ================================
# 1. 讀取和準備數據
# ================================

# 讀取數據 (請修改為你的檔案路徑)
data <- read_excel("C:/Users/deehu/Desktop/Program/data_analysis/cleaned_data_1.xlsx", sheet = "Cleaned_Data")

cat("原始數據筆數:", nrow(data), "\n")

# 過濾有效數據（排除 others 和注意力檢查）
valid_data <- data %>%
  filter(!is.na(resp_english_label),
         resp_english_label != "others",
         !grepl("attention_check", resp_image_path, fixed = TRUE))

cat("過濾後有效數據筆數:", nrow(valid_data), "\n")

# 分離乾淨 post 數據
clean_post_data <- valid_data %>%
  filter(resp_post_id %in% clean_post_ids)

cat("乾淨 post 數據筆數:", nrow(clean_post_data), "\n")

# ================================
# 2. 計算 meme 情緒分布的函數
# ================================

calculate_meme_distribution <- function(data_subset) {
  meme_dist <- data_subset %>%
    filter(resp_english_label %in% c("contempt", "anger", "disgust")) %>%
    group_by(resp_meme_name, resp_english_label) %>%
    summarise(count = n(), .groups = "drop") %>%
    group_by(resp_meme_name) %>%
    mutate(total = sum(count),
           percentage = count / total) %>%
    select(resp_meme_name, resp_english_label, percentage, total) %>%
    pivot_wider(names_from = resp_english_label, 
                values_from = percentage, 
                values_fill = 0) %>%
    # 確保所有三種情緒都存在
    mutate(contempt = ifelse(is.na(contempt), 0, contempt),
           anger = ifelse(is.na(anger), 0, anger),
           disgust = ifelse(is.na(disgust), 0, disgust))
  
  return(meme_dist)
}

# ================================
# 3. 計算兩種分布
# ================================

# 乾淨 post 的分布
clean_distribution <- calculate_meme_distribution(clean_post_data)
cat("乾淨 post 下的 meme 數量:", nrow(clean_distribution), "\n")

# 所有 post 的分布
all_distribution <- calculate_meme_distribution(valid_data)
cat("所有 post 下的 meme 數量:", nrow(all_distribution), "\n")

# ================================
# 4. 找出共同的 memes 並計算相似度
# ================================

# 合併兩個分布，只保留共同的 memes
comparison_data <- inner_join(clean_distribution, all_distribution, 
                              by = "resp_meme_name", 
                              suffix = c("_clean", "_all"))

cat("共同 meme 數量:", nrow(comparison_data), "\n")

# 計算 Cosine Similarity 的函數
calculate_cosine_similarity <- function(vec1, vec2) {
  dot_product <- sum(vec1 * vec2)
  norm1 <- sqrt(sum(vec1^2))
  norm2 <- sqrt(sum(vec2^2))
  
  if (norm1 == 0 || norm2 == 0) return(0)
  return(dot_product / (norm1 * norm2))
}

# 計算每個 meme 的 cosine similarity
comparison_data$cosine_similarity <- apply(comparison_data, 1, function(row) {
  clean_vec <- c(as.numeric(row["contempt_clean"]), 
                 as.numeric(row["anger_clean"]), 
                 as.numeric(row["disgust_clean"]))
  all_vec <- c(as.numeric(row["contempt_all"]), 
               as.numeric(row["anger_all"]), 
               as.numeric(row["disgust_all"]))
  
  calculate_cosine_similarity(clean_vec, all_vec)
})

# ================================
# 5. 統計摘要
# ================================

cat("\n=== 分析結果摘要 ===\n")
cat("共同 meme 數量:", nrow(comparison_data), "\n")
cat("平均 Cosine Similarity:", round(mean(comparison_data$cosine_similarity), 3), "\n")
cat("Cosine Similarity 標準差:", round(sd(comparison_data$cosine_similarity), 3), "\n")
cat("最小 Cosine Similarity:", round(min(comparison_data$cosine_similarity), 3), "\n")
cat("最大 Cosine Similarity:", round(max(comparison_data$cosine_similarity), 3), "\n")

# 相似度分類
high_similarity <- sum(comparison_data$cosine_similarity > 0.9)
medium_similarity <- sum(comparison_data$cosine_similarity > 0.6 & comparison_data$cosine_similarity <= 0.9)
low_similarity <- sum(comparison_data$cosine_similarity <= 0.6)

cat("\n=== 相似度分類 ===\n")
cat("高相似度 (>0.9):", high_similarity, "個 memes (", round(high_similarity/nrow(comparison_data)*100, 1), "%)\n")
cat("中等相似度 (0.6-0.9):", medium_similarity, "個 memes (", round(medium_similarity/nrow(comparison_data)*100, 1), "%)\n")
cat("低相似度 (<=0.6):", low_similarity, "個 memes (", round(low_similarity/nrow(comparison_data)*100, 1), "%)\n")

# ================================
# 6. 視覺化
# ================================

# 6.1 Cosine Similarity 分布直方圖
p1 <- ggplot(comparison_data, aes(x = cosine_similarity)) +
  geom_histogram(bins = 20, fill = "steelblue", color = "white", alpha = 0.7) +
  geom_vline(xintercept = mean(comparison_data$cosine_similarity), 
             color = "red", linetype = "dashed", linewidth = 1) +
  labs(title = "Cosine Similarity 分布",
       subtitle = paste("平均值:", round(mean(comparison_data$cosine_similarity), 3)),
       x = "Cosine Similarity",
       y = "Meme 數量") +
  theme_minimal() +
  theme(plot.title = element_text(hjust = 0.5, size = 14, face = "bold"))

print(p1)

# 6.2 相似度分類長條圖
similarity_categories <- data.frame(
  Category = c("高相似度\n(>0.9)", "中等相似度\n(0.6-0.9)", "低相似度\n(≤0.6)"),
  Count = c(high_similarity, medium_similarity, low_similarity),
  Percentage = c(high_similarity, medium_similarity, low_similarity) / nrow(comparison_data) * 100
)

p2 <- ggplot(similarity_categories, aes(x = Category, y = Count, fill = Category)) +
  geom_bar(stat = "identity", alpha = 0.9) +
  geom_text(aes(label = paste0(Count, "\n(", round(Percentage, 1), "%)")), 
            vjust = -0.5, size = 4, fontface = "bold") +
  scale_fill_manual(values = c("#2ecc71", "#f39c12", "#e74c3c")) +
  labs(title = "Meme 相似度分類",
       x = "相似度類別",
       y = "Meme 數量") +
  theme_minimal() +
  theme(plot.title = element_text(hjust = 0.5, size = 14, face = "bold"),
        legend.position = "none")

print(p2)

# 儲存圖表
ggsave("cosine_similarity_distribution.png", p1, width = 10, height = 6, dpi = 300)
ggsave("similarity_categories.png", p2, width = 8, height = 6, dpi = 300)

# ================================
# 7. 合併所有結果到單一 Excel 檔案
# ================================

# 7.1 準備所有數據表
detailed_comparison <- comparison_data %>%
  arrange(desc(cosine_similarity)) %>%
  mutate(
    similarity_category = case_when(
      cosine_similarity > 0.9~ "High",
      cosine_similarity > 0.6 ~ "Medium",
      TRUE ~ "Low"
    )
  ) %>%
  select(resp_meme_name, 
         contempt_clean, anger_clean, disgust_clean, total_clean,
         contempt_all, anger_all, disgust_all, total_all,
         cosine_similarity, similarity_category)

# 7.2 推薦系統用的完整 meme 情緒資料庫（使用所有 post 數據）
meme_emotion_database <- all_distribution %>%
  select(resp_meme_name, contempt, anger, disgust, total) %>%
  rename(meme_name = resp_meme_name) %>%
  arrange(meme_name)

# 7.3 高穩定性 memes（相似度 > 0.9）
high_stability_memes <- comparison_data %>%
  filter(cosine_similarity > 0.9) %>%
  select(resp_meme_name, contempt_all, anger_all, disgust_all, total_all, cosine_similarity) %>%
  rename(meme_name = resp_meme_name,
         contempt = contempt_all,
         anger = anger_all,
         disgust = disgust_all,
         total = total_all) %>%
  arrange(desc(cosine_similarity))

# 7.4 摘要統計
summary_stats <- data.frame(
  Metric = c("Total Common Memes", "Mean Cosine Similarity", "SD Cosine Similarity",
             "Min Cosine Similarity", "Max Cosine Similarity",
             "High Similarity Count (>0.9)", "Medium Similarity Count (0.6-0.9)", 
             "Low Similarity Count (<=0.6)", "High Similarity Percentage"),
  Value = c(nrow(comparison_data), 
            round(mean(comparison_data$cosine_similarity), 3),
            round(sd(comparison_data$cosine_similarity), 3),
            round(min(comparison_data$cosine_similarity), 3),
            round(max(comparison_data$cosine_similarity), 3),
            high_similarity, medium_similarity, low_similarity,
            round(high_similarity/nrow(comparison_data)*100, 1)),
  Description = c(
    "共同分析的 meme 總數",
    "平均餘弦相似度",
    "餘弦相似度標準差", 
    "最小餘弦相似度",
    "最大餘弦相似度",
    "高穩定性 meme 數量",
    "中等穩定性 meme 數量",
    "低穩定性 meme 數量", 
    "高穩定性 meme 百分比"
  )
)

# 7.5 創建 Excel 工作簿並添加工作表
wb <- createWorkbook()

# 添加工作表
addWorksheet(wb, "Summary", tabColour = "red")
addWorksheet(wb, "Meme_Database_All", tabColour = "blue") 
addWorksheet(wb, "Meme_Database_Stable", tabColour = "green")
addWorksheet(wb, "Detailed_Comparison", tabColour = "orange")

# 寫入數據
writeData(wb, "Summary", summary_stats, startRow = 1)
writeData(wb, "Meme_Database_All", meme_emotion_database, startRow = 1) 
writeData(wb, "Meme_Database_Stable", high_stability_memes, startRow = 1)
writeData(wb, "Detailed_Comparison", detailed_comparison, startRow = 1)

# 設定標題樣式
title_style <- createStyle(fontSize = 14, textDecoration = "bold", 
                           fgFill = "#DCE6F1", border = "TopBottomLeftRight")

# 應用樣式到標題行
addStyle(wb, "Summary", title_style, rows = 1, cols = 1:3, gridExpand = TRUE)
addStyle(wb, "Meme_Database_All", title_style, rows = 1, cols = 1:5, gridExpand = TRUE)
addStyle(wb, "Meme_Database_Stable", title_style, rows = 1, cols = 1:6, gridExpand = TRUE) 
addStyle(wb, "Detailed_Comparison", title_style, rows = 1, cols = 1:11, gridExpand = TRUE)

# 自動調整欄寬
setColWidths(wb, "Summary", cols = 1:3, widths = "auto")
setColWidths(wb, "Meme_Database_All", cols = 1:5, widths = "auto")
setColWidths(wb, "Meme_Database_Stable", cols = 1:6, widths = "auto")
setColWidths(wb, "Detailed_Comparison", cols = 1:11, widths = "auto")

# 儲存 Excel 檔案
excel_filename <- "meme_analysis_complete_results.xlsx"
saveWorkbook(wb, excel_filename, overwrite = TRUE)

cat("\n=== Excel 檔案已生成 ===\n")
cat("檔案名稱:", excel_filename, "\n")
cat("包含工作表:\n")
cat("1. Summary - 分析摘要統計\n")
cat("2. Meme_Database_All - 推薦系統資料庫(所有 memes)\n") 
cat("3. Meme_Database_Stable - 推薦系統資料庫(高穩定性 memes)\n")
cat("4. Detailed_Comparison - 詳細比較分析\n")

# ================================
# 8. 顯示生成的檔案和預覽數據
# ================================

cat("\n=== 檔案生成完成 ===\n")
cat("工作目錄:", getwd(), "\n")
cat("生成的檔案:\n")
cat("1. meme_similarity_comparison.csv - 完整比較分析結果\n")
cat("2. meme_emotion_database_all.csv - 推薦系統資料庫(所有 memes)\n")
cat("3. meme_emotion_database_stable.csv - 推薦系統資料庫(高穩定性 memes)\n")
cat("4. analysis_summary.csv - 分析摘要統計\n")

# 檢查檔案是否存在
generated_files <- c("meme_similarity_comparison.csv", 
                     "meme_emotion_database_all.csv",
                     "meme_emotion_database_stable.csv", 
                     "analysis_summary.csv")

for (file in generated_files) {
  if (file.exists(file)) {
    cat("✓", file, "- 生成成功\n")
  } else {
    cat("✗", file, "- 生成失敗\n")
  }
}

# ================================
# 9. 預覽關鍵數據
# ================================

cat("\n=== 推薦系統資料庫預覽 (所有 memes) ===\n")
print(head(meme_emotion_database, 10))

cat("\n=== 高穩定性 Memes 預覽 ===\n")
print(head(high_stability_memes, 10))

cat("\n=== 相似度最低的 5 個 Memes ===\n")
print(head(detailed_comparison %>% arrange(cosine_similarity), 5))

# ================================
# 10. 決策建議
# ================================

cat("\n=== 決策建議 ===\n")
if (high_similarity/nrow(comparison_data) > 0.9) {
  cat("🎯 建議使用 'meme_emotion_database_all.csv' (所有 memes)\n")
  cat("原因: ", round(high_similarity/nrow(comparison_data)*100, 1), "% 的 memes 具有高穩定性 (>0.9)\n")
  cat("平均相似度: ", round(mean(comparison_data$cosine_similarity), 3), " (非常穩定)\n")
} else if (high_similarity/nrow(comparison_data) > 0.6) {
  cat("⚠️ 建議使用 'meme_emotion_database_stable.csv' (高穩定性 memes)\n")
  cat("原因: 只有 ", round(high_similarity/nrow(comparison_data)*100, 1), "% 的 memes 具有高穩定性\n")
} else {
  cat("❌ 建議重新檢視數據品質\n")
  cat("原因: 高穩定性 memes 比例過低 (", round(high_similarity/nrow(comparison_data)*100, 1), "%)\n")
}

cat("\n=== 分析完成 ===\n")