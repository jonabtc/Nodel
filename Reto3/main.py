import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from chromedriver_py import binary_path

user = None
password = None
link = None


def _extract_shares(item):
    post_shares = item.find_all(class_="_4vn1")
    shares = ""
    for postShare in post_shares:

        x = postShare.string
        if x is not None:
            x = x.split(">", 1)
            shares = x
        else:
            shares = "0"
    return shares


def _extract_comments(item):
    post_comments = item.findAll("div", {"class": "_4eek"})
    comments = dict()

    for comment in post_comments:
        if comment.find(class_="_6qw4") is None:
            continue

        commenter = comment.find(class_="_6qw4").text
        comments[commenter] = dict()

        comment_text = comment.find("span", class_="_3l3x")

        if comment_text is not None:
            comments[commenter]["text"] = comment_text.text

        comment_link = comment.find(class_="_ns_")
        if comment_link is not None:
            comments[commenter]["link"] = comment_link.get("href")

        comment_pic = comment.find(class_="_2txe")
        if comment_pic is not None:
            comments[commenter]["image"] = comment_pic.find(class_="img").get("src")

        comment_list = item.find('ul', {'class': '_7791'})
        if comment_list:
            comments = dict()
            comment = comment_list.find_all('li')
            if comment:
                for litag in comment:
                    aria = litag.find("div", {"class": "_4eek"})
                    if aria:
                        commenter = aria.find(class_="_6qw4").text
                        comments[commenter] = dict()
                        comment_text = litag.find("span", class_="_3l3x")
                        if comment_text:
                            comments[commenter]["text"] = comment_text.text
                            # print(str(litag)+"\n")

                        comment_link = litag.find(class_="_ns_")
                        if comment_link is not None:
                            comments[commenter]["link"] = comment_link.get("href")

                        comment_pic = litag.find(class_="_2txe")
                        if comment_pic is not None:
                            comments[commenter]["image"] = comment_pic.find(class_="img").get("src")

                        replies_list = litag.find(class_="_2h2j")
                        if replies_list:
                            reply = replies_list.find_all('li')
                            if reply:
                                comments[commenter]['reply'] = dict()
                                for litag2 in reply:
                                    aria2 = litag2.find("div", {"class": "_4efk"})
                                    if aria2:
                                        replier = aria2.find(class_="_6qw4").text
                                        if replier:
                                            comments[commenter]['reply'][replier] = dict()

                                            reply_text = litag2.find("span", class_="_3l3x")
                                            if reply_text:
                                                comments[commenter]['reply'][replier][
                                                    "reply_text"] = reply_text.text

                                            r_link = litag2.find(class_="_ns_")
                                            if r_link is not None:
                                                comments[commenter]['reply']["link"] = r_link.get("href")

                                            r_pic = litag2.find(class_="_2txe")
                                            if r_pic is not None:
                                                comments[commenter]['reply']["image"] = r_pic.find(
                                                    class_="img").get("src")
    return comments


def _extract_reaction(item):
    toolbar = item.find_all(attrs={"role": "toolbar"})

    if not toolbar:  # pretty fun
        return
    reaction = dict()
    for toolbar_child in toolbar[0].children:
        str = toolbar_child['data-testid']
        reaction = str.split("UFI2TopReactions/tooltip_")[1]

        reaction[reaction] = 0

        for toolbar_child_child in toolbar_child.children:

            num = toolbar_child_child['aria-label'].split()[0]

            # fix weird ',' happening in some reaction values
            num = num.replace(',', '.')

            if 'K' in num:
                number = float(num[:-1]) * 1000
            else:
                number = float(num)

            reaction[reaction] = number
    return reaction


def _extract_html(bs_data):
    # Add to check
    with open('./bs.html', "w", encoding="utf-8") as file:
        file.write(str(bs_data.prettify()))

    k = bs_data.find_all(class_="_5pcr userContentWrapper")
    post_dict = []

    for item in k:
        post_item = dict()
        post_item['shares'] = _extract_shares(item)
        post_item['comments'] = _extract_comments(item)
        post_dict['reaction'] = _extract_reaction(item)

    return post_dict


def _login(browser, email, password):
    browser.get("http://facebook.com")
    browser.maximize_window()
    browser.find_element_by_name("email").send_keys(email)
    browser.find_element_by_name("pass").send_keys(password)
    browser.find_element_by_name('login').click()
    time.sleep(5)


def extract(page):
    option = Options()
    option.add_argument("--disable-infobars")
    option.add_argument("start-maximized")
    option.add_argument("--disable-extensions")

    # Block all notifications
    option.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2
    })

    browser = webdriver.Chrome(executable_path=binary_path, options=option)

    _login(browser, user, password)

    browser.get(page)

    # first uncollapse collapsed comments
    uncollapse_comments_buttons_x_path = '//a[contains(@class,"_666h")]'
    uncollapse_comments_buttons = browser.find_elements_by_xpath(uncollapse_comments_buttons_x_path)
    for uncollapse_comment in uncollapse_comments_buttons:
        action = webdriver.common.action_chains.ActionChains(browser)
        try:
            action.move_to_element_with_offset(uncollapse_comment, 5, 5)
            action.perform()
            uncollapse_comment.click()
        except:
            pass

        rank_dropdowns = browser.find_elements_by_class_name('_2pln')
        rank_x_path = '//div[contains(concat(" ", @class, " "), "uiContextualLayerPositioner") and not(contains(' \
                      'concat(" ", @class, " "), "hidden_elem"))]//div/ul/li/a[@class="_54nc"]/span/span/div[' \
                      '@data-ordering="RANKED_UNFILTERED"] '

        for rank_dropdown in rank_dropdowns:
            action = webdriver.common.action_chains.ActionChains(browser)
            try:
                action.move_to_element_with_offset(rank_dropdown, 5, 5)
                action.perform()
                rank_dropdown.click()
            except:
                pass

            # if modal is opened filter comments
            ranked_unfiltered = browser.find_elements_by_xpath(rank_x_path)  # RANKED_UNFILTERED => (All Comments)
            if len(ranked_unfiltered) > 0:
                try:
                    ranked_unfiltered[0].click()
                except:
                    pass

        more_comments = browser.find_elements_by_xpath('//a[@class="_4sxc _42ft"]')

        while len(more_comments) != 0:
            for moreComment in more_comments:
                action = webdriver.common.action_chains.ActionChains(browser)
                try:
                    action.move_to_element_with_offset(moreComment, 5, 5)
                    action.perform()
                    moreComment.click()
                    browser.execute_script("arguments[0].click();", user)
                except:
                    pass

    browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit('user, password and link are required arguments')

    user, password, link = sys.argv[1:]
    extract(page=link)

