import os
import shutil
import re

def delete_create_dir(path):
    """
    """
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)


def clean_create_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)
    else:
        for f in os.listdir(path):
            os.remove(os.path.join(path, f))

def clean_filename(text):
    text = [t.strip() for t in text.split("/") if len(t.strip()) > 0][-1] # from http...../abc/def to dfe
    text = re.sub(r"[\\/:\"*?<>|]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    #text = re.sub(r"[^\w\s]", "-", text)
    #text =  re.sub("[^a-zA-Z' ]+", '', text).replace(":", "-")
    return text

def html_filename(text):
    """
    Args:
        - text (str): URL or other txt
    Returns:
        String containing valid filename
    """
    text = clean_filename(text.strip())
    if len(text) == 0:
        text =  "no_name"
    return "{}.html".format(text[:50])