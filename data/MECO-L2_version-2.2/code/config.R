rm(list = ls())

library(cowplot)
library(ggplot2)
library(Hmisc)
library(lme4)
library(psych)
library(reshape2)
library(tidyverse)
library(xtable)

# Runs code on data for uncommented wave value
WAVE = 1 # Runs code on Wave 1 data
# WAVE = 2 # Runs code on Wave 2 data

WRITE_AUX_FILES = T

dataset_dir <- paste0("./data/MECO-L2_version-2.2/", "wave-", WAVE, "/")

primary_data_dir <- paste0(dataset_dir, "primary-data/")
eyetracking_data_dir <- paste0(primary_data_dir, "eye-tracking/")
comprehension_data_dir <- paste0(primary_data_dir, "comprehension/")
individual_differences_data_dir <- paste0(primary_data_dir, "individual-differences/")

aux_files_dir <- paste0(dataset_dir, "auxiliary-files/")

if (WRITE_AUX_FILES) {
  if (!dir.exists(aux_files_dir)) {
    dir.create(aux_files_dir, recursive = TRUE)
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
    "joint_comp_L2_Wave2_trimmed.rda"
  )
  #
  acc_breakdown_data <- paste0(
    comprehension_data_dir, 
    "joint_l2_Wave2_acc_breakdown_trimmed"
  )
  #
  by_subject_L2_data <- paste0(aux_files_dir, "by.sub.l2.rda")
}

by_subject_L1_data <- "./data/by.sub.l1.rda"
