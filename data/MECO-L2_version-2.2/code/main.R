rm(list = ls())

library(cowplot)
library(ggplot2)
library(Hmisc)
library(lme4)
library(psych)
library(reshape2)
library(tidyverse)
library(xtable)

# Runs code on data for wave value
WAVE <- 1

WRITE_AUX_FILES <- F

SAVE_PLOT_IMAGES <- F

print(paste("Running data mapping configuration for Wave", WAVE, "..."))
source("./data/MECO-L2_version-2.2/code/config.R")

print(paste("Running pipeline for Wave", WAVE, "..."))
source("./data/MECO-L2_version-2.2/code/pipeline.R")

print(paste("Running plots for Wave", WAVE, "..."))
source("./data/MECO-L2_version-2.2/code/plots.R")

print("All done!")