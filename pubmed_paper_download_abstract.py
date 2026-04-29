from Bio import Entrez
from bs4 import BeautifulSoup
import requests
import os
import time
import pandas as pd

Entrez.email = "cao.weiguo@mayo.edu"
save_path="/home/m253461/projects/03rdoc/pubmed"
UNPAYWALL_API = "https://api.unpaywall.org/v2/"
SCI_HUB_URL = "https://sci-hub.se/"

# retrieve PubMed with PMID
def search_pubmed(query, retmax=500):
    handle = Entrez.esearch(db="pubmed", term=query, retmax=retmax)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]  

# get the abstract and pmc id
def fetch_pubmed_details(pmids):
    ids = ",".join(pmids)
    handle = Entrez.efetch(db="pubmed", id=ids, rettype="xml", retmode="text")
    records = Entrez.read(handle)
    handle.close()
    articles = []

    for i, article in enumerate(records["PubmedArticle"]):
        print("====> the current id is {}/{}".format(i+1,len(records["PubmedArticle"])))
        pmid = article["MedlineCitation"]["PMID"]
        title = article["MedlineCitation"]["Article"]["ArticleTitle"]
        abstract = article["MedlineCitation"]["Article"].get("Abstract", {}).get("AbstractText", [""])[0]
        pmc_id = None
        doi = None

        

        # look for pmc id and doi
        for article_id in article["PubmedData"]["ArticleIdList"]:
            if article_id.attributes.get("IdType") == "pmc":
                pmc_id = article_id
            elif article_id.attributes.get("IdType") == "doi":
                doi = article_id
        
        articles.append({"pmid": str(pmid), "title": str(title), "abstract": str(abstract), "pmc_id": str(pmc_id), "doi": str(doi)})
    return articles

# get the full paper via pmc id
def download_pmc_fulltext(pmc_id, save_path="full_texts"):
    url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
    response = requests.get(url)

    if response.status_code == 200:
        os.makedirs(save_path, exist_ok=True)
        filepath = os.path.join(save_path, f"{pmc_id}.pdf")
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {pmc_id}")
    else:
        print(f"❌ Failed to download: {pmc_id}")
        return False
    return True

'''
# get the full paper via doi 
def download_from_doi(doi):
    sci_hub_url = f"https://sci-hub.se/{doi}"
    print(f"Check Sci-Hub for: {sci_hub_url}")
'''
# get the full paper via doi
def download_from_doi(doi, save_dir):
    sci_hub_url=f"{SCI_HUB_URL}{doi}"
    response = requests.get(sci_hub_url)
    soup = BeautifulSoup(response.content, "html.parser")

    unpaywall_url=f"{UNPAYWALL_API}{doi}?email=cao.weiguo@mayo.edu"
    
    # Find PDF link
    pdf_link = None
    for iframe in soup.find_all("iframe"):
        if "pdf" in iframe["src"]:
            pdf_link = iframe["src"]
            break
    #download from sci-hub
    if not pdf_link:
        response = requests.get(unpaywall_url).json()
        resp=response.get("best_oa_location", {})
        if resp is None:
            print(f"❌ No Open Access PDF found for {doi}")
            return False
        pdf_url = response.get("best_oa_location", {}).get("url_for_pdf")

        if not pdf_url:
            print(f"❌ No Open Access PDF found for {doi}")
            return False
        # Download the PDF
        pdf_response = requests.get(pdf_link)
        if pdf_response.status_code == 200:
            filename = os.path.join(save_dir, f"{doi.replace('/', '_')}.pdf")
            with open(filename, "wb") as f:
                f.write(pdf_response.content)
            print(f"✅ Downloaded: {filename}")
            return True
        else:
            print(f"❌ cannot download PDF for {doi}")
            return False

    #download from unpaywall
    # Download and save the PDF
    pdf_response = requests.get(pdf_url)
    if pdf_response.status_code == 200:
        filename = os.path.join(save_dir, f"{doi.replace('/', '_')}.pdf")
        with open(filename, "wb") as f:
            f.write(pdf_response.content)
        print(f"✅ Downloaded: {filename}")
        return True
    else:
        print(f"❌ cannot download PDF for {doi}")
        return False

# main
if __name__ == "__main__":
    os.makedirs(save_path, exist_ok=True)
    query = f"((Sleep-Wake Disorders[Title/Abstract]) OR (Sleep disorders[Title/Abstract]) OR (Dyssomnias[Title/Abstract]) OR (Parasomnias[Title/Abstract]) OR (Sleep disturbance[Title/Abstract]) OR (Sleep Deprivation[Title/Abstract]) OR (Sleep fragmentation[Title/Abstract]) OR (Insomnia[Title/Abstract]) OR (Fatal Familial Insomnia[Title/Abstract]) OR (Organic insomnia[Title/Abstract]) OR (Hypersomnia[Title/Abstract]) OR (Hypersomnolence Disorder[Title/Abstract]) OR (Disorders of Excessive Somnolence[Title/Abstract]) OR (Idiopathic Hypersomnia[Title/Abstract]) OR (Kleine-Levin Syndrome[Title/Abstract]) OR (Excessive daytime sleepiness[Title/Abstract]) OR (Organic hypersomnia[Title/Abstract]) OR (Sleep apnea[Title/Abstract]) OR (Sleep Apnea Syndromes[Title/Abstract]) OR (Central Sleep Apnea[Title/Abstract]) OR (Obstructive Sleep Apnea[Title/Abstract]) OR (Obstructive Sleep Apnea Hypopnea[Title/Abstract]) OR (Sleep-Related Hypoventilation[Title/Abstract]) OR (Obesity Hypoventilation Syndrome[Title/Abstract]) OR (Organic sleep apnea[Title/Abstract]) OR (Circadian Rhythm Sleep-Wake Disorders[Title/Abstract]) OR (Jet Lag Syndrome[Title/Abstract]) OR (Sleep Disorders[Title/Abstract]) OR (Circadian Rhythm[Title/Abstract]) OR (REM Sleep Behavior Disorder[Title/Abstract]) OR (Rapid Eye Movement (REM) Sleep Behavior Disorder[Title/Abstract]) OR (REM Sleep Parasomnias[Title/Abstract]) OR (Non-Rapid Eye Movement (NREM) Sleep Arousal Disorders[Title/Abstract]) OR (Sleep Arousal Disorders[Title/Abstract]) OR (Night terrors[Title/Abstract]) OR (Somnambulism[Title/Abstract]) OR (Nightmare Disorder[Title/Abstract]) OR (Sleep Paralysis[Title/Abstract]) OR (Nocturnal Paroxysmal Dystonia[Title/Abstract]) OR (Sleep Bruxism[Title/Abstract]) OR (Restless Legs Syndrome[Title/Abstract]) OR (Periodic Limb Movement Disorder[Title/Abstract]) OR (Nocturnal Myoclonus Syndrome[Title/Abstract]) OR (Sleep-related movement disorders[Title/Abstract]) OR (Narcolepsy[Title/Abstract]) OR (Disorder of sleep of non-organic origin[Title/Abstract]) OR (Cataplexy[Title/Abstract]) OR (Sleep Initiation and Maintenance Disorders[Title/Abstract]) OR (Sleep-Wake Transition Disorders[Title/Abstract]) OR (High-altitude periodic breathing[Title/Abstract])) AND ((\"2024/07/01\"[Date - Publication] : \"2024/12/31\"[Date - Publication]))"
    pmids = search_pubmed(query, retmax=50000)
    articles = fetch_pubmed_details(pmids)
    '''
    errorlist=[]
    for i,article in enumerate(articles):
        print("====> the current: {}/{}, title:{}".format(i,len(articles),article['title']))
        print(f"PMID: {article['pmid']}, PMC ID: {article['pmc_id']}, DOI: {article['doi']}")

        if article["pmc_id"]:
            re=download_pmc_fulltext(article["pmc_id"],save_path)
            if re==False:
                errorlist.append(str(article["pmc_id"]))
        elif article["doi"]:
            re=download_from_doi(article["doi"],save_path)
            if re==False:
                errorlist.append(str(article['doi']))
        else:
            errorlist.append("neither pmc_id nor doi")
        time.sleep(1)
    '''
    df=pd.DataFrame(articles)
    pubmedfile=os.path.join(save_path,"pubmed_abstract_title.csv")
    df.to_csv(pubmedfile)
    print("==== Done ====")