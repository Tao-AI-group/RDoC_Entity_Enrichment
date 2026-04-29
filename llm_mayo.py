import os
from dotenv import load_dotenv
import torch, gc
import requests
import json
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline 
from peft import LoraConfig, get_peft_model, TaskType 
from vllm import LLM, SamplingParams
from openai import OpenAI

#open ai with private information
class openai_api_p:
    def __init__(self, engine = "gpt-4o", api_key="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"):
        self.model = engine
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)

    def predict_zero_shot(self, instruction="", prompts="", max_new_tokens=2048):
        if len(prompts.strip())==0 or len(instruction)==0:
            return []
        
        # Generate response
        #messageset=[{"role": "system", "content": f"{instruction}"},
        #        {"role": "user", "content": f"User:{prompts}"}]
        userinput=f'Task:{instruction}, \n Article: {prompts}'
        try:
            response = self.client.responses.create(
                model=self.model,
                input = userinput)
            #answer = response.choices[0].message.content.strip()
            answer = response.output_text.strip()
        except Exception as e:
            answer = 'NA'
        return answer

#open ai with aws
#engine:gpt-5
#version:'2024-10-21'
# OR
#engine:gpt-4o
#version:'2024-04-14'
class openai_api:
    def __init__(self, engine='gpt-5', api_version='2025-10-21', env_path='/home/m308371/.env'):
        self.engine = engine
        self.api_version = api_version
        home_directory = os.path.expanduser("~")
        if os.path.exists(env_path)==False:
            env_path=os.path.join(home_directory,'.env')
        self.env_path = env_path
        self.api_config = self.get_mccaif_azure_openai_config()

    #set api token for openai
    def get_apigee_token(self, client_id, secret_id, apigee_url):
        """ get_apigee_token: get apigee token using client_id and secret_id through Mayo MCC INTERNAL production portal url 
            IN:
                client_id: client id from Apigee Prod Consumer Portal
                secret_id: secret id from  Apigee Prod Consumer Portal
                apigee_url: Mayo MCC INTERNAL production portal apigee url
            RETURN:
                apigee_token: apigee token to access Azure OpenAI service
        """
        payload = f'grant_type=client_credentials&client_id={client_id}&client_secret={secret_id}'
        headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            response = requests.request("POST", apigee_url, headers=headers, data=payload)
            print(response.text)

            #apigee_token = response.text.strip() #"YOUR_APIGEE_TOKEN_HERE"
            parsed_json = json.loads(response.text)
            apigee_token = parsed_json['access_token']
        except Exception as e:
            apigee_token=''

        return apigee_token

    def get_mccaif_azure_openai_config(self): #, model_name='gpt-4', api_version='2023-05-15', env_path='/home/m308371/.env'):
        """ get_apigee_openpi_config: get Azure OpenAI config using apigee token
            IN:
                engine: either "gpt-35-turbo", "gpt-35-turbo-16k", "gpt-4", or "gpt-4-32k
                api_version: api version, e.g., '2023-05-15'
                env_path: env path which contains the following setting,
                    client_id: client id from apigee
                    secret_id: secret id from apigee
                    apigee_token_url: https://internal.mcc.api.mayo.edu/oauth/token
                    apigee_url: https://internal.mcc.api.mayo.edu
            RETURN:
                api_config: Azure OpenAI config with apigee token
        """
        if not load_dotenv(self.env_path):
            print('It seems .env hide somewhere, please put in your home or current project folder and try again...')
            exit()
        # get apigee openai config
        client_id = os.environ['APIGEEX_CLIENT_ID'] #"lqY4Jtvo1rwZWN6HEhtDl1pnaGoSGKhEUNMsmdFjo5L8gtTm"
        #print(f'client id: {client_id}')
        secret_id = os.environ['APIGEEX_SECRET_ID'] #"0SCGrsTPHkB1B73Y9EuQF9yd41BhDmeSIUqJ68pFRd25k85RoHcPuc0A5TdlH80K"
        apigee_token_url = os.environ['APIGEEX_TOKEN_URL'] #"https://mcc.apix.mayo.edu/oauth/token"
        apigee_url = os.environ['APIGEEX_URL'] #"https://mcc.apix.mayo.edu"
        # get apigee token
        try:
            apigee_token = self.get_apigee_token(client_id, secret_id, apigee_token_url)
            api_config = {
                'client_id': client_id,
                'secret_id': secret_id,
                'apigee_token_url': apigee_token_url,
                'apigee_url': apigee_url,                      
                'engine': self.engine,
                'api_version': self.api_version,
                'azure_openai_url': apigee_url + f"/llm-azure-openai/openai/deployments/{self.engine}/chat/completions?api-version={self.api_version}",
                'headers': {'Content-Type': 'application/x-www-form-urlencoded'},
                'payload': f'grant_type=client_credentials&client_id={client_id}&client_secret={secret_id}'
                #'endpoint_payload' : {},
            }
        except Exception as e:
            api_config = None

        return api_config

    #prediction with azure openai
    def predict_zero_shot(self, instruction="", prompts="", max_new_tokens=512):
        if self.api_config is None or len(instruction)==0 or len(prompts)==0:
            return "Need instructin or prompts"

        # Send the request to generate the Apigee Token
        response = requests.request("POST", self.api_config['apigee_token_url'], headers=self.api_config['headers'], data=self.api_config['payload'])
        if response.status_code!=200:
            return "Apigee token failed"
        apigee_token=response.json().get("access_token")
        
        self.max_new_tokens=max_new_tokens

        # process csv file to get response from openai API
        headers = {'Authorization': f'Bearer {apigee_token}'}
        messages = [
            {"role": "system", "content": instruction},
            {"role": "user", "content": prompts}
        ]
        #max_tokens=int(1.5*len(prompt))
        endpoint_payload = {
            "messages": messages,
            "max_completion_tokens": max_new_tokens
        }
        
        try:
            response = requests.request("POST", self.api_config['azure_openai_url'], headers=headers, json=endpoint_payload)
            if response.status_code!=200:
                return "Request failed"
            json_object = json.loads(response.text)
            keys=json_object.keys()
            if 'choices' not in keys:
                return "No 'choices' in json"
            answer = json_object['choices'][0]['message']['content'].strip(" ")
        except Exception as e:
            answer = "Request Exception"
        return answer

class llama:
    def __init__(self, modelpath="", version='3.3-70B', max_new_tokens=2148):
        self.modelpath=modelpath
        self.version=version
        self.max_new_tokens=max_new_tokens
        self.loadmodel()
    
    #load model
    def loadmodel(self):
        if os.path.exists(self.modelpath)==False:
            self.pipe=None
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.modelpath)
            model = AutoModelForCausalLM.from_pretrained(self.modelpath, torch_dtype=torch.bfloat16, device_map="auto")
            
            # Configure LoRA
            lora_config = LoraConfig(
                r=8,
                lora_alpha=16,
                lora_dropout=0.1,
                bias="none",
                task_type=TaskType.CAUSAL_LM
            )

            model = get_peft_model(model, lora_config)
            model.eval()  # Set to eval for inference
            self.pipe = pipeline("text-generation", model=model, tokenizer=tokenizer,torch_dtype=torch.bfloat16, device_map="auto", temperature=0.5)
        except Exception as e:
            self.pipe=None

    def predict_zero_shot(self, instruction="", prompts="", max_new_tokens=2048):
        if len(instruction)==0 or len(prompts)==0:
            return ""
        if self.pipe is None:
            return ""
        self.max_new_tokens=max_new_tokens
        user_prompt=f"Instruction: {instruction}\n User: {prompts}\n"
        try:
            output = self.pipe(user_prompt, max_new_tokens=self.max_new_tokens, num_return_sequences=1)
            response = output[0]['generated_text']
        except Exception as e:
            response = 'NA'
        return response

class qwen:
    def __init__(self, modelpath="", version='3-14B', max_new_tokens=2148):
        self.modelpath=modelpath
        self.version=version
        self.max_new_tokens=max_new_tokens
        self.loadmodel()
    
    #load model
    def loadmodel(self):
        if os.path.exists(self.modelpath)==False:
            self.pipe=None
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.modelpath)
            model = AutoModelForCausalLM.from_pretrained(self.modelpath, torch_dtype=torch.bfloat16, device_map="auto")
            
            # Configure LoRA
            lora_config = LoraConfig(
                r=8,
                lora_alpha=16,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                lora_dropout=0.1,
                bias="none",
                task_type=TaskType.CAUSAL_LM
            )

            model = get_peft_model(model, lora_config)

            self.pipe = pipeline("text-generation", model=model, tokenizer=tokenizer,torch_dtype=torch.bfloat16, device_map="auto", temperature=0.5)
        except Exception as e:
            self.pipe=None

    def predict_zero_shot(self, instruction="", prompts="", max_new_tokens=8192):
        if len(instruction)==0 or len(prompts)==0:
            return ""
        if self.pipe is None:
            return ""
        self.max_new_tokens=max_new_tokens
        user_prompt=f"Instruction: {instruction}\n User: {prompts}\n"

        try:
            output = self.pipe(user_prompt, max_new_tokens=self.max_new_tokens, num_return_sequences=1)
            response = output[0]['generated_text']
        except Exception as e:
            response = 'NA'
        return response

class medgemma:
    def __init__(self, modelpath="", version='27b-text-it', max_new_tokens=8192):
        self.modelpath=modelpath
        self.version=version
        self.max_new_tokens=max_new_tokens
        self.loadmodel()
    
    #load model
    def loadmodel(self):
        if os.path.exists(self.modelpath)==False:
            self.pipe=None
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.modelpath)
            model = AutoModelForCausalLM.from_pretrained(self.modelpath, torch_dtype=torch.bfloat16, device_map="auto")
            
            # Configure LoRA
            lora_config = LoraConfig(
                r=8,
                lora_alpha=16,
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
                lora_dropout=0.1,
                bias="none",
                task_type=TaskType.CAUSAL_LM
            )

            model = get_peft_model(model, lora_config)
            
            self.pipe = pipeline("text-generation", model=model, tokenizer=tokenizer,torch_dtype=torch.bfloat16, device_map="auto", temperature=0.5)
        except Exception as e:
            self.pipe=None

    def predict_zero_shot(self, instruction="", prompts="", max_new_tokens=8192):
        if len(instruction)==0 or len(prompts)==0:
            return ""
        if self.pipe is None:
            return ""
        self.max_new_tokens=max_new_tokens
        user_prompt=f"Instruction: {instruction}\n User: {prompts}\n"
        try:
            output = self.pipe(user_prompt, max_new_tokens=self.max_new_tokens, num_return_sequences=1)
            response = output[0]['generated_text']
        except Exception as e:
            response = 'NA'
        return response

#create model using vllm api
class vllm_model:
    def __init__(self, modelpath="", gpu_num=1, gpu_memory_utilization=0.70, max_num_seqs=256, temperature=0.8, top_p=0.95):
        self.modelpath=modelpath
        self.max_new_tokens=256
        self.gpu_num=gpu_num
        self.gpu_memory_utilization=gpu_memory_utilization
        self.temperature=temperature
        self.max_num_seqs=max_num_seqs
        self.top_p=top_p
        self.llm=None
        self.loadmodel()

    def loadmodel(self):
        if os.path.exists(self.modelpath)==False:
            self.llm=None
            return
        #create the model
        print(f'---->create a new model')
        self.llm = LLM(model=self.modelpath, tensor_parallel_size=self.gpu_num,gpu_memory_utilization=self.gpu_memory_utilization, max_num_seqs=self.max_num_seqs)

    def closemodel(self):
        if self.llm is None:
            return
        del self.llm
        gc.collect()
        torch.cuda.empty_cache()
    '''
    def predict_zero_shot(self, instruction="", prompts=[], max_new_tokens=2048):
        if len(instruction)==0 and len(prompts)==0:
            return []
        #combine instruct and prompts, set the parameters
        self.max_new_tokens=max_new_tokens
        user_prompts=[]
        for i, item in enumerate(prompts):
            iuser_prompt=f"Instruction: {instruction}\n User: {item}\n"
            user_prompts.append(iuser_prompt)
        params = SamplingParams(temperature=self.temperature, top_p=self.top_p, max_tokens=self.max_new_tokens)
        #genearate the results
        try:
            outputs = self.llm.generate(user_prompts, params)
        except Exception as e:
            return []
        #extract results
        answers=[]
        for output in outputs:
            text = output.outputs[0].text
            answers.append(text)
        #self.closemodel()
        return answers
    '''
    def predict_zero_shot(self, instruction="", prompts=[], max_new_tokens=2048):
        if len(instruction)==0 and len(prompts)==0:
            return []
        #combine instruct and prompts, set the parameters
        self.max_new_tokens=max_new_tokens
        formatted_prompts = []
        # Get the tokenizer from the loaded LLM instance
        if self.llm is None:
            return []
        tokenizer = self.llm.get_tokenizer()
        for item in prompts:
            # 1. Create the structured message format
            messages = [
                {"role": "system", "content": instruction},
                {"role": "user", "content": item}
            ]
            
            # 2. Apply the chat template with the hard switch
            # This ensures the <think> tokens are never triggered
            text_prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False  # The Hard Switch from the README
            )
            formatted_prompts.append(text_prompt)
        
        # 3. Adjust SamplingParams for non-thinking mode (recommended)
        '''
        params = SamplingParams(
            temperature=self.temperature, 
            top_p=self.top_p, 
            max_tokens=self.max_new_tokens,
            stop=["<|endoftext|>", "<|im_end|>"] # Ensure clean stops
        )
        '''
        params = SamplingParams(
            temperature=self.temperature,#0, 
            min_p=0.05, 
            max_tokens=self.max_new_tokens,
            stop=["<|im_end|>"] # Ensure clean stops
        )
        
        try:
            # Generate using the formatted strings
            outputs = self.llm.generate(formatted_prompts, params)
        except Exception as e:
            print(f"Error: {e}")
            return []
        
        #extract results
        answers=[]
        for output in outputs:
            text = output.outputs[0].text.replace('\n','').strip()
            answers.append(text)
        #self.closemodel()
        return answers
'''
#Testing code
if __name__ == "__main__":

    engine='gpt-4o'
    llm=openai_api_p(engine=engine)

    # test azure openai
    engine='gpt-5'
    api_version='2024-10-21'
    #instruction = "You are an AI assistant specialized in HPV consultant that helps doctors to answer questions from public, which may include teenagers, parents, and community workers."
    instruction = "You are an AI assistant."
    #with open('/home/m253461/projects/06violin/data/myocarditis/Abstract/PMC8255555.html','r') as f:
    #    prompt=f.read()
    prompt="Tell me where is the capital of USA."
    env_path = "/home/m253461/.env" # set to your .env path
    openai_test=openai_api(engine=engine, api_version=api_version,env_path=env_path)
    pred=openai_test.predict_zero_shot(instruction=instruction, prompts=prompt)
    print(f"====> context: {instruction}")
    print(f"====> prompt:{prompt}")
    print(f"====> prediction: {pred}")
    print('test mccaif azure openai done.')

    #test llama3.3
    llama33=llama(modelpath="/home/m253461/meta-llama/Llama-3.3-70B-Instruct")
    instruction="hello"
    prompt = "tell me one story of the White House."
    response = llama33.predict_zero_shot(instruction=instruction, prompt=prompt)
    print(f"====> user:{prompt}\n")
    print(f"====> answer:{response}\n")
   
    #test medgemma
    mgemma=medgemma(modelpath="/home/m253461/google/medgemma-27b-it")
    instruction="hello"
    prompt = "tell me one story of the White House."
    response = mgemma.predict_zero_shot(instruction=instruction, prompt=prompt)
    print(f"====> user:{prompt}\n")
    print(f"====> answer:{response}\n")

    #test vllm
    os.environ["CUDA_VISIBLE_DEVICES"] = "3,2,1,0"
    device = torch.device("cuda")
    vllm_llama=vllm_model(modelpath='/home/m253461/meta-llama/Llama-3.3-70B-Instruct',gpu_num=4)
    instuction='do predict for the following user input.'
    prompts = [
        "Hello, my name is",
        "The president of the United States is",
        "The capital of France is",
        "The future of AI is",
        ]
    results=vllm_llama.predict_zero_shot(instruction=instuction,prompts=prompts)

    print(prompts)
    print(results)

'''