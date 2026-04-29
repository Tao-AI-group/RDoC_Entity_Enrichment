import os
import sys
import glob
import json
from datetime import datetime as dt
import shutil
import torch
#import numpy as np
import pandas as pd
if '/home/m253461/projects/tools' not in sys.path:
    sys.path.insert(0, '/home/m253461/projects/tools')
from llm_mayo import openai_api, openai_api_p, vllm_model
#from pubmed_abstract_download import pubmed_abstract_download

#modelfolder="/home/m253461/meta-llama/Llama-3.3-70B-Instruct"
modelfolder="/home/m253461/qwen/Qwen3-14B"
#modelfolder="/home/m253461/qwen/Qwen3-32B"
#modelfolder="/home/m253461/google/medgemma-27b-it"

#srcfolder="/home/m253461/projects/03rdoc/pubmed/rdoc"
srcfilepath="/home/m253461/projects/03rdoc/results/pubmed_sleep_disorder_abstract_20240701_20250630_groundtruth_corpus_100.csv"
#srcfilepath="/home/m253461/projects/03rdoc/results/articlelist_lifang.csv"
dstfolder_base="/home/m253461/projects/03rdoc/pubmed/rdoc_table_groundtruth"
#query="sleep disorder[Title/Abstract]"
#db="pubmed"
model='qwen'   #'gpt', 'gpt_p', 'llama', 'qwen','medgemma'
engine='gpt-4o' #'gpt-4-1-deployment', 'gpt-4o'
version='2024-06-01' #'2024-05-01-preview', '2024-06-01'
batchsize=16
times=10
now=dt.now()
if model!='gpt' and model!='gpt_p':
    modeldir=os.path.basename(modelfolder)
    mpos=modeldir.find('-')
    model=modeldir[:mpos]
    version=modeldir[(mpos+1):]
else:
    batchsize=1
date_str = now.strftime("%Y_%m_%d")
dstfolder=dstfolder_base+"_"+model+"_"+version+"_"+date_str
category=['cells', 'genes','molecules']

env_path='~/.env'

# set gpu environment
os.environ["CUDA_VISIBLE_DEVICES"] = "3,2,1,0"
device = torch.device("cuda")
gpu_num=len(os.environ["CUDA_VISIBLE_DEVICES"].split(','))

#open the article
def open_article(filepath=""):
    if os.path.exists(filepath)==False:
        return ""
    with open(filepath,'r') as fp:
        txt=fp.read()
    return txt

#open one article and extract the major content
def extract_article(filepath=""):
    if os.path.exists(filepath)==False:
        return ""
    
    with open(filepath,'r') as fp:
        txt=fp.read()
    txt_lower=txt.lower()
    abs_pos=txt_lower.find('abstract</h2>')
    if abs_pos==-1 or abs_pos>len(txt)*0.6:
        return ""
    ref_pos=txt_lower.find('references</h2>')
    if ref_pos==-1 or ref_pos<=abs_pos:
        return ""
    
    art_txt=txt[abs_pos:ref_pos]
    return art_txt, abs_pos, ref_pos

#extract the first word from string
def extract_1st_substr(content=""):
    if len(content)==0:
        return ''
    substr=''
    for i, ichar in content:
        if '0'<=ichar<='9':
            substr=substr+ichar
        else:
            break
    return substr

#estimate the token number
def estimate_token_from(string_obj=""):
    if len(string_obj)==0:
        return 0
    word_count=len(string_obj.split())
    maxlength=int(word_count*1.5)
    return maxlength

#estimage the max token number
def estimate_token_from_batch(instruction="", userinputs=[]):
    instruct_words=len(instruction.strip().split(" "))
    ui_max=0
    for txt in userinputs:
        t_max=len(txt.strip().split(" "))
        if t_max>ui_max:
            ui_max=t_max

    maxlength=int((instruct_words+ui_max)*1.5)
    return maxlength

#drop the user input from the answer
def drop_user_input_from_answer(answer="", instruction="", userinput=""):
    if len(answer)==0:
        return answer
    answer_s0=answer.replace(instruction,"")
    answer_s1=answer_s0.replace("Instruction:","")
    answer_s2=answer_s1.replace(userinput,"")
    answer_s3=answer_s2.replace("User:","")
    return answer_s3


def drop_user_input_from_answer_batch(answers=[],instruction="", userinputs=[]):
    if len(answers)==0 or len(userinputs)==0 or (len(answers)!=len(userinputs)):
        return []
    answers_d=[]
    for i in range(len(answers)):
        itxt=drop_user_input_from_answer(answer=answers[i], instruction=instruction, userinput=userinputs[i])
        answers_d.append(itxt.strip())

    return answers_d

def addtodictlist(dictlist=[], dict={}):
    if len(dict)==0:
        return dictlist
    if len(dictlist)==0:
        dictlist.append(dict)
        return dictlist
    found=False
    for i, item in enumerate(dictlist):
        if item['pmid']==dict['pmid'] and item['entity_full_name']==dict['entity_full_name']:
            found=True
            break
    if found==False:
        dictlist.append(dict)
    return dictlist

#extract all dict unit
def extract_dicts_from(string_obj=""):
    if len(string_obj)==0:
        return []
    thinkpos=string_obj.find('</think>')
    if thinkpos!=-1:
        string_obj=string_obj.split('</think>')[1]
    string_obj=string_obj.strip()
    string_obj=string_obj.replace('",\n    }','"}')
    #check the validality of the dict
    #find the first pmid
    pos0=string_obj.find("\"PMID\":")
    if pos0!=-1:
        comma0=string_obj.find(',',pos0+5)
        pmidstr=string_obj[pos0+5:comma0]
        is_str=pmidstr.find('"')
        if is_str==-1:
            return []

    pos0=string_obj.find('"PMID": "..."')
    if pos0!=-1:
        pos1=string_obj.find('}', pos0+5)
        if pos1==-1:
            return[]
        else:
            string_obj=string_obj[pos1+1:]
    dictlist=[]
    try:
        found_left_brackets=False
        for i in range(len(string_obj)):
            if string_obj[i]=='{' and found_left_brackets==False:
                istart=i
                found_left_brackets=True
                
            if string_obj[i]=='}' and found_left_brackets==True:
                iend=i+1
                found_left_brackets=False
                isubstring=string_obj[istart:iend]
                idict=json.loads(isubstring)
                
                #add the current dict into dictlist. if the dictlist contains the same entity_name, this dict will be omitted
                dictlist=addtodictlist(dictlist,idict)
    except Exception as e:
        return []
    
    return dictlist

#extract dict from answers, batch processing
def extract_dicts_from_batch(answer_s):
    if len(answer_s)==0:
        return []
    dictset=[]
    for i, ianswer in enumerate(answer_s):
        idictlist=extract_dicts_from(string_obj=ianswer)
        dictset=dictset+idictlist
    return dictset

#export to csv
def export(filepath="", dict=None):
    #if os.path.exists(filepath)==False:
    #    return None
    df=pd.DataFrame(dict)
    df.to_csv(filepath)

#load data file, shared by history note and processed results
def load_data(filepath=""):
    if os.path.exists(filepath)==False:
        return []
    df=pd.read_csv(filepath)
    dictlist=df.to_dict(orient='records')
    return dictlist

#check processing record from dataset
def check_record_by(dataset=None, pmid=''):
    found=False
    if dataset is None or len(pmid)==0:
        return found
    for i, irecord in dataset.iterrows():
        if irecord['pmid']==pmid.strip():
            found=True
            break
    return found

#check processing record from dataset, batch processing
def check_record_by_batch(dataset=None, pmids=[]):
    found=False
    if dataset is None or len(pmids)==0:
        return found
    for i, irecord in dataset.iterrows():
        for j, jpmid in enumerate(pmids):
            if irecord['pmid']==jpmid.strip():
                found=True
                return found
    return found

if __name__=="__main__":
    if os.path.exists(dstfolder)==False:
        os.mkdir(dstfolder)

    #load the model
    if model=='gpt':
        llm=openai_api(engine=engine, api_version=version,env_path=env_path)# use pubmed api to donwload the abstract to replace AI method
        times=20
    elif model=='gpt_p':
        llm=openai_api_p(engine=engine, api_key="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")# use private account of openai api to start the openai
        times=20
    else:
        llm=vllm_model(modelpath=modelfolder,gpu_num=gpu_num,gpu_memory_utilization=0.55, max_num_seqs=32)
        times=15

    
    #load history note
    historyfilepath=os.path.join(dstfolder,'history.csv')
    if os.path.exists(historyfilepath):
        history=load_data(filepath=historyfilepath)
    else:
        history=[]

    #load the processed results
    dstfilepath=os.path.join(dstfolder,'rdoc_terms_extract_from_pubmed_'+model+'_'+version+'_'+date_str+'.csv')
    if os.path.exists(dstfilepath):
        dictlist=load_data(filepath=dstfilepath)
    else:
        dictlist=[]
    #
    #set instruction
    instruction=f"""You are a psychiatric expert focusing on sleep wake disorders. 
    Sleep wake disorders include  Sleep disorders, Dyssomnias, Insomnia, Hypersomnia, Parasomnia, Sleep fragmentation, Night terrors, Sleep apnea, Hypersomnolence disorders, Excessive daytime sleepiness, Narcolepsy, Sleep-Related Hypoventilation, Nightmare Disorder, Rapid Eye Movement Sleep Behavior Disorder, Restless Legs Syndrome, High-altitude periodic breathing, Periodic limb movement disorder, Sleep-related movement disorders, Disorder of sleep of non-organic origin, Sleep disturbance, Sleep-Wake Disorders, Sleep Deprivation, Nocturnal Paroxysmal Dystonia, Sleep Arousal Disorders, Sleep Bruxism, Sleep-Wake Transition Disorders, Fatal Familial Insomnia, Organic insomnia, Disorders of Excessive Somnolence, Idiopathic Hypersomnia, Kleine-Levin Syndrome, Organic hypersomnia, Sleep Apnea Syndromes, Central Sleep Apnea, Obstructive Sleep Apnea, obstructive Sleep Apnea Hypopnea, Obesity Hypoventilation Syndrome, Organic sleep apnea, Circadian Rhythm Sleep-Wake Disorders, Jet Lag Syndrome, Circadian Rhythm Disorders, Rapid Eye Movement Sleep Behavior Disorder, Rapid Eye Movement Sleep Parasomnias, Non-Rapid Eye Movement Sleep Arousal Disorders, Somnambulism, Sleep Paralysis, Nocturnal Myoclonus Syndrome, Sleep Initiation and Maintenance Disorders, and Cataplexy.
    Your task is to extract sleep wake disorder-related entities, including three types: cell, gene and molecule, from PubMed articles based on their titles or abstracts. Specifically, 
    A cell is a fundamental structural and functional unit of life, such as blood platelet, leukocyte, endocrine cell. 
    A gene is a specific genetic variant, polymorphism, or other genomic feature, such as SLC6A4 (serotonin transporter gene), COMT (catechol-O-methyltransferase gene). 
    A molecule is the biochemical substance that underlies and helps characterize specific biological or psychological functions, such as neurotransmitters (glutamate, gamma-aminobutyric acid, etc.), neuromodulators (adenosine, nitric oxide, etc.), peptides (neuropeptide S), and other signaling molecules. Please do not include genes in molecules.

    Please follow steps as below:
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
    Finally, output results only in the following Python list-of-dictionaries format, with no explanations, no reasoning, no thinking and no extra text:
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
    If no valid entities are found, return [].
    """
    
    df0=pd.read_csv(srcfilepath)
    idx=df0['label']==1
    df=df0[idx]
    #articlelist=sorted(glob.glob1(srcfolder,"*.txt"))
    if len(df)==0:
        sys.exit()
    batch=(len(df)+batchsize-1)//batchsize
    for row in range(0,len(df),batchsize):
        bn=row
        if row+batchsize>=len(df):
            en=len(df)
        else:
            en=bn+batchsize
        
        #batch processing, collect articles
        ipmids=df[bn:en]['pmid'].tolist()
        #check in history records
        ifound=check_record_by_batch()
        print(f'====>Iteration:{row//batchsize+1}, total: {len(df)}, batchsize: {batchsize}')
        if ifound:
            print("----> this article has been tackled. skipped!")
            continue
        iuserinputs=df[bn:en]['abstract'].tolist()

        it0=dt.now()
        

        try:
            if model=='gpt' or model=='gpt_p':
                i_max_new_tokens=estimate_token_from_batch(instruction=instruction,userinputs=iuserinputs)
                ianswers=llm.predict_zero_shot(instruction=instruction, prompts=iuserinputs[0], max_new_tokens=i_max_new_tokens*times)
                if ianswers=='NA':
                    print("----> nothing was extracted. skipped!")
                    continue
                
                answer_s=drop_user_input_from_answer_batch(answers=[ianswers],instruction=instruction, userinputs=iuserinputs)
            else:
                i_max_new_tokens=estimate_token_from_batch(instruction=instruction,userinputs=iuserinputs)
                ianswers=llm.predict_zero_shot(instruction=instruction, prompts=iuserinputs, max_new_tokens=i_max_new_tokens*times)
                if ianswers=='NA':
                    print("----> nothing was extracted. skipped!")
                    continue

                answer_s=drop_user_input_from_answer_batch(answers=ianswers,instruction=instruction, userinputs=iuserinputs)
            
            idictlist0=extract_dicts_from_batch(answer_s)
        except Exception as e:
            idictlist0=[]
            answer_s=[]
        if len(idictlist0)==0 or len(answer_s)==0:
            print("----> nothing was extracted. skipped!")
            continue
        
        #add time stamp
        it1=dt.now()
        idlen=len(idictlist0)
        idictlist=[]
        for i,idict in enumerate(idictlist0):
            idict['time_start']=it0
            idict['time_end']=it1
            elapsed=it1-it0
            idict['time_elapsed']=elapsed.total_seconds()
            idictlist.append(idict)
        dictlist=dictlist+idictlist

        #export the answer
        for j, jpmid in enumerate(ipmids):
            jarticlename=str(jpmid)+".txt" 
            if j>=len(answer_s):
                continue
            jdstfilepath=os.path.join(dstfolder,jarticlename)
            with open(jdstfilepath, 'w') as f:
                f.write(answer_s[j])
            f.close()
        print(f"===>start:{it0}, end:{it1}, interval:{it1-it0}")

        #save the processed results and history note
        #if row%batchsize==0 and row!=0:
        export(filepath=dstfilepath,dict=dictlist)
        export(filepath=historyfilepath,dict=history)
    if model!='gpt' and model!='gpt_p':
        llm.closemodel()
    if len(dictlist)==0:
        sys.exit()
    export(filepath=dstfilepath,dict=dictlist)
    export(filepath=historyfilepath,dict=history)
    print(f"====> Done")