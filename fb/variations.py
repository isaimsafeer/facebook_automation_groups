import time
import random
import pyautogui  # For controlling the system cursor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def initialize_driver():
    # Configure Chrome options
    options = Options()
    options.add_argument("--disable-notifications")  # Disable notifications
    options.add_argument("--start-maximized")       # Start browser maximized
    
    # Initialize WebDriver
    driver = webdriver.Chrome(options=options)
    return driver

def random_scrolling(driver):

    # Randomly set the duration between 10 and 30 seconds
    lower_bound = random.randint(1, 10)  # Random lower bound
    upper_bound = random.randint(20, 50)  # Random upper bound, ensuring upper > lower

    # Ensure that the lower bound is less than the upper bound
    if lower_bound >= upper_bound:
        lower_bound, upper_bound = upper_bound, lower_bound

    # duration = random.randint(10,30)
    # Generate a random duration within the randomized range
    duration = random.randint(lower_bound, upper_bound)
    print(f"Scrolling for {duration} seconds")

    end_time = time.time() + duration  # Calculate end time
    actions = ActionChains(driver)
    
    while time.time() < end_time:
        # Randomly decide to scroll up or down
        direction = random.choice(['up', 'down'])
        # Generate a random scroll distance
        scroll_distance = random.randint(200, 800)
        
        if direction == 'down':
            actions.scroll_by_amount(0, scroll_distance).perform()
        else:  # Scroll up
            actions.scroll_by_amount(0, -scroll_distance).perform()
        
        # Wait for a random time before the next scroll
        time.sleep(random.uniform(0.5, 2))

def random_cursor_movement():

    # Randomly set the duration between 10 and 30 seconds
    lower_bound = random.randint(1, 10)  # Random lower bound
    upper_bound = random.randint(20, 50)  # Random upper bound, ensuring upper > lower

    # Ensure that the lower bound is less than the upper bound
    if lower_bound >= upper_bound:
        lower_bound, upper_bound = upper_bound, lower_bound

    # duration = random.randint(10,30)
    # Generate a random duration within the randomized range
    duration = random.randint(lower_bound, upper_bound)
    print(f"Cursor movement duration: {duration} seconds")

    screen_width, screen_height = pyautogui.size()  # Get screen resolution
    end_time = time.time() + duration  # Calculate end time

    while time.time() < end_time:
        # Generate random coordinates within the screen
        x = random.randint(0, screen_width)
        y = random.randint(0, screen_height)
        
        # Move the cursor to the random position
        pyautogui.moveTo(x, y, duration=random.uniform(0.1, 0.5))  # Smooth movement
        
        # Wait for a random time before the next movement
        time.sleep(random.uniform(0.5, 1.5))

def open_new_tab(driver):
    # List of 10 websites
    websites = [
        "https://www.w3schools.com/",
        "https://www.python.org/",
        "https://www.youtube.com/",
        "https://www.wikipedia.org/",
        "https://www.github.com/",
        "https://www.stackoverflow.com/",
        "https://www.reddit.com/",
        "https://www.medium.com/",
        "https://www.mozilla.org/",
        "https://www.bing.com/",
        "https://www.cnn.com",
        "https://www.nytimes.com",
        "https://www.pinterest.com",
        "https://www.quora.com",
        "https://www.foxnews.com",
        "https://www.imdb.com",
        "https://www.khanacademy.org",
        "https://www.ebay.com",
        "https://www.tumblr.com",
        "https://www.nike.com",
        "https://www.spotify.com",
        "https://www.udemy.com",
        "https://www.stackexchange.com",
        "https://www.behance.net",
        "https://www.squarespace.com",
        "https://www.dropbox.com",
        "https://www.weather.com",
        "https://www.amazon.com",
        "https://www.huffpost.com",
        "https://www.flickr.com",
        "https://www.linkedin.com",
        "https://www.instagram.com",
        "https://www.facebook.com",
        "https://www.twitter.com",
        "https://www.ted.com",
        "https://www.coursera.org",
        "https://www.edx.org",
        "https://www.netflix.com",
        "https://www.airbnb.com",
        "https://www.booking.com",
        "https://www.tripadvisor.com",
        "https://www.paypal.com",
        "https://www.slack.com",
        "https://www.trello.com",
        "https://www.zoom.us",
        "https://www.skype.com",
        "https://www.whatsapp.com",
        "https://www.telegram.org",
        "https://www.discord.com",
        "https://www.microsoft.com",
        "https://www.apple.com",
        "https://www.adobe.com",
        "https://www.canva.com",
        "https://www.dribbble.com",
        "https://www.deviantart.com",
        "https://www.soundcloud.com",
        "https://www.vimeo.com",
        "https://www.dailymotion.com",
        "https://www.twitch.tv",
        "https://www.reuters.com",
        "https://www.bbc.com",
        "https://www.forbes.com",
        "https://www.bloomberg.com",
        "https://www.wsj.com",
        "https://www.nationalgeographic.com",
        "https://www.sciencedaily.com",
        "https://www.nature.com",
        "https://www.acm.org",
        "https://www.ieee.org",
        "https://www.springer.com",
        "https://www.jstor.org",
        "https://www.arxiv.org",
        "https://www.github.io",
        "https://www.gitlab.com",
        "https://www.bitbucket.org",
        "https://www.heroku.com",
        "https://www.digitalocean.com",
        "https://www.linode.com",
        "https://www.aws.amazon.com",
        "https://www.azure.microsoft.com",
        "https://www.cloud.google.com",
        "https://www.oracle.com",
        "https://www.ibm.com",
        "https://www.salesforce.com",
        "https://www.shopify.com",
        "https://www.etsy.com",
        "https://www.alibaba.com",
        "https://www.target.com",
        "https://www.walmart.com",
        "https://www.bestbuy.com",
        "https://www.homedepot.com",
        "https://www.lowes.com",
        "https://www.costco.com",
        "https://www.ikea.com",
        "https://www.zara.com",
        "https://www.hm.com",
        "https://www.forever21.com",
        "https://www.gap.com",
        "https://www.uniqlo.com",
        "https://www.macys.com",
        "https://www.nordstrom.com",
        "https://www.sephora.com",
        "https://www.ulta.com",
        "https://www.wayfair.com",
        "https://www.overstock.com",
        "https://www.ebay.co.uk",
        "https://www.craigslist.org",
        "https://www.indeed.com",
        "https://www.glassdoor.com",
        "https://www.monster.com",
        "https://www.linkedin.com/jobs",
        "https://www.upwork.com",
        "https://www.fiverr.com",
        "https://www.freelancer.com",
        "https://www.peopleperhour.com",
        "https://www.guru.com",
        "https://www.99designs.com",
        "https://www.topcoder.com",
        "https://www.hackerrank.com",
        "https://www.codewars.com",
        "https://www.leetcode.com",
        "https://www.codechef.com",
        "https://www.spoj.com",
        "https://www.hackerearth.com",
        "https://www.kaggle.com",
        "https://www.datacamp.com",
        "https://www.codecademy.com",
        "https://www.freecodecamp.org",
        "https://www.pluralsight.com",
        "https://www.lynda.com",
        "https://www.skillshare.com",
        "https://www.masterclass.com",
        "https://www.domestika.org",
        "https://www.creativelive.com",
        "https://www.udacity.com",
        "https://www.futurelearn.com",
        "https://www.open.edu",
        "https://www.saylor.org",
        "https://www.alison.com",
        "https://www.classcentral.com",
        "https://www.mooc.org",
        "https://www.openculture.com",
        "https://www.edureka.co",
        "https://www.simplilearn.com",
        "https://www.coursera.com",
        "https://www.edx.com",
        "https://www.udemy.com",
        "https://www.khanacademy.com",
        "https://www.academia.edu",
        "https://www.researchgate.net",
        "https://www.jstor.org",
        "https://www.springer.com",
        "https://www.sciencedirect.com",
        "https://www.nature.com",
        "https://www.cell.com",
        "https://www.thelancet.com",
        "https://www.bmj.com",
        "https://www.nejm.org",
        "https://www.sciencemag.org",
        "https://www.pnas.org",
        "https://www.jamanetwork.com",
        "https://www.plos.org",
        "https://www.frontiersin.org",
        "https://www.mdpi.com",
        "https://www.hindawi.com"
    ]
    
    # Pick a random website from the list
    website = random.choice(websites)
    
    # Open a new tab
    driver.execute_script("window.open('"+ website + "','_blank')")
    
    # Wait for the new tab to open
    time.sleep(1)

    # Switch to the new tab (the last one)
    driver.switch_to.window(driver.window_handles[-1])

    # Wait a little after typing
    time.sleep(2)

    # Close the current tab
    driver.close()

    # Switch back to the original tab
    driver.switch_to.window(driver.window_handles[-1])

    
def do_nothing():
    pass


def open_new_window(driver_main):
    try:
        websites = [
            "https://www.w3schools.com/",
            "https://www.python.org/",
            "https://www.youtube.com/",
            "https://www.wikipedia.org/",
            "https://www.github.com/",
            "https://www.stackoverflow.com/",
            "https://www.reddit.com/",
            "https://www.medium.com/",
            "https://www.mozilla.org/",
            "https://www.bing.com/",
            "https://www.cnn.com",
            "https://www.nytimes.com",
            "https://www.pinterest.com",
            "https://www.quora.com",
            "https://www.foxnews.com",
            "https://www.imdb.com",
            "https://www.khanacademy.org",
            "https://www.ebay.com",
            "https://www.tumblr.com",
            "https://www.nike.com",
            "https://www.spotify.com",
            "https://www.udemy.com",
            "https://www.stackexchange.com",
            "https://www.behance.net",
            "https://www.squarespace.com",
            "https://www.dropbox.com",
            "https://www.weather.com",
            "https://www.amazon.com",
            "https://www.huffpost.com",
            "https://www.flickr.com",
            "https://www.linkedin.com",
            "https://www.instagram.com",
            "https://www.facebook.com",
            "https://www.twitter.com",
            "https://www.ted.com",
            "https://www.coursera.org",
            "https://www.edx.org",
            "https://www.netflix.com",
            "https://www.airbnb.com",
            "https://www.booking.com",
            "https://www.tripadvisor.com",
            "https://www.paypal.com",
            "https://www.slack.com",
            "https://www.trello.com",
            "https://www.zoom.us",
            "https://www.skype.com",
            "https://www.whatsapp.com",
            "https://www.telegram.org",
            "https://www.discord.com",
            "https://www.microsoft.com",
            "https://www.apple.com",
            "https://www.adobe.com",
            "https://www.canva.com",
            "https://www.dribbble.com",
            "https://www.deviantart.com",
            "https://www.soundcloud.com",
            "https://www.vimeo.com",
            "https://www.dailymotion.com",
            "https://www.twitch.tv",
            "https://www.reuters.com",
            "https://www.bbc.com",
            "https://www.forbes.com",
            "https://www.bloomberg.com",
            "https://www.wsj.com",
            "https://www.nationalgeographic.com",
            "https://www.sciencedaily.com",
            "https://www.nature.com",
            "https://www.acm.org",
            "https://www.ieee.org",
            "https://www.springer.com",
            "https://www.jstor.org",
            "https://www.arxiv.org",
            "https://www.github.io",
            "https://www.gitlab.com",
            "https://www.bitbucket.org",
            "https://www.heroku.com",
            "https://www.digitalocean.com",
            "https://www.linode.com",
            "https://www.aws.amazon.com",
            "https://www.azure.microsoft.com",
            "https://www.cloud.google.com",
            "https://www.oracle.com",
            "https://www.ibm.com",
            "https://www.salesforce.com",
            "https://www.shopify.com",
            "https://www.etsy.com",
            "https://www.alibaba.com",
            "https://www.target.com",
            "https://www.walmart.com",
            "https://www.bestbuy.com",
            "https://www.homedepot.com",
            "https://www.lowes.com",
            "https://www.costco.com",
            "https://www.ikea.com",
            "https://www.zara.com",
            "https://www.hm.com",
            "https://www.forever21.com",
            "https://www.gap.com",
            "https://www.uniqlo.com",
            "https://www.macys.com",
            "https://www.nordstrom.com",
            "https://www.sephora.com",
            "https://www.ulta.com",
            "https://www.wayfair.com",
            "https://www.overstock.com",
            "https://www.ebay.co.uk",
            "https://www.craigslist.org",
            "https://www.indeed.com",
            "https://www.glassdoor.com",
            "https://www.monster.com",
            "https://www.linkedin.com/jobs",
            "https://www.upwork.com",
            "https://www.fiverr.com",
            "https://www.freelancer.com",
            "https://www.peopleperhour.com",
            "https://www.guru.com",
            "https://www.99designs.com",
            "https://www.topcoder.com",
            "https://www.hackerrank.com",
            "https://www.codewars.com",
            "https://www.leetcode.com",
            "https://www.codechef.com",
            "https://www.spoj.com",
            "https://www.hackerearth.com",
            "https://www.kaggle.com",
            "https://www.datacamp.com",
            "https://www.codecademy.com",
            "https://www.freecodecamp.org",
            "https://www.pluralsight.com",
            "https://www.lynda.com",
            "https://www.skillshare.com",
            "https://www.masterclass.com",
            "https://www.domestika.org",
            "https://www.creativelive.com",
            "https://www.udacity.com",
            "https://www.futurelearn.com",
            "https://www.open.edu",
            "https://www.saylor.org",
            "https://www.alison.com",
            "https://www.classcentral.com",
            "https://www.mooc.org",
            "https://www.openculture.com",
            "https://www.edureka.co",
            "https://www.simplilearn.com",
            "https://www.coursera.com",
            "https://www.edx.com",
            "https://www.udemy.com",
            "https://www.khanacademy.com",
            "https://www.academia.edu",
            "https://www.researchgate.net",
            "https://www.jstor.org",
            "https://www.springer.com",
            "https://www.sciencedirect.com",
            "https://www.nature.com",
            "https://www.cell.com",
            "https://www.thelancet.com",
            "https://www.bmj.com",
            "https://www.nejm.org",
            "https://www.sciencemag.org",
            "https://www.pnas.org",
            "https://www.jamanetwork.com",
            "https://www.plos.org",
            "https://www.frontiersin.org",
            "https://www.mdpi.com",
            "https://www.hindawi.com"
    ]
        driver_main.minimize_window()
        website = random.choice(websites)
        driver = webdriver.Chrome()
        time.sleep(5)
        driver.get(website)
        random_scrolling(driver)
        driver.quit()
        driver_main.maximize_window()
    except Exception as e:
        pass


def open_settings():
    try:
        # Open the Settings app (Win + I)
        pyautogui.hotkey('win', 'i')
        time.sleep(5)  # Wait for the Settings app to open
        random_cursor_movement()
        # Close the Settings app using Alt + F4
        pyautogui.hotkey('alt', 'f4')
    except:
        pass

def random_variation(driver=None):

    # Randomly select between random_scrolling and random_cursor_movement
    choice = random.choice([random_cursor_movement, do_nothing,  open_new_window, open_new_tab])

    if choice == do_nothing:
        do_nothing()
        print("Nothing is called")

    elif choice == open_new_window:
        open_new_window(driver)
        print("New window variation called")

    elif choice == open_settings:
        open_settings()
    else:
        random_cursor_movement()
        print("Random curser movement is called")


