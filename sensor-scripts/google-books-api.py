import urllib.request
import json
import textwrap

base_api_link = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
user_input = input("Enter ISBN: ").strip()
with urllib.request.urlopen(base_api_link + user_input) as f:
    text = f.read()
decoded_text = text.decode("utf-8")
obj = json.loads(decoded_text)  # deserializes decoded_text to a Python object
#print(len(obj))
#print(obj)
print(obj["totalItems"])
volume_info = obj["items"][0]
authors = obj["items"][0]["volumeInfo"]["authors"]
#publisher = obj["items"][0]["volumeInfo"]["publisher"]
image = obj["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]

title = volume_info["volumeInfo"]["title"]
description = textwrap.fill(volume_info["searchInfo"]["textSnippet"], width=65)
pageCount = volume_info["volumeInfo"]["pageCount"]
language = volume_info["volumeInfo"]["language"]

print(title, description, authors, pageCount, language , image)
