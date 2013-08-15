require("ggplot2")

plot_xdd <- function(f, m) {
    cat("Processing: ", f, m , "\n")
    df=read.csv(f, strip.white=TRUE)

    # compute min and max 
    ymin=as.integer(min(df$bw))
    ymax=as.integer(max(df$bw))


    xmin=as.integer(min(df$dev.num))
    xmax=as.integer(max(df$dev.num))

    quartz(type="pdf", file=paste("xdd-", m, ".pdf", sep=""))
    theme_set(theme_bw(base_family="Lucida Grande", base_size=18))
    g = qplot(dev.num, bw,
            data=df,
            shape=factor(df$qd),
            color=factor(df$qd),
            method=loess,
            #geom=c("point", "smooth"),
            ylab="Max (MB/s)\n",
            xlab="\nNum of Devices",
            main=paste("XFS ", m, " xdd -dio, req.size=32768", sep=""))
    g = g + scale_shape_discrete(name="queue depth")
    g = g + scale_color_discrete(name="queue depth")
    g = g + geom_point(size=3.5)
    g = g + geom_line(size=1.5)
    g = g + opts(legend.position="top")
    g = g + scale_y_continuous(breaks=seq(ymin, ymax,
                    as.integer((ymax-ymin)/5)))
    g = g + scale_x_continuous(breaks=seq(xmin, xmax))
    g = g + opts(panel.grid.major = theme_line(color="grey80", size = 0.7, linetype = "dashed"))
    g = g + opts(panel.grid.minor = theme_line(color="grey80", size = 0.7, linetype = "dotted"))
 
    print(g)
    dev.off()
            
}

args = commandArgs(trailingOnly = TRUE)
print(args)
options(warn=-1)
plot_xdd(args[1], args[2])


