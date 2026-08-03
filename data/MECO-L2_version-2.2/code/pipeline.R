load_standardized <- function(file_path) {
  tmp_env <- new.env()
  load(file_path, envir = tmp_env)
  
  loaded_objects <- ls(tmp_env)
  
  if (length(loaded_objects) > 1) {
    warning(
      "File contains multiple objects. Returning the first one: ", 
      loaded_objects[1]
    )
  }
  
  return(tmp_env[[loaded_objects[1]]])
}

######## read main eye-tracking data file ###########

joint.data <- load_standardized(eyetracking_data)

###### remove outliers ###########

joint.data = joint.data[joint.data$dur > 80 | is.na(joint.data$dur)==T,]

crit = joint.data %>%
  group_by(lang, uniform_id) %>%
  dplyr::summarise(dur.crit = quantile(dur, 0.99, na.rm = T))


m = merge(joint.data, crit, by.x = c("lang", "uniform_id"), by.y = c("lang", "uniform_id"))  
m = m[m$skip == 1 | (m$dur < m$dur.crit),]

m -> joint.data
rm(m)

joint.data = joint.data[joint.data$skip == 1 | joint.data$nfix <= quantile(joint.data$nfix, 0.99, na.rm = T), ]
joint.data$nfix.inc = 0 #fixing NAs in nfix for skipped words. Replacing by 0s.
joint.data[
  is.na(joint.data$nfix) == F,
]$nfix.inc = joint.data[
  is.na(joint.data$nfix) == F,
]$nfix
summary(joint.data$nfix.inc)


######### data frame of subject means ##########
by.sub = joint.data %>% group_by(uniform_id) %>% dplyr::summarise(
  lang = unique(lang),
  skip = mean(skip, na.rm = T),
  nfix = mean(nfix, na.rm = T),
  dur = mean(dur, na.rm = T),
  reg.in = mean(reg.in, na.rm = T),
  firstfix.dur = mean(firstfix.dur, na.rm = T),
  firstrun.dur = mean(firstrun.dur, na.rm = T),
  refix = mean(refix, na.rm = T),
  reread = mean(reread, na.rm = T)
) 

table(by.sub$lang)


########## read reading rate ############

# Reading rate broken down by story and participant
read_rate <- load_standardized(reading_rate_data)

readrate_full <- read_rate
rm(read_rate)
readrate_full <- readrate_full %>% filter(rate < 1000)


readrate <- readrate_full %>% group_by(uniform_id) %>% dplyr::summarize(rate = mean(rate))

m = merge(by.sub, readrate)
m -> by.sub
rm(m, readrate)

##### create table of means #####
describeBy(
  x = by.sub[, 2:ncol(by.sub)], 
  group = by.sub$lang
) -> descr  ##NS: changed group = lang to group = by.sub$lang, otherwise I got an error.
data.frame(do.call(rbind, descr)) -> descr

pre_var <- do.call(
  rbind, 
  gregexpr(pattern = "\\.", text = rownames(descr))
)[,1]
substr(rownames(descr), 1, pre_var-1) -> descr$lang

substr(rownames(descr), pre_var+1, nchar(rownames(descr))) -> descr$var

descr <- descr[, c("var", "lang", "n", "mean", "sd", "se",  "median", "min", "max")]
descr = descr[-grep("lang", rownames(descr)),]
descr = descr[order(descr$var, descr$lang),]

for (i in 3:ncol(descr)) {
  descr[,i] = round(descr[,i], 2)
}

rownames(descr) = 1:nrow(descr)
descr = droplevels(descr)

# Reading comprehension accuracy data.

joint.comp <- load_standardized(comprehension_acc_data)

joint.comp -> joint.acc
table(joint.acc$lang)
rm(joint.comp)
joint.acc$lang = as.factor(joint.acc$lang)

describeBy(joint.acc[, c("accuracy")], group = joint.acc$lang) -> desc_acc
data.frame(do.call(rbind, desc_acc)) -> desc_acc

desc_acc$lang <- row.names(desc_acc)

substr(rownames(desc_acc), 4, nchar(rownames(desc_acc))) -> desc_acc$var
desc_acc <- desc_acc[, c("var", "lang", "n", "mean", "sd", "se",  "median", "min", "max")]
desc_acc = desc_acc[order(desc_acc$var, desc_acc$lang),]

for (i in 3:ncol(desc_acc)) {
  desc_acc[,i] = round(desc_acc[,i], 2)
}

rownames(desc_acc) = 1:nrow(desc_acc)
desc_acc = droplevels(desc_acc)
desc_acc$var = "acc"


# Reading individual differences data
joint_id <- load_standardized(individual_diff_data)

colnames(joint_id)

#renaming variables for figure
colnames(joint_id)[colnames(joint_id) == "TOWRE_word"] = "towre: swe"
colnames(joint_id)[colnames(joint_id) == "TOWRE_nonword"] = "towre: pde"

#note: here only use vocab 2-5: renamed simply as vocabulary
colnames(joint_id)[colnames(joint_id) == "vocab.t2.5"] = "vocabulary"
colnames(joint_id)[colnames(joint_id) == "vocab"] = "vocab.old.all"

colnames(joint_id)[colnames(joint_id) == "cft20"] = "cft"
colnames(joint_id)[colnames(joint_id) == "motiv"] = "motivation"

describeBy(joint_id[, -c(1,2,4)], group = joint_id$lang) -> desc_ind
data.frame(do.call(rbind, desc_ind)) -> desc_ind

str_split_fixed(rownames(desc_ind), pattern = "\\.", n = 2)[,1] -> desc_ind$lang
# substr(rownames(desc_ind), 1, 2) -> desc_ind$lang
str_split_fixed(rownames(desc_ind), pattern = "\\.", n = 2)[,2] -> desc_ind$var
# substr(rownames(desc_ind), 4, nchar(rownames(desc_ind))) -> desc_ind$var

desc_ind <- desc_ind[, c("var", "lang", "n", "mean", "sd", "se",  "median", "min", "max")]
desc_ind = desc_ind[order(desc_ind$var, desc_ind$lang),]

for (i in 3:ncol(desc_ind)) {
  desc_ind[,i] = round(desc_ind[,i], 2)
}

rownames(desc_ind) = 1:nrow(desc_ind)
desc_ind = droplevels(desc_ind)


descr <- data.frame(rbind(descr, desc_acc), stringsAsFactors = F)
rm(desc_acc)
descr$lang = as.factor(descr$lang)

## write auxiliary files
if (WRITE_AUX_FILES) {
  eyemove_lang <- paste0(aux_files_dir, "descriptive_eyemove_language.csv")
  write.csv(descr, eyemove_lang, quote = F, row.names = F)
  ind_lang <- "descriptive_ind_language.csv"
  write.csv(desc_ind, ind_lang, quote = F, row.names = F)
}

##### descriptive stats for read rate and acc by passage #####
fun25 = function(x) {
  return(quantile(x, 0.25))
}
fun75 = function(x) {
  return(quantile(x, 0.75))
}

describeBy(
  readrate_full$rate, 
  group = list(readrate_full$trialid, readrate_full$lang), 
  mat = T
) -> descr_rate_story
head(descr_rate_story)
colnames(descr_rate_story)[2:4] = c("trialid", "lang", "var")
descr_rate_story <- data.frame(
  descr_rate_story[, c("var", "lang", "trialid", "n", "mean", "sd", "se",  "median", "min", "max")], 
  stringsAsFactors = F)

readrate_full %>% group_by(lang, trialid) %>% dplyr::summarize(
  q1 = fun25(rate), 
  q3 = fun75(rate)
) -> tmp_rate

descr_rate_story = cbind(descr_rate_story, tmp_rate[, 3:4])
descr_rate_story$var = "rate"
for (i in 5:8) {
  descr_rate_story[,i] = round(descr_rate_story[,i])
}
head(descr_rate_story)

if (WRITE_AUX_FILES) {
  rate_passage <- paste0(aux_files_dir, "descriptive_rate_passage.csv")
  write.csv(descr_rate_story, file = rate_passage, quote = F, row.names = F)
}

joint.br.acc <- load_standardized(acc_breakdown_data)

describeBy(
  joint.br.acc$ACCURACY, 
  group = list(joint.br.acc$number, joint.br.acc$lang), 
  mat = T
) -> descr_acc_story
head(descr_acc_story)
colnames(descr_acc_story)[2:4] = c("trialid", "lang", "var")
descr_acc_story <- data.frame(
  descr_acc_story[, c("var", "lang", "trialid", "n", "mean", "sd", "se",  "median", "min", "max")], 
  stringsAsFactors = F
)

joint.br.acc %>% group_by(lang, number) %>% dplyr::summarize(
  q1 = fun25(ACCURACY), 
  q3 = fun75(ACCURACY)
) -> tmp_acc
descr_acc_story = cbind(descr_acc_story, tmp_acc[, 3:4])
descr_acc_story$var = "acc"
for (i in 5:8) {
  descr_acc_story[,i] = round(descr_acc_story[,i],2)
}
head(descr_acc_story)

if (WRITE_AUX_FILES) {
  acc_passage <- paste0(aux_files_dir, "descriptive_acc_passage.csv")
  write.csv(descr_acc_story[, 1:7], file = acc_passage, quote = F, row.names = F)
}


##### plot means #####
descr <- droplevels(descr)

## for readability change  variable labels
descr <- descr %>% dplyr::mutate(var.new = dplyr::recode(
    var,
    "acc" = "accuracy", 
    "dur" = "totalFixationDuration", 
    "firstfix.dur" = "firstFixationDuration", 
    "firstrun.dur" = "gazeDuration", 
    "nfix" = "nFixations", 
    "rate" = "readingRate", 
    "refix" = "refixation", 
    "reg.in" = "regressionIn", 
    "reread" = "rereading", 
    "skip" = "skipping"
  )
)
descr$var.new = factor(
  descr$var.new, 
  levels = c(
    "accuracy", 
    "totalFixationDuration", 
    "firstFixationDuration", 
    "gazeDuration", 
    "nFixations", 
    "readingRate", 
    "refixation", 
    "regressionIn", 
    "rereading", 
    "skipping"
  )
)

if (SAVE_PLOT_IMAGES) {
  plot1_file <- paste0(plot_files_dir, "figure1.2025_01_03.jpeg")
  jpeg(filename = plot1_file, width = 8.2, height = 9.1, units = "in", res = 300)
}

plot1 <- ggplot(
  aes(x = lang, y = mean, col = lang), 
  data = descr
) + 
  geom_point(stat = "identity") + 
  geom_errorbar(aes(ymin=mean - se, ymax=mean+se)) + 
  facet_wrap(~var.new, scales = "free", ncol = 3) + 
  theme(axis.text=element_text(size=5), axis.text.x = element_text(angle = 45, vjust = 1, hjust=1)) + 
  labs(col = "sample (L1)") + 
  theme_bw(base_size = 13) + theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1)) +
  theme(legend.position = "top") + theme(axis.title.x = element_blank(), axis.title.y = element_blank()) + 
  guides(col = guide_legend(nrow = 2)) 

print(plot1)

if (SAVE_PLOT_IMAGES) {
  dev.off()
}

desc_ind_plot <- desc_ind
table(desc_ind_plot$var)

if (SAVE_PLOT_IMAGES) {
  plot2_file <- paste0(plot_files_dir, "figure2.2025_01_03.jpeg")
  jpeg(filename = plot2_file, width = 8.2, height = 9.1, units = "in", res = 300)
}

plot2 <- ggplot(
  aes(x = lang, y = mean, col = lang), 
  data = desc_ind_plot
) + 
  geom_point(stat = "identity") + 
  geom_errorbar(aes(ymin=mean - se, ymax=mean+se)) + 
  facet_wrap(~var, scales = "free") + 
  theme(axis.text=element_text(size=5), axis.text.x = element_text(angle = 45, vjust = 1, hjust=1)) + 
  labs(col = "sample (L1)") +
  theme_bw(base_size = 13) + theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1)) +
  theme(legend.position = "top") + theme(axis.title.x = element_blank(), axis.title.y = element_blank()) + 
  guides(col = guide_legend(nrow = 2)) 

print(plot2)

if (SAVE_PLOT_IMAGES) {
  dev.off()
}
######## reliability (supplementary materials) ########

joint.data$split = as.factor(ifelse(joint.data$wordnum %% 2 == 1, "o", "e"))


# reliability at the level of subjects
by.sub.split = joint.data %>% 
  group_by(uniform_id, lang, split) %>% 
  dplyr::summarise(
  skip = mean(skip, na.rm = T),
  nfix = mean(nfix, na.rm = T),
  tft = mean(dur, na.rm = T),
  reg = mean(reg.in, na.rm = T),
  ffd = mean(firstfix.dur, na.rm = T),
  gd = mean(firstrun.dur, na.rm = T),
  reread = mean(reread, na.rm = T)
) 

head(by.sub.split)

langs = unique(by.sub.split$lang)
vars = colnames(by.sub.split[4:ncol(by.sub.split)])

n = length(langs)*length(vars)
d = data.frame(
  lang = character(n), 
  var = character(n), 
  split.half = numeric(n), 
  stringsAsFactors = F
)

count = 1
for (lang in langs) {
  for (var in vars) { 
    cor.tmp = cor.test(
      pull(
        by.sub.split[by.sub.split$lang == lang & by.sub.split$split == "e", var]
      ), 
      pull(
        by.sub.split[by.sub.split$lang == lang & by.sub.split$split == "o", var]
      )
    )
    cor.tmp = cor.tmp$estimate
    
    d$lang[count] = lang
    d$var[count] = var
    d$split.half[count] = as.numeric(cor.tmp)
    
    count = count + 1
  }
}
d
d$split.half.corrected = (2*d$split.half) / (1 + d$split.half)
aggregate(data = d, split.half ~ lang, FUN = mean)
aggregate(data = d, split.half.corrected ~ lang, FUN = mean)

#long to wide
rel.sub.wide.uncor = dcast(d, lang ~ var, value.var="split.half")
head(rel.sub.wide.uncor)

rel.sub.wide.uncor$mean.r = fisherz2r(
  rowMeans(fisherz(rel.sub.wide.uncor[,2:ncol(rel.sub.wide.uncor)]))
) #note: mean based on fisher tranformation


rel.sub.wide.uncor[,2:ncol(rel.sub.wide.uncor)] = round(
  rel.sub.wide.uncor[2:ncol(rel.sub.wide.uncor)], 2
)

rel.sub.wide.cor = dcast(d, lang ~ var, value.var="split.half.corrected")

rel.sub.wide.cor$mean.r = fisherz2r(
  rowMeans(fisherz(rel.sub.wide.cor[,2:ncol(rel.sub.wide.cor)]))
)
rel.sub.wide.cor[,2:ncol(rel.sub.wide.cor)] = round(
  rel.sub.wide.cor[2:ncol(rel.sub.wide.cor)], 2
)

values.uncor = as.matrix(rel.sub.wide.uncor[,2:ncol(rel.sub.wide.uncor)])
values.cor = as.matrix(rel.sub.wide.cor[,2:ncol(rel.sub.wide.cor)])

rel.sub.sum = matrix(
  paste(values.uncor, values.cor, sep = ", "), 
  nrow=nrow(values.uncor), 
  dimnames=dimnames(values.uncor)
)

rel.sub.sum = as.data.frame(rel.sub.sum)
rel.sub.sum$lang = rel.sub.wide.cor$lang ## rel.sub.sum: table of subject-level reliability (uncorrected and corrected)
rel.sub.sum

if (WRITE_AUX_FILES) {
  subject_reliability <- paste0(aux_files_dir, "rel.sub.csv")
  write.csv(rel.sub.sum, file = )
}

# reliability at the level of words
joint.data$split.sub = as.factor(
  ifelse(as.numeric(as.factor(joint.data$subid)) %% 2 == 0, "e", "o")
)


table(joint.data$lang, joint.data$split.sub)

joint.data$word.run.num = paste(
  joint.data$lang, 
  joint.data$trialid, 
  joint.data$wordnum, 
  sep = "_"
)

by.sub.split.word = joint.data %>% 
  group_by(word.run.num, lang, split.sub) %>% 
  dplyr::summarise(
  skip = mean(skip, na.rm = T),
  nfix = mean(nfix, na.rm = T),
  tft = mean(dur, na.rm = T),
  reg = mean(reg.in, na.rm = T),
  ffd = mean(firstfix.dur, na.rm = T),
  gd = mean(firstrun.dur, na.rm = T),
  reread = mean(reread, na.rm = T)
) 

head(by.sub.split.word)


langs = unique(by.sub.split.word$lang)
vars = colnames(by.sub.split.word[4:ncol(by.sub.split.word)])

n = length(langs)*length(vars)
d.split.half.words = data.frame(
  lang = character(n), 
  var = character(n), 
  split.half = numeric(n), 
  stringsAsFactors = F
)

count = 1
for (lang in langs) {
  for (var in vars) { 
    #two datasets: one even and one odd.
    even = by.sub.split.word[
      by.sub.split.word$lang == lang & 
      by.sub.split.word$split.sub == "e", 
    ]
    odd =  by.sub.split.word[
      by.sub.split.word$lang == lang & 
      by.sub.split.word$split.sub == "o", 
    ]
    
    #subset to intersect (in cases where number is different due to missing)
    even <- even[
      even$word.run.num %in% intersect(even$word.run.num, odd$word.run.num), 
    ]
    odd <- odd[
      odd$word.run.num %in% intersect(even$word.run.num, odd$word.run.num), 
    ]
    
    # remove outliters: these can be problematic sporadically in durational measures given the relatively small number of participants in each half of data.
    even[, var] <- ifelse(
      pull(even[, var]) > quantile(pull(even[, var]), 0.99, na.rm = T) | 
      pull(even[, var]) < quantile(pull(even[, var]), 0.01, na.rm = T),
      NA, 
      pull(even[, var])
    )
    odd[, var] <- ifelse(
      pull(odd[, var]) > quantile(pull(odd[, var]), 0.99, na.rm = T) | 
      pull(odd[, var]) < quantile(pull(odd[, var]), 0.01, na.rm = T), 
      NA, 
      pull(odd[, var])
    )
    
    cor.tmp = cor.test(pull(even[, var]), pull(odd[, var]))
    cor.tmp = cor.tmp$estimate
    
    d.split.half.words$lang[count] = lang
    d.split.half.words$var[count] = var
    d.split.half.words$split.half[count] = as.numeric(cor.tmp)
    
    count = count + 1
  }
}

d.split.half.words$split.half.corrected = (
  2 * d.split.half.words$split.half
) / (
  1 + d.split.half.words$split.half
)
aggregate(data = d.split.half.words, split.half ~ lang, FUN = mean)
aggregate(data = d.split.half.words, split.half.corrected ~ lang, FUN = mean)
aggregate(data = d.split.half.words, split.half.corrected ~ var, FUN = mean)

mean(d.split.half.words$split.half.corrected)
median(d.split.half.words$split.half.corrected)


rel.item.wide.uncor = dcast(d.split.half.words, lang ~ var, 
                            value.var="split.half")
head(rel.item.wide.uncor)

rel.item.wide.uncor$mean.r = fisherz2r(
  rowMeans(fisherz(rel.item.wide.uncor[,2:ncol(rel.item.wide.uncor)]))
)

rel.item.wide.uncor[,2:ncol(rel.item.wide.uncor)] = round(
  rel.item.wide.uncor[2:ncol(rel.item.wide.uncor)], 2
)

rel.item.wide.cor = dcast(d.split.half.words, lang ~ var, 
                          value.var="split.half.corrected")
head(rel.item.wide.cor)

rel.item.wide.cor$mean.r = fisherz2r(
  rowMeans(fisherz(rel.item.wide.cor[,2:ncol(rel.item.wide.cor)]))
)

rel.item.wide.cor[,2:ncol(rel.item.wide.cor)] = round(
  rel.item.wide.cor[2:ncol(rel.item.wide.cor)], 2
)


values.uncor = as.matrix(rel.item.wide.uncor[,2:ncol(rel.item.wide.uncor)])
values.cor = as.matrix(rel.item.wide.cor[,2:ncol(rel.item.wide.cor)])

rel.item.sum = matrix(
  paste(values.uncor, values.cor, sep = ", "), 
  nrow=nrow(values.uncor), 
  dimnames=dimnames(values.uncor)
)  ## rel.item.sum: table of item-level reliability (uncorrected and corrected)

rel.item.sum = as.data.frame(rel.item.sum)
rel.item.sum$lang = rel.item.wide.cor$lang
rel.item.sum

if (WRITE_AUX_FILES) {
  item_reliability <- paste0(aux_files_dir, "rel.item.csv")
  write.csv(rel.item.sum, file = item_reliability)
}

###### ICC for reading rate

read_rate <- load_standardized(reading_rate_data)

u <- read_rate
length(unique(u$trialid))

u.wide = dcast(data = u, uniform_id + lang ~ trialid, value.var="rate")

#all languages
psych::ICC(x = u.wide[,3:ncol(u.wide)], missing = T, lmer = T)

#ICC by language 
d.icc = data.frame(
  lang = character(length(unique(u.wide$lang))), 
  icc2k = numeric(length(unique(u.wide$lang))), 
  stringsAsFactors = F
)

count = 1
for (lang.curr in unique(u$lang)) { 
  d.icc$lang[count] = lang.curr
  d.curr = u.wide[u.wide$lang == lang.curr,]
  
  #note: outlier removal for ICC: if > 500 words per minute delete. 
  to.icc = d.curr[,3:ncol(u.wide)]
  to.icc[to.icc > 500] = NA
  
  icc.curr = psych::ICC(x = to.icc, missing = T, lmer = T)
  
  d.icc$icc2k[count] = icc.curr$results$ICC[5]
  
  count = count + 1
}

d.icc$icc2k = round(d.icc$icc2k, 2)
d.icc

if (WRITE_AUX_FILES) {
  icc = paste0(aux_files_dir, "icc.csv")
  write.csv(d.icc, file = icc)
}

##### correlation table #####
# Reading comprehension accuracy data.
joint.comp <- load_standardized(comprehension_acc_data)

joint.comp -> joint.acc

merge(
  by.sub, 
  joint.acc[, c("uniform_id", "accuracy")], 
  by.x = "uniform_id", 
  by.y = "uniform_id", 
  all = T
) -> by.sub1

by.sub1$accuracy -> by.sub1$acc
by.sub1$accuracy <- NULL

by.sub.ind = merge(
  by.sub1[,-2], 
  joint_id, 
  by.x = "uniform_id", 
  by.y = "uniform_id"
)

by.sub.numeric <- by.sub.ind %>% dplyr::select(where(is.numeric))

colnames(by.sub.ind)
rcorr(as.matrix(by.sub.numeric)) -> rc 

mat_corr = matrix(nrow = nrow(rc$r), ncol = ncol(rc$r), "")
mat_corr[upper.tri(mat_corr)] <- round(rc$r[upper.tri(rc$r)],2)
mat_corr[lower.tri(mat_corr)] <- round(rc$P[lower.tri(rc$P)],3)
data.frame(mat_corr) -> mat_corr
colnames(mat_corr) = rownames(mat_corr) = colnames(rc$r)

mat_corr #correlation table

if (WRITE_AUX_FILES) {
  correlation <- paste0(aux_files_dir, "cor.csv")
  write.csv(mat_corr, file = correlation)
}

saveRDS(by.sub.ind, file = paste0(aux_files_dir, "clean_by_sub_ind_wave", WAVE, ".rds"))
