####### L1-L2 Comparison & Variance Partitioning Plots #######

by.sub.l1 <- load_standardized(by_subject_L1_data)
colnames(by.sub.l1) <- paste0("l1_", colnames(by.sub.l1))

# Scale numeric L1 variables by language
by.sub.l1 <- by.sub.l1 %>%
  dplyr::group_by(l1_lang) %>%
  dplyr::mutate(dplyr::across(where(is.numeric), ~ as.numeric(scale(.x)))) %>%
  dplyr::ungroup()

# Prepare L2 Data (by.sub already in environment after running pipeline)
by.sub.l2 <- by.sub
colnames(by.sub.l2) <- paste0("l2_", colnames(by.sub.l2))

# Merge L1, L2, and Individual Differences
by.sub_merged <- dplyr::inner_join(
  by.sub.l1, 
  by.sub.l2, 
  by = c("l1_uniform_id" = "l2_uniform_id")
) %>% dplyr::rename(uniform_id = l1_uniform_id, lang = l2_lang) 

if (nrow(by.sub_merged) == 0) {
  
  print(paste("No matching L1 data found for Wave", WAVE, "- Skipping L1-L2 regressions and plots."))
  
} else {
    # Attach Individual Differences (joint_id) and filter out English (L1 readers)
    by.sub.ind <- dplyr::inner_join(by.sub_merged, joint_id, by = "uniform_id") %>%
    dplyr::filter(l1_lang != "en") %>%
    droplevels()

    # --- Plot 1: L1 vs L2 Reading Rate Scatterplot ---
    if (SAVE_PLOT_IMAGES) {
      l1_l2_readrate <- paste0(plot_files_dir, "L1_L2_readrate.jpeg")
      jpeg(filename = l1_l2_readrate, width = 8, height = 6, units = "in", res = 300)
    }

    l1_l2_readrate_plot <- ggplot(data = by.sub.ind, aes(x = l1_rate, y = l2_rate)) + 
    geom_point(size = 2) + 
    geom_smooth(method = lm, se = FALSE, color = "blue") +
    theme_bw(base_size = 18) + 
    xlab("L1 reading rate (scaled)") + 
    ylab("L2 reading rate")
    
    print(l1_l2_readrate_plot)

    if (SAVE_PLOT_IMAGES) dev.off()

    # --- Setup for Regression Plots (Fully Dynamic) ---
    # List the exact dependent variables we want to predict
    dv_vars <- c("skip", "nfix", "dur", "reg.in", "firstfix.dur", "firstrun.dur", "refix", "reread", "rate")

    # Dynamically grab individual difference predictors (only numeric columns, minus IDs)
    ind_vars <- joint_id %>%
    dplyr::select(where(is.numeric), -any_of(c("uniform_id", "subid"))) %>%
    colnames()

    # Initialize vectors to store R-squared values
    r2_full <- step1_l1_em <- step2_skill_tests <- step3_l2_sample <- numeric(length(dv_vars))
    l1_var <- skill_tests <- which_l2 <- overlap <- numeric(length(dv_vars))

    for (i in seq_along(dv_vars)) {
    l2_dv <- paste0("l2_", dv_vars[i])
    l1_iv <- paste0("l1_", dv_vars[i])
    
    # Skip loop iteration safely if a variable doesn't exist in a specific wave
    if (!(l2_dv %in% colnames(by.sub.ind)) || 
        !(l1_iv %in% colnames(by.sub.ind))
    ) next
    
    by.sub.ind$dv <- by.sub.ind[[l2_dv]]
    
    f_step1 <- as.formula(paste("dv ~", l1_iv))
    f_step2 <- as.formula(paste("dv ~", l1_iv, "+", paste(ind_vars, collapse = " + ")))
    f_step3 <- as.formula(paste("dv ~ l1_lang +", l1_iv, "+", paste(ind_vars, collapse = " + ")))
    
    mod.step1 <- lm(f_step1, data = by.sub.ind)
    mod.step2 <- lm(f_step2, data = by.sub.ind)
    mod.step3 <- lm(f_step3, data = by.sub.ind)
    
    # Calculate Hierarchical R2 differences
    r2_full[i] <- round(100 * summary(mod.step3)$adj.r.squared, 2)
    step1_l1_em[i] <- round(100 * summary(mod.step1)$adj.r.squared, 2)
    step2_skill_tests[i] <- round(
        100 * summary(mod.step2)$adj.r.squared, 2
    ) - step1_l1_em[i]
    step3_l2_sample[i] <- r2_full[i] - round(
        100 * summary(mod.step2)$adj.r.squared, 2
    )
    
    # Calculate Partitioning R2 differences
    mod.comp.l1_var <- lm(as.formula(paste("dv ~ l1_lang +", paste(ind_vars, collapse = " + "))), data = by.sub.ind)
    mod.comp.ind.diff <- lm(as.formula(paste("dv ~ l1_lang +", l1_iv)), data = by.sub.ind)
    mod.comp.lang <- lm(as.formula(paste("dv ~", l1_iv, "+", paste(ind_vars, collapse = " + "))), data = by.sub.ind)
    
    l1_var[i] <- r2_full[i] - round(100 * summary(mod.comp.l1_var)$adj.r.squared, 2)
    skill_tests[i] <- r2_full[i] - round(100 * summary(mod.comp.ind.diff)$adj.r.squared, 2)
    which_l2[i] <- r2_full[i] - round(100 * summary(mod.comp.lang)$adj.r.squared, 2)
    overlap[i] <- r2_full[i] - l1_var[i] - skill_tests[i] - which_l2[i]
    }

    # --- Plot 2: Hierarchical Regression Bar Plot ---
    df_hier_long <- data.frame(
    var = paste0("L2 ", dv_vars),
    r2_full = r2_full,
    `step1: L1 reading` = step1_l1_em,
    `step2: skill tests` = step2_skill_tests,
    `step3: L2 sample` = step3_l2_sample,
    check.names = FALSE
    ) %>%
    tidyr::pivot_longer(
        cols = starts_with("step"),
        names_to = "type",
        values_to = "r2"
    ) %>%
    dplyr::mutate(type = factor(type, levels = c("step3: L2 sample", "step2: skill tests", "step1: L1 reading")))

    if (SAVE_PLOT_IMAGES) {
      hierarchical_var <- paste0(plot_files_dir, "hierarchical_variance.jpeg")
      jpeg(filename = hierarchical_var, width = 10, height = 8, units = "in", res = 300)
    }

    hierarchical_var_plot <- ggplot(data = df_hier_long, aes(x = reorder(var, -r2_full), y = r2, fill = type)) + 
    geom_bar(position = "stack", stat = "identity") + 
    coord_cartesian(ylim = c(0, 100)) + 
    scale_fill_manual(values = c("steelblue4", "red", "orange")) +
    theme_bw(base_size = 18) + 
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1), legend.title = element_blank()) + 
    labs(x = "L2 reading measure", y = "percent variance explained")
    
    print(hierarchical_var_plot)

    if (SAVE_PLOT_IMAGES) dev.off()

    # --- Plot 3: Variance Partitioning Bar Plot ---
    df_part_long <- data.frame(
    var = paste0("L2 ", dv_vars),
    r2_full = r2_full,
    `L1 reading` = l1_var,
    `skill tests` = skill_tests,
    `L2 sample` = which_l2,
    `shared` = overlap,
    check.names = FALSE
    ) %>%
    tidyr::pivot_longer(
        cols = c("L1 reading", "skill tests", "L2 sample", "shared"),
        names_to = "type",
        values_to = "r2"
    ) %>%
    dplyr::mutate(type = factor(
        type, 
        levels = c("shared", "L2 sample", "skill tests", "L1 reading")
        )
    )

    if (SAVE_PLOT_IMAGES) {
      variance_part <- paste0(plot_files_dir, "variance_partitioning.jpeg")
      jpeg(filename = variance_part, width = 10, height = 8, units = "in", res = 300)
    }

    variance_part_plot <- ggplot(data = df_part_long, aes(x = reorder(var, -r2_full), y = r2, fill = type)) +
    geom_bar(position = "stack", stat = "identity") +
    coord_cartesian(ylim = c(0, 100)) +
    scale_fill_manual(values = c("purple", "steelblue4", "red", "orange")) +
    theme_bw(base_size = 18) +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1), legend.title = element_blank()) +
    labs(x = "L2 reading measure", y = "percent variance explained")
    
    print(variance_part_plot)

    if (SAVE_PLOT_IMAGES) dev.off()
}