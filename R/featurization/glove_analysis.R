
#
# R functions and packages for featurizing text with GloVe word embeddings
# 

library(data.table)
library(dplyr)
library(text2vec)
library(iterators)
library(Rtsne)
library(NLP)
library(openNLP)
library(doParallel)
library(foreach)


word_tokenizer <- function(txt, sta, wta) {
    #
    # Apply Stanford Tokenizer to txt, returning a vector of char() tokens
    # 

    words <- NLP::annotate(txt, list(sta, wta)) %>% 
    lapply(function(x) ifelse(x$type=='word',substr(txt,x$start,x$end),'')) %>%
    unlist()
    words <- words[words!='']

    return(words)
}


trainEmbeddings <- function(docs, 
                            term_count_min=5L, 
                            skip_grams_window=10L, 
                            word_vectors_size=300, 
                            x_max=100, 
                            n_iter=100, 
                            convergence_tol=0.001, 
                            alpha=0.05) {
    sta <- Maxent_Sent_Token_Annotator()
    wta <- Maxent_Word_Token_Annotator()
    docs <- tolower(docs)

    it <- itoken_parallel(docs, 
                          tokenizer=function(x) word_tokenizer(x, sta, wta), 
                          progressbar=TRUE)
    vocab <- create_vocabulary(it)

    pruned_vocab <- prune_vocabulary(vocab, term_count_min = term_count_min)
    vectorizer = vocab_vectorizer(pruned_vocab)
    tcm = create_tcm(it, vectorizer, skip_grams_window = skip_grams_window)

    glove = GlobalVectors$new(word_vectors_size=word_vectors_size, 
                              vocabulary = pruned_vocab, 
                              x_max = x_max, 
                              learning_rate = alpha)
    wv_main = glove$fit_transform(tcm, 
                                  n_iter = n_iter, 
                                  convergence_tol = convergence_tol, )

    # Combine context and target word vectors in the same manner as
    # original GloVe research 
    word_vectors = wv_main + t(glove$components)

    return(word_vectors)
}


gloved <- function(tokens, wv, sta, wta) {
    #
    # Average word embeddings for a text; ignore 
    # out-of-vocabulary words 
    # 

    tokens <- tokens[tokens %in% rownames(wv)]
    text <- wv[tokens, , drop=FALSE]

    vector <- colMeans(text)

    return(vector)
}


getTokens <- function(txts){
    tokens <- foreach(i = 1:length(txts), .inorder=TRUE, .export=c('word_tokenizer'),
                .packages = c('NLP','openNLP','dplyr'),
                .multicombine = TRUE, 
                .options.multicore = list(preschedule = FALSE)) %dopar% {
            word_tokenizer(txts[i], 
                           Maxent_Sent_Token_Annotator(),
                           Maxent_Word_Token_Annotator())
        }
    return(tokens)
}


deriveBias <- function(pairs, wv=word_vectors, method='mean', diag=FALSE) {
    #
    # Give a set of word pairs, calculate the average of their
    # differences as a "bias" vector.
    # 
    if(class(pairs) == 'list') {
        diffs <- lapply(pairs, function(x) wv[x[1],,drop=FALSE]-wv[x[2],,drop=FALSE])
        diffs <- do.call(rbind, diffs)
    } else {
        pairs <- pairs[tolower(pairs) %in% rownames(wv)]
        diffs <- wv[tolower(pairs),,drop=FALSE]
        method <- 'pca'
    }

    if(method=='pca'){
        pr.out <- prcomp(diffs, center=F, scale=F)
        b <- matrix(pr.out$rotation[,1],1,300)

        if(diag) {
            pr.var <- pr.out$sdev**2
            print(pr.var/sum(pr.var))
        }
    } else if(method=='mean') {
        b <- matrix(colMeans(diffs), 1, 300)
    }

    return(b)
}


biasComponent <- function(w1, b, wv=NULL, metric='pos') {
    #
    # Calculates the projection of word w1 on the bias direction b
    # 

    if(class(w1) == 'character') {
        w1 <- wv[w1,,drop=FALSE]
    }

    result <- as.numeric(w1 %*% t(b))/(sum(b**2) * b)

    if(metric == 'pos') {
        result <- sim2(result, w1, method='cosine', norm='l2')
    } else if(metric=='neg') {
        result <- -sim2(result, w1, method='cosine', norm='l2')
    } else if(metric=='abs') {
        result <- abs(sim2(result, w1, method='cosine', norm='l2'))
    } else {
        print('Unknown metric')
        return()
    }
    
    return(result)
}


avgBias <- function(tokens, bias, wv) {


    tokens <- tokens[tokens %in% rownames(wv)]
    embeddings <- wv[tokens, , drop=FALSE]
    embeddings <- lapply(1:nrow(embeddings), 
                         function(x) biasComponent(embeddings[x,,drop=FALSE], 
                                                   bias))
    bias <- mean(unlist(embeddings))
    return(bias)
}
