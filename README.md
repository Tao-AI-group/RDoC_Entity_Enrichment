# RDoC_Entity_Enrichment
# LLM-drived Entity enrichment  study for RDoC
# step 1, download articles from PubMed as the preparation for dataset construction
python pubmed_abstract_or_article_download_for_sleep_disorder_txt.py

# step 2, do article screening for data corpus
python llm_vllm_article_screening_rdoc_gpt.py

# step 3, entity extraction with llm
python llm_entity_extract_from_article_excel_vllm_batch_end2end.py

# step 4, entity standardization
python llm_vllm_rdoc_standardization.py

# note
# one corpus for this method: pubmed_sleep_disorder_abstract_20240701_20250630_groundtruth_corpus_100.csv
