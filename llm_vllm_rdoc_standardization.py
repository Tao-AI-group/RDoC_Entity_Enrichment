import os
import re
import sys
import json
import glob
from datetime import datetime as dt
import torch
#import numpy as np
import pandas as pd
if '/home/m253461/projects/tools' not in sys.path:
    sys.path.insert(0, '/home/m253461/projects/tools')
from llm_mayo import vllm_model
#from pubmed_abstract_download import pubmed_abstract_download

#modelfolder="/home/m253461/meta-llama/Llama-3.3-70B-Instruct"
modelfolder="/home/m253461/qwen/Qwen3-14B"
#modelfolder="/home/m253461/qwen/Qwen3-32B"
#modelfolder="/home/m253461/google/medgemma-27b-text-it"
gpu_num=4
batchsize=4

rdoc_extraction_ground_truth_path="/home/m253461/projects/03rdoc/results/rdoc_entity_matched_1_GT.xlsx"
umlsfilepath="/home/m253461/umls/2024AB/META/mr_conso_sty_eng.csv"
umlsfolder="/home/m253461/umls/2024AB/mrconso_split"
dstfolder_base="/home/m253461/projects/03rdoc/results"

# set gpu environment
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2,3"
device = torch.device("cuda")

#load one data, shared by history note and processed results
def loadone(filepath=""):
    if os.path.exists(filepath)==False:
        return []
    if filepath[-4:]=='.csv':
        df=pd.read_csv(filepath, engine='python')
    elif filepath[-4:]=='xlsx':
        df=pd.read_excel(filepath)
    else:
        with open(filepath,'r') as f:
            df=f.read().lower()
    return df

#load the dataset
def loaddataset(filepathset=[], folder=""):
    flen=len(filepathset)
    if flen==0:
        return []
    df=[]
    for i, ifilepath in enumerate(filepathset):
        ipath=os.path.join(folder, ifilepath)
        idf=loadone(ipath)
        df.append(idf)
    return df

#export to csv
def export(filepath="", dict=None):
    if os.path.exists(filepath):
        os.remove(filepath)
    df=pd.DataFrame(dict)
    df.to_csv(filepath)

#extract model name and verison from model folder
def extract_model_version(folder):
    if os.path.exists(folder)==False:
        return "",""
    
    basename=os.path.basename(folder)
    p=basename.find("-")
    if p==-1:
        return basename,""
    else:
        return basename[:p],basename[(p+1):]

#create the instruction and prompt
def create_prompt(text="", key=""):
    if len(text)==0 or len(key)==0:
        return ''

    prompt = f"""
        Role: You are a Bio-Medical Data Scientist specializing in high-precision entity normalization and terminology mapping.
        Instruction: I will provide a string containing multiple units separated by the $ delimiter. Each unit consists of an index and a text string, separated by the | character. I will also provide a keyword, {key}. Your task is to compare the text in each unit with the given keyword. 
        
        Input: {text}

        Tasks:
        1) Parse: Split the text into individual units. 
        2) Compare: For each unit, compare its string against ‘{key}’. 
        3) Calculate: Determine both the semantic similarity rate (3 decimal) and the string similarity rate(3 decimal). The semantic similarity score reflects meaning-level similarity, while the string similarity score is computed from character-level overlap (e.g., Levenshtein distance).
        4) Format: For each unit, output the index, semantic similarity, and string similarity, separated by '|'. 
        5) Final Output: Join these unit results using '$' as the separator and return the resulting string.
    """
    return prompt

#create prmpots for abstract set
def create_prompt_batch(textset=[], key=""):
    if len(textset)==0 or len(key)==0:
        return []

    promptset=[]
    for i, itext in enumerate(textset):
        iprompt=create_prompt(text=itext,key=key)
        if iprompt=="":
            continue
        promptset.append(iprompt)
    return promptset

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

# drop the user input from each corresponding answer
def drop_user_input_from_answer_batch(answers=[],instruction="", userinputs=[]):
    if len(answers)==0 or len(userinputs)==0 or (len(answers)!=len(userinputs)):
        return []
    answers_d=[]
    for i in range(len(answers)):
        itxt=drop_user_input_from_answer(answer=answers[i], instruction=instruction, userinput=userinputs[i])
        answers_d.append(itxt.strip())

    return answers_d

def validation(jsonset):
    jlen=len(jsonset)
    if jlen==0:
        return ""
    for i in range(jlen-1,-1,-1):
        ijson=jsonset[i].replace('\n',' ').strip()
        if len(ijson)==0:
            if i==jlen-1:
                jsonset=jsonset[:-1]
            elif i==0:
                jsonset=jsonset[1:]
            else:
                jsonset=jsonset[:i]+jsonset[i+1:]
            jlen=len(jsonset)
            continue
        ijstrset0=ijson.split('"sleep_wake_disorder_focus"')
        if len(ijstrset0)<2:
            if i==jlen-1:
                jsonset=jsonset[:-1]
            elif i==0:
                jsonset=jsonset[1:]
            else:
                jsonset=jsonset[:i]+jsonset[i+1:]
            jlen=len(jsonset)
            continue
        ijstrset1=ijstrset0[1].split('"reason"')
        imstrset2=ijstrset1[0].split('"include_or_not"')
        if len(imstrset2)<2:
            if i==jlen-1:
                jsonset=jsonset[:-1]
            elif i==0:
                jsonset=jsonset[1:]
            else:
                jsonset=jsonset[:i]+jsonset[i+1:]
            jlen=len(jsonset)
            continue
        true0=imstrset2[0].lower().find('true')
        false0=imstrset2[0].lower().find('false')
        true1=imstrset2[1].lower().find('true')
        false1=imstrset2[1].lower().find('false')
        if (true0==-1 and false0==-1) or (true1==-1 and false1==-1):
            if i==jlen-1:
                jsonset=jsonset[:-1]
            elif i==0:
                jsonset=jsonset[1:]
            else:
                jsonset=jsonset[:i]+jsonset[i+1:]
            jlen=len(jsonset)
    return jsonset

#extract dict from answers, batch processing
def extract_answer_from_batch(answer_s):
    if len(answer_s)==0:
        return []
    answerset=[]
    for i, ianswer in enumerate(answer_s):
        ipos=ianswer.find('</think>')
        if ipos==-1:
            ianswer=ianswer
        else:
            ianswer=ianswer[ipos+8:]
        ianswer=ianswer.replace('\n','')
        answerset.append(ianswer)
    return answerset

#extract top3 from text
def top3(text=""):
    tlen=len(text)
    if tlen==0:
        return []
    tset=[]
    unitset=text.split("$")
    for i, iunit in enumerate(unitset):
        if len(iunit)==0:
            continue
        if iunit[0]=='|':
            iunit=iunit[1:]
        if iunit[-1]=='$':
            iunit=iunit[:-1]
        ifieldset=iunit.split('|')
        itset={}
        itset['index']=int(ifieldset[0])
        ifld1str=ifieldset[1].replace('.','')
        if not ifld1str.isdigit():
            continue
        ifld2str=ifieldset[2].replace('.','')
        if not ifld2str.isdigit():
            continue
        itset['s_sem']=float(ifieldset[1])
        itset['s_str']=float(ifieldset[2])
        tset.append(itset)
    tset=sorted(tset, key=lambda x: (x['s_sem'],x['s_str']), reverse=True)
    tset_top3=tset[:3]
    return tset_top3

#extract top3 from a set of text
def extrach_top3_batch(textset=[]):
    tlen=len(textset)
    if tlen==0:
        return []
    
    tset=[]
    for i, itext in enumerate(textset):
        itset=top3(itext)
        tset+=itset
    return tset

#map the top 3 into a record
def flatten(candidates=[], key='', id="", df=None):
    if len(candidates)==0:
        return None
    record={}
    record['pmid']=id
    record['entity_name_GT']=key
    keys=candidates[0].keys()
    for i, ican in enumerate(candidates):
        for j, jkey in enumerate(keys):
            ijkey=jkey+"_"+str(i)
            record[ijkey]=ican[jkey]
            if jkey=="index":
                ijidx=ican[jkey]
                ijstrval=df.loc[ijidx,'STR']
                ijpnval=df.loc[ijidx,'PN']
                ijstrkey="STR_"+str(i)
                record[ijstrkey]=ijstrval
                ijpnkey="PN_"+str(i)
                record[ijpnkey]=ijpnval

    return record

def update_title_abstract(dictlist, df):
    dlen=len(dictlist)
    dflen=len(df)
    if dlen==0 or dflen==0 or dflen!=dflen:
        return dictlist
    dictset=[]
    for i in range(dlen):
        idict={}
        idict['pmid']=df.loc[df.index[i],'pmid']
        idict['title']=df.loc[df.index[i],'title']
        idict['abstract']=df.loc[df.index[i],'abstract']
        if 'large_language_model' in dictlist[i].keys():
            idict['large_language_model']=dictlist[i]['large_language_model']
        else:
            idict['large_language_model']='-1'
        if 'model_version' in dictlist[i].keys():
            idict['model_version']=dictlist[i]['model_version']
        else:
            idict['model_version']='-1'
        if 'sleep_wake_disorder_focus' in dictlist[i].keys():
            idict['sleep_wake_disorder_focus']=dictlist[i]['sleep_wake_disorder_focus']
        else:
            idict['sleep_wake_disorder_focus']=False
        if 'include_or_not' in dictlist[i].keys():
            idict['include_or_not']=dictlist[i]['include_or_not']
        else:
            idict['include_or_not']=False
        if 'reason' in dictlist[i].keys():
            idict['reason']=dictlist[i]['reason']
        else:
            idict['reason']="-1"
        dictset.append(idict)
    return dictset

if __name__=="__main__":
    if os.path.exists(rdoc_extraction_ground_truth_path)==False or os.path.exists(umlsfolder)==False or os.path.exists(umlsfilepath)==False:
        print("====> warning: source file path error! check the file path.")
        sys.exit()

    model,version=extract_model_version(modelfolder)
    if model=="":
        print("====> warning: model error! check model folder.")
        sys.exit()
    
    if version=="":
        version='0'
    #create the output folder
    tb = dt.now()
    date_str = tb.strftime("%Y_%m_%d")
    dstfolder=dstfolder_base+"_"+model+"_"+version+"_"+date_str
    if os.path.exists(dstfolder)==False:
        os.mkdir(dstfolder)
    '''
    #load the processed results
    dstfilepath=os.path.join(dstfolder,'article_screening_'+model+'_'+version+'_'+date_str+'.csv')
    if os.path.exists(dstfilepath):
        dictlist=load_data(filepath=dstfilepath)
    else:
        dictlist=[]
    '''
    dictlist=[]
    #loading model with vllm api
    llm=vllm_model(modelpath=modelfolder,gpu_num=gpu_num, gpu_memory_utilization=0.80, max_num_seqs=gpu_num*2)
    times=0.5

    #load the umls volumes
    umls_filepath_set=sorted(glob.glob1(umlsfolder,"*.txt"))
    umlsset=loaddataset(filepathset=umls_filepath_set, folder=umlsfolder)
    ulen=len(umlsset)
    if ulen==0:
        print("====> warning: source file is empty. make a double check!")
        sys.exit()        
    #load umls
    df_umls=loadone(umlsfilepath)
    #load rdoc entity groundtruth
    rdoc_gt=loadone(rdoc_extraction_ground_truth_path)

    sys_inst = "You are a subject matter expert in biomedical entity identification."
    errorlist=[]
    rdoc_gt_candidate=[]
    for i, irow in rdoc_gt.iterrows():
        ikey=irow['Groundtruth'].lower()
        #ikey='1,4-alpha-glucan branching enzyme'
        n=0
        ianswerset=[] # only maintain top 3 for each umls volume if they are not 0
        for j in range(0,len(umlsset),batchsize):
            bn=j
            #if bn>batchsize:
            #    break
            if j+batchsize>=len(umlsset):
                en=len(umlsset)
            else:
                en=bn+batchsize
            n+=batchsize
            iumlsset=umlsset[bn:en]
            #start time
            itb=dt.now()
            #batch processing, collect umls volumes
            jpromptset=create_prompt_batch(iumlsset,ikey)
            print(f'---->current key id={i+1}/{len(rdoc_gt)}, key={ikey}, Iteration of the current key:{j//batchsize+1}/{len(umlsset)//batchsize+1}, total: {len(umlsset)}, batchsize: {batchsize}')

            try:
                #i_max_new_tokens=estimate_token_from_batch(instruction=sys_inst,userinputs=ipromptset)
                ianswers=llm.predict_zero_shot(instruction=sys_inst, prompts=jpromptset, max_new_tokens=8192*2)
                
                #drop instrucion and prompt from each anwsers
                #answer_s=drop_user_input_from_answer_batch(answers=ianswers,instruction=sys_inst, userinputs=jpromptset)
                #ianswer0=extract_answer_from_batch(answer_s)

                #extract top 3
                itop3set=extrach_top3_batch(ianswers)
                ianswerset+=itop3set
            except Exception as e:
                print(f'-----> LLM prediction error: {e}')
                errorlist+=iumlsset
                continue
            #break
            #extract the top 3 from ianswer0, and add them into ianswerset
        ianswerset_sorted=sorted(ianswerset, key=lambda x: (x['s_sem'],x['s_str']), reverse=True)
        itop3=ianswerset_sorted[:3]

        #map the top 3 into a record
        ipmid=irow['pmid']
        irecord=flatten(itop3, ikey, ipmid, df_umls)
        rdoc_gt_candidate.append(irecord)

        #export
        basefilename=os.path.basename(rdoc_extraction_ground_truth_path)
        dstfilepath=os.path.join(dstfolder_base,basefilename[:-5]+"_"+model+"_"+version+"_"+date_str+".csv")
        export(filepath=dstfilepath,dict=rdoc_gt_candidate)
        #break

    #llm.closemodel()
    if len(rdoc_gt_candidate)==0:
        sys.exit()
    #export(filepath=dstfilepath,dict=dictlist)
    errorfilepath=dstfilepath[:-4]+"_error.csv"
    errordict={'pmid':errorlist}
    export(errorfilepath,errordict)

    te=dt.now()
    tinterval=te-tb
    hour, remainder = divmod(tinterval.seconds, 3600)
    minute, second = divmod(remainder, 60)
    print(f"====> time elapsed, {hour}:{minute}:{second}")
    print(f"====> Done")

