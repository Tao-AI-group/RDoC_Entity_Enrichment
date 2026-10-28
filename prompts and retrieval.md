# Supplementary 1. Query for article retrieval from PubMed
((Sleep-Wake Disorders[Title/Abstract]) OR (Sleep disorders[Title/Abstract]) OR (Dyssomnias [Title/Abstract]) OR (Parasomnias[Title/Abstract]) OR (Sleep disturbance[Title/Abstract]) OR (Sleep Deprivation[Title/Abstract]) OR (Sleep fragmentation[Title/Abstract]) OR (Insomnia[Title/Abstract]) OR (Fatal Familial Insomnia[Title/Abstract]) OR (Organic insomnia[Title/Abstract]) OR (Hypersomnia [Title/Abstract]) OR (Hypersomnolence Disorder [Title/Abstract]) OR (Disorders of Excessive Somnolence [Title/Abstract]) OR (Idiopathic Hypersomnia[Title/Abstract]) OR (Kleine-Levin Syndrome[Title/Abstract]) OR (Excessive daytime sleepiness[Title/Abstract]) OR (Organic hypersomnia[Title/Abstract]) OR (Sleep apnea[Title/Abstract]) OR (Sleep Apnea Syndromes [Title/Abstract]) OR (Central Sleep Apnea[Title/Abstract]) OR (Obstructive Sleep Apnea[Title/Abstract]) OR (Obstructive Sleep Apnea Hypopnea[Title/Abstract]) OR (Sleep-Related Hypoventilation [Title/Abstract]) OR (Obesity Hypoventilation Syndrome[Title/Abstract]) OR (Organic sleep apnea[Title/Abstract]) OR (Circadian Rhythm Sleep-Wake Disorders[Title/Abstract]) OR (Jet Lag Syndrome[Title/Abstract]) OR (Sleep Disorders[Title/Abstract]) OR (Circadian Rhythm[Title/Abstract]) OR (REM Sleep Behavior Disorder[Title/Abstract]) OR (Rapid Eye Movement (REM) Sleep Behavior Disorder[Title/Abstract]) OR (REM Sleep Parasomnias[Title/Abstract]) OR (Non-Rapid Eye Movement (NREM) Sleep Arousal Disorders[Title/Abstract]) OR (Sleep Arousal Disorders[Title/Abstract]) OR (Night terrors[Title/Abstract]) OR (Somnambulism[Title/Abstract]) OR (Nightmare Disorder [Title/Abstract]) OR (Sleep Paralysis[Title/Abstract]) OR (Nocturnal Paroxysmal Dystonia [Title/Abstract]) OR (Sleep Bruxism[Title/Abstract]) OR (Restless Legs Syndrome [Title/Abstract]) OR (Periodic Limb Movement Disorder[Title/Abstract]) OR (Nocturnal Myoclonus Syndrome [Title/Abstract]) OR (Sleep-related movement disorders[Title/Abstract]) OR (Narcolepsy[Title/Abstract]) OR (Disorder of sleep of non-organic origin[Title/Abstract]) OR (Cataplexy[Title/Abstract]) OR (Sleep Initiation and Maintenance Disorders[Title/Abstract]) OR (Sleep-Wake Transition Disorders [Title/Abstract]) OR (High-altitude periodic breathing[Title/Abstract]) OR (Sleep Wake Disorder[Majr])) AND (("2024/01/01"[Date - Publication] : "2025/10/01"[Date - Publication]))




# Supplementary II.  Article screening prompt
Role: You are an expert focusing on large language and sleep wake disorders.

Background
A paper is considered relevant to sleep-wake disorder if its primary objective addresses one or more of the following specific disorders or syndromes:
Sleep-Wake Disorders, Sleep disorders,  Dyssomnias, Parasomnias, Sleep disturbance, Sleep Deprivation, Sleep fragmentation, Insomnia, Fatal Familial Insomnia, Organic insomnia,         Hypersomnia, Hypersomnolence Disorder, Disorders of Excessive Somnolence, Idiopathic Hypersomnia, Kleine-Levin Syndrome, Excessive daytime sleepiness, Organic hypersomnia, Sleep apnea, Sleep Apnea Syndromes, Central Sleep Apnea, Obstructive Sleep Apnea, Obstructive Sleep Apnea Hypopnea, Sleep-Related Hypoventilation, Obesity Hypoventilation Syndrome, Organic sleep apnea, Circadian Rhythm Sleep-Wake Disorders, Jet Lag Syndrome, Circadian Rhythm, REM Sleep Behavior Disorder,  Rapid Eye Movement (REM) Sleep Behavior Disorder, REM Sleep Parasomnias, Non-Rapid Eye Movement (NREM) Sleep Arousal Disorders, sleep Arousal Disorders, Night terrors, Somnambulism, Nightmare Disorder, Sleep Paralysis, Nocturnal Paroxysmal Dystonia, Sleep Bruxism, Restless Legs Syndrome, Periodic Limb Movement Disorder, Nocturnal Myoclonus Syndrome, Sleep-related movement disorders, Narcolepsy, Disorder of sleep of non-organic origin, Cataplexy, Sleep Initiation and Maintenance Disorders, Sleep-Wake Transition Disorders, and High-altitude periodic breathing.

Task:
1) Extract the major diseases or disorders discussed in the article.
2) Determine whether the extracted diseases/disorders are closely related to sleep–wake disorders (True/False).
3) Decide whether the article should be included in our study (True/False).
4) Assign a confidence score for your decision (0...100).
5) Provide a brief rationale for your decision.

Input:
{abstract}

Output:
Return only a Python dictionary in exactly the following format:
{{
        "large_language_model": "{model}",
        "model_version": "{version}",
        "sleep_wake_disorder_focus": true/false,
        "include_or_not": true/false,
        "confidence":(0...100)
        "reason":"..."
}}
Note that only return the python dictionary rather than any other information such as thinking, explanations, or reasoning.
Both "sleep_wake_disorder_focus" and "include_or_not" must be Boolean values (true or false)(lower case), not strings. "confidence" represents confidenced score of decision which is varying from 0 to 100.


 
# Supplementary Method III. Entity extraction prompt
Role: You are a psychiatric expert focusing on sleep wake disorders.

Backgroup: Sleep wake disorders include  Sleep disorders, Dyssomnias, Insomnia, Hypersomnia, Parasomnia, Sleep fragmentation, Night terrors, Sleep apnea, Hypersomnolence disorders, Excessive daytime sleepiness, Narcolepsy, Sleep-Related Hypoventilation, Nightmare Disorder, Rapid Eye Movement Sleep Behavior Disorder, Restless Legs Syndrome, High-altitude periodic breathing, Periodic limb movement disorder, Sleep-related movement disorders, Disorder of sleep of non-organic origin, Sleep disturbance, Sleep-Wake Disorders, Sleep Deprivation, Nocturnal Paroxysmal Dystonia, Sleep Arousal Disorders, Sleep Bruxism, Sleep-Wake Transition Disorders, Fatal Familial Insomnia, Organic insomnia, Disorders of Excessive Somnolence, Idiopathic Hypersomnia, Kleine-Levin Syndrome, Organic hypersomnia, Sleep Apnea Syndromes, Central Sleep Apnea, Obstructive Sleep Apnea, obstructive Sleep Apnea Hypopnea, Obesity Hypoventilation Syndrome, Organic sleep apnea, Circadian Rhythm Sleep-Wake Disorders, Jet Lag Syndrome, Circadian Rhythm Disorders, Rapid Eye Movement Sleep Behavior Disorder, Rapid Eye Movement Sleep Parasomnias, Non-Rapid Eye Movement Sleep Arousal Disorders, Somnambulism, Sleep Paralysis, Nocturnal Myoclonus Syndrome, Sleep Initiation and Maintenance Disorders, and Cataplexy.

Task: Your task is to extract sleep wake disorder-related entities, including three types: cell, gene and molecule, from PubMed articles based on their titles or abstracts. Specifically,
 A cell is a fundamental structural and functional unit of life, such as blood platelet, leukocyte, endocrine cell.
 A gene is a specific genetic variant, polymorphism, or other genomic feature, such as SLC6A4 (serotonin transporter gene), COMT (catechol-O-methyltransferase gene).
A molecule is the biochemical substance that underlies and helps characterize specific biological or psychological functions, such as neurotransmitters (glutamate, gamma-aminobutyric acid, etc.), neuromodulators (adenosine, nitric oxide, etc.), peptides (neuropeptide S), and other signaling molecules. Please do not include genes in molecules.

Rules: Please follow steps as below:
1,Read the title and abstract of each article sentence by sentence.
2,Identify sleep wake disorders.
3,Identify and write down interested entities (molecule, cell, or gene) that have solid association with sleep wake disorder. Don’t extract disease, tissue, organ, or anything else other than a cell, gene, or molecule.
4, If the extracted entity is an adjective, return it along with the noun it modifies, if such a noun exists in the same sentence.
5,If the entity is an abbreviation of a single term, identify its full name and write down both.
6,If the entity is not an abbreviation, identify its abbreviation and write down both.
7,If the entity includes both the full name and its abbreviation, separate them and write down both.
8, Find the UMLS concept or term most similar to this full name and write it down.
9,Provide source sentences that include the interested entities, sleep wake disorders, and their associations.
10,Based on this paper, summarize the associations between the entity and sleep-wake disorders primarily discussed in the study.

Output: Finally, output results only in the following Python list-of-dictionaries format, with no explanations, no reasoning, no thinking and no extra text:
[
       {{
           "pmid": "...",
           "entity_type": "...",
           'entity_name':"...",
           "entity_full_name": "...",
           "entity_abbreviation": "...",
           "UMLS_name":"..."
           "associated_sleep_wake_disorder": "...",
           "source_sentence": "...",
           "association": "..."
       }},
       ...
]
If no valid entities are found, return []





# Supplementary IV. Entity name normalization prompt
Role: You are an expert in Natural Language Processing (NLP) and data normalization.

Task: I will provide an Excel file containing a list of entities in a specific column. Your task is to normalize these entities according to the rules below and return the results in the exact same order as the input to ensure data integrity.

Normalization Rules:
(1) Remove Abbreviations: If an entity contains a full name followed by its abbreviation in parentheses—e.g., "Artificial Intelligence (AI)"—remove the parentheses and the abbreviation, keeping only the full name "Artificial Intelligence".
(2) Lemmatization: Convert all plural nouns to their singular form.
(3) Case Normalization: Convert all text to lowercase.
(4) Strip all leading/trailing whitespace and normalize internal spacing by replacing multiple spaces with a single one.
(5) For abbreviated entities containing a hyphen (-) or underscore (_), search the column for a matching entity where these characters are either removed or replaced by a space.
Priority 1: Replace the original with the version containing no symbols. If both a space-separated version and a version with no spaces exist, prioritize the space-separated version.
Priority 2: If no such match is found and the original has an underscore, replace it with a version that uses a hyphen instead (if it exists).
Priority 3: If an entity has a hyphen, search for a version without the hyphen. If both a space-separated and a non-spaced version exist, prioritize the version with no spaces.
General Rule: If two abbreviated entities differ only by a space, the version with the space is considered the standard format.
(6) Otherwise, keep the original format.

Output Requirements: 
(1) Process the entities one by one.
(2) Export the final list as a clean column that corresponds perfectly to the original row order.
(3) Do not add any additional commentary or change the count of the items.
(4) provide both the raw data and the final results so I can easily compare the differences.





# Supplementary Method V. Entity standardization prompt
Role: You are an expert in Natural Language Processing (NLP), specifically specializing in Entity Linking and Medical Data Normalization.

Task: Perform an entity alignment between the entity name in the CSV file and the STR values in the UMLS datasets. For every entity in the CSV, identify the top 3 most similar candidates from the UMLS data.

Rules:
1)String Similarity: Calculate the lexical overlap (e.g., Levenshtein or Jaro-Winkler) on a scale of 0–100.
2)Semantic Similarity: Calculate the contextual/semantic similarity (using embeddings or domain-specific semantic mapping) on a scale of 0–100.
3)Preservation: Maintain the original order of entities as they appear in the CSV file.

Input Data:
1,UMLS Reference Sets: Four truncated Excel files containing the following fields:
STR (Entity Name), CUI (Concept Unique Identifier), PN (Preferred Name), STY (Semantic Type).
2,Source Document: A CSV file containing extracted biomedical data with the fields: pmid, entity type, entity name, source sentence, and major disease.

Output Format: Return a List of Dictionaries (one dictionary per entity). Each dictionary must contain the top 3 candidates, with each candidate providing the following 4 records: PN (Preferred Name), STY (Semantic Type), CUI (Concept Unique Identifier), Similarity Score (Combined or individual scores as specified).
Example Dictionary Structure:
Python
{
  "original_entity": "example_name",
  "candidates": [
    {"PN": "...", "STY": "...", "CUI": "...", "score": 95},
    {"PN": "...", "STY": "...", "CUI": "...", "score": 92},
    {"PN": "...", "STY": "...", "CUI": "...", "score": 88}
  ]
}
