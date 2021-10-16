# $> module load R/4.0.5
# install.packages("RSQLite")
# install.packages("dbplyr")
# install.packages("tidyverse")

library(tidyverse)
library(RSQLite)
library(dbplyr)

db <- src_sqlite("signal.db", create = F)

signal = tbl(db, "signal")
target = tbl(db, "target")

all <- signal %>% left_join(target, by=c("target_id"="id"))
print(all)
