

#
# Featurization script
# 

setwd("C:/users/ben_ryan/documents/git/ugb/R/featurization")
source("clustering.R")
source('glove_analysis.R')
source('bias_themes_analysis.R')

registerDoParallel(detectCores())

#
# Get the raw text data for embedding training
# 

b_corp <- fread('C:/users/ben_ryan/documents/darpa ugb/breitbart_texts.csv',
                header=FALSE)

bv = trainEmbeddings(b_corp$V2, alpha=0.05)
write.table(bv,
            'breitbart_embeddings_wComments.txt',
            col.names=FALSE,
            quote=FALSE,
            fileEncoding='utf-8')

# To read in again from saved:
# bv = fread('breitbart_embeddings_wComments.txt', header=FALSE)
# terms <- bv$V1
# bv[,V1:=NULL]
# bv <- data.matrix(bv)
# rownames(bv) <- terms

#
#
# Begin feature extraction from articles and comments datasets
#
# 

barts = fread('breitbart_articles.csv') #load breitbart articles
bcs = fread('breitbart_comments.csv') #load breitbart comments

# 
# Derive bias component vectors
# 

gender_bias <- deriveBias(genderPairs, wv=bv, method='pca', diag=TRUE)
race_bias <- deriveBias(adj_race_names, wv=bv, diag=TRUE)
power_bias <- deriveBias(powerPairs, wv=bv, method='pca', diag=TRUE)

#
# Derive embeddings for articles and article titles, and merge into one 
# data.table. 
# 

arts_text_tokens = getTokens(barts$art_text)
bgloved_arts <- lapply(arts_text_tokens, gloved, wv=bv)
bgloved_arts <- data.table(do.call(rbind, bgloved_arts))

# 
# Propagate bias components
#

gender <- foreach(i = 1:nrow(bgloved_arts),
                  .inorder=TRUE,
                  .export=c('biasComponent','avgBias','bv','gender_bias','power_bias','race_bias'),
                  .packages = c('NLP','openNLP','dplyr'),
                  .multicombine = TRUE, 
                  .options.multicore = list(preschedule = FALSE)) %dopar% {
            avgBias(arts_text_tokens[[i]], gender_bias, bv)
        }

bgloved_arts$gender <- unlist(gender)


race <- foreach(i = 1:nrow(bgloved_arts),
                  .inorder=TRUE,
                  .multicombine = TRUE, 
                  .options.multicore = list(preschedule = FALSE)) %dopar% {
            avgBias(arts_text_tokens[[i]], race_bias, bv)
        }

bgloved_arts$race <- unlist(race)


power <- foreach(i = 1:nrow(bgloved_arts),
                  .inorder=TRUE,
                  .multicombine = TRUE, 
                  .options.multicore = list(preschedule = FALSE)) %dopar% {
            avgBias(arts_text_tokens[[i]], power_bias, bv)
        }

bgloved_arts$power <- unlist(power)

# 
# Set column names and add article id
#

names(bgloved_arts) <- paste('art_text_embeddings_',names(bgloved_arts), sep='')
bgloved_arts$art_id <- barts$art_id

#
# Add in the article metadata (sentiment scores and number of comments per article)
# 

sent_cols <- c(names(barts)[names(barts) %like% 'sent_'], 'art_comments', 'art_id')
bgloved_arts <- merge(bgloved_arts, barts[,sent_cols,with=FALSE], by='art_id')

#
# Okay, now article titles, same deal
# 

arts_title_tokens = getTokens(barts$art_title)
bgloved_titles <- lapply(arts_title_tokens, gloved, wv=bv)
bgloved_titles <- data.table(do.call(rbind, bgloved_titles))

gender <- foreach(i = 1:nrow(bgloved_titles),
                  .inorder=TRUE,
                  .export=c('biasComponent','avgBias','bv','gender_bias','power_bias','race_bias'),
                  .packages = c('NLP','openNLP','dplyr'),
                  .multicombine = TRUE, 
                  .options.multicore = list(preschedule = FALSE)) %dopar% {
            avgBias(arts_title_tokens[[i]], gender_bias, bv)
        }

bgloved_titles$gender <- unlist(gender)


race <- foreach(i = 1:nrow(bgloved_titles),
                  .inorder=TRUE,
                  .multicombine = TRUE, 
                  .options.multicore = list(preschedule = FALSE)) %dopar% {
            avgBias(arts_title_tokens[[i]], race_bias, bv)
        }

bgloved_titles$race <- unlist(race)


power <- foreach(i = 1:nrow(bgloved_titles),
                  .inorder=TRUE,
                  .multicombine = TRUE, 
                  .options.multicore = list(preschedule = FALSE)) %dopar% {
            avgBias(arts_title_tokens[[i]], power_bias, bv)
        }

bgloved_titles$power <- unlist(power)

# 
# Set column names and add article id
#

names(bgloved_titles) <- paste('title_embeddings_',names(bgloved_titles), sep='')
bgloved_titles$art_id <- barts$art_id

#
# Goody! Now merge the two together. 
# 

bgloved_arts <- merge(bgloved_titles, bgloved_arts, by='art_id')

# 
# Seems like a good point to save. 
# 

fwrite(bgloved_arts, 'breitbart_articles_features.csv')

#
# Now, for the comments!
# 

comment_txt_tokens = getTokens(bcs$comment_txt)
bgloved_comments <- lapply(getTokens(bcs$comment_txt), gloved, wv=bv)
bgloved_comments <- data.table(do.call(rbind, bgloved_comments))

gender <- foreach(i = 1:nrow(bgloved_comments),
                  .inorder=TRUE,
                  .export=c('biasComponent','avgBias','bv','gender_bias','power_bias','race_bias'),
                  .packages = c('NLP','openNLP','dplyr'),
                  .multicombine = TRUE, 
                  .options.multicore = list(preschedule = FALSE)) %dopar% {
            avgBias(comment_txt_tokens[[i]], gender_bias, bv)
        }

bgloved_comments$gender <- unlist(gender)


race <- foreach(i = 1:nrow(bgloved_comments),
                  .inorder=TRUE,
                  .multicombine = TRUE, 
                  .options.multicore = list(preschedule = FALSE)) %dopar% {
            avgBias(comment_txt_tokens[[i]], race_bias, bv)
        }

bgloved_comments$race <- unlist(race)


power <- foreach(i = 1:nrow(bgloved_comments),
                  .inorder=TRUE,
                  .multicombine = TRUE, 
                  .options.multicore = list(preschedule = FALSE)) %dopar% {
            avgBias(comment_txt_tokens[[i]], power_bias, bv)
        }

bgloved_comments$power <- unlist(power)

# 
# Set column names and add article id for merging
#

names(bgloved_comments) <- paste('comment_embeddings_',names(bgloved_comments), sep='')
bgloved_comments$art_id <- bcs$art_id


# 
# Perform clustering of comments based on word usage
# 

text_embed_cols <- names(bgloved_comments)[names(bgloved_comments) %like% '_V']
group_clusters <- pickBestCluster(bgloved_comments[,text_embed_cols,with=F])

#
# Merge in the comments metadata (sentiment scores, author and upvotes)
# 

cols <- c(names(bcs)[names(bcs) %like% 'sent_'], 'commenter', 'upvotes', 'art_id')
bgloved_comments <- merge(bgloved_comments, bcs[,cols, with=FALSE], by='art_id')

# 
# Visualize comments clusters 
# 
# cls <- unique(bgloved_comments$CLUSTER)
# colors = rainbow(length(cls))
# names(colors) = cls
# tsne <- Rtsne(unique(bgloved_comments[,text_embed_cols, with=F],
#               dims = 2, 
#               perplexity=4, 
#               verbose=TRUE, 
#               max_iter = 500)
# plot(rtsne$Y, t='n', main="tsne")
# text(rtsne$Y, labels=cls, col=colors[cls])
# 

#
# Finally, merge these all together, and save out to file. 
#

bgloved <- merge(bgloved_arts, bgloved_comments, by='art_id')
fwrite(bgloved, 'breitbart_combined_features.csv')

