require("ggplot2")

plot_xfs <- function(file) {
    cat("Processing: ", file, "\n")
    df=read.csv(file, strip.white=TRUE)

    # compute min and max 
    ymin=as.integer(min(df$bw))
    ymax=as.integer(max(df$bw))

    tsize=df$tsize[1]
    np = ymax

    xmin=as.integer(min(df$np))
    xmax=as.integer(max(df$np))

    quartz(type="pdf", file=paste("ior_", tsize, ".pdf", sep =""))
    theme_set(theme_bw(base_family="Lucida Grande", base_size=18))
    g = qplot(np, bw,
            data=df,
            shape=factor(df$mode),
            color=factor(df$mode),
            method=loess,
            # geom=c("point", "smooth"),
            ylab="Max (MB/s)\n",
            xlab="\nNum of clients",
            main=paste("IOR: transfer size=", tsize,sep=""))
    g = g + scale_shape_discrete(name="IO mode")
    g = g + scale_color_discrete(name="IO mode")
    g = g + geom_point(size=3)
    g = g + geom_line(size=1.5)
    g = g + opts(legend.position="top")
    #g = g + scale_y_continuous(breaks=seq(ymin, ymax,
    #                as.integer((ymax-ymin)/5)))
    g = g + coord_cartesian(ylim=c(0,2500)) + scale_y_continuous(breaks=seq(0, 2500,500))
    g = g + scale_x_continuous(breaks=seq(xmin, xmax))

    g = g + opts(panel.grid.major = theme_line(color="grey80", size = 0.7, linetype = "dashed"))
    g = g + opts(panel.grid.minor = theme_line(color="grey80", size = 0.7, linetype = "dotted"))
    print(g)
    dev.off()
            
}


args = commandArgs(trailingOnly = TRUE)
options(warn=-1)
plot_xfs(args[1])


