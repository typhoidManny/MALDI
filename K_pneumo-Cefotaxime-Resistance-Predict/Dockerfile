FROM rocker/r-ver:4.3.0

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    libxml2-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R packages separately so if one fails you can see which one
RUN Rscript -e "install.packages('MALDIquant', \
    repos='https://cloud.r-project.org', \
    lib='/usr/local/lib/R/site-library')"

RUN Rscript -e "install.packages('MALDIquantForeign', \
    repos='https://cloud.r-project.org', \
    lib='/usr/local/lib/R/site-library')"

# Verify both installed correctly
RUN Rscript -e "library(MALDIquant); cat('MALDIquant OK\n')"
RUN Rscript -e "library(MALDIquantForeign); cat('MALDIquantForeign OK\n')"

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

RUN useradd -m -u 1000 user
RUN chown -R 1000:1000 /app
USER user

EXPOSE 7860

CMD ["python3", "app.py"]