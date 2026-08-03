dataset_dir <- paste0("./data/MECO-L2_version-2.2/", "wave-", WAVE, "/")

primary_data_dir <- paste0(dataset_dir, "primary-data/")
eyetracking_data_dir <- paste0(primary_data_dir, "eye-tracking/")
comprehension_data_dir <- paste0(primary_data_dir, "comprehension/")
individual_differences_data_dir <- paste0(primary_data_dir, "individual-differences/")

aux_files_dir <- paste0(dataset_dir, "auxiliary-files/")
plot_files_dir <- paste0(aux_files_dir, "plots/")

if (WRITE_AUX_FILES) {
  if (!dir.exists(aux_files_dir)) {
    dir.create(aux_files_dir, recursive = TRUE)
  }
}

if (SAVE_PLOT_IMAGES) {
  if (!dir.exists(plot_files_dir)) {
    dir.create(plot_files_dir, recursive = TRUE)
  }
}

if (WAVE == 1) {
  #
  eyetracking_data <- paste0(
    eyetracking_data_dir, 
    "joint_data_l2_trimmed_version2.2.rda"
  )
  #
  reading_rate_data <- paste0(
    eyetracking_data_dir, 
    "joint.l2.readrate_version2.2.rda"
  )
  #
  comprehension_acc_data <- paste0(comprehension_data_dir, "joint.comp.l2.rda")
  # 
  individual_diff_data <- paste0(
    individual_differences_data_dir, 
    "joint.ind.diff.l2.rda"
  )
  #
  acc_breakdown_data <- paste0(
    comprehension_data_dir, 
    "joint_l2_acc_breakdown.rda"
  )
  #
  by_subject_L2_data <- paste0(aux_files_dir, "by.sub.l2.rda")
} else {
  #
  eyetracking_data <- paste0(
    eyetracking_data_dir, 
    "joint_data_trimmed_L2_wave2_version2.2.rda"
  )
  #
  reading_rate_data <- paste0(
    eyetracking_data_dir, 
    "joint_readrate_L2_wave2_version2.2.rda"
  )
  #
  comprehension_acc_data <- paste0(
    comprehension_data_dir, 
    "joint_comp_L2_Wave2_trimmed.rda"
  )
  #
  individual_diff_data <- paste0(
    individual_differences_data_dir, 
    "joint.ind.diff.l2.w2.rda"
  )
  #
  acc_breakdown_data <- paste0(
    comprehension_data_dir, 
    "joint_l2_Wave2_acc_breakdown_trimmed.rda"
  )
  #
  by_subject_L2_data <- paste0(aux_files_dir, "by.sub.l2.rda")
}

by_subject_L1_data <- "./data/by.sub.l1.rda"

by_subject_comp <- paste0(aux_files_dir, "clean_by_sub_ind_wave", WAVE, ".rds")
