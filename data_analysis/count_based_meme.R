# COUNT-BASED MEME ANALYSIS - Using Dominant Emotion Count Only

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

# Fixed Chinese characters
target_emotions_english <- c("anger", "contempt", "disgust")
target_emotions_chinese <- c("‘Å­", "ÝpÃï", "…’º")

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

# Count-based classification function
classify_meme_by_count <- function(contempt_count, anger_count, disgust_count) {
  contempt_count[is.na(contempt_count)] <- 0
  anger_count[is.na(anger_count)] <- 0
  disgust_count[is.na(disgust_count)] <- 0
  
  observed <- c(contempt_count, anger_count, disgust_count)
  total_responses <- sum(observed)
  
  if (total_responses == 0) return(NULL)
  
  # Find maximum count
  max_count <- max(observed)
  
  # Check which emotions have the maximum count
  contempt_is_max <- contempt_count == max_count
  anger_is_max <- anger_count == max_count
  disgust_is_max <- disgust_count == max_count
  
  # Count how many emotions are tied at maximum
  emotions_at_max <- sum(contempt_is_max, anger_is_max, disgust_is_max)
  
  # Determine dominant emotion(s)
  dominant_emotions <- c()
  if (contempt_is_max) dominant_emotions <- c(dominant_emotions, "Contempt")
  if (anger_is_max) dominant_emotions <- c(dominant_emotions, "Anger")
  if (disgust_is_max) dominant_emotions <- c(dominant_emotions, "Disgust")
  
  # Calculate percentages
  percentages <- round((observed / total_responses) * 100, 1)
  
  return(list(
    contempt_count = contempt_count,
    anger_count = anger_count,
    disgust_count = disgust_count,
    contempt_pct = percentages[1],
    anger_pct = percentages[2],
    disgust_pct = percentages[3],
    total_responses = total_responses,
    max_count = max_count,
    emotions_at_max = emotions_at_max,
    contempt_is_dominant = contempt_is_max,
    anger_is_dominant = anger_is_max,
    disgust_is_dominant = disgust_is_max,
    dominant_emotions = paste(dominant_emotions, collapse = ", "),
    classification_type = case_when(
      emotions_at_max == 1 ~ "Single_Dominant",
      emotions_at_max == 2 ~ "Dual_Dominant",
      emotions_at_max == 3 ~ "Triple_Tie",
      TRUE ~ "Unknown"
    )
  ))
}

# Emotion summary for visualization
meme_emotion_summary <- usable_posts_data %>%
  group_by(!!sym(meme_col), resp_label) %>%
  summarise(count = n(), .groups = "drop") %>%
  group_by(!!sym(meme_col)) %>%
  mutate(total = sum(count), percentage = round((count / total) * 100, 1)) %>%
  ungroup()

unique_memes <- sort(unique(usable_posts_data[[meme_col]]))
meme_results <- list()

# Analyze each meme using count-based method
for (meme_id in unique_memes) {
  meme_data <- usable_posts_data %>% filter(!!sym(meme_col) == meme_id)
  if (nrow(meme_data) == 0) next
  
  emotion_counts <- table(meme_data$resp_label)
  
  # Extract counts based on language
  if ("anger" %in% names(emotion_counts)) {
    contempt_count <- as.numeric(emotion_counts["contempt"][1] %||% 0)
    anger_count <- as.numeric(emotion_counts["anger"][1] %||% 0)
    disgust_count <- as.numeric(emotion_counts["disgust"][1] %||% 0)
  } else {
    contempt_count <- as.numeric(emotion_counts["ÝpÃï"][1] %||% 0)
    anger_count <- as.numeric(emotion_counts["‘Å­"][1] %||% 0)
    disgust_count <- as.numeric(emotion_counts["…’º"][1] %||% 0)
  }
  
  result <- classify_meme_by_count(contempt_count, anger_count, disgust_count)
  
  if (!is.null(result)) {
    meme_results[[as.character(meme_id)]] <- c(list(meme_id = meme_id), result)
  }
}

# Convert results to dataframe
meme_analysis_df <- do.call(rbind, lapply(meme_results, function(x) {
  data.frame(
    Meme_ID = x$meme_id,
    Total_Responses = x$total_responses,
    Contempt_Count = x$contempt_count,
    Anger_Count = x$anger_count,
    Disgust_Count = x$disgust_count,
    Contempt_Pct = x$contempt_pct,
    Anger_Pct = x$anger_pct,
    Disgust_Pct = x$disgust_pct,
    Max_Count = x$max_count,
    Emotions_At_Max = x$emotions_at_max,
    Contempt_Is_Dominant = x$contempt_is_dominant,
    Anger_Is_Dominant = x$anger_is_dominant,
    Disgust_Is_Dominant = x$disgust_is_dominant,
    Dominant_Emotions = x$dominant_emotions,
    Classification_Type = x$classification_type,
    stringsAsFactors = FALSE
  )
}))

if (is.null(meme_analysis_df) || nrow(meme_analysis_df) == 0) {
  stop("No meme data found")
}

meme_analysis_df <- meme_analysis_df[order(meme_analysis_df$Meme_ID), ]

# Create emotion-specific dataframes
contempt_memes <- meme_analysis_df[meme_analysis_df$Contempt_Is_Dominant == TRUE, ]
anger_memes <- meme_analysis_df[meme_analysis_df$Anger_Is_Dominant == TRUE, ]
disgust_memes <- meme_analysis_df[meme_analysis_df$Disgust_Is_Dominant == TRUE, ]

# Multi-emotion memes (ties)
multi_emotion_memes <- meme_analysis_df[meme_analysis_df$Emotions_At_Max > 1, ]

# Summary statistics
total_memes <- nrow(meme_analysis_df)
single_dominant_memes <- sum(meme_analysis_df$Classification_Type == "Single_Dominant")
multi_dominant_memes <- sum(meme_analysis_df$Classification_Type %in% c("Dual_Dominant", "Triple_Tie"))

# Split data for visualization
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

# Enhanced visualization highlighting dominant emotions
create_count_based_plot <- function(data, meme_range, meme_column, meme_analysis_df) {
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
  single_dominant_range <- sum(analysis_in_range$Classification_Type == "Single_Dominant", na.rm = TRUE)
  multi_dominant_range <- sum(analysis_in_range$Emotions_At_Max > 1, na.rm = TRUE)
  
  # Set colors and labels based on language
  if ("anger" %in% unique(data$resp_label)) {
    color_values <- c("anger" = "#DC143C", "contempt" = "#2E8B57", "disgust" = "#9370DB")
    label_names <- c("anger" = "Anger", "contempt" = "Contempt", "disgust" = "Disgust")
    emotion_mapping <- c("Anger" = "anger", "Contempt" = "contempt", "Disgust" = "disgust")
  } else {
    color_values <- c("‘Å­" = "#DC143C", "ÝpÃï" = "#2E8B57", "…’º" = "#9370DB")
    label_names <- c("‘Å­" = "Anger", "ÝpÃï" = "Contempt", "…’º" = "Disgust")
    emotion_mapping <- c("Anger" = "‘Å­", "Contempt" = "ÝpÃï", "Disgust" = "…’º")
  }
  
  # Highlight dominant emotions
  data$is_dominant_emotion <- FALSE
  
  for (i in 1:nrow(data)) {
    meme_id <- data[[meme_column]][i]
    meme_row <- analysis_in_range[analysis_in_range$Meme_ID == meme_id, ]
    
    if (nrow(meme_row) > 0) {
      current_emotion_label <- data$resp_label[i]
      
      if (current_emotion_label == emotion_mapping["Contempt"] && meme_row$Contempt_Is_Dominant) {
        data$is_dominant_emotion[i] <- TRUE
      } else if (current_emotion_label == emotion_mapping["Anger"] && meme_row$Anger_Is_Dominant) {
        data$is_dominant_emotion[i] <- TRUE
      } else if (current_emotion_label == emotion_mapping["Disgust"] && meme_row$Disgust_Is_Dominant) {
        data$is_dominant_emotion[i] <- TRUE
      }
    }
  }
  
  p <- ggplot(data, aes(x = factor(!!sym(meme_column)), y = percentage, fill = resp_label)) +
    geom_col(position = "dodge", width = 0.7, 
             aes(color = ifelse(is_dominant_emotion, "#FFD700", "black"),
                 size = ifelse(is_dominant_emotion, 1.2, 0.3))) +
    scale_fill_manual(values = color_values, name = "Emotion", labels = label_names) +
    scale_color_identity() +
    scale_size_identity() +
    scale_y_continuous(limits = c(0, 100), breaks = seq(0, 100, 20)) +
    labs(x = "Meme ID", y = "Response Percentage (%)", 
         title = paste0("Memes ", meme_range, " - Count-Based Emotion Classification")) +
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
  
  # Add info box
  p <- p + 
    annotation_custom(
      grob = rectGrob(gp = gpar(fill = "lightblue", col = "black", lwd = 1)),
      xmin = 0.5, xmax = 5.0, ymin = 80, ymax = 100
    ) +
    annotate("text", x = 2.5, y = 90,
             label = paste0("Single dominant: ", single_dominant_range, "/", total_memes_range, 
                            "\nMulti-dominant: ", multi_dominant_range, "/", total_memes_range,
                            "\nGold borders: Dominant emotions (highest count)"),
             size = 3, hjust = 0.5, vjust = 0.5, fontface = "bold")
  
  # Color meme IDs based on classification type
  classification_colors <- rep("black", length(memes_in_range))
  names(classification_colors) <- as.character(sort(memes_in_range))
  
  for (i in 1:nrow(analysis_in_range)) {
    meme_id <- as.character(analysis_in_range$Meme_ID[i])
    if (meme_id %in% names(classification_colors)) {
      if (analysis_in_range$Emotions_At_Max[i] > 1) {
        classification_colors[meme_id] <- "purple"  # Multi-dominant
      } else {
        classification_colors[meme_id] <- "red"     # Single dominant
      }
    }
  }
  
  p <- p + theme(axis.text.x = element_text(angle = 45, hjust = 1, size = 9,
                                            colour = classification_colors[as.character(sort(memes_in_range))]))
  
  return(p)
}

# Create plots
count_plot1 <- create_count_based_plot(meme_data_part1, "1-25", meme_col, meme_analysis_df)
count_plot2 <- create_count_based_plot(meme_data_part2, "26-50", meme_col, meme_analysis_df)

# Combined figure
figure_count <- grid.arrange(
  textGrob("Count-Based Meme Emotion Analysis: Classification by Highest Emotion Count", 
           gp = gpar(fontsize = 14, fontface = "bold"), hjust = 0.5),
  count_plot1, count_plot2,
  heights = c(0.08, 0.46, 0.46), ncol = 1
)

ggsave(paste0(output_dir, "Count_Based_Meme_Emotion_Analysis.png"), figure_count,
       width = 12, height = 10, dpi = 300, bg = "white")

# Classification type distribution plot
classification_summary <- meme_analysis_df %>%
  count(Classification_Type) %>%
  mutate(Percentage = round(n/sum(n)*100, 1))

figure_classification <- ggplot(classification_summary, aes(x = Classification_Type, y = n, fill = Classification_Type)) +
  geom_col(alpha = 0.8, color = "black", linewidth = 0.5) +
  geom_text(aes(label = paste0(n, "\n(", Percentage, "%)")), 
            vjust = 0.5, fontface = "bold", size = 4) +
  scale_fill_manual(values = c("Single_Dominant" = "#4ECDC4", 
                               "Dual_Dominant" = "#FFE66D", 
                               "Triple_Tie" = "#FF6B6B"),
                    name = "Classification Type") +
  labs(x = "Classification Type", y = "Number of Memes", 
       title = "Meme Classification Distribution - Count-Based Method",
       subtitle = "Based on highest emotion count (ties allowed)") +
  theme_classic(base_size = 11) +
  theme(
    plot.title = element_text(size = 12, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 10, hjust = 0.5, color = "darkgray"),
    legend.position = "bottom",
    axis.text = element_text(size = 10, color = "black"),
    axis.title = element_text(size = 11, color = "black", face = "bold")
  )

ggsave(paste0(output_dir, "Count_Based_Classification_Distribution.png"), figure_classification,
       width = 8, height = 6, dpi = 300, bg = "white")

# Three-block visualization
create_count_based_three_block <- function(meme_analysis_df, output_dir) {
  
  contempt_cb <- meme_analysis_df %>% filter(Contempt_Is_Dominant == TRUE)
  anger_cb <- meme_analysis_df %>% filter(Anger_Is_Dominant == TRUE)
  disgust_cb <- meme_analysis_df %>% filter(Disgust_Is_Dominant == TRUE)
  
  if (nrow(contempt_cb) == 0 && nrow(anger_cb) == 0 && nrow(disgust_cb) == 0) {
    return(NULL)
  }
  
  emotion_colors <- c("Anger" = "#E53E3E", "Contempt" = "#38A169", "Disgust" = "#805AD5")
  bg_colors <- c("Anger" = "#FED7D7", "Contempt" = "#C6F6D5", "Disgust" = "#E9D8FD")
  
  all_meme_names <- unique(c(as.character(contempt_cb$Meme_ID), 
                             as.character(anger_cb$Meme_ID), 
                             as.character(disgust_cb$Meme_ID)))
  max_name_length <- max(nchar(all_meme_names))
  
  # Adjust block dimensions - making blocks much larger
  block_width <- max(30, max_name_length * 0.8)     # Much larger width
  block_height <- block_width * 3                   # Very tall blocks  
  block_spacing <- block_width * 0.3                # Adjust spacing proportionally
  
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
      Multi_Emotion = meme_df$Emotions_At_Max > 1,
      stringsAsFactors = FALSE
    )
    
    return(positions)
  }
  
  contempt_positions <- arrange_memes_count_based(contempt_cb, center_x_contempt, "CONTEMPT", 
                                                  emotion_colors["Contempt"], bg_colors["Contempt"])
  anger_positions <- arrange_memes_count_based(anger_cb, center_x_anger, "ANGER", 
                                               emotion_colors["Anger"], bg_colors["Anger"])
  disgust_positions <- arrange_memes_count_based(disgust_cb, center_x_disgust, "DISGUST", 
                                                 emotion_colors["Disgust"], bg_colors["Disgust"])
  
  all_positions <- rbind(contempt_positions, anger_positions, disgust_positions)
  
  # Calculate shared memes
  contempt_shared <- sum(contempt_cb$Emotions_At_Max > 1)
  anger_shared <- sum(anger_cb$Emotions_At_Max > 1)
  disgust_shared <- sum(disgust_cb$Emotions_At_Max > 1)
  
  blocks_data <- data.frame(
    Emotion = c("CONTEMPT", "ANGER", "DISGUST"),
    x_center = c(center_x_contempt, center_x_anger, center_x_disgust),
    y_center = rep(center_y, 3),
    Color = c(emotion_colors["Contempt"], emotion_colors["Anger"], emotion_colors["Disgust"]),
    BG_Color = c(bg_colors["Contempt"], bg_colors["Anger"], bg_colors["Disgust"]),
    Count = c(nrow(contempt_cb), nrow(anger_cb), nrow(disgust_cb)),
    Shared_Count = c(contempt_shared, anger_shared, disgust_shared),
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
                  label = paste0("(", Count, " memes, ", Shared_Count, " tied)"),
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
    xlim(-(total_width/2 + block_width*0.15), (total_width/2 + block_width*0.15)) +
    ylim(-(block_height/2 + block_height*0.05), (block_height/2 + block_height*0.05)) +
    
    labs(title = "Count-Based Emotion Classification",
         subtitle = paste0("Memes classified by highest emotion count (ties allowed)\n",
                           "* indicates memes with tied counts | Total classifications: ", 
                           nrow(all_positions))) +
    
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
  
  footer_y <- -(block_height/2 + block_height*0.03)  # Reduced margin for larger blocks
  p <- p + 
    annotate("text", x = 0, y = footer_y, 
             label = "Classification based on highest emotion count (equal counts = multiple categories)",
             size = 4.5, hjust = 0.5, vjust = 0.5,
             color = "#718096", fontface = "italic")
  
  ggsave(paste0(output_dir, "Count_Based_Three_Block_Distribution.png"), p,
         width = 24, height = 16, dpi = 300, bg = "#FAFAFA")
  
  return(list(plot = p, positions = all_positions, summary = blocks_data))
}

# Create three-block visualization
if (total_memes > 0) {
  count_three_block <- create_count_based_three_block(meme_analysis_df, output_dir)
}

# Summary statistics
emotion_summary <- data.frame(
  Emotion = c("Contempt", "Anger", "Disgust"),
  Dominant_Count = c(nrow(contempt_memes), nrow(anger_memes), nrow(disgust_memes)),
  Percentage_of_Total = c(
    round(nrow(disgust_memes)/total_memes*100, 1)
  ),
  Tied_Count = c(
    sum(contempt_memes$Emotions_At_Max > 1),
    sum(anger_memes$Emotions_At_Max > 1),
    sum(disgust_memes$Emotions_At_Max > 1)
  ),
  Avg_Count = c(
    ifelse(nrow(contempt_memes) > 0, round(mean(contempt_memes$Contempt_Count), 1), 0),
    ifelse(nrow(anger_memes) > 0, round(mean(anger_memes$Anger_Count), 1), 0),
    ifelse(nrow(disgust_memes) > 0, round(mean(disgust_memes$Disgust_Count), 1), 0)
  ),
  Avg_Percentage = c(
    ifelse(nrow(contempt_memes) > 0, round(mean(contempt_memes$Contempt_Pct), 1), 0),
    ifelse(nrow(anger_memes) > 0, round(mean(anger_memes$Anger_Pct), 1), 0),
    ifelse(nrow(disgust_memes) > 0, round(mean(disgust_memes$Disgust_Pct), 1), 0)
  ),
  stringsAsFactors = FALSE
)

# Overall summary
overall_summary <- data.frame(
  Category = c("Single Dominant", "Multi Dominant (Tied)", "Total"),
  N = c(single_dominant_memes, multi_dominant_memes, total_memes),
  Percentage = c(paste0(round(single_dominant_memes/total_memes*100, 1), "%"),
                 paste0(round(multi_dominant_memes/total_memes*100, 1), "%"), 
                 "100.0%"),
  stringsAsFactors = FALSE
)

# Create Excel output
wb_count <- createWorkbook()

# Summary sheet
addWorksheet(wb_count, "Summary")
writeData(wb_count, "Summary", "Count-Based Meme Emotion Analysis Summary", 
          startRow = 1, startCol = 1)
writeData(wb_count, "Summary", overall_summary, startRow = 3, startCol = 1)
writeData(wb_count, "Summary", "Emotion-Specific Statistics", startRow = 8, startCol = 1)
writeData(wb_count, "Summary", emotion_summary, startRow = 10, startCol = 1)
writeData(wb_count, "Summary", "Classification Type Distribution", startRow = 15, startCol = 1)
writeData(wb_count, "Summary", classification_summary, startRow = 17, startCol = 1)

# Complete analysis
addWorksheet(wb_count, "Complete_Analysis")
writeData(wb_count, "Complete_Analysis", "Complete Count-Based Analysis", 
          startRow = 1, startCol = 1)
writeData(wb_count, "Complete_Analysis", meme_analysis_df, startRow = 3, startCol = 1)

# Individual emotion sheets
addWorksheet(wb_count, "Contempt_Memes")
writeData(wb_count, "Contempt_Memes", 
          paste0("Contempt Dominant Memes (", nrow(contempt_memes), " memes)"), 
          startRow = 1, startCol = 1)
if (nrow(contempt_memes) > 0) {
  writeData(wb_count, "Contempt_Memes", contempt_memes, startRow = 3, startCol = 1)
}

addWorksheet(wb_count, "Anger_Memes")
writeData(wb_count, "Anger_Memes", 
          paste0("Anger Dominant Memes (", nrow(anger_memes), " memes)"), 
          startRow = 1, startCol = 1)
if (nrow(anger_memes) > 0) {
  writeData(wb_count, "Anger_Memes", anger_memes, startRow = 3, startCol = 1)
}

addWorksheet(wb_count, "Disgust_Memes")
writeData(wb_count, "Disgust_Memes", 
          paste0("Disgust Dominant Memes (", nrow(disgust_memes), " memes)"), 
          startRow = 1, startCol = 1)
if (nrow(disgust_memes) > 0) {
  writeData(wb_count, "Disgust_Memes", disgust_memes, startRow = 3, startCol = 1)
}

# Multi-emotion memes (tied counts)
if (nrow(multi_emotion_memes) > 0) {
  addWorksheet(wb_count, "Multi_Emotion_Memes")
  writeData(wb_count, "Multi_Emotion_Memes", 
            paste0("Memes with Tied Emotion Counts (", nrow(multi_emotion_memes), " memes)"), 
            startRow = 1, startCol = 1)
  writeData(wb_count, "Multi_Emotion_Memes", multi_emotion_memes, startRow = 3, startCol = 1)
}

# Emotion distribution data
meme_complete_summary <- meme_emotion_summary %>%
  pivot_wider(names_from = resp_label, values_from = c(count, percentage),
              names_sep = "_", values_fill = 0)

addWorksheet(wb_count, "Emotion_Distribution")
writeData(wb_count, "Emotion_Distribution", "Meme Emotion Distribution Data", 
          startRow = 1, startCol = 1)
writeData(wb_count, "Emotion_Distribution", meme_complete_summary, startRow = 3, startCol = 1)

# Save workbook
saveWorkbook(wb_count, paste0(output_dir, "count_based_meme_analysis.xlsx"), overwrite = TRUE)

