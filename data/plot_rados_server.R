require("ggplot2")
plot_xfs <- function(file) {
    cat("Processing: ", file, "\n")
    df=read.csv(file, strip.white=TRUE)

    # compute min and max 
    ymin=as.integer(min(df$bw))
    ymax=as.integer(max(df$bw))


    xmin=as.integer(min(df$node.num))
    xmax=as.integer(max(df$node.num))

    quartz(type="pdf", file="rados_server.pdf")
    theme_set(theme_bw(base_family="Lucida Grande", base_size=18))
    g = qplot(node.num, bw,
            data=df,
            shape=factor(df$mode),
            color=factor(df$mode),
            ylab="Max (MB/s)\n",
            xlab="\nNum of servers",
            main="Scaling server numbers")
    g = g + scale_shape_discrete(name="IO mode")
    g = g + scale_color_discrete(name="IO mode")
    g = g + geom_point(size=3.5)
    #g = g + geom_smooth(method=loess, se=FALSE)
    g = g + geom_line(size=1.5)
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


