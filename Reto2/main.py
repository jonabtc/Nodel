# POST_LINK = "https://www.instagram.com/p/B166OkVBPJR"
import pandas as pd
from instagram_private_api import Client

USER = ''
PASSWORD = ''
MEDIA_ID = '2124266262036279889'

api = Client(USER, PASSWORD)
results = api.media_comments(MEDIA_ID)
counter = 0


def get_entry(item, caption, id_father=None):
    entry = {
        "post": item.get('text'),
        "caption": caption,
        "date": item.get("created_at"),
        "likesComment": item.get('comment_like_count'),
        "IdFatherComment": item.get('pk'),
        "IdChildComment": None,
        "Username": item.get("user")["username"],
    }
    if id_father is not None:
        entry.update({"IdFatherComment": id_father, "IdChildComment": item['pk']})
    return entry


def classify_comments(comments, caption):
    classified = []
    for item in comments:
        classified.append(get_entry(item, caption))
        if item['child_comment_count'] > 0:
            child = get_children(item['pk'], caption)
            classified.extend(child)
    return classified


def get_children(comment_id, caption):
    global counter
    child_entries = []
    child_comments_result = api.comment_replies(MEDIA_ID, comment_id)
    child_comments = child_comments_result.get('child_comments')
    for child in child_comments:
        child_entries.append(get_entry(child, caption, id_father=comment_id))
        counter += 1
    return child_entries


def get_commits():
    treated_comments = []
    result = api.media_comments(MEDIA_ID, reverse=False)
    next_min_id = result.get('next_min_id')
    caption = result.get('caption')['text']
    treated_comments.extend(classify_comments(result.get('comments'), caption))
    while True:
        result = api.media_comments(MEDIA_ID, min_id=next_min_id)
        next_min_id = result.get('next_min_id')
        treated_comments.extend(classify_comments(result.get('comments'), result.get('caption')['text']))
        if next_min_id is None:
            break
    return treated_comments


if __name__ == '__main__':
    commits = get_commits()
    df = pd.DataFrame(commits)
    df.to_csv('dataresponse.csv', index=False)

