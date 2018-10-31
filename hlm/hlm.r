#!/usr/local/bin/R
# hierarchical modeling for ugb
# questions? contact matt_hoover@gallup.com

# load libraries
library(data.table)
library(ggplot2)
library(lme4)
library(reshape2)
library(sjstats)

# get passed arguments
args <- commandArgs(trailingOnly = TRUE)
nargs <- sapply(args, function(x) {strsplit(x, '_')[[1]][1]})

# load data
d <- list()
for(i in 1:(length(args)-1)) {
    d[[i]] <- fread(paste('hlm', args[i], sep = '/'))
    d[[i]]$source <- nargs[i]
}
d <- do.call(rbind, d)

# prep modeling loop
metric_measure <- grep(args[length(args)], names(d))
outcomes <- grep('^z', names(d))
mod_results <- list()
i <- 1

# model against synthetic outcomes
for(outcome in outcomes) {
    mod <- d[, lmer(.SD[[outcome]] ~
                    .SD[[metric_measure[1]]] +
                    .SD[[metric_measure[2]]] +
                    title_sent_neg +
                    title_sent_pos +
                    art_sent_neg +
                    art_sent_pos +
                    art_comments +
                    .SD[[metric_measure[3]]] +
                    upvotes +
                    comm_sent_neg +
                    comm_sent_pos +
                    (1 | source) +
                    (1 | art_id) +
                    (1 | CLUSTER),
                    d, REML = FALSE)]
    mod_results[[i]] <- list(icc = icc(mod),
                             predictors = names(fixef(mod)),
                             estimate = coef(summary(mod))[, 1],
                             sterr = coef(summary(mod))[, 2],
                             tval = coef(summary(mod))[, 3])
    print(paste('Finished model', i, 'of', length(outcomes)))
    i <- i + 1
}

# create diagnostics
# iccs
iccs <- data.frame(
    n = 1:length(outcomes),
    Article = do.call(c, lapply(mod_results, function(x) {x$icc[1]})),
    Cluster = do.call(c, lapply(mod_results, function(x) {x$icc[2]})),
    Source = do.call(c, lapply(mod_results, function(x) {x$icc[3]}))
)
iccs_l <- melt(iccs, id.vars = 'n')
names(iccs_l)[2:3] <- c('Level', 'ICC')

pdf('hlm/icc_visual.pdf', height = 7.5, width = 10)
    print(ggplot(iccs_l, aes(x = n, y = ICC)) +
        geom_point(aes(color = Level)) +
        theme_bw() +
        labs(title = 'ICC Values by Level', x = 'Iteration') +
        theme(legend.position = 'bottom')
    )
dev.off()

# estimates
varnames <- c(
    paste0('Title embeddings (', args[length(args)], ')'),
    paste0('Article embeddings (', args[length(args)], ')'),
    'Title sentiment (negative)',
    'Title sentiment (positive)',
    'Article sentiment (negative)',
    'Article sentiment (positive)',
    'Nbr article comments',
    'Nbr upvotes',
    'Comment sentiment (negative)',
    'Comment sentiment (positive)'
)

# note: predictors 2-8 and 10-12 are of interest; predictor 1 is the intercept
#       and predictor 10 is weakly correlated to the outcome and therefore
#       inherently biased
ests <- do.call(rbind, mapply(function(x, i) {
    return(data.frame(
        n = i,
        Variable = varnames,
        Estimate = x$estimate[c(2:8, 10:12)],
        Signif = ifelse(abs(x$tval[c(2:8, 10:12)]) > 1.96, 1, 0)
    ))
}, mod_results, as.list(1:50), SIMPLIFY = FALSE))

pdf('hlm/estimate_visual.pdf', height = 7.5, width = 10)
    print(ggplot(ests, aes(x = n, y = Estimate)) +
        geom_point(aes(color = as.factor(Signif))) +
        scale_color_manual(name = 'Significance',
                           values = c('black', 'red'),
                           labels = c('Insignificant', 'Significant')) +
        facet_wrap(vars(Variable), nrow = 5, ncol = 2, scales = 'free_y') +
        theme_bw() +
        labs(title = 'Point Estimates and Statistical Significance by Variable',
             x = 'Iteration') +
        theme(legend.position = 'bottom'))
dev.off()
