from Bio import Entrez
from bs4 import BeautifulSoup
import requests
from requests_html import HTMLSession
from requests.exceptions import ConnectionError
import os
import sys
import time
import pandas as pd
from datetime import datetime, timedelta

#query="((Sleep disorders[Title/Abstract]) OR (Dyssomnias[Title/Abstract]) OR (Insomnia[Title/Abstract]) OR ([Hypersomnia[Title/Abstract]) OR (parasomnia[Title/Abstract]) OR (Sleep fragmentation[Title/Abstract]) OR (Night terrors[Title/Abstract]) OR (Sleep apnea[Title/Abstract]) OR (Hypersomnolence disorders[Title/Abstract]) OR (Excessive daytime sleepiness[Title/Abstract]) OR (Narcolepsy[Title/Abstract]) OR (Sleep-Related Hypoventilation[Title/Abstract]) OR (Nightmare Disorder[Title/Abstract]) OR (Rapid Eye Movement (REM) Sleep Behavior Disorder[Title/Abstract]) OR (Restless Legs Syndrome[Title/Abstract]) OR (High-altitude periodic breathing[Title/Abstract]) OR (periodic limb movement disorder[Title/Abstract]) OR (Sleep-related movement disorders[Title/Abstract]) OR (Disorder of sleep of non-organic origin[Title/Abstract]) OR (Sleep disturbance[Title/Abstract]) OR (Sleep-Wake Disorders[Title/Abstract]) OR (Sleep Deprivation[Title/Abstract]) OR (Nocturnal Paroxysmal Dystonia[Title/Abstract]) OR (Sleep Arousal Disorders[Title/Abstract]) OR (Sleep Bruxism[Title/Abstract]) OR (Sleep-Wake Transition Disorders[Title/Abstract]) OR Sleep Wake Disorders[Majr]))"
query=f"((Sleep-Wake Disorders[Title/Abstract]) OR (Sleep disorders[Title/Abstract]) OR (Dyssomnias[Title/Abstract]) OR (Parasomnias[Title/Abstract]) OR (Sleep disturbance[Title/Abstract]) OR (Sleep Deprivation[Title/Abstract]) OR (Sleep fragmentation[Title/Abstract]) OR (Insomnia[Title/Abstract]) OR (Fatal Familial Insomnia[Title/Abstract]) OR (Organic insomnia[Title/Abstract]) OR (Hypersomnia[Title/Abstract]) OR (Hypersomnolence Disorder[Title/Abstract]) OR (Disorders of Excessive Somnolence[Title/Abstract]) OR (Idiopathic Hypersomnia[Title/Abstract]) OR (Kleine-Levin Syndrome[Title/Abstract]) OR (Excessive daytime sleepiness[Title/Abstract]) OR (Organic hypersomnia[Title/Abstract]) OR (Sleep apnea[Title/Abstract]) OR (Sleep Apnea Syndromes[Title/Abstract]) OR (Central Sleep Apnea[Title/Abstract]) OR (Obstructive Sleep Apnea[Title/Abstract]) OR (Obstructive Sleep Apnea Hypopnea[Title/Abstract]) OR (Sleep-Related Hypoventilation[Title/Abstract]) OR (Obesity Hypoventilation Syndrome[Title/Abstract]) OR (Organic sleep apnea[Title/Abstract]) OR (Circadian Rhythm Sleep-Wake Disorders[Title/Abstract]) OR (Jet Lag Syndrome[Title/Abstract]) OR (Sleep Disorders[Title/Abstract]) OR (Circadian Rhythm[Title/Abstract]) OR (REM Sleep Behavior Disorder[Title/Abstract]) OR (Rapid Eye Movement (REM) Sleep Behavior Disorder[Title/Abstract]) OR (REM Sleep Parasomnias[Title/Abstract]) OR (Non-Rapid Eye Movement (NREM) Sleep Arousal Disorders[Title/Abstract]) OR (Sleep Arousal Disorders[Title/Abstract]) OR (Night terrors[Title/Abstract]) OR (Somnambulism[Title/Abstract]) OR (Nightmare Disorder[Title/Abstract]) OR (Sleep Paralysis[Title/Abstract]) OR (Nocturnal Paroxysmal Dystonia[Title/Abstract]) OR (Sleep Bruxism[Title/Abstract]) OR (Restless Legs Syndrome[Title/Abstract]) OR (Periodic Limb Movement Disorder[Title/Abstract]) OR (Nocturnal Myoclonus Syndrome[Title/Abstract]) OR (Sleep-related movement disorders[Title/Abstract]) OR (Narcolepsy[Title/Abstract]) OR (Disorder of sleep of non-organic origin[Title/Abstract]) OR (Cataplexy[Title/Abstract]) OR (Sleep Initiation and Maintenance Disorders[Title/Abstract]) OR (Sleep-Wake Transition Disorders[Title/Abstract]) OR (High-altitude periodic breathing[Title/Abstract]) OR (Sleep Wake Disorder[Majr])) "
output_filename="pubmed_adrd_abstract_20000101.csv"
save_path="/home/m253461/projects/03rdoc/dataset/pubmed_sleep_disorder"
noncontent=True #False: full paper; True: only for abstract
date_start='20240701'
date_end='20250630'
period_days=184 #days
Entrez.email = "cao.weiguo@mayo.edu"
UNPAYWALL_API = "https://api.unpaywall.org/v2/"
SCI_HUB_URL = "https://sci-hub.se/"

# save the keyword
def save_retrieval_keywords(keywords="", filepath=""):
    with open(filepath,'w') as f:
        f.write(keywords)
    f.close()

#
def generatedatelist(startdate='20190101', enddate='20241231', period=180):
    # Convert to datetime
    start = datetime.strptime(startdate, "%Y%m%d")
    end = datetime.strptime(enddate, "%Y%m%d")

    # Generate ranges
    ranges = []
    currentstart = start

    while currentstart <= end:
        currentend = currentstart + timedelta(days=period - 1)
        if currentend > end:
            currentend = end
        ranges.append((
            currentstart.strftime("%Y/%m/%d"),
            currentend.strftime("%Y/%m/%d")
        ))
        currentstart = currentend + timedelta(days=1)
    return ranges
'''
# retrieve PubMed with PMID, the maximum is over 9999
def search_pubmed_v1(query, total=200000, batchsize=5000):
    if len(query)==0 or total<=0 or batchsize<=0:
        return []
    record=[]
    for start in range(0,total,batchsize):
        ihandle = Entrez.esearch(db="pubmed", term=query, retstart=start, retmax=batchsize)
        irecord = Entrez.read(ihandle)
        ihandle.close()
        record+=irecord["IdList"] 
    
    return record

# retrieve PubMed with PMID, maximum is 9999
def search_pubmed_v0(query, total=200000, batchsize=5000):
    handle = Entrez.esearch(db="pubmed", term=query, retstart=0, retmax=total)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]  
'''

#retrieve pubmed with query from date_start to date_end
def search_pubmed(query="", from_date='2019/01/01', to_date='2019/6/30'):
    #("2024/07/01"[Date - Publication] : "2024/12/31"[Date - Publication])
    date_str=f"({from_date}[Date - Publication] : {to_date}[Date - Publication])"
    query_n=query+" AND "+date_str
    handle = Entrez.esearch(db="pubmed", term=query_n, retstart=0, retmax=9999)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]

#retrieve from pubmed and return the pmid set
def retrieve(query="", from_date='20190101', to_date='20241231', period=183):
    if len(query)==0:
        return []
    datelist=generatedatelist(startdate=from_date,enddate=to_date,period=period)
    if len(datelist)==0:
        return []
    pmids=[]
    for ipair in datelist:
        istart=ipair[0]
        iend=ipair[1]
        irecord=search_pubmed(query=query, from_date=istart, to_date=iend)
        pmids.append(irecord)
    return pmids, datelist

# abstract parser
def parse_abstract(abstract=[]):
    ablen=len(abstract)
    if ablen==0:
        return ""
    abstr="Abstract\n"
    if ablen==1:
        abstr+=str(abstract[0])+"\n"
        return abstr
    
    for i in range(ablen):
        iattr=abstract[i].attributes['Label']
        abstr+=iattr+":"+str(abstract[i])+"\n"

    return abstr

# get the abstract and pmc id
def fetch_pubmed_one_group(pmids=[], period=[]):

    ids = ",".join(pmids)
    handle = Entrez.efetch(db="pubmed", id=ids, rettype="xml", retmode="text")
    records = Entrez.read(handle)
    handle.close()
    articles = []
    idx=1
    palen=len(records["PubmedArticle"])
    for article in records["PubmedArticle"]:
        pmid = article["MedlineCitation"]["PMID"]
        print(f"====> start:{period[0]}, end:{period[1]}, {idx}/{palen}: {pmid}")
        if idx<14:
            idx+=1
            continue
        title = article["MedlineCitation"]["Article"]["ArticleTitle"]
        articledate=article["MedlineCitation"]["Article"]['ArticleDate']
        if len(articledate)==0:
            articledatestr='19000101'
        else:
            articledatestr=articledate[0]['Year']+articledate[0]['Month']+articledate[0]['Day']
        journal=article["MedlineCitation"]["Article"]['Journal']['Title']
        abstract = article["MedlineCitation"]["Article"].get("Abstract", {}).get("AbstractText", [""])#[0]
        abstract_str=parse_abstract(abstract)

        idx=idx+1
        # look for pmc id and doi
        pmc_id=""
        doi=""
        for article_id in article["PubmedData"]["ArticleIdList"]:
            if article_id.attributes.get("IdType") == "pmc":
                pmc_id = article_id
            elif article_id.attributes.get("IdType") == "doi":
                doi = article_id
        if len(abstract_str)==0:
            article_abstract='-1'
        else:
            article_abstract="Title: "+title+'\n' + "PMID: "+pmid+ '\n'+ "PMCID:"+pmc_id+'\n' \
                    'doi:'+doi+'\n' + abstract_str
        articles.append({"pmid": pmid, "title": title, "abstract": article_abstract, "pmc_id": pmc_id, "doi": doi,'Journal':journal,'date':articledatestr,'diseases':[], 'label':0, 'llm':'','time_elapsed':-1})
        
    return articles

#get all papers
def fetch_pubmed_all(pmidset=[], dateset=[]):
    if len(pmidset)==0:
        return[]
    articles=[]
    for ipmids, idateset in zip(pmidset,dateset):
        iarticles=fetch_pubmed_one_group(ipmids,idateset)
        articles+=iarticles
    return articles

# get the full paper via pmc id
def download_one_fullarticle_pmc(pmcid="", folder=""):
    if os.path.exists(folder)==False:
        return {
            'exist': False,
            'url': f'{pmcid}',
            'status': f'failed to open folder',
            'message': f"Error: {folder} does not exist"
        }
    if len(pmcid)==0:
        return {
            'exist': False,
            'url': f'{pmcid}',
            'status': f'failed to open the arricle with the pmcid',
            'message': f"Error: pmcid is empty"
        }

    session=HTMLSession()
    headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'}
    try:
        base_url='https://www.ncbi.nlm.nih.gov/pmc/articles/'   #'https://pmc.ncbi.nlm.nih.gov/articles/articles/'
        response=session.get(base_url + pmcid+'/', headers=headers, timeout=10)
        #pdf_url='https://www.ncbi.nlm.nih.gov' + r.html.find('usa-link display-flex usa-tooltip__trigger',first=True).attrs('href')
        filename=pmcid+".html"
        filepath=os.path.join(folder,filename)
        with open(filepath,'w') as f:
            f.write(str(response.content))
        f.close()
        return {
                    'exist': True,
                    'url': base_url + pmcid,
                    'status': response.status_code,
                    'message': f"Done"
                }
    except Exception as e:
        return {
            'exist': False,
            'url': base_url + pmcid,
            'status': response.status_code,
            'message': f"Error: {str(e)}"
        }

# download a full article from a DOI
#folder is the output folder
def download_one_fullarticle_doi(doi_url="", folder=""):
    if os.path.exists(folder)==False:
        return {
            'exist': False,
            'url': f'{doi_url}',
            'status': f'failed to open folder',
            'message': f"Error: {folder} does not exist"
        }
    if len(doi_url)==0:
        return {
            'exist': False,
            'url': f'{doi_url}',
            'status': f'failed to open the doi',
            'message': f"Error: doi is empty"
        }

    # Set up headers to mimic a browser on macos
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
    }
    
    # Follow redirects manually with a delay
    try:
        # First request to get the redirect URL
        response = requests.get(doi_url, headers=headers, allow_redirects=False)
        
        if response.status_code in (301, 302, 303, 307, 308):
            redirect_url = response.headers['Location']
            print(f"Redirected to: {redirect_url}")
            
            # Second request to the actual article page
            final_response = requests.get(redirect_url, headers=headers)
            
            if final_response.status_code == 200:
                # Save the HTML to a file
                doi_file_path=os.path.join(folder,f"{doi_url[8:].replace('/',"_")}.html")
                with open(doi_file_path, 'w', encoding='utf-8') as f:
                    f.write(final_response.text)

                return {
                    'exist': True,
                    'url': redirect_url,
                    'status': final_response.status_code,
                    'message': f"Done"
                }
            else:
                return {
                    'exist': False,
                    'url': redirect_url,
                    'status': final_response.status_code,
                    'message': f"Failed to access the article page. Status code: {final_response.status_code}"
                }
        else:
            return {
                'exist': False,
                'url': "no redirect_url",
                'status': response.status_code,
                'message': f"Failed to get redirect. Status code: {response.status_code}"
            }
            
    except Exception as e:
        return {
            'exist': False,
            'url': "no redirect_url",
            'status': response.status_code,
            'message': f"Error: {str(e)}"
        }
    
# main
if __name__ == "__main__":
    os.makedirs(save_path, exist_ok=True)
    #pmids = search_pubmed_v0(query, total=200000, batchsize=5000)
    pmidset, dateset=retrieve(query=query,from_date=date_start,to_date=date_end,period=period_days)
    articles=fetch_pubmed_all(pmidset, dateset)
    article_filepath=os.path.join(save_path,output_filename)
    df_article=pd.DataFrame(articles)
    art_idx=df_article['abstract']!='-1'
    df_article=df_article[art_idx]
    df_article.drop_duplicates(subset=['pmid'], keep='first', inplace=True)
    df_article.to_csv(article_filepath)
    print("====>article number:{}".format(len(articles)))
    if noncontent==True:
        print("====>Done")
        sys.exit()
    else:
        keyword_path=os.path.join(save_path,'retrieval_keywords.html')
        save_retrieval_keywords(keywords=query,filepath=keyword_path)
        resultlist=[]
        for i,article in enumerate(articles):
            print("====> the current: {}/{}, title:{}".format(i+1,len(articles),article['title']))
            print(f"PMID: {article['pmid']}, PMC ID: {article['pmc_id']}, DOI: {article['doi']}")

            if article["pmc_id"]:
                re=download_one_fullarticle_pmc(article["pmc_id"],save_path)
                re['title']=str(article['title'])
                resultlist.append(re)
            elif article["doi"]:
                base_doi="https://doi.org/"
                re=download_one_fullarticle_doi(base_doi+article["doi"],save_path)
                re['title']=str(article['title'])
                resultlist.append(re)
            else:
                re={
                'exist': False,
                'url': "paper link",
                'status': "exception",
                'message': f"Error: neither pmc nor doi exist",
                'title':str(article['title'])
                }
                resultlist.append(re)
        
        df=pd.DataFrame(resultlist)
        errorfile=os.path.join(save_path,"pubmed_article_download_report.csv")
        df.to_csv(errorfile)
        print("==== Done ====")
