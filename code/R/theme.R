library(ggplot2)
library(patchwork)
library(scales)

palette_contract <- c(
  neutral_dark = "#272727",
  neutral_mid = "#767676",
  neutral_light = "#D8D8D8",
  signal_blue = "#3182BD",
  signal_teal = "#33B5A5",
  accent_red = "#D24B40",
  accent_orange = "#E28E2C"
)

if (.Platform$OS.type == "windows") {
  windowsFonts(yahei = windowsFont("Microsoft YaHei"))
  FONT_CN <- "yahei"
} else {
  FONT_CN <- "sans"
}

theme_nature_contract <- function(base_size = 8, base_family = FONT_CN) {
  theme_classic(base_size = base_size, base_family = base_family) +
    theme(
      axis.line = element_line(linewidth = 0.35, colour = "black"),
      axis.ticks = element_line(linewidth = 0.35, colour = "black"),
      axis.title = element_text(size = base_size),
      axis.text = element_text(size = base_size - 0.5),
      legend.title = element_text(size = base_size - 0.3),
      legend.text = element_text(size = base_size - 0.7),
      strip.text = element_text(size = base_size - 0.3, face = "bold"),
      plot.title = element_text(size = base_size + 0.5, face = "bold"),
      plot.tag = element_text(size = base_size + 1, face = "bold"),
      panel.grid = element_blank(),
      legend.position = "right",
      plot.margin = margin(4, 6, 4, 4)
    )
}

theme_set(theme_nature_contract())

geom_break <- function(break_x, ci_lo = NULL, ci_hi = NULL, color = palette_contract[["accent_red"]]) {
  layers <- list()
  if (!is.null(ci_lo) && !is.null(ci_hi)) {
    layers <- c(layers, list(
      annotate("rect", xmin = ci_lo, xmax = ci_hi, ymin = -Inf, ymax = Inf, fill = color, alpha = 0.12)
    ))
  }
  c(layers, list(geom_vline(xintercept = break_x, linetype = "dashed", linewidth = 0.5, colour = color)))
}

geom_step_means <- function(data, ycol, breaks, color = palette_contract[["neutral_dark"]]) {
  cuts <- c(-Inf, as.numeric(breaks), Inf)
  data$seg <- cut(as.numeric(data$month_date), breaks = cuts, labels = FALSE)
  seg <- aggregate(data[[ycol]], by = list(data$seg), FUN = mean, na.rm = TRUE)
  bounds <- c(min(data$month_date), breaks, max(data$month_date))
  frame <- data.frame(x0 = bounds[-length(bounds)], x1 = bounds[-1], y = seg$x)
  geom_segment(data = frame, aes(x = x0, xend = x1, y = y, yend = y), colour = color, linewidth = 0.8)
}

save_pub_r <- function(plot, filename, width_mm = 183, height_mm = 100, dpi = 600) {
  width <- width_mm / 25.4
  height <- height_mm / 25.4
  svglite::svglite(paste0(filename, ".svg"), width = width, height = height)
  print(plot)
  dev.off()
  grDevices::cairo_pdf(paste0(filename, ".pdf"), width = width, height = height, family = FONT_CN)
  print(plot)
  dev.off()
  ragg::agg_tiff(paste0(filename, ".tiff"), width = width, height = height, units = "in", res = dpi)
  print(plot)
  dev.off()
  ragg::agg_png(paste0(filename, ".png"), width = width, height = height, units = "in", res = 200)
  print(plot)
  dev.off()
  invisible(filename)
}

month_axis <- function() {
  list(
    scale_x_date(date_breaks = "1 year", date_labels = "%Y", expand = expansion(mult = c(0.01, 0.01))),
    theme(axis.text.x = element_text(size = 6.5))
  )
}

label_minus <- function(values) {
  gsub("-", "\u2212", format(values, trim = TRUE, scientific = FALSE))
}

to_date <- function(ym) {
  as.Date(paste0(ym, "01"), format = "%Y%m%d")
}
