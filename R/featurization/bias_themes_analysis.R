
#
# Defining and deriving biases
# 

biasComponent <- function(w1, b, metric='abs') {
    #
    # Calculates the projection of word w1 on the bias direction b
    # 

    if(metric == 'pos') {
        result <- sim2(b, w1, method='cosine', norm='l2')
    } else if(metric=='neg') {
        result <- -sim2(b, w1, method='cosine', norm='l2')
    } else if(metric=='abs') {
        result <- abs(sim2(b, w1, method='cosine', norm='l2'))
    } else {
        print('Unknown metric')
        return()
    }
    
    return(result)
}


getBias <- function(tokens, bias, wv, ret=c('mean', 'list')) {

    tokens <- tokens[tokens %in% rownames(wv)]
    embeddings <- wv[tokens, , drop=FALSE]
    embeddings <- lapply(1:nrow(embeddings), 
                         function(x) biasComponent(embeddings[x,,drop=FALSE], 
                                                   bias))
    
    if(ret=='mean') {
        bias <- mean(unlist(embeddings))
    } else if (ret=='list') {
        bias <- unlist(embeddings)
    }

    return(bias)
}


biasDropOut <- function(axes, agg='mean') {
    dropOutList = list()

    for(i in 1:nrow(axes)) {
        axp <- axes[-i,,drop=FALSE]

        if (agg=='pca') {
            agg_axp <- matrix(prcomp(axp)$rotation[,1],1,dim(wv)[2])
        } else {
            agg_axp <- matrix(colMeans(axp), 1, dim(wv)[2])
        }

        dropOutList[[i]] <- sim2(x=axp, y=agg_axp, method='cosine', norm='l2')
    }

    dropOutMat <- dropOutList[[1]]

    for (i in 2:length(dropOutList)) {
       dropOutMat <- merge(dropOutMat, dropOutList[[i]], by='row.names', all=TRUE)
       rownames(dropOutMat) <- dropOutMat$Row.names
       dropOutMat <- as.matrix(dropOutMat[,-1])
       colnames(dropOutMat) <- rownames(axes)[1:i]
    }

    dr

    return(dropOutMat)
}


biasPairDist <- function(pairs, wv, agg=c('mean','pca','none'), dropout=FALSE) {
    axes <- lapply(pairs, function(x) wv[x[1],,drop=FALSE] - wv[x[2],,drop=FALSE])
    axes <- do.call(rbind, axes)

    if (agg != 'none') {
        dropout = TRUE
        if (agg=='mean') {
            agg_bias <- matrix(colMeans(axes), 1, dim(wv)[2])
        } else if (agg=='pca') {
            agg_bias <- matrix(prcomp(axes)$rotation[,1],1,dim(wv)[2])
        }

        distmat <- sim2(x=axes, y=agg_bias, method='cosine', norm='l2')

        if (dropout) {
            dropout <- biasDropOut(axes, agg)
            drop_diffs <- sweep(dropout, MARGIN=1, distmat, `-`)
            best_drop <- which.max(colMeans(drop_diffs, na.rm=TRUE))
        }

    } else {
            distmat <- sim2(axes, method='cosine', norm='l2')
            dropout <- NA
    }

    dist <- list('distmat'=distmat, 'drop_out'=dropout)

    if (!class(dropout)=='logical') {
        dist$best_drop <- best_drop
    }

    return(dist)
}


visualizePairs <- function(pairs, wv, tsne=NULL) {
    words <- unique(unlist(pairs))
    colors = rainbow(length(words))
    names(colors) = words

    if(is.null(tsne)) {
        perp <- min(c(floor(length(words)/4)-1, 50))

        tsne <- Rtsne(wv[words,,drop=FALSE],
                      dims = 2, 
                      perplexity=perp, 
                      verbose=TRUE, 
                      max_iter = 5000,
                      check_duplicates=FALSE)
        plot(tsne$Y, t='n', main="tsne")
        text(tsne$Y, labels=words, col=colors[words])
    } else {
        tsne <- Rtsne(wv,
                      dims = 2, 
                      perplexity=50, 
                      verbose=TRUE, 
                      max_iter = 500,
                      check_duplicates=FALSE)
        plot(tsne$Y[rownames(wv) %in% words,], t='n', main="tsne")
        text(tsne$Y[rownames(wv) %in% words,], labels=words, col=colors[words])
    }

}


genderPairs <- list(c('she','he'), c('her','his'), c('woman','man'),
                c('herself','himself'), c('women','men'), c('mary','john'),
                c('mother','father'), c('girl','boy'), c('gal','guy'))

gender_words <- unlist(genderPairs)


white_names <- c('Adam', 'Chip', 'Harry', 'Josh', 'Roger', 'Alan', 'Frank',
    'Ian', 'Justin', 'Ryan', 'Andrew', 'Fred', 'Jack', 'Matthew', 'Stephen',
    'Brad', 'Greg', 'Jed', 'Paul', 'Todd', 'Brandon', 'Hank', 'Jonathan',
    'Peter', 'Wilbur', 'Amanda', 'Courtney', 'Heather', 'Melanie', 'Sara',
    'Amber', 'Crystal', 'Katie', 'Meredith', 'Shannon', 'Betsy', 'Donna',
    'Kristin', 'Nancy', 'Stephanie', 'Bobbie-Sue', 'Ellen', 'Lauren', 'Peggy',
    'Sue-Ellen', 'Colleen', 'Emily', 'Megan', 'Rachel', 'Wendy', 'Brendan',
    'Geoffrey', 'Brett', 'Jay', 'Neil', 'Allison', 'Anne', 'Carrie', 'Jill',
    'Laurie', 'Kristen', 'Sarah')

black_names <- c('Alonzo', 'Jamel', 'Lerone', 'Percell', 'Theo', 'Alphonse',
    'Jerome', 'Rasaan', 'Torrance', 'Lamar', 'Lionel',
    'Rashaun', 'Tvree', 'Deion', 'Lamont', 'Malik', 'Terrence', 'Tyrone',
    'Everol', 'Lavon', 'Marcellus', 'Terryl', 'Wardell', 'Aiesha', 'Lashelle',
    'Nichelle', 'Shereen', 'Temeka', 'Latisha', 'Shaniqua', 'Tameisha',
    'Teretha', 'Jasmine', 'Latonya', 'Shanise', 'Tanisha', 'Tia', 'Lakisha',
    'Latoya', 'Sharise', 'Tashika', 'Yolanda', 'Lashandra', 'Malika', 'Shavonn',
    'Tawanda', 'Yvette', 'Darnell', 'Hakim', 'Jermaine', 'Kareem', 'Jamal',
    'Leroy', 'Rasheed', 'Tremayne', 'Aisha', 'Ebony', 'Keisha',
    'Kenya', 'Tamika')
    
powerPairs <- list(c('feel','think'), c('original', 'reliable'), 
    c('tender','tough'), c('touching','convincing'), c('curious','accepting'), 
    c('unplanned','scheduled'), c('compassion','clout'), c('spontaneous','secure'), 
    c('rebel','conform'), c('gentle','firm'), c('creative','consistent'), 
    c('sensitive','strong'), c('skeptical', 'trusting'), c('innovative','traditional'))

