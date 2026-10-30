source(file.path("code", "R", "theme.R"))
library(dplyr)

dir.create("figures", showWarnings = FALSE)
data <- read.csv(file.path("data", "analysis", "e5_peak_composition_cases.csv"), fileEncoding = "UTF-8-BOM")
population <- read.csv(file.path("data", "analysis", "e4_peak_composition_all.csv"), fileEncoding = "UTF-8-BOM")

BAND <- 1.7
MED <- median(population$deviation)
N_IN <- sum(abs(population$deviation) <= BAND)
N_OUT <- sum(population$deviation > BAND)
PCT_IN <- round(100 * N_IN / nrow(population), 1)
BW <- 0.5

fmt_month <- function(values) paste0(substr(values, 1, 4), "-", substr(values, 5, 6))
minus <- function(values) gsub("-", "\u2212", values)
fmt_dev <- function(values) ifelse(abs(values) < 0.05, "0.0", minus(sprintf("%+.1f", values)))

ND <- palette_contract[["neutral_dark"]]
NM <- palette_contract[["neutral_mid"]]
NL <- palette_contract[["neutral_light"]]

data <- data %>%
  mutate(dir = ifelse(deviation > 0.05, "pos", ifelse(deviation < -0.05, "neg", "flat")),
         col = c(pos = palette_contract[["accent_red"]], neg = palette_contract[["signal_blue"]],
                 flat = palette_contract[["neutral_mid"]])[dir]) %>%
  arrange(deviation) %>%
  mutate(ylab = factor(sprintf("%s  %s", name, fmt_month(peak_month)),
                       levels = sprintf("%s  %s", name, fmt_month(peak_month))))

counts <- population %>%
  mutate(bin = floor(deviation / BW) * BW) %>%
  count(bin)

pa <- ggplot() +
  annotate("rect", xmin = -BAND, xmax = BAND, ymin = -Inf, ymax = Inf, fill = NL, alpha = 0.55) +
  geom_col(data = counts, aes(x = bin + BW / 2, y = n), width = BW * 0.9,
           fill = NM, colour = "white", linewidth = 0.18) +
  geom_vline(xintercept = c(-BAND, BAND), linetype = "dashed", linewidth = 0.3, colour = NM) +
  geom_vline(xintercept = 0, linewidth = 0.35, colour = ND) +
  annotate("text", x = -6.5, y = Inf, vjust = 1.45, hjust = 0, family = FONT_CN, size = 2.3, colour = ND,
           label = minus(sprintf("%d 个国家（地区）｜中位数 %+.2f 个百分点", nrow(population), MED))) +
  annotate("text", x = 4.55, y = Inf, vjust = 1.45, hjust = 1, lineheight = 1.1,
           family = FONT_CN, size = 2.3, colour = NM,
           label = sprintf("浅灰带 ＝ ±%.1f 个百分点\n%d 国（%.1f%%）在带内，%d 国超出", BAND, N_IN, PCT_IN, N_OUT)) +
  scale_x_continuous(limits = c(-6.6, 4.6), breaks = c(-6, -4, -2, 0, 2, 4), labels = label_minus) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.26))) +
  labs(x = NULL, y = "国家数（个）", tag = "a")

data <- data %>%
  mutate(lab_hj = ifelse(deviation < -0.05, 1, 0),
         lab_x = deviation + ifelse(deviation < -0.05, -0.32, 0.32)) %>%
  mutate(lab_hj = ifelse(code == "UKR", 0, lab_hj),
         lab_x = ifelse(code == "UKR", deviation + 0.32, lab_x),
         lab_hj = ifelse(code == "USA", 1, lab_hj),
         lab_x = ifelse(code == "USA", deviation - 0.32, lab_x))

pb <- ggplot(data, aes(y = ylab)) +
  annotate("rect", xmin = -BAND, xmax = BAND, ymin = -Inf, ymax = Inf, fill = NL, alpha = 0.55) +
  geom_vline(xintercept = c(-BAND, BAND), linetype = "dashed", linewidth = 0.3, colour = NM) +
  geom_vline(xintercept = 0, linewidth = 0.35, colour = ND) +
  geom_segment(aes(x = -7.1, xend = 4.9, y = ylab, yend = ylab), colour = "white", linewidth = 0.1) +
  geom_point(aes(x = deviation), size = 2.7, colour = data$col) +
  geom_text(aes(x = lab_x, label = fmt_dev(deviation)), hjust = data$lab_hj,
            size = 2.2, family = "Arial", colour = ND) +
  scale_x_continuous(limits = c(-6.6, 4.6), breaks = c(-6, -4, -2, 0, 2, 4), labels = label_minus) +
  scale_y_discrete(expand = expansion(add = c(0.62, 0.62))) +
  labs(x = "峰值月当月的美国行为体份额偏离基线（百分点）", y = NULL, tag = "b",
       caption = paste0("浅灰带＝±1.7 个百分点（多数国别落于带内）；偏离以月为单位计算，同月达到峰值的国家取同一数值\n",
                        "俄乌冲突月（2022-03）另有俄、波、摩、拉脱维亚；巴以冲突月（2023-10）另有埃及、约旦、阿鲁巴"))

figure2 <- pa / pb +
  plot_annotation(tag_levels = "a") +
  plot_layout(heights = c(1, 1.35)) &
  theme(plot.tag = element_text(size = 9, face = "bold", family = "Arial"),
        axis.text.y = element_text(size = 7.2),
        plot.caption = element_text(size = 6.2, colour = NM, hjust = 0, lineheight = 1.25, margin = margin(t = 3)),
        plot.margin = margin(4, 8, 4, 4))

save_pub_r(figure2, file.path("figures", "figure2_peak_composition"), width_mm = 150, height_mm = 152)
cat(sprintf("figure2: %d entities, median %+.2f, within %d\n", nrow(population), MED, N_IN))
