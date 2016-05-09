import scraperwiki
import lxml.html
import microdata
import urllib
from urlparse import urljoin

def process_recipe_list(url, recipes):
    print "process_recipe_list : " + str(len(recipes)) + " recipes found"
    for recipe in recipes :
        recipe_link = recipe.cssselect("a")[0]
        recipe_url_relative = recipe_link.attrib.get('href')
        recipe_url = urljoin(url, recipe_url_relative)
        scrape_recipe(recipe_url)

def scrape_recipe(recipe_url) :
    if not recipe_exists(recipe_url):        
        print "Not Scraping " + recipe_url + ", already exists"
    else:
        print "Scraping recipe microdata: " + recipe_url
        items = microdata.get_items(urllib.urlopen(recipe_url))
        for item in items:
            recipe_model = { "url" : recipe_url, "name" : item.name, "recipe" : item.json() }
            scraperwiki.sqlite.save(unique_keys=["url"], table_name="recipes", data=recipe_model)

def recipe_exists (url):
    print "recipe_exists : " + url
    count = 0
    
    result = scraperwiki.sqlite.execute("select count(*) from recipes where url = ?", (url))
    count = int(result["data"][0][0])  
        #print "result : " + str(result)
        #print "result['data'] : " + str(result["data"])
        #print "result['data'][0] : " + str(result["data"][0])
        #print "result['data'][0][0] : " + str(result["data"][0][0])
        #print "result is list : " + str(type(result) is list)
        #print "result['data'] is list : " + str(type(result["data"]) is list)
        #print "result['data'][0][0] is list : " + str(type(result["data"][0][0]) is list)
        #print "Count : " + str(count)
    return count > 0

def scrape_chefs_az() :
    print "Scraping chefs a-z"
    #For a-z - 97, 122
    for i in range(97, 122):
        page = "http://www.bbc.co.uk/food/chefs/by/letters/" + chr(i)
        html = scraperwiki.scrape(page)
        root = lxml.html.fromstring(html)
        chefs = root.cssselect(".resource.chef")
        for chef in chefs:
            recipes_link = chef.cssselect("a")[0]
            chef_name = recipes_link.text_content()
            recipes_url_relative = recipes_link.attrib.get('href')
            recipes_url = urljoin(page, recipes_url_relative)
            print "Chef: " + recipes_url, chef_name.encode('utf-8').strip()
            chef_model = { "url" : recipes_url, "name" : chef_name }
            
            scraperwiki.sqlite.save(unique_keys=["url"], table_name="chefs", data=chef_model)
            html = scraperwiki.scrape(recipes_url)
            
            root = lxml.html.fromstring(html)
            
            recipes = root.cssselect(".resource-list li")
            
            print str(len(recipes)) + " found"
            process_recipe_list(page, recipes)
                
scraperwiki.sqlite.save(unique_keys=["url"], table_name="recipes", data={"url" : "http://test.org", "name" : "Test Recipe", "recipe" : "test recipe"})
scrape_chefs_az()
