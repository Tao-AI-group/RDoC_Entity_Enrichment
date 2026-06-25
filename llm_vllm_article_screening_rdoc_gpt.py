import os
import re
import sys
import json
from datetime import datetime as dt
import torch
#import numpy as np
import pandas as pd
if '/home/m253461/projects/tools' not in sys.path:
    sys.path.insert(0, '/home/m253461/projects/tools')
from llm_mayo import vllm_model, openai_api, openai_api_p

vllm=False  #False: non-vllm, True: vllm
###########
modelfolder="/home/m253461/meta-llama/Llama-3.3-70B-Instruct"
#modelfolder="/home/m253461/qwen/Qwen3-14B"
#modelfolder="/home/m253461/qwen/Qwen3-32B"
#modelfolder="/home/m253461/google/medgemma-27b-text-it"

###########
engine='gpt-4o'
api_version='2024-06-01'
env_path='~/.env'

#gpu and batch parameter
gpu_num=4
batchsize=8

srcfilepath="/home/m253461/projects/03rdoc/dataset/pubmed_sleep_disorder_batch/pubmed_sleep_disorder_abstract_2025.csv"
dstfolder_base="/home/m253461/projects/03rdoc/dataset/pubmed_sleep_disorder/pubmed_sleep_disorder_article_screening"

# set gpu environment
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2,3"
device = torch.device("cuda")

#load data file, shared by history note and processed results
def load_data(filepath=""):
    if os.path.exists(filepath)==False:
        return []
    df=pd.read_csv(filepath)
    dictlist=df.to_dict(orient='records')
    return dictlist

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
def create_prompt(abstract="", model="", version=""):
    if len(abstract)==0 or len(model)==0:
        return ''
    if version=="":
        version='0'

    prompt = f"""
    Role: You are an expert focusing on large language and sleep wake disorders.

    Background
    A paper is considered relevant to sleep-wake disorder if its primary objective addresses one or more of the following specific disorders or syndromes:
    Sleep-Wake Disorders, Sleep disorders, Dyssomnias, Parasomnias, Sleep disturbance, Sleep Deprivation, Sleep fragmentation, Insomnia, Fatal Familial Insomnia, Organic insomnia, Hypersomnia, Hypersomnolence Disorder, Disorders of Excessive Somnolence, Idiopathic Hypersomnia, Kleine-Levin Syndrome, Excessive daytime sleepiness, Organic hypersomnia, Sleep apnea, Sleep Apnea Syndromes, Central Sleep Apnea, Obstructive Sleep Apnea, Obstructive Sleep Apnea Hypopnea, Sleep-Related Hypoventilation, Obesity Hypoventilation Syndrome, Organic sleep apnea, Circadian Rhythm Sleep-Wake Disorders, Jet Lag Syndrome, Circadian Rhythm, REM Sleep Behavior Disorder, Rapid Eye Movement (REM) Sleep Behavior Disorder, REM Sleep Parasomnias, Non-Rapid Eye Movement (NREM) Sleep Arousal Disorders, sleep Arousal Disorders, Night terrors, Somnambulism, Nightmare Disorder, Sleep Paralysis, Nocturnal Paroxysmal Dystonia, Sleep Bruxism, Restless Legs Syndrome, Periodic Limb Movement Disorder, Nocturnal Myoclonus Syndrome, Sleep-related movement disorders, Narcolepsy, Disorder of sleep of non-organic origin, Cataplexy, Sleep Initiation and Maintenance Disorders, Sleep-Wake Transition Disorders, and High-altitude periodic breathing.

    Input:{ abstract }

    Task:
    You are a biomedical expert. Before giving your final answer, you must reason through the following steps explicitly and out loud. Show your thinking at each step.
    Step 1 — Extract diseases/disorders:
    Read the abstract carefully. List all the major diseases, disorders, or clinical conditions mentioned or studied in this article.
    Step 2 — Assess relevance to sleep-wake disorders:
    For each extracted disease/disorder, reason about whether it is directly or closely related to the sleep-wake disorder list above. Consider whether it appears on the list, or whether it is a known comorbidity, cause, or consequence of a listed disorder. Conclude with True or False for each.
    Step 3 — Make an inclusion decision:
    Based on your reasoning in Steps 1 and 2, decide whether the primary objective of this article is focused on sleep-wake disorders. If the sleep-wake disorder is incidental or secondary, the answer should be False. Conclude with True or False.
    Step 4 — Assign a confidence score:
    Reflect on how clear or ambiguous the evidence was across Steps 1–3. Assign a confidence score from 0 (completely uncertain) to 100 (completely certain) for your inclusion decision.
    Step 5 — Summarize your rationale:
    Write a concise 1–2 sentence summary explaining the key reason behind your inclusion decision.

    Output:
    R After completing all reasoning steps above, return your final answer as a Python dictionary in exactly the following format:
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
    """
    return prompt

#create prmpots for abstract set
def create_prompt_batch(abstractset=[], model="", version=""):
    if len(abstractset)==0 or len(model)==0:
        return []
    if version=="":
        version='0'
    promptset=[]
    for i, iabstract in enumerate(abstractset):
        iprompt=create_prompt(iabstract,model, version)
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
def extract_dicts_from_batch(answer_s, model, version):
    if len(answer_s)==0:
        return []
    dictset=[]
    for i, ianswer in enumerate(answer_s):
        ijsonmatch=re.findall(r'\{.*?\}', ianswer, re.DOTALL)#re.search(r'\{.*\}',ianswer,re.DOTALL)
        ijsonmatch=validation(ijsonmatch)
        try:
            itext=max(ijsonmatch, key=len).replace('\'s','').replace('\n',' ').replace('\'','').replace('True', 'true').replace('False','false')
            idictlist=json.loads(itext)
        except Exception as e:
            idictlist={
                "large_language_model": model,
                "model_version": version,
                "sleep_wake_disorder_focus": "false",
                "include_or_not": "false",
                "reason":"no"
                }
        
        dictset.append(idictlist)
    return dictset

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
    if os.path.exists(srcfilepath)==False:
        print("====> warning: source file path error! check the file path.")
        sys.exit()
    if vllm==True:
        model,version=extract_model_version(modelfolder)
    else:
        model=engine
        version='v0'

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
    
    #load the processed results
    dstfilepath=os.path.join(dstfolder,'article_screening_'+model+'_'+version+'_'+date_str+'.csv')
    if os.path.exists(dstfilepath):
        dictlist=load_data(filepath=dstfilepath)
    else:
        dictlist=[]
    if vllm==True:
        #loading model with vllm api
        llm=vllm_model(modelpath=modelfolder,gpu_num=gpu_num, gpu_memory_utilization=0.80, max_num_seqs=gpu_num*2)
    else:
        #llm=openai_api(engine=engine, api_version=api_version,env_path=env_path)
        llm=openai_api_p(engine=engine)

    times=0.5

    #do prediction for each article
    df=pd.read_csv(srcfilepath)
    dflen=len(df)
    if dflen==0:
        print("====> warning: source file is empty. make a double check!")
        sys.exit()

    sys_inst = "You are a subject matter expert in sleep disorder supporting the screening of research literature."
    errorlist=[]
    n=0
    for row in range(0,len(df),batchsize):
        #if n<1024:
        #    n+=batchsize
        #    continue
        bn=row
        if row+batchsize>=len(df):
            en=len(df)
        else:
            en=bn+batchsize
        n+=batchsize
        itb=dt.now()
        #batch processing, collect articles
        ipmids=df[bn:en]['pmid'].tolist()
        
        iabstractset=df[bn:en]['abstract'].tolist()
        ipromptset=create_prompt_batch(iabstractset,model,version)
        
        #use llm to do prediction 
        print(f'---->Iteration:{row//batchsize+1}/{len(df)//batchsize+1}, total: {len(df)}, batchsize: {batchsize}')
        try:
            i_max_new_tokens=estimate_token_from_batch(instruction=sys_inst,userinputs=ipromptset)
            ipromptset=ipromptset[0]
            ianswers=llm.predict_zero_shot(instruction=sys_inst, prompts=ipromptset, max_new_tokens=i_max_new_tokens//2)#, max_new_tokens=int(i_max_new_tokens//times))
            
            #drop instrucion and prompt from each anwsers
            answer_s=drop_user_input_from_answer_batch(answers=ianswers,instruction=sys_inst, userinputs=ipromptset)
            idictlist0=extract_dicts_from_batch(answer_s, model, version)
        except Exception as e:
            print(f'-----> LLM prediction error: {e}')
            errorlist+=ipmids
            continue
            
        if len(idictlist0)==0:
            print("----> python dictiony parsing is over. Nothing was extracted. Skipped!")
            errorlist+=ipmids
            continue
        
        idictlist0=update_title_abstract(idictlist0,df[bn:en])
        dictlist=dictlist+idictlist0
        export(filepath=dstfilepath,dict=dictlist)

        #time
        ite=dt.now()
        itbe=ite-itb
        ihour,irem=divmod(itbe.seconds,3600)
        iminute,isecond=divmod(irem,60)
        print(f"---->time elapsed for iteration {row+1}, {ihour}:{iminute}:{isecond}")

    #llm.closemodel()
    if len(dictlist)==0:
        sys.exit()
    export(filepath=dstfilepath,dict=dictlist)
    errorfilepath=dstfilepath[:-4]+"_error.csv"
    errordict={'pmid':errorlist}
    export(errorfilepath,errordict)

    te=dt.now()
    tinterval=te-tb
    hour, remainder = divmod(tinterval.seconds, 3600)
    minute, second = divmod(remainder, 60)
    print(f"====> time elapsed, {hour}:{minute}:{second}")
    print(f"====> Done")

