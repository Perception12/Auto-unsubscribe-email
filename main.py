import imaplib
import email
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests

# Load environment variables (e.g., email credentials) from a .env file
load_dotenv()

# Retrieve email username and password from environment variables
username = os.getenv("EMAIL")
password = os.getenv("PASSWORD")

def connect_to_email():
    """
    Connect to the email server using IMAP and select the inbox.
    Returns the IMAP connection object if successful, otherwise None.
    """
    try:
        # Connect to the Gmail IMAP server over SSL
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(username, password)
        print("Successfully connected to the mailbox.")
        # Select the inbox folder to read emails
        imap.select("inbox")
        return imap
    except Exception as e:
        # Handle connection errors gracefully
        print(f"Failed to connect to the email account: {e}")
        return None

def extract_links_from_html(html_content):
    """
    Parse the HTML content of an email to extract unsubscribe links.
    Returns a list of unsubscribe links found in the email.
    """
    # Use BeautifulSoup to parse HTML and find all links with "unsubscribe" in the href
    soup = BeautifulSoup(html_content, "html.parser")
    links = [link["href"] for link in soup.find_all("a", href=True) if "unsubscribe" in link["href"].lower()]
    return links

def click_link(link):
    """
    Attempt to visit the provided unsubscribe link using a GET request.
    Logs the success or failure of the operation.
    """
    try:
        response = requests.get(link)
        if response.status_code == 200:
            print("Successfully visited ", link)
        else:
            print("Failed to visit ", link, " error code: ", response.status_code)
    except Exception as e:
        # Handle any errors encountered during the HTTP request
        print("Error with", link, str(e))

def search_for_emails():
    """
    Search for emails containing the word "unsubscribe" in their body.
    Extract and return unsubscribe links from the found emails.
    """
    mail = connect_to_email()
    if not mail:
        return []

    # Search for emails with "unsubscribe" in their body
    _, search_data = mail.search(None, '(BODY "unsubscribe")')
    data = search_data[0].split()
    links = []

    # Iterate through the found emails
    for num in data:
        _, data = mail.fetch(num, "(RFC822)")  # Fetch the email content
        msg = email.message_from_bytes(data[0][1])

        # Check if the email has multiple parts (e.g., plain text and HTML)
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    # Decode the HTML content and extract unsubscribe links
                    html_content = part.get_payload(decode=True).decode()
                    links.extend(extract_links_from_html(html_content))
        else:
            # For single-part emails, process the HTML content directly
            content_type = msg.get_content_type()
            content = msg.get_payload(decode=True).decode()
            if content_type == "text/html":
                links.extend(extract_links_from_html(content))
    
    # Logout from the email server after processing
    mail.logout()
    return links

def save_links(link_list):
    """
    Save the extracted unsubscribe links to a file named 'links.txt'.
    """
    with open("links.txt", "w") as f:
        f.write("\n".join(link_list))

# Main execution flow
# Step 1: Search for unsubscribe links in emails
links = search_for_emails()

# Step 2: Visit each unsubscribe link
for link in links:
    click_link(link)

# Step 3: Save the unsubscribe links to a file for future reference
save_links(links)
