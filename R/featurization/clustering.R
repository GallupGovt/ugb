getPackages <- function (list.of.packages) {
#
# Takes a list or vector of package names and loads them, installing first if they 
# are not already installed.
# 
  new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]

  if(length(new.packages)) install.packages(new.packages)
  lapply(list.of.packages,require,character.only=T)
}


runClusters <- function(dat,maxClusters=15,setClusters=1,reproducable=FALSE) {
#
# Takes in a data.table and clusters based on all variables.
# if "setClusters" is defined greater than 1, maxClusters is ignored. If reproducable
# is a number, use that to set.seed().
# Returns list of clustering models.
# 

    if (setClusters>1) {
        if (reproducable) set.seed(reproducable)
        cl <- list(kmeans(dat,setClusters,nstart=20))
    } else {
        cl <- foreach(x=2:maxClusters, .export="runClusters", .packages=c("foreach","doParallel")) %dopar% {
            if (reproducable) set.seed(reproducable)
            clPrime <- runClusters(dat, setClusters=x, reproducable=reproducable)
            clPrime[[which.min(unlist(lapply(clPrime,function(x) x$tot.withinss)))]]
            # kmeans(dat,x,nstart=20)
        }
    }

    return(cl)
}


dist2d <- function(a,b,c) {
#
# Calculates Euclidean distance between two points
# 
    v1 <- b - c
    v2 <- a - b
    m <- cbind(v1,v2)
    d <- abs(det(m))/sqrt(sum(v1*v1))
} 


pickBestCluster <- function(dat,groups=1,maxClusters=15,setClusters=1,reproducable=FALSE,plot=TRUE) {
#
# Performs an ensemble k-means clustering on a data.table of variables. The data is split into 
# "groups" segments and 2:maxClusters k-means clustering attempts are run on each segment. 
# Performance (reduction in between-class-sum-of-squares) is calculated for each k, and results
# are averaged across the segments. Euclidean distance is employed to choose the best cluster #
# via the "elbow method." A final "best" k-means clustering is run on the whole dataset and
# a cluster membership vector is returned.
# 

    args <- c(maxClusters,setClusters,reproducable)

    if (setClusters==1) {
        dat[,sampNum:=sample(1:groups,nrow(dat),rep=T)]

        if (groups!=1) {
            datSamples <- split(dat,by="sampNum")
        } else {
            datSamples <- list(dat)
        }        

        cl <- lapply(datSamples,function(x) runClusters(x[,sampNum:=NULL],args[1],args[2],args[3]))

        performance <- lapply(cl,function(x) unlist(lapply(x,function(y)y$betweenss/y$totss)))
        assign("clusterOptions",cl,.GlobalEnv)
        assign("clustering",performance,.GlobalEnv)
        performance <- colMeans(as.data.frame(do.call(rbind, performance)))

        if(plot) plot(2:maxClusters,diff(c(0,performance)),type="b",col="red")

        performance <- cbind(seq.int(length(performance)),diff(c(0,performance)))
        pt1 <- performance[1,]
        pt2 <- performance[nrow(performance),]

        clustPerf <- apply(performance,1,function(x)dist2d(x,pt1,pt2))
        assign("clustPerf",clustPerf,.GlobalEnv)

        bestClust <- which.max(clustPerf)+1
        args[2] <- bestClust
        dat[,sampNum:=NULL]
    }

    cl <- runClusters(dat,args[1],args[2],args[3])
    bestClust <- which.min(unlist(lapply(cl,function(x) x$tot.withinss)))
    cl <- cl[[which.min(unlist(lapply(cl,function(x) x$tot.withinss)))]]
    cl$seed <- bestClust
    assign("bestClust",cl,.GlobalEnv)
    dat[,CLUSTER:=as.factor(cl$cluster)]

    return(dat$CLUSTER)
}
