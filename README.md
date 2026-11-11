### This package provides tools for enriching biological entities (cells, genes, and molecules) to support sleep-wake disorder research within the RDoC framework.  The whole procedure include four steps: 1) article downloading from PUBMED, 2) Article screening, 3) entity extraction with LLM, and 4) entity standardization with LLMs and fuzziwuzzy.
article title: Large Language Models-Powered Enrichment of the Units of Analysis of the RDoC Framework

This package includes:<br>
--prompts and retrieval.md: article retrieval and prompts;<br>
--llm_mayo.py: the library of LLMS;<br>
--pubmed_abstract_or_article_download_for_sleep_disorder_txt.py: article download from PubMed;<br>
--llm_vllm_article_screening_rdoc_gpt.py: article screening;<br>
--llm_entity_extract_from_article_excel_vllm_batch_end2end.py: entity extraction with LLM;<br>
--llm_vllm_rdoc_standardization.py: entity standardication with UMLS.<br>

###Running environments
--OS: Linux, MacOS, Windows;
--platform: Python 3.8-3.12 + torch 2.9;
--GPU: cuda11.0-cuda13.

###local LLM deployment with sglang
$ pip install sglang==0.5.10.post1
$ CUDA_VISIBLE_DEVICES=0,1,2,3 python -m sglang.launch_server --model-path /home/m123456/qwen/Qwen3.6-27B --served-model-name qwen3.6-27b --tp-size 4 --host 127.0.0.1 --port 20001 --mem-fraction-static 0.85 --context-length 131072 --reasoning-parser qwen3 --api-key infodev



### LLM-drived Entity enrichment  study for RDoC
### step 1, download articles from PubMed as the preparation for dataset construction
$ python pubmed_abstract_or_article_download_for_sleep_disorder_txt.py
key arguments (defaults are given in the code):
  query----a string containing keywords and query rules;
  output_filename----a csv filename;
  save_path----a path of the output;
  noncontent----download full paper or only abastract #False: full paper; True: only for abstract;
  date_start----start date of the publication;
  date_end----end date of the publication;
  period_days----an integer representing the period of publication which is use to used to cap the maximum retrieval limit.

### step 2, do article screening for data corpus
$ python llm_vllm_article_screening_rdoc_gpt.py
key arguments (defaults are given in the code):
  modelfolder---- the folder of the local LLM used in this code;
  engine---- gpt engine;
  api_version----gpt api version;
  env_path----local environment path of gpt setting;
  gpu_num----an integer representing the gpu number;
  batchsize----batch size.

### step 3, entity extraction with llm
$ python llm_entity_extract_from_article_excel_vllm_batch_end2end.py
key arguments (defaults are given in the code):
  modelfolder---- the folder of the local LLM used in this code;
  srcfilepath---- a csv file which contains the article informaiton(pmid, title, abstract, pmcid,doi, and journal);
  dstfolder_base---- a folder for the output (extracted entities);
  model----local LLM's name;
  engine---- gpt engine;
  api_version----gpt api version;
  env_path----local environment path of gpt setting;
  batchsize---- an integer representing the batch size.

### step 4, entity standardization
$ python llm_vllm_rdoc_standardization.py
key arguments (defaults are given in the code):
  modelfolder---- the folder of the local LLM used in this code;
  gpu_num----an integer representing the gpu number;
  batchsize----batch size;
  rdoc_extraction_ground_truth_path---- the full path of the extracted entities (an excel file);
  umlsfilepath----the the full path of UMLS file(a csv file);
  dstfolder_base---- a folder for the output (standardized entities).

### note
one corpus for this method: pubmed_sleep_disorder_abstract_20240701_20250630_groundtruth_corpus_100.csv
