#!/usr/loca/bin/R
# generate individual level bias scores for ugb
# questions? contact matt_hoover@gallup.com

# load libraries
library(data.table)

# define constants
key_vars <- c(
    'art_id',
    'title_embeddings_gender',
    'title_embeddings_race',
    'title_embeddings_power',
    'art_text_embeddings_gender',
    'art_text_embeddings_race',
    'art_text_embeddings_power',
    'title_sent_neg',
    'title_sent_neu',
    'title_sent_pos',
    'art_sent_neg',
    'art_sent_neu',
    'art_sent_pos',
    'art_comments',
    'CLUSTER',
    'comment_embeddings_gender',
    'comment_embeddings_race',
    'comment_embeddings_power',
    'upvotes',
    'comm_sent_neg',
    'comm_sent_neu',
    'comm_sent_pos',
    'commenter',
    'comment_embed_sum'
)

# create functions
build_scores <- function(n = 500) {
    results <- list()
    for(i in 1:n) {
        his <- runif(11, 0, 1)
        his <- his[order(his)]
        los <- sapply(his, function(x) {runif(1, 0, x)})
        los <- his - los
        wgts <- c(runif(1, 0, 1), runif(1, 0, .5))
        tmp <- (
            commenters$med_comm_embed * wgts[1] +
            1 / commenters$med_art_comments * wgts[2]
        )
        cuts <- as.numeric(quantile(tmp, seq(0, 1, .1), na.rm = TRUE))
        score <- ifelse(tmp > cuts[1] & tmp <= cuts[2], runif(length(tmp), los[1], his[1]),
            ifelse(tmp > cuts[2] & tmp <= cuts[3], runif(length(tmp), los[2], his[2]),
            ifelse(tmp > cuts[3] & tmp <= cuts[4], runif(length(tmp), los[3], his[3]),
            ifelse(tmp > cuts[4] & tmp <= cuts[5], runif(length(tmp), los[4], his[4]),
            ifelse(tmp > cuts[5] & tmp <= cuts[6], runif(length(tmp), los[5], his[5]),
            ifelse(tmp > cuts[6] & tmp <= cuts[7], runif(length(tmp), los[6], his[6]),
            ifelse(tmp > cuts[7] & tmp <= cuts[8], runif(length(tmp), los[7], his[7]),
            ifelse(tmp > cuts[8] & tmp <= cuts[9], runif(length(tmp), los[8], his[8]),
            ifelse(tmp > cuts[9] & tmp <= cuts[10], runif(length(tmp), los[9], his[9]),
            ifelse(tmp > cuts[10] & tmp <= cuts[11], runif(length(tmp), los[10], his[10]),
                   runif(length(tmp), los[11], his[11])
        ))))))))))
        results[[i]] <- list(iter = i,
                             bias = score,
                             weights = wgts,
                             low_vals = los,
                             high_vals = his
        )
        names(results)[i] <- paste0('z', i)
        print(paste('Finished iteration', i, 'of', n))
    }
    return(results)
}

# get passed arguments
args <- commandArgs(trailingOnly = TRUE)

# load data
d <- fread(paste('data', args[1], sep = '/'))
cols <- grep('comment_embeddings_V', names(d))
d$comment_embed_sum <- apply(d[, ..cols], 1, sum)
d$comment_embed_sum <- (d$comment_embed_sum -
                        mean(d$comment_embed_sum)) / sd(d$comment_embed_sum)

# deal with subset of variables of interest
slim <- d[, ..key_vars]

# clean up variables
slim$upvotes <- as.numeric(gsub('[^0-9+\\-]', '', slim$upvotes))

# aggregate to individual commenter
commenters <- slim[,
    list(med_gender = median(comment_embeddings_gender, na.rm = TRUE),
         med_race = median(comment_embeddings_race, na.rm = TRUE),
         med_power = median(comment_embeddings_power, na.rm = TRUE),
         med_upvotes = median(upvotes, na.rm = TRUE),
         med_sent_neg = median(comm_sent_neg, na.rm = TRUE),
         med_sent_pos = median(comm_sent_pos, na.rm = TRUE),
         med_art_comments = median(art_comments, na.rm = TRUE),
         med_comm_embed = median(comment_embed_sum, na.rm = TRUE)
    ),
    by = list(commenter = commenter)
]

# create bias scores
bias_scores <- build_scores()

# merge bias scores back to data
tmp <- mapply(function(x, name) {
    set(commenters, j = name, value = x$bias)
}, bias_scores, names(bias_scores), SIMPLIFY = FALSE)

merge_cols <- grep('commenter|^z', names(commenters))
slim <- merge(slim, commenters[, ..merge_cols], by = 'commenter')

# generate metadata for outputting
metad <- data.frame(do.call(rbind, lapply(bias_scores, function(x) {
    return(c(x$iter, paste(x$weights, collapse = ','),
             paste(x$low_vals, collapse = ','),
             paste(x$high_vals, collapse = ',')))
})))
names(metad) <- c('iteration', 'weights', 'low_values', 'high_values')
metad$variable <- rownames(metad)

# write to disk
write.csv(slim, file = paste('hlm', args[2], sep = '/'), row.names = FALSE)
write.csv(metad, file = paste('hlm', args[3], sep = '/'), row.names = FALSE)
