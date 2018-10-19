
#
# Defining and deriving biases
# 

genderPairs <- list(c('she','he'), c('her','his'), c('woman','man'),
                c('herself','himself'), c('daughter','son'), 
                c('mother','father'), c('girl','boy'), c('female','male'))

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

racePairs <- list(c('Ebony','Ellen'), c('Lakisha','Jonathan'), c('Temeka','Jack'),
                c('Everol','Josh'), c('Lavon','Roger'), c('Teretha','Craig'), 
                c('Bobbie-Sue','Aisha'), c('Marcellus','Alan'), c('Rasheed','Nancy'), 
                c('Malik','Adam'), c('Terrence','Chip'), c('Tia','Hank'), 
                c('Kareem','Peter'), c('Tyrone','Harry'), c('Terryl','Frank'), 
                c('Jamal','Donna'), c('Keisha','Megan'), c('Tawanda','Kristin'), 
                c('Deion','Fred'), c('Lamar','Ian'), c('Tvree','Andrew'), 
                c('Latisha','Todd'), c('Tremayne','Emily'), c('Jermaine','Sue-Ellen'), 
                c('Rashaun','Ryan'), c('Lionel','Justin'), c('Lashelle','Greg'), 
                c('Lamont','Matthew'), c('Tamika','Wendy'), c('Yvette','Stephanie'), 
                c('Shavonn','Betsy'), c('Nichelle','Jed'), c('Latonya','Courtney'), 
                c('Wardell','Stephen'), c('Lashandra','Meredith'), c('Tanisha','Melanie'), 
                c('Leroy','Colleen'), c('Kenya','Rachel'), c('Darnell','Jay'), 
                c('Yolanda','Geoffrey'), c('Hakim','Neil'), c('Rasaan','Wilbur'), 
                c('Theo','Brad'), c('Alphonse','Paul'), c('Torrance','Amanda'), 
                c('Aiesha','Heather'), c('Jerome','Brandon'), c('Tashika','Brendan'), 
                c('Percell','Amber'), c('Malika','Anne'), c('Latoya','Brett'), 
                c('Sharise','Allison'), c('Lerone','Sara'), c('Jasmine','Lauren'), 
                c('Shereen','Crystal'), c('Shanise','Peggy'), c('Tameisha','Shannon'), 
                c('Shaniqua','Katie'))

#
# Unfortunately many names (mostly "black" names) did not occur in the Breitbart corpus, 
# so this bias component must be derived slightly differently. Here we take a basket of
# terms and compute the first principle component of the entire basket. 
# 

adj_race_names <- unlist(racePairs)
adj_race_names <- adj_race_names[tolower(adj_race_names) %in% rownames(bv)]
adj_race_names <- c(sample(adj_race_names[adj_race_names %in% white_names],length(adj_race_names[adj_race_names %in% black_names])),
                    adj_race_names[adj_race_names %in% black_names])

powerPairs <- list(c('feel','think'), c('original', 'reliable'), 
    c('tender','tough'), c('touching','convincing'), c('curious','accepting'), 
    c('unplanned','scheduled'), c('compassion','clout'), c('spontaneous','secure'), 
    c('rebel','conform'), c('gentle','firm'), c('creative','consistent'), 
    c('sensitive','strong'), c('skeptical', 'trusting'), c('innovative','traditional'))

