# Importing the libraries
from flask import Flask, render_template, url_for, request, flash, redirect
import pandas as pd
import requests
from bs4 import BeautifulSoup as soup
from urllib.request import urlopen 
import re
import pymongo

app = Flask(__name__)

app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

@app.route("/")
def home():
    return render_template("Home.html")

@app.route("/sentiment")
def sentiment():
    return render_template("sentiment.html")

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/scrap", methods=["POST", "GET"])
def scrap():
    search = request.form.get("searchstring")
    
    # Opening the page after search and storing it 
    flipkart_url = "https://www.flipkart.com/search?q=" + str(search)
    uClient = urlopen(flipkart_url)
    flipkartPage = uClient.read()
    uClient.close()
    flipkart_html = soup(flipkartPage, "html.parser")
    
    # Getting all the div which have the listings of all the products and their links
    container = flipkart_html.find_all('div', {'class':"_2kHMtA"})
    
    # Getting list of all the links of product pages in the container
    product_links = []
    for li in container:
        links = li.a["href"]
        product_links.append(links)
    
    # Scrapping the data (Product name, user name, rating, review heading, review) from each page
    #data = []
    for i in range(len(product_links)):
        data_dict = {
            "Product_name":[],
            "Product_ratings":[],
            "Product_headings":[],
            "Product_reviews":[]
        }

        # this will open and read each product page
        product_url = "https://www.flipkart.com" + product_links[i]
        uClient_product = urlopen(product_url)
        productPage = uClient_product.read()
        uClient_product.close()
        product_html = soup(productPage, "html.parser")
        
        # scraping the name of the product
        tempproduct_name = product_html.find_all('span', {"class":"B_NuCI"})
        data_dict["Product_name"].append(tempproduct_name[0].text)
        
        # Getting the link of all reviews page of the product
        review_page_link = [li.get('href') for li in product_html.find_all('a', attrs={'href' : re.compile("/product-reviews/")})]
            
        # this will be our link for the all reviews page
        recent_ReviewPage = review_page_link[-1].replace("marketplace=FLIPKART", "aid=overall&certifiedBuyer=false&sortOrder=MOST_RECENT")
        
        # Opening the reviews page
        review_page = "https://www.flipkart.com" + recent_ReviewPage
        uClient_review = urlopen(review_page)
        ReviewPage = uClient_review.read()
        uClient_review.close()
        ReviewPage_html = soup(ReviewPage, "html.parser")
        
        # Getting the link of first 10 review pages
        review_10pages = [rev.get("href") for rev in ReviewPage_html.find_all("a", {'class':'ge-49M'})]
        
        # Scrapping ratings, review headings and reviews of all 10 pages
        for rat in review_10pages:
            review_page_10 = "https://www.flipkart.com" + rat
            uClient_review10 = urlopen(review_page_10)
            ReviewPage_10 = uClient_review10.read()
            uClient_review10.close()
        
            ReviewPage10_html = soup(ReviewPage_10, "html.parser")
        
            # Extracting ratings
            Page_ratings = ReviewPage10_html.find_all('div', {'class': "_3LWZlK"})
            Ratings = []
            for i in Page_ratings:
                temp_Ratings = i.text
                if "." in temp_Ratings:
                    pass
                else:
                    Ratings.append(temp_Ratings)
            data_dict["Product_ratings"].append(Ratings)

            # Extracting Review Headings
            temp_headings = ReviewPage10_html.find_all('p', {'class': "_2-N8zT"})
            Headings = []
            for i in temp_headings:
                for j in i:
                    temp_Headings = j.text
                    Headings.append(temp_Headings)
            data_dict["Product_headings"].append(Headings)

            # Extracting Reviews
            temp_reviews = ReviewPage10_html.find_all('div', {'class': "t-ZTKy"})
            Reviews = []
            for i in temp_reviews:
                for j in i:
                    t_Reviews = j.text
                    t_Reviews = t_Reviews[:-9]
                    Reviews.append(t_Reviews)
            data_dict["Product_reviews"].append(Reviews)
        
        # MONGO DB (Uploading of the data)
        client = pymongo.MongoClient("mongodb://localhost:27017")

        data = client["Reviews"]
        collection = data[str(search)]

        collection.insert_one(data_dict)
    
    # flash("Extraction Done")
    return redirect("results")

@app.route("/results", methods=['GET'])
def results():
    client = pymongo.MongoClient("mongodb://localhost:27017")

    data = client["Reviews"]
    collection = data['iphone']
    df = collection.find() #pd.DataFrame(list(collection.find()))
    #df = pd.DataFrame()
    '''for dt in collection.find():
        
        df.append(mo_data, ignore_index=True)'''
    #df = pd.dataFrame({"name":[1,2,3,4],"class":["sameer","aman","priyanshu","riddhi"]})
    return render_template('results.html',  tables=df)#[df.to_html(classes='data')]) #, titles=df.columns.values


if __name__ == "__main__":
    app.run(debug=False)

