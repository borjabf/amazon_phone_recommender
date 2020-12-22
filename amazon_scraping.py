from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
import time 
import random
from selenium.common.exceptions import NoSuchElementException
from pymongo import MongoClient 
import spacy

client = MongoClient("URI_MONGODB")
db = client["Amazon"]
ProductCollection = db["Productos"] 

negativo=pd.read_csv('negativo.csv')
positivo=pd.read_csv('positivo.csv')
negativo.columns=["lexico"]
positivo.columns=["lexico"]

nlp = spacy.load("es_core_news_lg")


def cleanText(text):
    doc = nlp(text)
    clean = list()
    for i in doc:
        if i.is_stop == False and i.is_punct == False:
            if i.lemma_ == i.text:
                clean.append(i.lower_)
            else:
                clean.append(i.lemma_)
    return ' '.join(clean)



driver = webdriver.Chrome(path + '/chromedriver')
                          
driver.implicitly_wait(3)

url = "https://www.amazon.es/s?bbn=599370031&rh=n%3A17425698031&brr=1&rd=1&ref=Oct_s9_apbd_odnav_hd_bw_bj2KsR_1"
driver.get(url)

tiempo=random.randint(2, 10)
contador_1=0
while contador_1<20:  
    time.sleep(1)
    try:
        cookies = driver.find_element_by_xpath("//span[@class='a-declarative']")
        cookies_1 = cookies.find_element_by_id('sp-cc-accept').click()
    except NoSuchElementException:
        pass

    page = driver.page_source
    soup = BeautifulSoup(page, 'html.parser')
    names_list = [name.text.strip() for name in soup.find_all('span', class_='a-size-medium a-color-base a-text-normal')]
    name_in_mongo = [product['Nombre'] for product in list(ProductCollection.aggregate([{'$project': {'Nombre':1}}]))]
    name_not_in_mongo=[]
    for name in names_list:
        if name not in name_in_mongo:
            name_not_in_mongo.append(name)
    
    if name_not_in_mongo:
        for name in name_not_in_mongo:
            try:
                cookies = driver.find_element_by_xpath("//span[@class='a-declarative']")
                cookies_1 = cookies.find_element_by_id('sp-cc-accept').click()
            except NoSuchElementException:
                pass
            # click new product
            time.sleep(tiempo)
            try:
                driver.find_element_by_link_text(name.replace('\xa0', ' ')).click()   
                time.sleep(tiempo)
                page = driver.page_source
                soup = BeautifulSoup(page, 'html.parser')   
            except NoSuchElementException:
                continue                                                                                                                                                    
            # Name
            nombre=soup.find("span", {"id":"productTitle"})
            if nombre:
                nombre=nombre.get_text().strip()
            time.sleep(tiempo)
            
            # Brand
            brand_list = []
            for info in soup.find_all('table', id='productDetails_techSpec_section_1'):
                for brand in info.find_all('td', class_='a-size-base'):
                    brand_list.append(brand.text)
            if brand_list:
                brand = brand_list[0].strip()
            else:
                brand = None
                    
            # Price 
            precio1=soup.find("span", { "id" : "price_inside_buybox" })
            precio2=soup.find("span", { "id" : "newBuyBoxPrice" })
            if precio1:
                if '.' not in precio1.get_text():
                    precio=float(precio1.get_text().strip().replace('€', '').strip().replace(',','.'))
                else:
                    precio=float(precio1.get_text().strip().replace('€', '').strip().replace('.','').replace(',','.'))
            elif precio2:
                if '.' not in precio2.get_text():
                    precio=float(precio2.get_text().strip().replace('€', '').strip().replace(',','.'))
                else:
                    precio=float(precio1.get_text().strip().replace('€', '').strip().replace('.','').replace(',','.'))
            else: 
                precio=None
            time.sleep(tiempo)
            
            # Review mean score
            rsn=soup.find("span", { "data-hook" : "rating-out-of-text"})
            if rsn:
                rsn_string = rsn.get_text().strip()
                if len(rsn_string)==6:
                    review_mean=float(rsn_string[0])
                else: 
                    review_mean=float(rsn_string[0:3].replace(',','.'))  
            else:
                review_mean = None
                
            
            # URL
            url_actual=driver.current_url
            
            # Review text
            reviews={}
            identificador_2=0
            try:
                driver.find_element_by_link_text('Ver todas las reseñas').click()
                time.sleep(tiempo)
                page = driver.page_source
                soup = BeautifulSoup(page, 'html.parser')
                
                for review in soup.find_all('span', {'data-hook': 'review-body'}):
                    if review:
                        reviews[str(identificador_2)]=review.span.text.strip()
                        identificador_2+=1
                driver.back()  
                    
            except NoSuchElementException:
                pass
                
            # MongoDB insert
            ProductCollection.insert_one({"Nombre":nombre,"Marca":brand,"Precio":precio,"media":review_mean,"url":url_actual,"reviews_txt":reviews})
            producto=list(ProductCollection.find({"Nombre":nombre}))[0]
            reviews=producto["reviews_txt"]
            if reviews:
                for review in nlp.pipe(reviews.values()):
                    clean_review = nlp(cleanText(review.text))
                    sentence_tokens = []
                    sentence_tokens.append([token.text for token in clean_review])
                    polaridades=[]
                    for word in sentence_tokens[0]:
                        if word in negativo["lexico"].values:
                            polaridades.append(-1)
                        elif word in positivo["lexico"].values:
                            polaridades.append(1)
                    suma=0
                    for element in polaridades:
                        suma+=element
                    if suma != 0:
                        media=suma/len(polaridades)
                ProductCollection.update({"Nombre":nombre},{"$set":{"Media_sentimiento":media}})
            producto=list(ProductCollection.find({"Nombre":nombre}))[0]
            try:
                if producto["Media_sentimiento"]>0:
                    nombre_producto=producto["Nombre"]
                    ProductCollection.update({"Nombre":nombre_producto},{"$set":{"Sentimiento":"Positivo"}})
                else:
                    nombre_producto=producto["Nombre"]
                    ProductCollection.update({"Nombre":nombre_producto},{"$set":{"Sentimiento":"Negativo"}})
            except KeyError:
                pass
            producto=list(ProductCollection.find({"Nombre":nombre}))[0]
            try:
                if producto['media'] and producto['Media_sentimiento']:
                    score = producto['media'] * producto['Media_sentimiento']
                    nombre_producto=producto["Nombre"]
                    ProductCollection.update({'Nombre':nombre_producto}, {'$set':{'Score':score}})
            except KeyError:
                pass   
            
            driver.back()
    
    time.sleep(1)
    try:
        cookies = driver.find_element_by_xpath("//span[@class='a-declarative']")
        cookies_1 = cookies.find_element_by_id('sp-cc-accept').click()
    except NoSuchElementException:
        pass
    contador_1+=1
    nextPage = driver.find_element_by_partial_link_text('Siguiente')
    nextPage.click()