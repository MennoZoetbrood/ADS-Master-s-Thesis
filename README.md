# Unsupervised Topic Modelling on European Vulnerability Data

This repository contains the code and supporting materials for my Master's thesis for the programme Applied Data Science at Utrecht University.

The project explores how BERTopic can be used to identify interpretable themes in vulnerability descriptions from the European Vulnerability Database (EUVD), and how the prevalence of these themes can be monitored retrospectively over time.

## Project Overview

Public vulnerability databases contain large numbers of short textual descriptions of disclosed cybersecurity vulnerabilities. This project applies unsupervised topic modelling to structure these descriptions into interpretable themes.

The main goals of the project are to:

- extract recurring themes from EUVD vulnerability descriptions;
- compare a general embedding model with a cybersecurity-specific embedding model;
- evaluate topic quality using both automatic metrics and qualitative inspection;
- aggregate topic assignments over time to support retrospective topic monitoring.

## Data

The data used in this project come from a fixed snapshot of the European Vulnerability Database (EUVD), collected through ENISA's public API.

The snapshot covers the period from 1 May 2016 to 1 May 2026. The raw export contained 268,022 vulnerability records. After filtering rejected, malformed, or otherwise unsuitable records, the final working corpus contained 254,247 records.

The full dataset is not included in this repository because of file-size limitations. The data can be reconstructed from the EUVD API using the collection and preprocessing steps described in the thesis/code.

## Methodology

The project uses BERTopic to model vulnerability descriptions. Two BERTopic pipelines were compared:

1. MiniLM
   A general-purpose sentence-transformer baseline using `all-MiniLM-L6-v2`.

2. SecureBERT 
   A cybersecurity-specific embedding model using `ehsanaghaei/SecureBERT`.

Both models used the same general BERTopic pipeline structure, including preprocessing, dimensionality reduction, clustering, and topic representation. The main difference between the two models was the embedding model.

Topic quality was evaluated using a custom Python evaluation suite, including:

- topic coherence;
- topic diversity;
- outlier rates;
- clustering diagnostics;
- holdout coverage;
- qualitative dashboard inspection;
- expert review of sampled SecureBERT topics.

## Results

Both models identified meaningful latent structures in the EUVD vulnerability descriptions.

MiniLM produced a larger number of topics with broader thematic diversity. SecureBERT produced fewer topics, but these were generally more coherent and slightly better at covering later holdout records. Because of its domain-specific interpretability, SecureBERT was selected as the preferred final model.

The final workflow also aggregates topic assignments into monthly counts and normalised topic shares. These time series can be used for retrospective inspection of how vulnerability-description themes change over time.

## Important Limitations

This project models the language of disclosed EUVD vulnerability records. It does not model all real-world vulnerabilities.

The results should therefore be interpreted as exploratory and retrospective. The model does not predict future vulnerability trends, and topic assignments should not be treated as definitive vulnerability categories.
