library(ggplot2)
library(patchwork)
library(scales)

source(file.path("code", "R", "theme.R"))
dir.create("figures", showWarnings = FALSE)

PAL <- c(above = "#3D6B7D", below = "#D9D2C7", usa = "#BC5A45", chn = "#2A3E4C",
         refline = "#A8A8A8", ink = "#1F1F1F", ink_mid = "#6F6F6F", num = "#3A3A3A",
         line = "#E4E4E4", bubble = "#3D6B7D")

cn <- c(USA = "美国", ISR = "以色列", PSE = "巴勒斯坦", NZL = "新西兰", AUS = "澳大利亚", GBR = "英国",
        CAN = "加拿大", RUS = "俄罗斯", UKR = "乌克兰", IRN = "伊朗", SAU = "沙特", NGA = "尼日利亚",
        PAK = "巴基斯坦", CHN = "中国大陆", BRA = "巴西", IDN = "印尼", IND = "印度", AFG = "阿富汗",
        PRK = "朝鲜", TWN = "台湾地区", VEN = "委内瑞拉")

data <- read.csv(file.path("data", "analysis", "e1_visibility_multiplier.csv"))
selected <- c("ISR", "PSE", "NZL", "USA", "AUS", "GBR", "CAN", "UKR", "SAU", "RUS", "IRN", "NGA",
              "PAK", "CHN", "BRA", "IDN", "IND")
panel_data <- data[data$country %in% selected, ]
panel_data$label <- cn[panel_data$country]
panel_data <- panel_data[order(panel_data$visibility_multiplier), ]
panel_data$label <- factor(panel_data$label, levels = panel_data$label)
panel_data$fill <- ifelse(panel_data$country == "USA", PAL[["usa"]],
                   ifelse(panel_data$country == "CHN", PAL[["chn"]],
                   ifelse(panel_data$visibility_multiplier >= 1, PAL[["above"]], PAL[["below"]])))
panel_data$num_col <- ifelse(panel_data$country == "USA", PAL[["usa"]],
                      ifelse(panel_data$country == "CHN", PAL[["chn"]], PAL[["num"]]))
panel_data$num_face <- ifelse(panel_data$country %in% c("USA", "CHN"), "bold", "plain")
n_a <- nlevels(panel_data$label)
XMIN <- 0.0892

pa <- ggplot(panel_data, aes(x = visibility_multiplier, y = label)) +
  geom_rect(aes(xmin = XMIN, xmax = visibility_multiplier,
                ymin = as.numeric(label) - 0.29, ymax = as.numeric(label) + 0.29, fill = fill),
            show.legend = FALSE) +
  annotate("segment", x = XMIN, xend = 200, y = 6.5, yend = 6.5, colour = PAL[["line"]], linewidth = 0.35) +
  geom_vline(xintercept = 1, linetype = "dashed", linewidth = 0.4, colour = PAL[["refline"]]) +
  geom_text(aes(x = visibility_multiplier * 1.22, label = sprintf("%.2f", visibility_multiplier)),
            hjust = 0, size = 2.9, colour = panel_data$num_col, fontface = panel_data$num_face) +
  annotate("text", x = 1.16, y = n_a + 0.80, label = "按人口应得 = 1", hjust = 0, size = 2.9, colour = "#7A7A7A") +
  annotate("text", x = 1.6, y = 1.78, hjust = 0, label = "G7 提及 43.9%", size = 2.6, colour = PAL[["ink_mid"]]) +
  annotate("text", x = 1.6, y = 1.22, hjust = 0, label = "南方七国 7.6%", size = 2.6, colour = PAL[["ink_mid"]]) +
  annotate("text", x = 30, y = 5.4, label = "■ 美国", hjust = 0, size = 2.2, colour = PAL[["usa"]]) +
  annotate("text", x = 30, y = 4.8, label = "■ 中国大陆", hjust = 0, size = 2.2, colour = PAL[["chn"]]) +
  annotate("text", x = 30, y = 4.2, label = "■ 高于人口应得", hjust = 0, size = 2.2, colour = PAL[["above"]]) +
  annotate("text", x = 30, y = 3.6, label = "■ 低于人口应得", hjust = 0, size = 2.2, colour = PAL[["below"]]) +
  scale_fill_identity() +
  scale_x_log10(breaks = c(0.1, 0.3, 1, 3, 10, 30), labels = c("0.1", "0.3", "1", "3", "10", "30"),
                expand = expansion(mult = c(0.02, 0.30))) +
  scale_y_discrete(expand = expansion(add = c(0.55, 1.20))) +
  labs(x = "能见度倍率（新闻流提及份额 ÷ 人口份额，对数轴）", y = NULL, tag = "a") +
  theme_nature_contract(base_size = 9) +
  theme(axis.text.y = element_text(size = 9, colour = PAL[["ink"]]),
        axis.text.x = element_text(size = 8.5, colour = PAL[["ink"]]),
        axis.title.x = element_text(size = 8.5, colour = PAL[["ink"]]))

events <- c(USA = "国会山事件", ISR = "加沙战争", AFG = "美军撤离", UKR = "俄乌开战", PRK = "金特会",
            TWN = "佩洛西窜访台湾", IRN = "苏莱曼尼", VEN = "承认瓜伊多", SAU = "卡舒吉案")
selected_peaks <- c("USA", "ISR", "AFG", "UKR", "PRK", "TWN", "IRN", "VEN", "SAU")
peaks <- read.csv(file.path("data", "analysis", "e3_peak_months.csv"))
peaks <- peaks[peaks$country %in% selected_peaks, ]
peaks$month <- sub(":.*", "", peaks$peak1)
peaks$share <- as.numeric(sub("%", "", sub(".*:", "", peaks$peak1)))
peaks$date <- as.Date(paste0(peaks$month, "01"), format = "%Y%m%d")
peaks$label <- cn[peaks$country]
peaks$event <- events[peaks$country]
peaks <- peaks[order(peaks$date, decreasing = TRUE), ]
peaks$ylabel <- factor(peaks$label, levels = rev(peaks$label))
peaks$col <- ifelse(peaks$country == "USA", PAL[["usa"]], PAL[["bubble"]])
n_b <- nlevels(peaks$ylabel)
peaks$dia_mm <- sqrt(scales::rescale(peaks$share, to = c(2.2^2, 6.2^2)))
peaks$nudge_mo <- peaks$dia_mm / 2 * 3 + ifelse(peaks$share < 3, 1.0, 4)
legend_data <- data.frame(x = as.Date(c("2017-01-01", "2020-08-01", "2024-04-01")),
                          share = c(5, 15, 30), lab = c("5%", "15%", "30%"))

pb <- ggplot(peaks, aes(x = date, y = ylabel)) +
  geom_segment(aes(x = as.Date("2015-03-01"), xend = date, y = ylabel, yend = ylabel),
               linewidth = 0.3, colour = PAL[["line"]]) +
  geom_point(aes(size = share), shape = 21, fill = peaks$col, colour = "white", stroke = 0.4, show.legend = FALSE) +
  geom_text(aes(x = date, y = ylabel, label = event), hjust = 0,
            nudge_x = peaks$nudge_mo * 30.4, size = 2.8, colour = PAL[["ink_mid"]]) +
  geom_point(data = legend_data, aes(x = x, y = n_b + 1.70, size = share), inherit.aes = FALSE,
             shape = 21, fill = PAL[["bubble"]], colour = "white", stroke = 0.4, show.legend = FALSE) +
  geom_text(data = legend_data, aes(x = x, y = n_b + 0.95, label = lab), inherit.aes = FALSE,
            hjust = 0.5, size = 2.9, colour = PAL[["ink"]]) +
  annotate("text", x = as.Date("2015-04-01"), y = n_b + 2.45, label = "峰值月份额",
           hjust = 0, size = 2.9, colour = PAL[["ink"]]) +
  scale_size_continuous(range = c(2.2, 6.2)) +
  scale_x_date(breaks = seq(as.Date("2016-01-01"), as.Date("2026-01-01"), by = "2 years"),
               date_labels = "%Y", limits = c(as.Date("2015-03-01"), as.Date("2027-06-01")),
               expand = expansion(mult = c(0.01, 0.01))) +
  scale_y_discrete(expand = expansion(add = c(0.5, 2.8))) +
  labs(x = NULL, y = NULL, tag = "b") +
  theme_nature_contract(base_size = 9) +
  theme(legend.position = "none", axis.text.y = element_text(size = 9, colour = PAL[["ink"]]),
        axis.text.x = element_text(size = 8.5, colour = PAL[["ink"]]))

figure1 <- pa + pb + plot_layout(widths = c(1, 1.4))
save_pub_r(figure1, file.path("figures", "figure1_visibility"), width_mm = 183, height_mm = 95)
cat(sprintf("figure1: %d visibility rows, %d peak rows\n", n_a, n_b))
