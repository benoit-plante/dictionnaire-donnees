# Write the SAS version of the fictional database (v0.2, step 8).
#
# Python cannot write .sas7bdat files; R's haven package can. This script is a development
# tool only: the tool itself never needs R. It reads the Stata version written by
# generer_bases_fictives.py and writes etude-sommeil.sas7bdat next to it. The file is kept
# in the repository, and the tests check that it gives the same profile as the Stata one.
#
# Usage, from the repository root, after generer_bases_fictives.py:
#     Rscript scripts/generer_sas.R [folder]

args <- commandArgs(trailingOnly = TRUE)
folder <- if (length(args) > 0) args[[1]] else file.path("exemples", "bases-fictives")

suppressPackageStartupMessages(library(haven))

data <- read_dta(file.path(folder, "etude-sommeil.dta"))
# SAS keeps variable labels, not value labels (they live in a separate format catalog).
data[] <- lapply(data, zap_labels)
target <- file.path(folder, "etude-sommeil.sas7bdat")
suppressWarnings(write_sas(data, target))  # write_sas is marked as superseded, still works

# The header holds the creation and modification times (two doubles, seconds since 1960,
# at bytes 164 and 172): fixed, so that the bytes are the same at every run.
bytes <- readBin(target, "raw", file.info(target)$size)
fixed <- as.numeric(difftime(as.POSIXct("2026-01-01", tz = "UTC"),
                             as.POSIXct("1960-01-01", tz = "UTC"), units = "secs"))
stamp <- writeBin(fixed, raw(), size = 8, endian = "little")
bytes[165:172] <- stamp
bytes[173:180] <- stamp
writeBin(bytes, target)
cat(target, "\n")
