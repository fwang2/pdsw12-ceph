xdd = function(file, mode) {
    print(file)
    print(mode)
    }

args = commandArgs(trailingOnly=TRUE)
print(args)
xdd (args[1],args[2])
