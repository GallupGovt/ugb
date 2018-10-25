#!/usr/loca/bin/R
# hierarchical modeling for ugb
# questions? contact matt_hoover@gallup.com

# load libraries
library(data.table)
library(lme4)

# get passed arguments
args <- commandArgs(trailingOnly = TRUE)
args <- c('breitbart_modeling_data.csv')

# load data
d <- fread(paste('hlm', args[1], sep = '/'))

gender_mod <- lmer(gender_bias ~
            title_embeddings_gender +
            art_text_embeddings_gender +
            title_sent_neg +
            title_sent_pos +
            art_sent_neg +
            art_sent_pos +
            art_comments +
            comment_embeddings_gender +
            upvotes +
            comm_sent_neg +
            comm_sent_pos +
            (1 | art_id) +
            (1 | CLUSTER),
            d, REML = FALSE
)

race_mod <- lmer(race_bias ~
            title_embeddings_race +
            art_text_embeddings_race +
            title_sent_neg +
            title_sent_pos +
            art_sent_neg +
            art_sent_pos +
            art_comments +
            comment_embeddings_race +
            upvotes +
            comm_sent_neg +
            comm_sent_pos +
            (1 | art_id) +
            (1 | CLUSTER),
            d, REML = FALSE
)

power_mod <- lmer(power_bias ~
            title_embeddings_power +
            art_text_embeddings_power +
            title_sent_neg +
            title_sent_pos +
            art_sent_neg +
            art_sent_pos +
            art_comments +
            comment_embeddings_power +
            upvotes +
            comm_sent_neg +
            comm_sent_pos +
            (1 | art_id) +
            (1 | CLUSTER),
            d, REML = FALSE
)

