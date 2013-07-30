
plot_mdtest <- function(file) {
    cat("Processing: ", file, "\n")
    df=read.csv(file, strip.white=TRUE, skip=1)

    quartz(type="pdf", file="mdtest.pdf")
    theme_set(theme_bw(base_family="Lucida Grande"))
    
    df2 = melt(df, id.vars=c("client.num", "mode"))
    names(df2)[3] = "ops"
    names(df2)[4] = "max"
    g = qplot(client.num, max, data=df2,
              ylab = "Max (ops/second)",
              xlab = "Number of clients",
              main = "-n 1000 [-u] -y -w 1048576 -i 5")
    g = g + geom_point(size=3.5)
    g = g + geom_line(size=1.5)
    g = g + facet_grid(mode ~ ops)
    # g = g + opts(aspect.ratio = 2)
    # g = g + opts(plot.margin = unit(c(1,1,2,2), 'lines'))
    g = g + opts(panel.grid.major = theme_line(color="grey80", size = 0.7, linetype = "dashed"))
    g = g + opts(panel.grid.minor = theme_line(color="grey80", size = 0.7, linetype = "dotted"))
    
    print(g)
    
      
    quartz(type="pdf", file="mdtest-fcreate.pdf")
    theme_set(theme_bw(base_family="Lucida Grande"))
    df2 = subset(df, , c("client.num", "mode", "fcreate"))
    df2 = melt(df2, id.vars=c("client.num", "mode"))
    names(df2)[3] = "ops"
    names(df2)[4] = "max"
    g = qplot(client.num, max, data=df2,
              ylab = "Max (ops/second)",
              xlab = "Number of clients")
    g = g + geom_point(size=3.5)
    g = g + geom_line(size=1.5)
    g = g + facet_grid(mode ~ ops)
    # g = g + opts(aspect.ratio = 2)
    # g = g + opts(plot.margin = unit(c(1,1,2,2), 'lines'))
    g = g + opts(panel.grid.major = theme_line(color="grey80", size = 0.7, linetype = "dashed"))
    g = g + opts(panel.grid.minor = theme_line(color="grey80", size = 0.7, linetype = "dotted"))

    print(g)

    quartz(type="pdf", file="mdtest-dcreate.pdf")
    theme_set(theme_bw(base_family="Lucida Grande"))
    df2 = subset(df, , c("client.num", "mode", "dcreate"))
    df2 = melt(df2, id.vars=c("client.num", "mode"))
    names(df2)[3] = "ops"
    names(df2)[4] = "max"
    g = qplot(client.num, max, data=df2,
              ylab = "Max (ops/second)",
              xlab = "Number of clients")
    g = g + geom_point(size=3.5)
    g = g + geom_line(size=1.5)
    g = g + facet_grid(mode ~ ops)
    # g = g + opts(aspect.ratio = 2)
    # g = g + opts(plot.margin = unit(c(1,1,2,2), 'lines'))
    g = g + opts(panel.grid.major = theme_line(color="grey80", size = 0.7, linetype = "dashed"))
    g = g + opts(panel.grid.minor = theme_line(color="grey80", size = 0.7, linetype = "dotted"))
    
    print(g)
    
    
    dev.off()
            
}
library(ggplot2)
library(grid)
library(reshape2)
args = commandArgs(trailingOnly = TRUE)
options(warn=-1)
plot_mdtest(args[1])


