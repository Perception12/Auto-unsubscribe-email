import imaplib
import email
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests

load_dotenv()

username = os.getenv("EMAIL")
password = os.getenv("PASSWORD")

def connect_to_email():
    try:
        # Connect to the Gmail IMAP server
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(username, password)
        print("Successfully connected to the mailbox.")
        imap.select("inbox")
        return imap
    except Exception as e:
        print(f"Failed to connect to the email account: {e}")
        return None

def extract_links_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    links = [link["href"] for link in soup.find_all("a", href=True) if "unsubscribe" in link["href"].lower()]
    return links

def click_link(link):
    try:
        response = requests.get(link)
        if response.status_code == 200:
            print("Successfully visited ", link)
        else:
            print("Failed to visit ", link, " error code: ", response.status_code)
    except Exception as e:
        print("Error with", link, str(e))

def search_for_emails():
    mail = connect_to_email()
    _, search_data = mail.search(None, '(BODY "unsubscribe")')
    data = search_data[0].split()
    links = []

    for num in data:
        _, data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "test/html":
                    html_content = part.get_payload(decode=True).decode()
                    links.extend(extract_links_from_html(html_content))
        else:
            content_type = msg.get_content_type()
            content = msg.get_payload(decode=True).decode()
            if content_type == "text/html":
                links.extend(extract_links_from_html(content))
    mail.logout()
    return links

def save_links(link_list):
    with open("links.txt", "w") as f:
        f.write("\n".join(link_list))

links = search_for_emails()

for link in links:
    click_link(link)

save_links(links)