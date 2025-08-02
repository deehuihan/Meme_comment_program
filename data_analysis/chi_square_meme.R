# PART 2: MULTI-LABEL MEME ANALYSIS - ALLOWING EMOTION OVERLAP

rm(list = ls())

required_packages <- c("readxl", "dplyr", "ggplot2", "gridExtra", "grid", "openxlsx", "tidyr", "purrr")
for (pkg in required_packages) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    install.packages(pkg, dependencies = TRUE, quiet = TRUE)
    library(pkg, character.only = TRUE)
  } else {
    library(pkg, character.only = TRUE)
  }
}

file_path <- "C:/Users/deehu/Desktop/Program/data_analysis/cleaned_data_1.xlsx"
complete_analysis_file <- "C:/Users/deehu/Desktop/Program/data_analysis/Complete_Post_Analysis_Results.csv"
output_dir <- "C:/Users/deehu/Desktop/Program/data_analysis/"

if (!file.exists(file_path)) stop("Data file not found")
if (!file.exists(complete_analysis_file)) stop("Complete_Post_Analysis_Results.csv not found")

complete_results <- read.csv(complete_analysis_file)
usable_post_ids <- complete_results$Post_ID[complete_results$Significant == FALSE]

data <- read_excel(file_path)

clean_data <- data %>%
  filter(!is.na(resp_post_id)) %>%
  filter(!is.na(resp_label)) %>%
  filter(!grepl("attention", tolower(as.character(resp_post_id)), fixed = TRUE))

unique_labels <- unique(clean_data$resp_label)

target_emotions_english <- c("anger", "contempt", "disgust")
target_emotions_chinese <- c("憤怒", "輕蔑", "厭惡")

found_english <- sum(target_emotions_english %in% unique_labels)
found_chinese <- sum(target_emotions_chinese %in% unique_labels)

if (found_english >= found_chinese && found_english > 0) {
  target_emotions <- target_emotions_english
} else if (found_chinese > 0) {
  target_emotions <- target_emotions_chinese
} else {
  stop(paste("No matching emotion labels found. Available labels:", paste(unique_labels, collapse = ", ")))
}

usable_posts_data <- clean_data %>%
  filter(resp_post_id %in% usable_post_ids) %>%
  filter(resp_label %in% target_emotions)

if (nrow(usable_posts_data) == 0) {
  stop("No data found")
}

meme_columns <- names(usable_posts_data)[grepl("meme", names(usable_posts_data), ignore.case = TRUE)]
if (length(meme_columns) == 0) {
  stop("No meme columns found")
}
meme_col <- meme_columns[1]

# Chi-square function (for reference)
chi_square_goodness_of_fit <- function(observed_counts, expected_proportions = c(33, 33, 34)) {
  observed_counts <- as.numeric(observed_counts)
  observed_counts[is.na(observed_counts)] <- 0
  total_count <- sum(observed_counts)
  if (total_count == 0) return(NULL)
  tryCatch({
    chi_result <- chisq.test(observed_counts, p = expected_proportions / 100)
    list(
      chi_square = as.numeric(chi_result$statistic),
      p_value = as.numeric(chi_result$p.value),
      significant = as.numeric(chi_result$p.value) < 0.10
    )
  }, error = function(e) NULL)
}

# Individual emotion tests (PRIMARY METHOD - no Bonferroni correction for more inclusive results)
test_individual_emotions <- function(contempt_count, anger_count, disgust_count, total_responses) {
  expected_proportion <- 1/3  # 33.33%
  
  contempt_pvalue <- tryCatch({
    if (total_responses >= 10) {
      binom.test(contempt_count, total_responses, p = expected_proportion, 
                 alternative = "greater")$p.value
    } else {
      1
    }
  }, error = function(e) 1)
  
  anger_pvalue <- tryCatch({
    if (total_responses >= 10) {
      binom.test(anger_count, total_responses, p = expected_proportion, 
                 alternative = "greater")$p.value
    } else {
      1
    }
  }, error = function(e) 1)
  
  disgust_pvalue <- tryCatch({
    if (total_responses >= 10) {
      binom.test(disgust_count, total_responses, p = expected_proportion, 
                 alternative = "greater")$p.value
    } else {
      1
    }
  }, error = function(e) 1)
  
  # Use standard alpha = 0.05 (no correction for more inclusive results)
  alpha <- 0.05
  contempt_significant <- contempt_pvalue <= alpha
  anger_significant <- anger_pvalue <= alpha
  disgust_significant <- disgust_pvalue <= alpha
  
  significant_emotions_count <- sum(contempt_significant, anger_significant, disgust_significant)
  
  return(list(
    contempt_pvalue = round(contempt_pvalue, 4),
    anger_pvalue = round(anger_pvalue, 4),
    disgust_pvalue = round(disgust_pvalue, 4),
    contempt_significant = contempt_significant,
    anger_significant = anger_significant,
    disgust_significant = disgust_significant,
    significant_emotions_count = significant_emotions_count
  ))
}

meme_emotion_summary <- usable_posts_data %>%
  group_by(!!sym(meme_col), resp_label) %>%
  summarise(count = n(), .groups = "drop") %>%
  group_by(!!sym(meme_col)) %>%
  mutate(total = sum(count), percentage = round((count / total) * 100, 1)) %>%
  ungroup()

unique_memes <- sort(unique(usable_posts_data[[meme_col]]))
meme_results <- list()

for (meme_id in unique_memes) {
  meme_data <- usable_posts_data %>% filter(!!sym(meme_col) == meme_id)
  if (nrow(meme_data) == 0) next
  
  emotion_counts <- table(meme_data$resp_label)
  
  if ("anger" %in% names(emotion_counts)) {
    contempt_count <- as.numeric(emotion_counts["contempt"][1] %||% 0)
    anger_count <- as.numeric(emotion_counts["anger"][1] %||% 0)
    disgust_count <- as.numeric(emotion_counts["disgust"][1] %||% 0)
  } else {
    contempt_count <- as.numeric(emotion_counts["輕蔑"][1] %||% 0)
    anger_count <- as.numeric(emotion_counts["憤怒"][1] %||% 0)
    disgust_count <- as.numeric(emotion_counts["厭惡"][1] %||% 0)
  }
  
  contempt_count[is.na(contempt_count)] <- 0
  anger_count[is.na(anger_count)] <- 0
  disgust_count[is.na(disgust_count)] <- 0
  
  observed <- c(contempt_count, anger_count, disgust_count)
  total_responses <- sum(observed)
  
  if (total_responses >= 10) {
    chi_result <- chi_square_goodness_of_fit(observed)
    individual_tests <- test_individual_emotions(contempt_count, anger_count, disgust_count, total_responses)
    
    if (!is.null(chi_result)) {
      percentages <- round((observed / total_responses) * 100, 1)
      max_idx <- which.max(observed)
      dominant_emotion <- c("Contempt", "Anger", "Disgust")[max_idx]
      dominant_pct <- percentages[max_idx]
      
      significant_emotions_list <- c()
      if (individual_tests$contempt_significant) significant_emotions_list <- c(significant_emotions_list, "Contempt")
      if (individual_tests$anger_significant) significant_emotions_list <- c(significant_emotions_list, "Anger")
      if (individual_tests$disgust_significant) significant_emotions_list <- c(significant_emotions_list, "Disgust")
      
      has_significant_emotions <- length(significant_emotions_list) > 0
      
      meme_results[[as.character(meme_id)]] <- list(
        meme_id = meme_id, total_labels = total_responses,
        contempt_count = contempt_count, anger_count = anger_count, disgust_count = disgust_count,
        contempt_pct = percentages[1], anger_pct = percentages[2], disgust_pct = percentages[3],
        
        chi_square = round(chi_result$chi_square, 2), 
        p_value = round(chi_result$p_value, 3),
        overall_significant = chi_result$significant,
        
        contempt_pvalue = individual_tests$contempt_pvalue,
        anger_pvalue = individual_tests$anger_pvalue,
        disgust_pvalue = individual_tests$disgust_pvalue,
        contempt_significant = individual_tests$contempt_significant,
        anger_significant = individual_tests$anger_significant,
        disgust_significant = individual_tests$disgust_significant,
        
        dominant_emotion = dominant_emotion,
        dominant_pct = dominant_pct,
        significant_emotions = if(length(significant_emotions_list) > 0) paste(significant_emotions_list, collapse = ", ") else "None",
        significant_emotions_count = individual_tests$significant_emotions_count,
        has_any_significant_emotion = has_significant_emotions
      )
    }
  }
}

meme_analysis_df <- do.call(rbind, lapply(meme_results, function(x) {
  data.frame(
    Meme_ID = x$meme_id, 
    Total_Labels = x$total_labels,
    Contempt_Count = x$contempt_count, 
    Anger_Count = x$anger_count, 
    Disgust_Count = x$disgust_count,
    Contempt_Pct = x$contempt_pct, 
    Anger_Pct = x$anger_pct, 
    Disgust_Pct = x$disgust_pct,
    
    Chi_Square = x$chi_square, 
    P_Value = x$p_value, 
    Overall_Significant = x$overall_significant,
    
    Contempt_PValue = x$contempt_pvalue,
    Anger_PValue = x$anger_pvalue,
    Disgust_PValue = x$disgust_pvalue,
    Contempt_Significant = x$contempt_significant,
    Anger_Significant = x$anger_significant,
    Disgust_Significant = x$disgust_significant,
    
    Dominant_Emotion = x$dominant_emotion,
    Dominant_Pct = x$dominant_pct,
    Significant_Emotions = x$significant_emotions,
    Significant_Emotions_Count = x$significant_emotions_count,
    Has_Any_Significant_Emotion = x$has_any_significant_emotion,
    
    Category = ifelse(x$has_any_significant_emotion, "Emotionally Biased", "Emotionally Neutral"),
    stringsAsFactors = FALSE
  )
}))

if (is.null(meme_analysis_df) || nrow(meme_analysis_df) == 0) {
  stop("No meme data found")
}

meme_analysis_df <- meme_analysis_df[order(meme_analysis_df$Meme_ID), ]

total_memes <- nrow(meme_analysis_df)
biased_memes <- sum(meme_analysis_df$Has_Any_Significant_Emotion)
neutral_memes <- sum(!meme_analysis_df$Has_Any_Significant_Emotion)

# Create multi-label classifications
contempt_memes <- meme_analysis_df[meme_analysis_df$Contempt_Significant == TRUE, ]
anger_memes <- meme_analysis_df[meme_analysis_df$Anger_Significant == TRUE, ]
disgust_memes <- meme_analysis_df[meme_analysis_df$Disgust_Significant == TRUE, ]

unique_meme_ids <- unique(meme_emotion_summary[[meme_col]])

if (is.character(unique_meme_ids)) {
  all_memes <- sort(unique_meme_ids)
  mid_point <- ceiling(length(all_memes) / 2)
  
  meme_part1_ids <- all_memes[1:mid_point]
  meme_part2_ids <- all_memes[(mid_point + 1):length(all_memes)]
  
  meme_data_part1 <- meme_emotion_summary %>% filter(!!sym(meme_col) %in% meme_part1_ids)
  meme_data_part2 <- meme_emotion_summary %>% filter(!!sym(meme_col) %in% meme_part2_ids)
} else {
  meme_data_part1 <- meme_emotion_summary %>% filter(!!sym(meme_col) >= 1, !!sym(meme_col) <= 25)
  meme_data_part2 <- meme_emotion_summary %>% filter(!!sym(meme_col) >= 26, !!sym(meme_col) <= 50)
}

# Enhanced visualization with multi-emotion highlighting
create_multi_emotion_plot <- function(data, meme_range, meme_column, meme_analysis_df) {
  if (nrow(data) == 0) {
    return(ggplot() +
             annotate("text", x = 0.5, y = 0.5, label = paste("No data available for", meme_range),
                      size = 5, hjust = 0.5, vjust = 0.5) +
             labs(title = paste0("Memes ", meme_range)) +
             theme_void() +
             theme(plot.title = element_text(size = 12, face = "bold", hjust = 0.5)))
  }
  
  memes_in_range <- unique(data[[meme_column]])
  analysis_in_range <- meme_analysis_df[meme_analysis_df$Meme_ID %in% memes_in_range, ]
  total_memes_range <- nrow(analysis_in_range)
  biased_memes_range <- sum(analysis_in_range$Has_Any_Significant_Emotion, na.rm = TRUE)
  biased_percentage <- ifelse(total_memes_range > 0, round(biased_memes_range/total_memes_range*100, 1), 0)
  
  if ("anger" %in% unique(data$resp_label)) {
    color_values <- c("anger" = "#DC143C", "contempt" = "#2E8B57", "disgust" = "#9370DB")
    label_names <- c("anger" = "Anger", "contempt" = "Contempt", "disgust" = "Disgust")
    emotion_mapping <- c("Anger" = "anger", "Contempt" = "contempt", "Disgust" = "disgust")
  } else {
    color_values <- c("憤怒" = "#DC143C", "輕蔑" = "#2E8B57", "厭惡" = "#9370DB")
    label_names <- c("憤怒" = "Anger", "輕蔑" = "Contempt", "厭惡" = "Disgust")
    emotion_mapping <- c("Anger" = "憤怒", "Contempt" = "輕蔑", "Disgust" = "厭惡")
  }
  
  # Enhanced highlighting for ALL significant emotions (not just dominant)
  data$is_significant_emotion <- FALSE
  
  for (i in 1:nrow(data)) {
    meme_id <- data[[meme_column]][i]
    meme_row <- analysis_in_range[analysis_in_range$Meme_ID == meme_id, ]
    
    if (nrow(meme_row) > 0) {
      current_emotion_label <- data$resp_label[i]
      
      if (current_emotion_label == emotion_mapping["Contempt"] && meme_row$Contempt_Significant) {
        data$is_significant_emotion[i] <- TRUE
      } else if (current_emotion_label == emotion_mapping["Anger"] && meme_row$Anger_Significant) {
        data$is_significant_emotion[i] <- TRUE
      } else if (current_emotion_label == emotion_mapping["Disgust"] && meme_row$Disgust_Significant) {
        data$is_significant_emotion[i] <- TRUE
      }
    }
  }
  
  p <- ggplot(data, aes(x = factor(!!sym(meme_column)), y = percentage, fill = resp_label)) +
    geom_col(position = "dodge", width = 0.7, 
             aes(color = ifelse(is_significant_emotion, "#FFD700", "black"),
                 size = ifelse(is_significant_emotion, 1.0, 0.3))) +
    scale_fill_manual(values = color_values, name = "Emotion", labels = label_names) +
    scale_color_identity() +
    scale_size_identity() +
    scale_y_continuous(limits = c(0, 100), breaks = seq(0, 100, 20)) +
    labs(x = "Meme ID", y = "Response Percentage (%)", 
         title = paste0("Memes ", meme_range, " - Multi-Label Emotion Analysis")) +
    theme_classic(base_size = 11) +
    theme(
      plot.title = element_text(size = 12, face = "bold", hjust = 0.5, margin = margin(b = 15)),
      axis.text.x = element_text(angle = 45, hjust = 1, size = 9),
      axis.text.y = element_text(size = 9),
      axis.title = element_text(size = 10, face = "bold"),
      legend.position = "right",
      legend.text = element_text(size = 10),
      panel.grid.major.y = element_line(color = "grey90", size = 0.3),
      panel.grid.minor = element_blank(),
      plot.margin = margin(10, 10, 10, 10)
    )
  
  p <- p + 
    annotation_custom(
      grob = rectGrob(gp = gpar(fill = "lightblue", col = "black", lwd = 1)),
      xmin = 0.5, xmax = 5.0, ymin = 80, ymax = 100
    ) +
    annotate("text", x = 2.5, y = 90,
             label = paste0("Biased memes: ", biased_memes_range, "/", total_memes_range, 
                            " (", biased_percentage, "%)\n",
                            "Gold borders: Significant emotions (p ≤ 0.05)\n",
                            "Multi-label classification allowed"),
             size = 3, hjust = 0.5, vjust = 0.5, fontface = "bold")
  
  # Color significant meme IDs
  significant_memes <- analysis_in_range[analysis_in_range$Has_Any_Significant_Emotion == TRUE, ]
  if (total_memes_range > 0 && nrow(significant_memes) > 0) {
    meme_id_colors <- rep("black", length(memes_in_range))
    names(meme_id_colors) <- as.character(sort(memes_in_range))
    
    for (sig_meme in significant_memes$Meme_ID) {
      if (as.character(sig_meme) %in% names(meme_id_colors)) {
        meme_id_colors[as.character(sig_meme)] <- "red"
      }
    }
    
    p <- p + theme(axis.text.x = element_text(angle = 45, hjust = 1, size = 9,
                                              colour = meme_id_colors[as.character(sort(memes_in_range))]))
  }
  
  return(p)
}

multi_plot1 <- create_multi_emotion_plot(meme_data_part1, "1-25", meme_col, meme_analysis_df)
multi_plot2 <- create_multi_emotion_plot(meme_data_part2, "26-50", meme_col, meme_analysis_df)

figure_multi <- grid.arrange(
  textGrob("Multi-Label Meme Emotion Analysis: Overlapping Emotion Classification", 
           gp = gpar(fontsize = 14, fontface = "bold"), hjust = 0.5),
  multi_plot1, multi_plot2,
  heights = c(0.08, 0.46, 0.46), ncol = 1
)

ggsave(paste0(output_dir, "Multi_Label_Meme_Emotion_Analysis.png"), figure_multi,
       width = 12, height = 10, dpi = 300, bg = "white")

figure_pvalue <- ggplot(meme_analysis_df, aes(x = P_Value, fill = Category)) +
  geom_histogram(bins = 15, alpha = 0.8, color = "black", linewidth = 0.3, 
                 boundary = 0, binwidth = 0.03) +
  geom_vline(xintercept = 0.05, linetype = "dashed", color = "red", linewidth = 0.8) +
  scale_fill_manual(values = c("Emotionally Biased" = "#FF6B6B", "Emotionally Neutral" = "#4ECDC4"), 
                    name = "Multi-Label\nClassification") +
  scale_x_continuous(limits = c(0, 0.50), breaks = seq(0, 0.50, 0.05),
                     labels = sprintf("%.2f", seq(0, 0.50, 0.05))) +
  labs(x = "Chi-square P-value", y = "Number of Memes", 
       title = "P-value Distribution - Multi-Label Classification",
       subtitle = "Classification based on Individual Tests (p ≤ 0.05)") +
  theme_classic(base_size = 11) +
  theme(
    plot.title = element_text(size = 12, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 10, hjust = 0.5, color = "darkgray"),
    legend.position = "bottom", legend.text = element_text(size = 10),
    axis.text = element_text(size = 10, color = "black"),
    axis.title = element_text(size = 11, color = "black", face = "bold")
  )

ggsave(paste0(output_dir, "Multi_Label_P_value_Distribution.png"), figure_pvalue,
       width = 8, height = 6, dpi = 300, bg = "white")

# Enhanced multi-label three-block visualization
create_multi_label_three_block <- function(meme_analysis_df, output_dir) {
  contempt_memes <- meme_analysis_df[meme_analysis_df$Contempt_Significant == TRUE, ]
  anger_memes <- meme_analysis_df[meme_analysis_df$Anger_Significant == TRUE, ]
  disgust_memes <- meme_analysis_df[meme_analysis_df$Disgust_Significant == TRUE, ]
  
  if (nrow(contempt_memes) == 0 && nrow(anger_memes) == 0 && nrow(disgust_memes) == 0) {
    return(NULL)
  }
  
  emotion_colors <- c("Anger" = "#E53E3E", "Contempt" = "#38A169", "Disgust" = "#805AD5")
  bg_colors <- c("Anger" = "#FED7D7", "Contempt" = "#C6F6D5", "Disgust" = "#E9D8FD")
  
  all_meme_names <- unique(c(as.character(contempt_memes$Meme_ID), 
                             as.character(anger_memes$Meme_ID), 
                             as.character(disgust_memes$Meme_ID)))
  max_name_length <- max(nchar(all_meme_names))
  
  block_width <- max(12, max_name_length * 0.25)
  block_height <- block_width * 1.618
  block_spacing <- block_width * 0.4
  
  total_width <- 3 * block_width + 2 * block_spacing
  center_x_contempt <- -total_width/2 + block_width/2
  center_x_anger <- 0
  center_x_disgust <- total_width/2 - block_width/2
  center_y <- 0
  
  arrange_memes_multi <- function(meme_df, center_x, emotion_name, emotion_color, bg_color, all_analysis_df) {
    if (nrow(meme_df) == 0) {
      return(data.frame(
        Meme_Name = character(0), x = numeric(0), y = numeric(0),
        Emotion = character(0), Color = character(0), BG_Color = character(0),
        Multi_Emotion = logical(0), stringsAsFactors = FALSE
      ))
    }
    
    n_memes <- nrow(meme_df)
    line_height <- 1.8
    header_height <- 3.5
    padding <- 2.5
    content_area_height <- block_height - header_height - padding
    
    if (n_memes == 1) {
      start_y <- 0
      actual_line_height <- 0
    } else {
      total_text_height <- (n_memes - 1) * line_height
      if (total_text_height <= content_area_height) {
        start_y <- total_text_height / 2
        actual_line_height <- line_height
      } else {
        actual_line_height <- max(1.2, content_area_height / (n_memes - 1))
        start_y <- content_area_height / 2
      }
    }
    
    positions <- data.frame(
      Meme_Name = as.character(meme_df$Meme_ID),
      x = rep(center_x, n_memes),
      y = start_y - (0:(n_memes-1)) * actual_line_height,
      Emotion = rep(emotion_name, n_memes),
      Color = rep(emotion_color, n_memes),
      BG_Color = rep(bg_color, n_memes),
      Multi_Emotion = meme_df$Significant_Emotions_Count > 1,
      stringsAsFactors = FALSE
    )
    
    return(positions)
  }
  
  contempt_positions <- arrange_memes_multi(contempt_memes, center_x_contempt, "CONTEMPT", 
                                            emotion_colors["Contempt"], bg_colors["Contempt"], meme_analysis_df)
  anger_positions <- arrange_memes_multi(anger_memes, center_x_anger, "ANGER", 
                                         emotion_colors["Anger"], bg_colors["Anger"], meme_analysis_df)
  disgust_positions <- arrange_memes_multi(disgust_memes, center_x_disgust, "DISGUST", 
                                           emotion_colors["Disgust"], bg_colors["Disgust"], meme_analysis_df)
  
  all_positions <- rbind(contempt_positions, anger_positions, disgust_positions)
  
  # Calculate overlaps
  contempt_overlap <- sum(contempt_memes$Significant_Emotions_Count > 1)
  anger_overlap <- sum(anger_memes$Significant_Emotions_Count > 1)
  disgust_overlap <- sum(disgust_memes$Significant_Emotions_Count > 1)
  
  blocks_data <- data.frame(
    Emotion = c("CONTEMPT", "ANGER", "DISGUST"),
    x_center = c(center_x_contempt, center_x_anger, center_x_disgust),
    y_center = rep(center_y, 3),
    Color = c(emotion_colors["Contempt"], emotion_colors["Anger"], emotion_colors["Disgust"]),
    BG_Color = c(bg_colors["Contempt"], bg_colors["Anger"], bg_colors["Disgust"]),
    Count = c(nrow(contempt_memes), nrow(anger_memes), nrow(disgust_memes)),
    Overlap_Count = c(contempt_overlap, anger_overlap, disgust_overlap),
    stringsAsFactors = FALSE
  )
  
  p <- ggplot() +
    geom_rect(data = blocks_data,
              aes(xmin = x_center - block_width/2, xmax = x_center + block_width/2,
                  ymin = y_center - block_height/2, ymax = y_center + block_height/2,
                  fill = BG_Color),
              alpha = 0.7, color = "white", size = 2.5) +
    
    geom_rect(data = blocks_data,
              aes(xmin = x_center - block_width/2, xmax = x_center + block_width/2,
                  ymin = y_center - block_height/2, ymax = y_center + block_height/2),
              fill = NA, color = "#2D3748", size = 2, alpha = 0.9) +
    
    geom_text(data = blocks_data,
              aes(x = x_center, y = block_height/2 - 1.8, 
                  label = Emotion, color = Color),
              size = 9, fontface = "bold", hjust = 0.5, vjust = 0.5) +
    
    geom_text(data = blocks_data,
              aes(x = x_center, y = block_height/2 - 3.2, 
                  label = paste0("(", Count, " memes, ", Overlap_Count, " overlaps)"),
                  color = Color),
              size = 4.5, hjust = 0.5, vjust = 0.5, alpha = 0.8) +
    
    geom_text(data = all_positions,
              aes(x = x, y = y, 
                  label = ifelse(Multi_Emotion, paste0(Meme_Name, "*"), Meme_Name),
                  color = Color),
              size = 4.5, fontface = ifelse(all_positions$Multi_Emotion, "bold", "plain"),
              hjust = 0.5, vjust = 0.5) +
    
    scale_fill_identity() +
    scale_color_identity() +
    
    coord_fixed(ratio = 1) +
    xlim(-(total_width/2 + block_width*0.35), (total_width/2 + block_width*0.35)) +
    ylim(-(block_height/2 + block_height*0.4), (block_height/2 + block_height*0.45)) +
    
    labs(title = "Multi-Label Meme Emotion Classification",
         subtitle = paste0("Memes can appear in multiple emotion categories (Individual Tests p ≤ 0.05)\n",
                           "* indicates memes with overlapping emotions | Total unique memes: ", 
                           length(unique(all_positions$Meme_Name)))) +
    
    theme_void() +
    theme(
      plot.title = element_text(size = 26, face = "bold", hjust = 0.5,
                                color = "#1A202C", margin = margin(b = 10)),
      plot.subtitle = element_text(size = 13, hjust = 0.5, color = "#4A5568",
                                   margin = margin(b = 35), lineheight = 1.4),
      plot.background = element_rect(fill = "#FAFAFA", color = NA),
      panel.background = element_rect(fill = "#FAFAFA", color = NA),
      plot.margin = margin(45, 45, 35, 45)
    )
  
  footer_y <- -(block_height/2 + block_height*0.28)
  p <- p + 
    annotate("text", x = 0, y = footer_y, 
             label = "Multi-label classification allows memes to belong to multiple emotion categories",
             size = 4.5, hjust = 0.5, vjust = 0.5,
             color = "#718096", fontface = "italic")
  
  ggsave(paste0(output_dir, "Multi_Label_Three_Block_Distribution.png"), p,
         width = 24, height = 16, dpi = 300, bg = "#FAFAFA")
  
  return(list(plot = p, positions = all_positions, summary = blocks_data))
}

if (biased_memes > 0) {
  multi_three_block <- create_multi_label_three_block(meme_analysis_df, output_dir)
}

# Create comprehensive summary data
meme_bias_summary <- data.frame(
  Category = c("Emotionally Biased Memes", "Emotionally Neutral Memes", "Total"),
  N = c(biased_memes, neutral_memes, total_memes),
  Percentage = c(paste0(round(biased_memes/total_memes*100, 1), "%"),
                 paste0(round(neutral_memes/total_memes*100, 1), "%"), "100.0%"),
  Mean_Chi_Square = c(
    ifelse(biased_memes > 0, round(mean(meme_analysis_df$Chi_Square[meme_analysis_df$Has_Any_Significant_Emotion]), 2), "—"),
    ifelse(neutral_memes > 0, round(mean(meme_analysis_df$Chi_Square[!meme_analysis_df$Has_Any_Significant_Emotion]), 2), "—"),
    round(mean(meme_analysis_df$Chi_Square), 2)
  ),
  Mean_P_Value = c(
    ifelse(biased_memes > 0, round(mean(meme_analysis_df$P_Value[meme_analysis_df$Has_Any_Significant_Emotion]), 3), "—"),
    ifelse(neutral_memes > 0, round(mean(meme_analysis_df$P_Value[!meme_analysis_df$Has_Any_Significant_Emotion]), 3), "—"),
    round(mean(meme_analysis_df$P_Value), 3)
  ),
  stringsAsFactors = FALSE
)

# Multi-label specific summaries
multi_label_summary <- data.frame(
  Emotion = c("Contempt", "Anger", "Disgust"),
  Significant_Memes = c(nrow(contempt_memes), nrow(anger_memes), nrow(disgust_memes)),
  Percentage_of_Total = c(
    round(nrow(contempt_memes)/total_memes*100, 1),
    round(nrow(anger_memes)/total_memes*100, 1),
    round(nrow(disgust_memes)/total_memes*100, 1)
  ),
  Overlapping_Memes = c(
    sum(contempt_memes$Significant_Emotions_Count > 1),
    sum(anger_memes$Significant_Emotions_Count > 1),
    sum(disgust_memes$Significant_Emotions_Count > 1)
  ),
  stringsAsFactors = FALSE
)

overlap_analysis <- meme_analysis_df %>%
  filter(Has_Any_Significant_Emotion == TRUE) %>%
  mutate(
    Overlap_Type = case_when(
      Significant_Emotions_Count == 1 ~ "Single Emotion",
      Significant_Emotions_Count == 2 ~ "Two Emotions", 
      Significant_Emotions_Count == 3 ~ "All Three Emotions",
      TRUE ~ "Unknown"
    )
  ) %>%
  count(Overlap_Type) %>%
  mutate(Percentage = round(n/sum(n)*100, 1))

meme_complete_summary <- meme_emotion_summary %>%
  pivot_wider(names_from = resp_label, values_from = c(count, percentage),
              names_sep = "_", values_fill = 0)

if (biased_memes > 0) {
  biased_memes_detailed <- meme_analysis_df[meme_analysis_df$Has_Any_Significant_Emotion, ] %>%
    select(Meme_ID, Total_Labels, Contempt_Pct, Anger_Pct, Disgust_Pct, 
           Dominant_Emotion, Dominant_Pct, Significant_Emotions, 
           Significant_Emotions_Count, Chi_Square, P_Value)
  colnames(biased_memes_detailed) <- c("Meme ID", "Sample Size", "Contempt %", 
                                       "Anger %", "Disgust %", "Dominant Emotion",
                                       "Dominant %", "Significant Emotions", 
                                       "Significant Count", "χ²", "p-value")
}

# Create comprehensive Excel file
wb_analysis <- createWorkbook()

# Multi-Label Summary
addWorksheet(wb_analysis, "Multi_Label_Summary")
writeData(wb_analysis, "Multi_Label_Summary", "Multi-Label Meme Emotion Analysis Summary", 
          startRow = 1, startCol = 1)
writeData(wb_analysis, "Multi_Label_Summary", meme_bias_summary, startRow = 3, startCol = 1)
writeData(wb_analysis, "Multi_Label_Summary", "Emotion-Specific Counts", startRow = 8, startCol = 1)
writeData(wb_analysis, "Multi_Label_Summary", multi_label_summary, startRow = 10, startCol = 1)

# Complete Analysis
addWorksheet(wb_analysis, "Complete_Analysis")
writeData(wb_analysis, "Complete_Analysis", "Complete Multi-Label Meme Analysis", 
          startRow = 1, startCol = 1)
writeData(wb_analysis, "Complete_Analysis", meme_analysis_df, startRow = 3, startCol = 1)

# Individual Emotion Categories
addWorksheet(wb_analysis, "Contempt_Memes")
writeData(wb_analysis, "Contempt_Memes", 
          paste0("Memes with Significant Contempt (", nrow(contempt_memes), " memes)"), 
          startRow = 1, startCol = 1)
if (nrow(contempt_memes) > 0) {
  writeData(wb_analysis, "Contempt_Memes", contempt_memes, startRow = 3, startCol = 1)
}

addWorksheet(wb_analysis, "Anger_Memes")
writeData(wb_analysis, "Anger_Memes", 
          paste0("Memes with Significant Anger (", nrow(anger_memes), " memes)"), 
          startRow = 1, startCol = 1)
if (nrow(anger_memes) > 0) {
  writeData(wb_analysis, "Anger_Memes", anger_memes, startRow = 3, startCol = 1)
}

addWorksheet(wb_analysis, "Disgust_Memes")
writeData(wb_analysis, "Disgust_Memes", 
          paste0("Memes with Significant Disgust (", nrow(disgust_memes), " memes)"), 
          startRow = 1, startCol = 1)
if (nrow(disgust_memes) > 0) {
  writeData(wb_analysis, "Disgust_Memes", disgust_memes, startRow = 3, startCol = 1)
}

# Overlap Analysis
addWorksheet(wb_analysis, "Overlap_Analysis")
writeData(wb_analysis, "Overlap_Analysis", "Emotion Overlap Analysis", 
          startRow = 1, startCol = 1)
writeData(wb_analysis, "Overlap_Analysis", overlap_analysis, startRow = 3, startCol = 1)

# Emotion Distribution
addWorksheet(wb_analysis, "Emotion_Distribution")
writeData(wb_analysis, "Emotion_Distribution", "Meme Emotion Distribution Data", 
          startRow = 1, startCol = 1)
writeData(wb_analysis, "Emotion_Distribution", meme_complete_summary, startRow = 3, startCol = 1)

# Biased Memes Details
if (biased_memes > 0) {
  addWorksheet(wb_analysis, "Biased_Memes_Details")
  writeData(wb_analysis, "Biased_Memes_Details", "All Emotionally Biased Memes (Multi-Label)", 
            startRow = 1, startCol = 1)
  writeData(wb_analysis, "Biased_Memes_Details", biased_memes_detailed, startRow = 3, startCol = 1)
}

saveWorkbook(wb_analysis, paste0(output_dir, "multi_label_meme_analysis.xlsx"), overwrite = TRUE)

# Also update original file name for compatibility
saveWorkbook(wb_analysis, paste0(output_dir, "meme_analysis.xlsx"), overwrite = TRUE)

# ============================================================================
# COUNT-BASED MULTI-EMOTION CLASSIFICATION
# 基於 Count 相等的多情緒分類法（加在 multi_label_meme_analysis 之後）
# ============================================================================

# ====================
# METHOD 4: COUNT-BASED EMOTION CLASSIFICATION
# ====================

# Create count-based classification
count_based_classification <- meme_analysis_df %>%
  mutate(
    # 找出最高的 count
    Max_Count = pmax(Contempt_Count, Anger_Count, Disgust_Count),
    
    # 找出有多少情緒達到最高 count
    Emotions_At_Max = (Contempt_Count == Max_Count) + 
      (Anger_Count == Max_Count) + 
      (Disgust_Count == Max_Count),
    
    # 識別所有達到最高 count 的情緒
    Count_Based_Emotions = pmap_chr(
      list(Contempt_Count, Anger_Count, Disgust_Count, Max_Count),
      function(c_count, a_count, d_count, max_count) {
        emotions <- c()
        if (c_count == max_count) emotions <- c(emotions, paste0("Contempt(", c_count, ")"))
        if (a_count == max_count) emotions <- c(emotions, paste0("Anger(", a_count, ")"))
        if (d_count == max_count) emotions <- c(emotions, paste0("Disgust(", d_count, ")"))
        
        return(paste(emotions, collapse = ", "))
      }
    ),
    
    # 分類類型
    Count_Classification_Type = case_when(
      Emotions_At_Max == 1 ~ "Single_Dominant",
      Emotions_At_Max == 2 ~ "Dual_Dominant", 
      Emotions_At_Max == 3 ~ "Triple_Tie",
      TRUE ~ "Unknown"
    ),
    
    # 為每種情緒判斷是否為 dominant
    Contempt_Is_Dominant = Contempt_Count == Max_Count,
    Anger_Is_Dominant = Anger_Count == Max_Count,
    Disgust_Is_Dominant = Disgust_Count == Max_Count
  )

# 為每種情緒創建基於 count 的分類列表
contempt_count_based <- count_based_classification %>% 
  filter(Contempt_Is_Dominant == TRUE) %>% 
  arrange(desc(Contempt_Count), desc(Contempt_Pct))

anger_count_based <- count_based_classification %>% 
  filter(Anger_Is_Dominant == TRUE) %>% 
  arrange(desc(Anger_Count), desc(Anger_Pct))

disgust_count_based <- count_based_classification %>% 
  filter(Disgust_Is_Dominant == TRUE) %>% 
  arrange(desc(Disgust_Count), desc(Disgust_Pct))

# ====================
# COUNT-BASED SUMMARY ANALYSIS
# ====================

# 計算各類型的分布
count_type_summary <- count_based_classification %>%
  count(Count_Classification_Type) %>%
  mutate(Percentage = round(n/sum(n)*100, 1))

# 各情緒的 count-based 統計
count_emotion_summary <- data.frame(
  Emotion = c("Contempt", "Anger", "Disgust"),
  Dominant_Count = c(nrow(contempt_count_based), nrow(anger_count_based), nrow(disgust_count_based)),
  Percentage_of_Total = c(
    round(nrow(contempt_count_based)/total_memes*100, 1),
    round(nrow(anger_count_based)/total_memes*100, 1),
    round(nrow(disgust_count_based)/total_memes*100, 1)
  ),
  Avg_Count = c(
    ifelse(nrow(contempt_count_based) > 0, round(mean(contempt_count_based$Contempt_Count), 1), 0),
    ifelse(nrow(anger_count_based) > 0, round(mean(anger_count_based$Anger_Count), 1), 0),
    ifelse(nrow(disgust_count_based) > 0, round(mean(disgust_count_based$Disgust_Count), 1), 0)
  ),
  Avg_Percentage = c(
    ifelse(nrow(contempt_count_based) > 0, round(mean(contempt_count_based$Contempt_Pct), 1), 0),
    ifelse(nrow(anger_count_based) > 0, round(mean(anger_count_based$Anger_Pct), 1), 0),
    ifelse(nrow(disgust_count_based) > 0, round(mean(disgust_count_based$Disgust_Pct), 1), 0)
  ),
  stringsAsFactors = FALSE
)

# 多情緒 memes 分析
multi_emotion_count_analysis <- count_based_classification %>%
  filter(Count_Classification_Type %in% c("Dual_Dominant", "Triple_Tie")) %>%
  select(Meme_ID, Total_Labels, Contempt_Count, Anger_Count, Disgust_Count,
         Contempt_Pct, Anger_Pct, Disgust_Pct, Count_Based_Emotions, 
         Count_Classification_Type, Emotions_At_Max) %>%
  arrange(desc(Emotions_At_Max), desc(Total_Labels))

# ====================
# COUNT-BASED THREE-BLOCK VISUALIZATION
# ====================

create_count_based_three_block <- function(count_classification_df, output_dir) {
  
  contempt_cb <- count_classification_df %>% filter(Contempt_Is_Dominant == TRUE)
  anger_cb <- count_classification_df %>% filter(Anger_Is_Dominant == TRUE)
  disgust_cb <- count_classification_df %>% filter(Disgust_Is_Dominant == TRUE)
  
  if (nrow(contempt_cb) == 0 && nrow(anger_cb) == 0 && nrow(disgust_cb) == 0) {
    return(NULL)
  }
  
  emotion_colors <- c("Anger" = "#E53E3E", "Contempt" = "#38A169", "Disgust" = "#805AD5")
  bg_colors <- c("Anger" = "#FED7D7", "Contempt" = "#C6F6D5", "Disgust" = "#E9D8FD")
  
  all_meme_names <- unique(c(as.character(contempt_cb$Meme_ID), 
                             as.character(anger_cb$Meme_ID), 
                             as.character(disgust_cb$Meme_ID)))
  max_name_length <- max(nchar(all_meme_names))
  
  block_width <- max(12, max_name_length * 0.25)
  block_height <- block_width * 1.618
  block_spacing <- block_width * 0.4
  
  total_width <- 3 * block_width + 2 * block_spacing
  center_x_contempt <- -total_width/2 + block_width/2
  center_x_anger <- 0
  center_x_disgust <- total_width/2 - block_width/2
  center_y <- 0
  
  arrange_memes_count_based <- function(meme_df, center_x, emotion_name, emotion_color, bg_color) {
    if (nrow(meme_df) == 0) {
      return(data.frame(
        Meme_Name = character(0), x = numeric(0), y = numeric(0),
        Emotion = character(0), Color = character(0), BG_Color = character(0),
        Multi_Emotion = logical(0), Emotion_Count = numeric(0),
        stringsAsFactors = FALSE
      ))
    }
    
    n_memes <- nrow(meme_df)
    line_height <- 1.8
    header_height <- 3.5
    padding <- 2.5
    content_area_height <- block_height - header_height - padding
    
    if (n_memes == 1) {
      start_y <- 0
      actual_line_height <- 0
    } else {
      total_text_height <- (n_memes - 1) * line_height
      if (total_text_height <= content_area_height) {
        start_y <- total_text_height / 2
        actual_line_height <- line_height
      } else {
        actual_line_height <- max(1.2, content_area_height / (n_memes - 1))
        start_y <- content_area_height / 2
      }
    }
    
    positions <- data.frame(
      Meme_Name = as.character(meme_df$Meme_ID),
      x = rep(center_x, n_memes),
      y = start_y - (0:(n_memes-1)) * actual_line_height,
      Emotion = rep(emotion_name, n_memes),
      Color = rep(emotion_color, n_memes),
      BG_Color = rep(bg_color, n_memes),
      Multi_Emotion = meme_df$Emotions_At_Max > 1,
      Emotion_Count = meme_df$Emotions_At_Max,
      stringsAsFactors = FALSE
    )
    
    return(positions)
  }
  
  contempt_positions_cb <- arrange_memes_count_based(contempt_cb, center_x_contempt, "CONTEMPT", 
                                                     emotion_colors["Contempt"], bg_colors["Contempt"])
  anger_positions_cb <- arrange_memes_count_based(anger_cb, center_x_anger, "ANGER", 
                                                  emotion_colors["Anger"], bg_colors["Anger"])
  disgust_positions_cb <- arrange_memes_count_based(disgust_cb, center_x_disgust, "DISGUST", 
                                                    emotion_colors["Disgust"], bg_colors["Disgust"])
  
  all_positions_cb <- rbind(contempt_positions_cb, anger_positions_cb, disgust_positions_cb)
  
  # 計算各情緒的多重情緒數量
  contempt_multi <- sum(contempt_cb$Emotions_At_Max > 1)
  anger_multi <- sum(anger_cb$Emotions_At_Max > 1)
  disgust_multi <- sum(disgust_cb$Emotions_At_Max > 1)
  
  blocks_data_cb <- data.frame(
    Emotion = c("CONTEMPT", "ANGER", "DISGUST"),
    x_center = c(center_x_contempt, center_x_anger, center_x_disgust),
    y_center = rep(center_y, 3),
    Color = c(emotion_colors["Contempt"], emotion_colors["Anger"], emotion_colors["Disgust"]),
    BG_Color = c(bg_colors["Contempt"], bg_colors["Anger"], bg_colors["Disgust"]),
    Count = c(nrow(contempt_cb), nrow(anger_cb), nrow(disgust_cb)),
    Multi_Count = c(contempt_multi, anger_multi, disgust_multi),
    stringsAsFactors = FALSE
  )
  
  p <- ggplot() +
    geom_rect(data = blocks_data_cb,
              aes(xmin = x_center - block_width/2, xmax = x_center + block_width/2,
                  ymin = y_center - block_height/2, ymax = y_center + block_height/2,
                  fill = BG_Color),
              alpha = 0.7, color = "white", size = 2.5) +
    
    geom_rect(data = blocks_data_cb,
              aes(xmin = x_center - block_width/2, xmax = x_center + block_width/2,
                  ymin = y_center - block_height/2, ymax = y_center + block_height/2),
              fill = NA, color = "#2D3748", size = 2, alpha = 0.9) +
    
    geom_text(data = blocks_data_cb,
              aes(x = x_center, y = block_height/2 - 1.8, 
                  label = Emotion, color = Color),
              size = 9, fontface = "bold", hjust = 0.5, vjust = 0.5) +
    
    geom_text(data = blocks_data_cb,
              aes(x = x_center, y = block_height/2 - 3.2, 
                  label = paste0("(", Count, " memes, ", Multi_Count, " shared)"),
                  color = Color),
              size = 4.5, hjust = 0.5, vjust = 0.5, alpha = 0.8) +
    
    geom_text(data = all_positions_cb,
              aes(x = x, y = y, 
                  label = ifelse(Multi_Emotion, paste0(Meme_Name, "*"), Meme_Name),
                  color = Color),
              size = 4.5, fontface = ifelse(all_positions_cb$Multi_Emotion, "bold", "plain"),
              hjust = 0.5, vjust = 0.5) +
    
    scale_fill_identity() +
    scale_color_identity() +
    
    coord_fixed(ratio = 1) +
    xlim(-(total_width/2 + block_width*0.35), (total_width/2 + block_width*0.35)) +
    ylim(-(block_height/2 + block_height*0.4), (block_height/2 + block_height*0.45)) +
    
    labs(title = "Count-Based Emotion Classification",
         subtitle = paste0("Memes classified by highest emotion count (ties allowed)\n",
                           "* indicates memes with tied emotion counts | Total classifications: ", 
                           nrow(all_positions_cb))) +
    
    theme_void() +
    theme(
      plot.title = element_text(size = 26, face = "bold", hjust = 0.5,
                                color = "#1A202C", margin = margin(b = 10)),
      plot.subtitle = element_text(size = 13, hjust = 0.5, color = "#4A5568",
                                   margin = margin(b = 35), lineheight = 1.4),
      plot.background = element_rect(fill = "#FAFAFA", color = NA),
      panel.background = element_rect(fill = "#FAFAFA", color = NA),
      plot.margin = margin(45, 45, 35, 45)
    )
  
  footer_y <- -(block_height/2 + block_height*0.28)
  p <- p + 
    annotate("text", x = 0, y = footer_y, 
             label = "Classification based on highest emotion count (equal counts = multiple emotions)",
             size = 4.5, hjust = 0.5, vjust = 0.5,
             color = "#718096", fontface = "italic")
  
  ggsave(paste0(output_dir, "Count_Based_Three_Block_Distribution.png"), p,
         width = 24, height = 16, dpi = 300, bg = "#FAFAFA")
  
  return(list(plot = p, positions = all_positions_cb, summary = blocks_data_cb))
}

# Create count-based three-block visualization
if (total_memes > 0) {
  count_based_three_block <- create_count_based_three_block(count_based_classification, output_dir)
}

# ====================
# COMPREHENSIVE METHODS COMPARISON UPDATE
# ====================

# 更新方法比較，加入 count-based 方法
comprehensive_methods_comparison <- data.frame(
  Method = c(
    "Multi-Label (Individual Tests p≤0.05)",
    "Highest Percentage (Simple)",
    "Quality Controlled (≥30%, gap≥5%)", 
    "Application Ready (≥25%)",
    "Count-Based (Highest Count)"
  ),
  Contempt_Count = c(
    nrow(contempt_memes),
    nrow(contempt_highest),
    nrow(contempt_quality),
    nrow(contempt_app),
    nrow(contempt_count_based)
  ),
  Anger_Count = c(
    nrow(anger_memes),
    nrow(anger_highest),
    nrow(anger_quality),
    nrow(anger_app),
    nrow(anger_count_based)
  ),
  Disgust_Count = c(
    nrow(disgust_memes),
    nrow(disgust_highest),
    nrow(disgust_quality),
    nrow(disgust_app),
    nrow(disgust_count_based)
  ),
  Multi_Emotion_Cases = c(
    sum(multi_emotion_analysis$Significant_Emotions_Count > 1),
    0,  # Highest percentage is mutually exclusive
    0,  # Quality controlled is mutually exclusive
    0,  # App ready is mutually exclusive
    nrow(multi_emotion_count_analysis)
  ),
  Method_Type = c(
    "Statistical + Overlap",
    "Percentage + Exclusive", 
    "Percentage + Exclusive",
    "Percentage + Exclusive",
    "Count + Overlap"
  ),
  stringsAsFactors = FALSE
)

# ====================
# ENHANCED EXCEL OUTPUT WITH COUNT-BASED METHOD
# ====================

# 更新 Methods_Comparison 工作表
wb_analysis$worksheets$Methods_Comparison <- NULL
addWorksheet(wb_analysis, "Methods_Comparison")
writeData(wb_analysis, "Methods_Comparison", "Comprehensive Methods Comparison (Including Count-Based)", 
          startRow = 1, startCol = 1)
writeData(wb_analysis, "Methods_Comparison", comprehensive_methods_comparison, startRow = 3, startCol = 1)

# Count-Based Classification
addWorksheet(wb_analysis, "Count_Based_Classification")
writeData(wb_analysis, "Count_Based_Classification", "Count-Based Classification Results", 
          startRow = 1, startCol = 1)
writeData(wb_analysis, "Count_Based_Classification", count_based_classification, startRow = 3, startCol = 1)

# Count-Based Summary
addWorksheet(wb_analysis, "Count_Based_Summary") 
writeData(wb_analysis, "Count_Based_Summary", "Count-Based Classification Summary", 
          startRow = 1, startCol = 1)
writeData(wb_analysis, "Count_Based_Summary", count_emotion_summary, startRow = 3, startCol = 1)
writeData(wb_analysis, "Count_Based_Summary", "Classification Type Distribution", startRow = 8, startCol = 1)
writeData(wb_analysis, "Count_Based_Summary", count_type_summary, startRow = 10, startCol = 1)

# Individual count-based emotion categories
addWorksheet(wb_analysis, "CB_Contempt_Memes")
writeData(wb_analysis, "CB_Contempt_Memes", 
          paste0("Contempt Memes - Count-Based (", nrow(contempt_count_based), " memes)"), 
          startRow = 1, startCol = 1)
if (nrow(contempt_count_based) > 0) {
  writeData(wb_analysis, "CB_Contempt_Memes", contempt_count_based, startRow = 3, startCol = 1)
}

addWorksheet(wb_analysis, "CB_Anger_Memes")
writeData(wb_analysis, "CB_Anger_Memes", 
          paste0("Anger Memes - Count-Based (", nrow(anger_count_based), " memes)"), 
          startRow = 1, startCol = 1)
if (nrow(anger_count_based) > 0) {
  writeData(wb_analysis, "CB_Anger_Memes", anger_count_based, startRow = 3, startCol = 1)
}

addWorksheet(wb_analysis, "CB_Disgust_Memes")
writeData(wb_analysis, "CB_Disgust_Memes", 
          paste0("Disgust Memes - Count-Based (", nrow(disgust_count_based), " memes)"), 
          startRow = 1, startCol = 1)
if (nrow(disgust_count_based) > 0) {
  writeData(wb_analysis, "CB_Disgust_Memes", disgust_count_based, startRow = 3, startCol = 1)
}

# Multi-emotion count analysis
if (nrow(multi_emotion_count_analysis) > 0) {
  addWorksheet(wb_analysis, "Multi_Count_Analysis")
  writeData(wb_analysis, "Multi_Count_Analysis", 
            paste0("Multi-Emotion Memes - Count-Based (", nrow(multi_emotion_count_analysis), " memes)"), 
            startRow = 1, startCol = 1)
  writeData(wb_analysis, "Multi_Count_Analysis", multi_emotion_count_analysis, startRow = 3, startCol = 1)
}

# Save updated comprehensive workbook
saveWorkbook(wb_analysis, paste0(output_dir, "comprehensive_meme_analysis.xlsx"), overwrite = TRUE)
saveWorkbook(wb_analysis, paste0(output_dir, "meme_analysis.xlsx"), overwrite = TRUE)