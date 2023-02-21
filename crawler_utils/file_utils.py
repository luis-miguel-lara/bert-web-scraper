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

def html_filename(text):
    """
    Args:
        - text (str): URL or other txt
    Returns:
        String containing valid filename
    """
    while " " * 2 in text:
        text = text.replace(" " * 2, " ")
    text =  re.sub("[^a-zA-Z' ]+", '', text).replace(":", "-").replace("/", "-") .replace("\\", "-").strip()
    if len(text) == 0:
        text =  "no_name"
    
    return "{}.html".format(text[:50])
