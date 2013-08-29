library("ggplot2")

myplot <- function (inf, outf) {

# read data, skip comments
df = read.csv(inf, comment.char = "#", strip.white = TRUE)

quartz(type="pdf", file=outf, width=10, height=6)
theme_set(theme_bw(base_family="Lucida Grande", base_size=18))


g = ggplot(df, aes(x=mode, y=bw, fill=factor(mode))) +
    geom_bar(stat="identity", position="dodge", color="black", width=0.5) +
    scale_fill_brewer(type="qual", palette=1)



# g = g + theme((aspect.ratio=1)


g = g + xlab("\n16GB BlockSize, 4 MB Read Ahead, 8 Client Nodes") + ylab("Throughput (MB /s) \n")

# change legend position
g = g + theme(legend.position="top")
#g = g + coord_fixed(ratio=5)

# hide the legend title
g = g + guides(fill=guide_legend(title=NULL))

# make more breaks along Y
g = g + scale_y_continuous(breaks=seq(0, 9000,1000))

# change grid line display
#g = g + theme(panel.grid.major = element_line(color="grey80", size = 0.7, linetype = "dashed"))
#g = g + theme(panel.grid.minor = element_line(color="grey80", size = 0.7, linetype = "dotted"))



print(g)
dev.off()
}


args = commandArgs(trailingOnly = TRUE)
print(args)
options(warn=-1)
myplot(args[1], args[2])
         