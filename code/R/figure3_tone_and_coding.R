library(ggplot2)
library(patchwork)
library(scales)

source(file.path("code", "R", "theme.R"))
dir.create("figures", showWarnings = FALSE)

brk2016 <- as.Date("2016-03-01")
brk1806 <- as.Date("2018-06-01")
brk2202 <- as.Date("2022-02-01")

e5 <- read.csv(file.path("data", "analysis", "e6_third_group_monthly.csv"), fileEncoding = "UTF-8-BOM")
e5$month_date <- as.Date(paste0(e5$month, "01"), format = "%Y%m%d")
labels <- c(allies = "盟友组 −1.389", third = "第三方组 −1.757", rivals = "对手组 −2.208")
long <- data.frame(
  month_date = rep(e5$month_date, 3),
  tone = c(e5$allies_tone, e5$third_tone, e5$rivals_tone),
  group = factor(rep(labels[c("allies", "third", "rivals")], each = nrow(e5)), levels = labels)
)
colors <- c("盟友组 −1.389" = palette_contract[["signal_blue"]],
            "第三方组 −1.757" = palette_contract[["neutral_mid"]],
            "对手组 −2.208" = palette_contract[["accent_red"]])

pa <- ggplot(long, aes(x = month_date, y = tone, colour = group)) +
  geom_hline(data = data.frame(y = c(-1.389, -1.757, -2.208), group = factor(labels, levels = labels)),
             aes(yintercept = y, colour = group), linetype = "dotted", linewidth = 0.3, alpha = 0.7) +
  geom_line(linewidth = 0.5) +
  geom_vline(xintercept = brk1806, linetype = "dashed", linewidth = 0.45, colour = palette_contract[["accent_red"]]) +
  geom_vline(xintercept = brk2202, linetype = "dashed", linewidth = 0.45, colour = palette_contract[["accent_red"]]) +
  annotate("text", x = brk1806, y = max(long$tone) + 0.05, label = "2018-06\n贸易战",
           hjust = -0.08, size = 2.3, lineheight = 0.95, colour = palette_contract[["accent_red"]]) +
  annotate("text", x = brk2202, y = max(long$tone) + 0.05, label = "2022-02\n俄乌",
           hjust = -0.08, size = 2.3, lineheight = 0.95, colour = palette_contract[["accent_red"]]) +
  scale_colour_manual(values = colors) +
  month_axis() +
  scale_y_continuous(expand = expansion(mult = c(0.05, 0.20)), labels = label_minus) +
  labs(x = NULL, y = "被报道情感（月度均值）", tag = "a", colour = NULL) +
  theme(legend.position = c(0.30, 0.13), legend.background = element_rect(fill = "white", colour = NA),
        legend.key.size = unit(3, "mm"), legend.text = element_text(size = 6.4))

monthly <- read.csv(file.path("data", "processed", "monthly_summary.csv"))
monthly$month_date <- as.Date(paste0(monthly$month, "01"), format = "%Y%m%d")
monthly <- monthly[monthly$month >= "201503", ]
monthly$us_share_pct <- monthly$us_share2 * 100

pb1 <- ggplot(monthly, aes(x = month_date, y = us_share_pct)) +
  geom_line(linewidth = 0.45, colour = palette_contract[["signal_blue"]]) +
  geom_break(brk2016) +
  geom_step_means(monthly, "us_share_pct", brk2016) +
  annotate("text", x = brk2016, y = max(monthly$us_share_pct) * 1.02, label = "2016-03",
           hjust = -0.05, size = 2.3, colour = palette_contract[["accent_red"]]) +
  month_axis() +
  scale_y_continuous(expand = expansion(mult = c(0.02, 0.14))) +
  labs(x = NULL, y = "涉美事件份额（%）", tag = "b")

pb2 <- ggplot(monthly, aes(x = month_date, y = goldstein)) +
  geom_line(linewidth = 0.45, colour = palette_contract[["neutral_mid"]]) +
  geom_smooth(method = "loess", span = 0.25, se = FALSE, linewidth = 0.6, colour = palette_contract[["neutral_dark"]]) +
  geom_break(brk2016) +
  month_axis() +
  labs(x = NULL, y = "Goldstein 烈度", tag = NULL)

right <- pb1 / pb2 + plot_layout(heights = c(1, 1))
figure3 <- pa | right
figure3 <- figure3 + plot_layout(widths = c(1.2, 1))
save_pub_r(figure3, file.path("figures", "figure3_tone_and_coding"), width_mm = 183, height_mm = 84)
cat("figure3 complete\n")
