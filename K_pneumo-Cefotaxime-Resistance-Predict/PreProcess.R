library("MALDIquant")
library("MALDIquantForeign")

args        <- commandArgs(trailingOnly = TRUE)
input_file  <- args[1]
output_file <- args[2]

# Validate
if (is.na(input_file) || is.na(output_file)) {
  stop("Usage: Rscript preprocess_spectrum.R <input.mzXML> <output.csv>")
}

if (!file.exists(input_file)) {
  stop(paste("Input file not found:", input_file))
}

# Import single file — not a directory
spectra_raw <- MALDIquantForeign::importMzXml(input_file)

if (length(spectra_raw) > 1) {
  spectra_raw <- list(averageMassSpectra(spectra_raw, method = "mean"))
}

# Preprocessing pipeline
spectra <- transformIntensity(spectra_raw, method = "sqrt")
spectra <- smoothIntensity(spectra, method = "SavitzkyGolay", halfWindowSize = 10)
spectra <- removeBaseline(spectra, method = "SNIP", iterations = 20)
spectra <- calibrateIntensity(spectra, method = "TIC")
spectra <- trim(spectra, range = c(2000, 20000))

# Export preprocessed spectrum
s  <- spectra[[1]]
df <- data.frame(mz = s@mass, intensity = s@intensity)
write.csv(df, output_file, row.names = FALSE)

cat("SUCCESS\n")