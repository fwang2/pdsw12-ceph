library("ggplot2")

# read data, skip comments
df = read.csv(file="replication.csv", comment.char = "#")


quartz(type="pdf", file="rep.pdf")
theme_set(theme_bw(base_family="Lucida Grande", base_size=18))


g = ggplot(df, aes(x=rep, y=bw, fill=factor(mode))) +
    geom_bar(stat="identity", position="dodge", color="black") +
    scale_fill_brewer(type="qual", palette=3)



# g = g + theme((aspect.ratio=1)


# g = g + ggtitle("RADOS bench throughput \n with different replication levels\n")
g = g + xlab("\nReplication Levels") + ylab("Throughput\n")

# change legend position
g = g + theme(legend.position="top")

# hide the legend title
g = g + guides(fill=guide_legend(title=NULL))

# make more breaks along Y
g = g + scale_y_continuous(breaks=seq(0, 10000,2000))

# change grid line display
#g = g + theme(panel.grid.major = element_line(color="grey80", size = 0.7, linetype = "dashed"))
#g = g + theme(panel.grid.minor = element_line(color="grey80", size = 0.7, linetype = "dotted"))



print(g)
dev.off()
