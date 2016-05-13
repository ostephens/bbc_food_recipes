import scraperwiki
import lxml.html
import microdata
import urllib
from urlparse import urljoin
import time

def scrape_recipe(recipe_url) :
    if recipe_exists(recipe_url):
        #print "Not Scraping " + recipe_url + ", already exists"
        return True
    else:
        #print "Scraping recipe microdata: " + recipe_url
        items = microdata.get_items(urllib.urlopen(recipe_url))
        for item in items:
            print "Scraping: " + item.name + "from" + recipe_url
            recipe_model = { "url" : recipe_url, "name" : item.name, "recipe" : item.json() }
            scraperwiki.sqlite.save(unique_keys=["url"], table_name="recipes", data=recipe_model)
        return True

def recipe_exists (url):
    count = 0
    result = scraperwiki.sqlite.execute("select count(*) from recipes where url = ?", (url))
    count = int(result["data"][0][0])  
    return count > 0

def tracker_exists(url):
    count = 0
    result = scraperwiki.sqlite.execute("select count(*) from tracker where url = ?", (url))
    count = int(result["data"][0][0])  
    return count > 0

def get_urlist_az(path,selector) :
    print "Scraping a-z for URLs"
    #For a-z - 97, 122
    for i in range(97, 122):
        page = "http://www.bbc.co.uk/food/"+path+"/by/letters/" + chr(i)
        html = scraperwiki.scrape(page)
        root = lxml.html.fromstring(html)
        items = root.cssselect(selector)
        for item in items:
            recipes_link = item.cssselect("a")[0]
            item_name = recipes_link.text_content()
            recipes_url_relative = recipes_link.attrib.get('href')
            recipes_url = urljoin(page, recipes_url_relative)
            #maybe take out the time in the line below
            #need to save selector as well
            if tracker_exists(recipes_url):
                return True
            else:
                tracker_model = { "url" : recipes_url, "status" : "", "time" : time.time() }
                scraperwiki.sqlite.save(unique_keys=["url"], table_name="tracker", data=tracker_model)

def scrape_by_url(url) :
    recipes_url = url
    print "Starting from: " + recipes_url
    try:
        see_all(recipes_url)
        tracker_model = { "url" : recipes_url, "status" : "SUCCESS", "time" : time.time() }
        scraperwiki.sqlite.save(unique_keys=["url"], table_name="tracker", data=tracker_model)
    except (KeyboardInterrupt, SystemExit):
        exit()
    except:
        tracker_model = { "url" : recipes_url, "status" : "ERROR", "time" : time.time() }
        scraperwiki.sqlite.save(unique_keys=["url"], table_name="tracker", data=tracker_model)


def see_all(url):
    html = scraperwiki.scrape(url)
    root = lxml.html.fromstring(html)
    see_all_link = root.cssselect(".see-all-search")[0].attrib.get('href')
    see_all_url = urljoin(url,see_all_link)
    try:
        results_list(see_all_url)
    except (KeyboardInterrupt, SystemExit):
        exit()
    except:
        tracker_model = { "url" : recipes_url, "status" : "ERROR", "time" : time.time() }
        scraperwiki.sqlite.save(unique_keys=["url"], table_name="tracker", data=tracker_model)

def results_list(url):
    html = scraperwiki.scrape(url)
    root = lxml.html.fromstring(html)
    recipes = root.cssselect("#article-list li")
    for recipe in recipes:
        recipe_link = recipe.cssselect("a")[0]
        recipe_url_relative = recipe_link.attrib.get('href')
        recipe_url = urljoin(url,recipe_url_relative)
        scrape_recipe(recipe_url)
    if(len(root.cssselect(".pagInfo-page-numbers-next.empty"))>0):
        #print "returning..."
        return True
    results_nav = root.cssselect(".see-all-search")
    for prev_next in results_nav:
        if(prev_next.attrib.get('rel')=="next"):
            next_link = prev_next.attrib.get('href')
            next_url = urljoin(url,next_link)
            #print "Going to next page: " + next_url
            time.sleep(0.5)
            results_list(next_url)
            #print "returning..."
            return True
#temporary line to get rid of unwanted table
scraperwiki.sqlite.execute("drop table errors")
#Make sure tables exit
tracker_model = { "url" : "http://test.org","status" : "", "time" : time.time() }
scraperwiki.sqlite.save(unique_keys=["url"], table_name="tracker", data=tracker_model)
scraperwiki.sqlite.execute("delete from tracker where url = \"http://test.org\"")
recipe_model = {"url" : "http://test.org", "name" : "Test Recipe", "recipe" : "test recipe"}
scraperwiki.sqlite.save(unique_keys=["url"], table_name="recipes", data=recipe_model)
scraperwiki.sqlite.execute("delete from recipes where url = \"http://test.org\"")

#scrape a list of seeding URLs - will only update if new
get_urlist_az("chefs",".resource.chef")
get_urlist_az("ingredients",".resource.food")

#scrape all URLs currently listed as errors
urls = scraperwiki.sqlite.execute("select url from tracker where (status is NULL OR status = 'ERROR' or status = '') ORDER BY time")
for url in urls['data']:
    scrape_by_url(url[0])

#scrape URLs that haven't been updated in a week
urls = scraperwiki.sqlite.execute("select url from tracker where status = 'SUCCESS' and time < ?",time.time()-604800.0)
for url in urls['data']:
    scrape_by_url(url[0])