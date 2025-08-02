# ====================
# PART 1: POST ANALYSIS AND SELECTION
# Analyzes posts and identifies usable ones with balanced emotional distribution
# ====================

rm(list = ls())

# Required packages
required_packages <- c("readxl", "dplyr", "ggplot2", "gridExtra", "grid", "openxlsx", "tidyr")
for (pkg in required_packages) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    install.packages(pkg, dependencies = TRUE, quiet = TRUE)
    library(pkg, character.only = TRUE)
  } else {
    library(pkg, character.only = TRUE)
  }
}

# ====================
# Read and Process Data
# ====================

file_path <- "C:/Users/deehu/Desktop/Program/data_analysis/cleaned_data_1.xlsx"

if (!file.exists(file_path)) stop("File not found")

data <- read_excel(file_path)

clean_data <- data %>%
  filter(!is.na(resp_post_id)) %>%
  filter(!is.na(resp_label)) %>%
  filter(!grepl("attention", tolower(as.character(resp_post_id)), fixed = TRUE))

# Check what emotion labels exist in the data
unique_labels <- unique(clean_data$resp_label)

# Define possible emotion labels
target_emotions_english <- c("anger", "contempt", "disgust")
target_emotions_chinese <- c("‘Å­", "ÝpÃï", "…’º")

# Determine which set of labels to use
found_english <- sum(target_emotions_english %in% unique_labels)
found_chinese <- sum(target_emotions_chinese %in% unique_labels)

if (found_english >= found_chinese && found_english > 0) {
  target_emotions <- target_emotions_english
} else if (found_chinese > 0) {
  target_emotions <- target_emotions_chinese
} else {
  stop(paste("No matching emotion labels found. Available labels:", paste(unique_labels, collapse = ", ")))
}

analysis_data <- clean_data %>%
  filter(resp_label %in% target_emotions)

# ====================
# Chi-Square Analysis Function
# ====================

chi_square_goodness_of_fit <- function(observed_counts, expected_proportions = c(33, 33, 34)) {
  observed_counts <- as.numeric(observed_counts)
  observed_counts[is.na(observed_counts)] <- 0
  
  total_count <- sum(observed_counts)
  if (total_count == 0) return(NULL)
  
  tryCatch({
    chi_result <- chisq.test(observed_counts, p = expected_proportions / 100)
    result <- list(
      chi_square = as.numeric(chi_result$statistic),
      p_value = as.numeric(chi_result$p.value),
      significant = as.numeric(chi_result$p.value) < 0.05
    )
    return(result)
  }, error = function(e) {
    return(NULL)
  })
}

# ====================
# Run Post Analysis
# ====================

unique_posts <- sort(unique(analysis_data$resp_post_id))
results <- list()

for (post_id in unique_posts) {
  post_data <- analysis_data %>% filter(resp_post_id == post_id)
  if (nrow(post_data) == 0) next
  
  emotion_counts <- table(post_data$resp_label)
  
  # Get counts based on which emotion labels we're using
  if ("anger" %in% names(emotion_counts)) {
    contempt_count <- as.numeric(emotion_counts["contempt"][1] %||% 0)
    anger_count <- as.numeric(emotion_counts["anger"][1] %||% 0)
    disgust_count <- as.numeric(emotion_counts["disgust"][1] %||% 0)
  } else {
    contempt_count <- as.numeric(emotion_counts["ÝpÃï"][1] %||% 0)
    anger_count <- as.numeric(emotion_counts["‘Å­"][1] %||% 0)
    disgust_count <- as.numeric(emotion_counts["…’º"][1] %||% 0)
  }
  
  # Replace NA with 0
  contempt_count[is.na(contempt_count)] <- 0
  anger_count[is.na(anger_count)] <- 0
  disgust_count[is.na(disgust_count)] <- 0
  
  observed <- c(contempt_count, anger_count, disgust_count)
  total_responses <- sum(observed)
  
  if (total_responses >= 10) {
    chi_result <- chi_square_goodness_of_fit(observed)
    if (!is.null(chi_result)) {
      percentages <- round((observed / total_responses) * 100, 1)
      
      results[[as.character(post_id)]] <- list(
        post_id = post_id,
        total_labels = total_responses,
        contempt_count = contempt_count,
        anger_count = anger_count,
        disgust_count = disgust_count,
        contempt_pct = percentages[1],
        anger_pct = percentages[2],
        disgust_pct = percentages[3],
        chi_square = round(chi_result$chi_square, 2),
        p_value = round(chi_result$p_value, 3),
        significant = chi_result$significant
      )
    }
  }
}

# Convert to dataframe
if (length(results) == 0) {
  stop("No posts found with sufficient data for analysis")
}

analysis_df <- do.call(rbind, lapply(results, function(x) {
  data.frame(
    Post_ID = x$post_id,
    Total_Labels = x$total_labels,
    Contempt_Count = x$contempt_count,
    Anger_Count = x$anger_count,
    Disgust_Count = x$disgust_count,
    Contempt_Pct = x$contempt_pct,
    Anger_Pct = x$anger_pct,
    Disgust_Pct = x$disgust_pct,
    Chi_Square = x$chi_square,
    P_Value = x$p_value,
    Significant = x$significant,
    Category = ifelse(x$significant, "Excluded", "Usable"),
    stringsAsFactors = FALSE
  )
}))

# Sort by Post_ID
analysis_df <- analysis_df[order(analysis_df$Post_ID), ]

# Calculate summary statistics
total_posts <- nrow(analysis_df)
usable_posts <- sum(!analysis_df$Significant)
excluded_posts <- sum(analysis_df$Significant)

# ====================
# Create Table 1: Statistical Summary
# ====================

# Calculate statistics for each category
usable_data <- analysis_df[!analysis_df$Significant, ]
excluded_data <- analysis_df[analysis_df$Significant, ]

table1 <- data.frame(
  Category = c("Usable Posts", "Excluded Posts", "Total"),
  N = c(usable_posts, excluded_posts, total_posts),
  Percentage = c(
    paste0(round(usable_posts/total_posts*100, 1), "%"),
    paste0(round(excluded_posts/total_posts*100, 1), "%"),
    "100.0%"
  ),
  Mean_Chi_Square = c(
    ifelse(usable_posts > 0, round(mean(usable_data$Chi_Square), 2), "¡ª"),
    ifelse(excluded_posts > 0, round(mean(excluded_data$Chi_Square), 2), "¡ª"),
    round(mean(analysis_df$Chi_Square), 2)
  ),
  Mean_P_Value = c(
    ifelse(usable_posts > 0, round(mean(usable_data$P_Value), 3), "¡ª"),
    ifelse(excluded_posts > 0, round(mean(excluded_data$P_Value), 3), "¡ª"),
    round(mean(analysis_df$P_Value), 3)
  ),
  Sample_Size_Range = c(
    ifelse(usable_posts > 0, 
           paste0(min(usable_data$Total_Labels), "-", max(usable_data$Total_Labels)), "¡ª"),
    ifelse(excluded_posts > 0, 
           paste0(min(excluded_data$Total_Labels), "-", max(excluded_data$Total_Labels)), "¡ª"),
    paste0(min(analysis_df$Total_Labels), "-", max(analysis_df$Total_Labels))
  ),
  stringsAsFactors = FALSE
)

# ====================
# Create Table 2: Detailed Results for Usable Posts
# ====================

# Filter only usable posts and sort by Post_ID
usable_posts_complete <- analysis_df[!analysis_df$Significant, ] %>%
  arrange(Post_ID) %>%
  select(Post_ID, Total_Labels, Contempt_Pct, Anger_Pct, Disgust_Pct, Chi_Square, P_Value)

# Rename columns for publication (always in English)
colnames(usable_posts_complete) <- c("Post ID", "Sample Size", "Contempt %", 
                                     "Anger %", "Disgust %", "Chi Square", "P Value")

# ====================
# FIGURE 1: P-value Distribution Histogram
# ====================

# Create output directory if it doesn't exist
output_dir <- "C:/Users/deehu/Desktop/Program/data_analysis/"
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Create academic-style plot
figure1 <- ggplot(analysis_df, aes(x = P_Value, fill = Category)) +
  geom_histogram(bins = 20, alpha = 0.8, color = "black", linewidth = 0.3, 
                 boundary = 0, binwidth = 0.02) +
  geom_vline(xintercept = 0.05, linetype = "dashed", color = "red", linewidth = 0.8) +
  scale_fill_manual(values = c("Excluded" = "#808080", "Usable" = "#404040"),
                    name = "") +
  scale_x_continuous(limits = c(0, 0.40), breaks = seq(0, 0.40, 0.05),
                     labels = sprintf("%.2f", seq(0, 0.40, 0.05))) +
  scale_y_continuous(breaks = function(x) {
    max_val <- max(x)
    if (max_val <= 5) {
      seq(0, max_val, by = 1)
    } else if (max_val <= 10) {
      seq(0, max_val, by = 2)
    } else if (max_val <= 20) {
      seq(0, max_val, by = 3)
    } else {
      seq(0, max_val, by = 5)
    }
  }) +
  labs(x = "P-value", y = "Number of Posts", title = NULL) +
  theme_classic(base_size = 11) +
  theme(
    legend.position = "bottom",
    legend.text = element_text(size = 10),
    axis.text = element_text(size = 10, color = "black"),
    axis.title = element_text(size = 11, color = "black", face = "bold"),
    axis.line = element_line(color = "black", linewidth = 0.5),
    axis.ticks = element_line(color = "black", linewidth = 0.5),
    panel.background = element_rect(fill = "white"),
    plot.background = element_rect(fill = "white"),
    legend.background = element_rect(fill = "white"),
    panel.grid = element_blank()
  )

ggsave(paste0(output_dir, "Post_P_value_Distribution.png"), figure1,
       width = 6, height = 4, dpi = 300, bg = "white")

# ====================
# FIGURE 2: Post Emotion Response Distributions
# ====================

# Prepare data for the emotion distribution chart
emotion_chart_data <- analysis_df %>%
  select(Post_ID, Contempt_Pct, Anger_Pct, Disgust_Pct, Chi_Square, P_Value, Category) %>%
  tidyr::gather(key = "Emotion", value = "Percentage", Contempt_Pct, Anger_Pct, Disgust_Pct) %>%
  mutate(
    Emotion = case_when(
      Emotion == "Contempt_Pct" ~ "Contempt",
      Emotion == "Anger_Pct" ~ "Anger", 
      Emotion == "Disgust_Pct" ~ "Disgust"
    ),
    Emotion = factor(Emotion, levels = c("Contempt", "Anger", "Disgust"))
  )

# Split data into two parts: Posts 1-25 and Posts 26-50
emotion_data_part1 <- emotion_chart_data %>% filter(Post_ID <= 25)
emotion_data_part2 <- emotion_chart_data %>% filter(Post_ID >= 26)

# Function to create individual plot
create_emotion_plot <- function(data, post_range) {
  # Get usable posts for this range
  usable_posts_in_range <- analysis_df %>% 
    filter(Post_ID %in% unique(data$Post_ID), Category == "Usable") %>%
    pull(Post_ID)
  
  # Create color vector for x-axis labels
  all_posts_in_range <- unique(data$Post_ID)
  label_colors <- ifelse(all_posts_in_range %in% usable_posts_in_range, "red", "black")
  
  # Always use English labels for display regardless of data language
  ggplot(data, aes(x = factor(Post_ID), y = Percentage, fill = Emotion)) +
    geom_col(position = "dodge", width = 0.8, color = "black", size = 0.3) +
    scale_fill_manual(values = c("Contempt" = "#2E8B57", "Anger" = "#DC143C", "Disgust" = "#9370DB"),
                      name = "") +
    scale_y_continuous(limits = c(0, 100), breaks = seq(0, 100, 20),
                       labels = paste0(seq(0, 100, 20))) +
    labs(x = "Post ID", 
         y = "Response Percentage (%)",
         title = paste0("Posts ", post_range)) +
    theme_classic(base_size = 11) +
    theme(
      plot.title = element_text(size = 12, face = "bold", hjust = 0.5, margin = margin(b = 15)),
      axis.text.x = element_text(angle = 45, hjust = 1, size = 9, 
                                 color = rep(label_colors, each = 1)),
      axis.text.y = element_text(size = 9),
      axis.title = element_text(size = 10, face = "bold"),
      legend.position = "right",
      legend.text = element_text(size = 10),
      panel.grid.major.y = element_line(color = "grey90", size = 0.3),
      panel.grid.minor = element_blank(),
      axis.line = element_line(color = "black", size = 0.5),
      axis.ticks = element_line(color = "black", size = 0.3),
      plot.margin = margin(10, 10, 10, 10)
    ) +
    # Add statistics box in top-left corner
    annotation_custom(
      grob = rectGrob(gp = gpar(fill = "lightblue", col = "black", lwd = 1)),
      xmin = 0.5, xmax = 5.0, ymin = 85, ymax = 98
    ) +
    annotation_custom(
      grob = textGrob(paste0("Neutral posts: ", 
                             length(usable_posts_in_range), "/", 
                             length(all_posts_in_range), " (", 
                             round(length(usable_posts_in_range)/length(all_posts_in_range)*100, 1), "%)\n",
                             "(Red labels: p > 0.05)"),
                      gp = gpar(fontsize = 9, col = "black"),
                      hjust = 0.5, vjust = 0.5),
      xmin = 0.5, xmax = 5.0, ymin = 85, ymax = 98
    )
}

# Create both plots
plot1 <- create_emotion_plot(emotion_data_part1, "1-25")
plot2 <- create_emotion_plot(emotion_data_part2, "26-50")

# Combine plots vertically
figure2_combined <- grid.arrange(
  textGrob("Post Emotion Response Distributions with Statistical Analysis", 
           gp = gpar(fontsize = 14, fontface = "bold"), hjust = 0.5),
  plot1,
  plot2,
  heights = c(0.08, 0.46, 0.46),
  ncol = 1
)

ggsave(paste0(output_dir, "Post_Emotion_Distributions.png"), figure2_combined,
       width = 12, height = 10, dpi = 300, bg = "white")

# ====================
# Create Single Excel File with Multiple Sheets
# ====================

# Create workbook
wb <- createWorkbook()

# Sheet 1: Summary Statistics
addWorksheet(wb, "Summary_Statistics")
writeData(wb, "Summary_Statistics", "Table 1. Statistical Summary of Post Selection Results", 
          startRow = 1, startCol = 1)
writeData(wb, "Summary_Statistics", table1, startRow = 3, startCol = 1)

# Sheet 2: Usable Posts Detail
addWorksheet(wb, "Usable_Posts_Detail")
writeData(wb, "Usable_Posts_Detail", "Table 2. Detailed Analysis of All Usable Posts", 
          startRow = 1, startCol = 1)
writeData(wb, "Usable_Posts_Detail", usable_posts_complete, startRow = 3, startCol = 1)

# Sheet 3: Complete Analysis Results
addWorksheet(wb, "Complete_Analysis_Results")
writeData(wb, "Complete_Analysis_Results", "Complete Post Analysis Results", 
          startRow = 1, startCol = 1)
writeData(wb, "Complete_Analysis_Results", analysis_df, startRow = 3, startCol = 1)

# Sheet 4: Usable Post IDs
usable_post_ids <- analysis_df$Post_ID[!analysis_df$Significant]
usable_ids_df <- data.frame(Usable_Post_IDs = usable_post_ids)
addWorksheet(wb, "Usable_Post_IDs")
writeData(wb, "Usable_Post_IDs", "Usable Post IDs for Meme Analysis", 
          startRow = 1, startCol = 1)
writeData(wb, "Usable_Post_IDs", usable_ids_df, startRow = 3, startCol = 1)

excel_path <- paste0(output_dir, "post_analysis.xlsx")
saveWorkbook(wb, excel_path, overwrite = TRUE)

write.csv(analysis_df, paste0(output_dir, "Complete_Post_Analysis_Results.csv"), row.names = FALSE)