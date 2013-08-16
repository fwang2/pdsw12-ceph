require("ggplot2")

plot_xfs <- function(file) {
    cat("Processing: ", file, "\n")
    df=read.csv(file, strip.white=TRUE)

    # compute min and max 
    ymin=as.integer(min(df$bw.max))
    ymax=as.integer(max(df$bw.max))


    xmin=as.integer(min(df$num.dev))
    xmax=as.integer(max(df$num.dev))

    quartz(type="pdf", file="xfs.pdf")
    theme_set(theme_bw(base_family="Lucida Grande", base_size=18))
    g = qplot(num.dev, bw.max,
            data=df,
            shape=factor(df$mode),
            color=factor(df$mode),
            method=loess,
            geom=c("point", "smooth"),
            ylab="Max (MB/s)\n",
            xlab="\nNum of Devices",
            main="XFS, xdd -dio qd=4, req.size=32768")
    g = g + scale_shape_discrete(name="IO mode")
    g = g + scale_color_discrete(name="IO mode")
    g = g + geom_point(size=3.5)
    g = g + geom_smooth(size=1.5)
    g = g + opts(legend.position="top")
    #g = g + scale_y_continuous(breaks=seq(ymin, ymax,
    #                as.integer((ymax-ymin)/5)))
    g = g + scale_x_continuous(breaks=seq(xmin, xmax))
    g = g + opts(panel.grid.major = theme_line(color="grey80", size = 0.7, linetype = "dashed"))
    g = g + opts(panel.grid.minor = theme_line(color="grey80", size = 0.7, linetype = "dotted"))
 
    print(g)
    dev.off()
            
}


args = commandArgs(trailingOnly = TRUE)
options(warn=-1)
plot_xfs(args[1])


