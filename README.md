### This package provides tools for enriching biological entities (cells, genes, and molecules) to support sleep-wake disorder research within the RDoC framework.  The whole procedure include four steps: 1) article downloading from PUBMED, 2) Article screening, 3) entity extraction with LLM, and 4) entity standardization with LLMs and fuzziwuzzy.
article title: Large Language Models-Powered Enrichment of the Units of Analysis of the RDoC Framework

This package includes:<br>
--prompts and retrieval.md: article retrieval and prompts;<br>
--llm_mayo.py: the library of LLMS;<br>
--pubmed_abstract_or_article_download_for_sleep_disorder_txt.py: article download from PubMed;<br>
--llm_vllm_article_screening_rdoc_gpt.py: article screening;<br>
--llm_entity_extract_from_article_excel_vllm_batch_end2end.py: entity extraction with LLM;<br>
--llm_vllm_rdoc_standardization.py: entity standardication with UMLS.<br>

###Running environments<br>
--OS: Linux, MacOS, Windows;<br>
--platform: Python 3.8-3.12 + torch 2.9;<br>
--GPU: cuda11.0-cuda13.<br>

###local LLM deployment with sglang<br>
$ pip install sglang==0.5.10.post1<br>
$ CUDA_VISIBLE_DEVICES=0,1,2,3 python -m sglang.launch_server --model-path /home/m123456/qwen/Qwen3.6-27B --served-model-name qwen3.6-27b --tp-size 4 --host 127.0.0.1 --port 20001 --mem-fraction-static 0.85 --context-length 131072 --reasoning-parser qwen3 --api-key infodev<br>



### LLM-drived Entity enrichment  study for RDoC<br>
### step 1, download articles from PubMed as the preparation for dataset construction<br>
$ python pubmed_abstract_or_article_download_for_sleep_disorder_txt.py<br>
key arguments (defaults are given in the code):<br>
  query----a string containing keywords and query rules;<br>
  output_filename----a csv filename;<br>
  save_path----a path of the output;<br>
  noncontent----download full paper or only abastract #False: full paper; True: only for abstract;<br>
  date_start----start date of the publication;<br>
  date_end----end date of the publication;<br>
  period_days----an integer representing the period of publication which is use to used to cap the maximum retrieval limit.<br>

### step 2, do article screening for data corpus<br>
$ python llm_vllm_article_screening_rdoc_gpt.py<br>
key arguments (defaults are given in the code):<br>
  modelfolder---- the folder of the local LLM used in this code;<br>
  engine---- gpt engine;<br>
  api_version----gpt api version;<br>
  env_path----local environment path of gpt setting;<br>
  gpu_num----an integer representing the gpu number;<br>
  batchsize----batch size.<br>

### step 3, entity extraction with llm<br>
$ python llm_entity_extract_from_article_excel_vllm_batch_end2end.py<br>
key arguments (defaults are given in the code):<br>
  modelfolder---- the folder of the local LLM used in this code;<br>
  srcfilepath---- a csv file which contains the article informaiton(pmid, title, abstract, pmcid,doi, and journal);<br>
  dstfolder_base---- a folder for the output (extracted entities);<br>
  model----local LLM's name;<br>
  engine---- gpt engine;<br>
  api_version----gpt api version;<br>
  env_path----local environment path of gpt setting;<br>
  batchsize---- an integer representing the batch size.<br>

### step 4, entity standardization<br>
$ python llm_vllm_rdoc_standardization.py<br>
key arguments (defaults are given in the code):<br>
  modelfolder---- the folder of the local LLM used in this code;<br>
  gpu_num----an integer representing the gpu number;<br>
  batchsize----batch size;<br>
  rdoc_extraction_ground_truth_path---- the full path of the extracted entities (an excel file);<br>
  umlsfilepath----the the full path of UMLS file(a csv file);<br>
  dstfolder_base---- a folder for the output (standardized entities).<br>

### note
one corpus for this method: pubmed_sleep_disorder_abstract_20240701_20250630_groundtruth_corpus_100.csv
