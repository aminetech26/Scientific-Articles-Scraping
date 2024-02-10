import ast
import requests
from googleapiclient.http import MediaIoBaseDownload
import google.generativeai as gemini
import io
import fitz
from date_exractor import *
from manual_scraping import *
import io
from Article import *
from Author import *
import time
import os

class GeminiScrapper:
    def __init__(self):
        self.article = Article()
        
    #SCRAPING MANUEL CONFIG
    text_start_keywords = ["1. Motivation and significance","I. Introduction","1. Introduction","I. Introduction", "Introduction"]
    text_end_keywords = ["REFERENCES","REFERENCES "," REFERENCES", "References","references"," REFERENCES", " References"," references","REFERENCES:", "References:","references:","REFERENCES"]
    reference_start_keywords = ["REFERENCES","REFERENCES", "References","references"," REFERENCES", " References"," references","REFERENCES:", "References:","references:","References "," References"," References ","References",]
    reference_end_keywords = ["Appendix", "APPENDIX"]


    def getArticleFromUrl(self,service,file_name,file_id,url):
       
        self.article.url = url


        #REQUEST CONFIG
        RETRY_ATTEMPTS = 3  
        ATTEMPT = 1
        ALL_SUCCESS = False

        #GEMINI MODEL CONFIG
        gemini.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        generationconfig = {"max_output_tokens": 2048,"temperature": 0.9,"top_p": 1,"top_k": 1}
        model = gemini.GenerativeModel("gemini-pro",generation_config=generationconfig)
        
        #FILE DOWNLOAD

        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(file_name, mode='wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")
        print("Download Complete!")
        if done:
            doc = fitz.open(file_name)
            text = doc[0].get_text()
            #PROMPT CONFIG
            prompts = {
            "title": f"Return the title of this scientific article without any additional text or prefix in the response. Article Text: {text}",
            "authors": f"Return the complete list of full names of the authors of this article as a list separated by commas. Without any prefix or additional text in the response.Article Text:{text}",
            "abstract": f"Please provide the full abstract of the article as it appears in the article without any additional text or prefix in the response.Article Text:{text}",
            "keywords": f"Return the list of keywords of this article as a list separated by commas. Without any prefix or additional text in the response.Article Text:{text}",
            "publication-date": f"Please extract a publication date from the article. If the specific publication date is not clearly indicated, provide either the acceptance date of the article or the date of the conference where the article was presented. If no specific date is clearly indicated, please provide an approximate date based on the content of the article, using a reasonable estimate. Return only the date without any prefix or additional text in the response.Article Text:{text}",
            "institutions": f"Return all institutions to which all authors of this article belong. The response should be in the form of a dictionary with the authors of the article as keys and their respective institutions as values. The response should not contain any additional text or prefix.Article Text:{text}",
            }
            while ATTEMPT <= RETRY_ATTEMPTS:
                    for champ, prompt in prompts.items():

                        response = model.generate_content([prompt])
                        
                        if response.status_code == 200:
                            print(print(f"(response : {response})"))
                            print(f"({champ}):")
                            print(f"Result ({champ}): {response.text}")
                            if champ == "titre":
                                self.article.titre = response.text
                            elif champ == "resume":
                                self.article.resume = response.text
                            elif champ == "mots-cles":
                                self.article.mots_cles = [mot.strip() for mot in response.text.split(',')]
                            elif champ == "date-de-publication":
                                date_str = response.text
                                dateDePublication = extract_date_from_text(date_str)
                                self.article.dateDePublication = dateDePublication
                            elif champ == "institutions":
                                response_text = response.text
                                # Use ast.literal_eval to safely parse the string into a dictionary
                                institutions_dict = ast.literal_eval(response_text)
                                if isinstance(institutions_dict, dict):
                                    for author_name, institution in institutions_dict.items():
                                        print(author_name)
                                        print(institution)
                                        author = Author(nom=author_name.strip(), institution=institution.strip())
                                        self.article.authors.append(author)

                                    print(self.article.authors)                          
                        else:
                            print(f"Attempt {ATTEMPT}/{RETRY_ATTEMPTS} - Retrying after 5 seconds...")
                            ALL_SUCCESS = False  # Une requête a échoué, ne pas mettre à jour le fichier
                            time.sleep(5)
                            break
                    if ALL_SUCCESS:
                        break  
                    else:
                        print(f"Attempt {ATTEMPT}/{RETRY_ATTEMPTS} - Retrying after 5 seconds...")
                        time.sleep(5)
                        ATTEMPT += 1

            text = extract_text_between_markers(doc,self.text_start_keywords,self.text_end_keywords)
            self.article.texteIntegral = text
            references = extract_references(doc,self.reference_start_keywords,self.reference_end_keywords)
            self.article.referencesBibliographiques = references
            return self.article
        else:
            return None