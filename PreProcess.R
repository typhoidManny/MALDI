install.packages("MALDIquant")
install.packages("MALDIquantForeign")
library("MALDIquant")
library("MALDIquantForeign")

cat("Enter the path to the directory containing your mzXML files: ")
input_dir <- readLines(con = stdin(), n = 1)
input_dir <- trimws(input_dir)  # remove any accidental whitespace

# Validate before importing
if (!dir.exists(input_dir)) {
  stop(paste("Directory not found:", input_dir))
}

mzxml_files <- list.files(input_dir, pattern = "\\.mzXML$", 
                           ignore.case = TRUE)

if (length(mzxml_files) == 0) {
  stop(paste("No mzXML files found in:", input_dir))
}

cat(paste("Found", length(mzxml_files), "mzXML files. Importing...\n"))

spectra <- MALDIquantForeign::importMzXml(input_dir)
length(spectra)

file_paths <- sapply(spectra, function(s) s@metaData$file)
length(unique(file_paths))
table(table(file_paths))

unique_files <- unique(file_paths)
spectra_merged <- lapply(unique_files, function(f) {
    idx   <- which(file_paths == f)
    file_spectra   <- spectra[idx]
    averageMassSpectra(file_spectra, method = "mean")
})

length(spectra_merged)

#variance stabilization using sqrt transform
spectra_merged <- transformIntensity(spectra_merged, method = "sqrt")

#smoothing using the Savitzky-Golay algorithm
spectra_merged <- smoothIntensity(spectra_merged, method = "SavitzkyGolay", halfWindowSize = 10)

#Baseline removal using the SNIP algorithm
spectra_merged <- removeBaseline(spectra_merged, method = "SNIP", iterations = 20)

#intensity calibration using total ion current normalization
spectra_merged <- calibrateIntensity(spectra_merged, method = "TIC")

#trimming to the proper m/z range
spectra_merged <- trim(spectra_merged, range = c(2000, 20000))

plot(spectra_merged[[1]], main="Processed Spectra", xlab="m/z", ylab="Intensity")

bin_size <- 3
mz_min <- 2000
mz_max <- 20000
n_bins <- (mz_max -mz_min) / bin_size

bin_spectrum <- function(spectrum){
  mz        <- spectrum@mass
  intensity <- spectrum@intensity
  bins      <- numeric(n_bins)
  idx       <- floor((mz-mz_min)/bin_size) + 1
  valid     <- idx >= 1 & idx <= n_bins
  idx_valid <- idx[valid]
  int_valid <- intensity[valid]
  
  for (j in seq_along(idx_valid)){
    bins[idx_valid[j]] <- bins[idx_valid[j]] + int_valid[j]
  }
  return(bins)
}

X_matrix <- do.call(rbind, lapply(spectra_merged, bin_spectrum))

sample_ids         <- tools::file_path_sans_ext(basename(unique_files))
rownames(X_matrix) <- sample_ids

write.csv(X_matrix, "feature_matrix.csv")
