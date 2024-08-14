import email
from imapclient import IMAPClient
import ssl
from datetime import datetime, timedelta  # Import datetime module
import time
import http.client, urllib

# credential handling
import os
from dotenv import load_dotenv   #for python-dotenv method
load_dotenv()                    #for python-dotenv method

#Pushover Keys
PUSHOVER_USER= os.getenv("PUSHOVER_USER")
API_TOKEN= os.getenv("API_TOKEN")

# IMAP Keys
HOST= os.getenv("HOST")
USERNAME= os.getenv("EMAIL_USERNAME")
PASSWORD= os.getenv("PASSWORD")
PORT= int(os.getenv("PORT"))

# General Settings
PAUSE_START= datetime.strptime(os.getenv("PAUSE_START"), "%H:%M").time()
PAUSE_END= datetime.strptime(os.getenv("PAUSE_END"), "%H:%M").time()
SKIP_WEEKEND= int(os.getenv("SKIP_WEEKEND"))

print("CONFIGURATION:")
print("PUSHOVER_USER: ", PUSHOVER_USER)
print("API_TOKEN: ", API_TOKEN)
print("Host: ", HOST)
print("USERNAME: ", USERNAME)
#print("PASSWORD: ", PASSWORD)

print("PAUSE-START:", PAUSE_START)
print("PAUSE-END: ", PAUSE_END)


# Just for better readability
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Function to check if it's time to pause checking emails
def should_pause_checking():
    current_time = datetime.now().time()
    current_day = datetime.now().weekday()  # 0 = Monday, 1 = Tuesday, ..., 6 = Sunday

    # Check if it's Saturday (5) or Sunday (6), or if it's within the pause time
    if current_day >= SKIP_WEEKEND or (PAUSE_START <= current_time or current_time <= PAUSE_END):
        return True
    else:
        return False

# handles push notifications, through pushover api, uses post request
def notification(TITLE, MESSAGE: str):
    PRIORITY = '0'

    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
      urllib.parse.urlencode({
        "token": API_TOKEN,
        "user": PUSHOVER_USER,
        "message": MESSAGE,
        "priority": PRIORITY,
        "title": TITLE,
      }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

    print(bcolors.OKGREEN + "Sent Push Notification" + bcolors.ENDC, flush=True)
 

# Logs in a normal non-idle session, and fetches the newest messages
# Handles formating
def parse_email_and_notify():
    with IMAPClient(host=HOST, ssl=True, port=PORT) as server:

        server.login(USERNAME, PASSWORD)
        time.sleep(7) # sleep to allow time for server to process new message
        server.select_folder("INBOX", readonly=True)

        time.sleep(10)
        server.noop()
        time.sleep(5)

        print(bcolors.OKCYAN + f"[{datetime.now().strftime('%d-%m | %H:%M')}] Started parsing messages" + bcolors.ENDC, flush=True)

        today_date = datetime.now().strftime('%d-%b-%Y')
        messages = server.search(['UNSEEN', 'SINCE', today_date])

        print(bcolors.OKCYAN + "Messages Recieved" + bcolors.ENDC, flush=True)

        time.sleep(10)

        if messages:
            latest_message_id = messages[-1]
            uid, message_data = server.fetch(latest_message_id, "RFC822").popitem()
            email_message = email.message_from_bytes(message_data[b"RFC822"])

            # Extract Senders Name
            sender_address = email_message.get("From")
            sender_name = sender_address.split("<", 1)[0].strip() if "<" in sender_address else sender_address.strip()

            # Limit subject length to 40 characters
            subject = email_message.get("Subject")[:30] + "..."

            notification(sender_name, subject)

            # Writing message details to console
            #print(bcolors.WARNING, email_message.get("From"), email_message.get("Subject"), bcolors.ENDC, flush=True)
            #print("From: ", sender_name, flush=True)
            #print("Subject: ", subject, flush=True)
        else:
            print(bcolors.FAIL + f"[{datetime.now().strftime('%d-%m | %H:%M')}] ERROR: Fetch mail called, but not found" + bcolors.ENDC, flush=True)

# Connect to the IMAP server
# Define the IMAPClient initialization and login outside the loop
server = IMAPClient(host=HOST, ssl=True, port=993)

# Login and select the INBOX folder in read-only mode
server.login(USERNAME, PASSWORD)
server.select_folder("INBOX", readonly=True)

# Start the IDLE mode
server.idle()

print(bcolors.OKGREEN + f"[{datetime.now().strftime('%d-%m | %H:%M')}] SUCCESS: connection established in IDLE mode \t (^c to quit)" + bcolors.ENDC, flush=True)

try:
    # Continuously check _and_notifyfor new emails
    while True:
        # Check if it's time to pause checking emails
        if should_pause_checking():
            print(bcolors.FAIL + f"[{datetime.now().strftime('%d-%m | %H:%M')}] Pausing Listner till next working hours..." + bcolors.ENDC, flush=True)
            server.idle_done()  # End IDLE mode
            server.logout()     # Logout from the server
            del server          # Delete the server object

            # Sleep until 7 AM
            current_time = datetime.now().time()
            seconds_until_7am = (datetime.combine(datetime.now().date(), datetime.strptime("07:00", "%H:%M").time()) - datetime.combine(datetime.now().date(), current_time)).seconds
            time.sleep(seconds_until_7am)

            print(bcolors.OKGREEN + f"[{datetime.now().strftime('%d-%m | %H:%M')}] Reinitializing connection to IMAP sever." + bcolors.ENDC, flush=True)

            # TODO: Put this in a function
            # Reinitialize connection to the IMAP server
            server = IMAPClient(host=HOST, ssl=True, port=993)
            server.login(USERNAME, PASSWORD)

            # Start the IDLE mode
            server.select_folder("INBOX", readonly=True)
            server.idle()

            continue  # Skip email processing

        # Wait for up to 20 minutes for an IDLE response
        responses = server.idle_check(timeout=1200)

        print(f"[{datetime.now().strftime('%d-%m | %H:%M')}] Server sent:", responses if responses else "nothing", flush=True)

        for response in responses:
            if any(isinstance(item, bytes) and b'EXISTS' in item for item in response):
                  parse_email_and_notify()

except KeyboardInterrupt:
    print(f"[{datetime.now().strftime('%d-%m | %H:%M')}] Exiting IDLE mode", flush=True)

finally:
    try:
        # End the IDLE mode to return to normal operation
        server.idle_done()
        # Logout from the server
        server.logout()
    except: print(f"[{datetime.now().strftime('%d-%m | %H:%M')}] Exited during pause, Listner already shutdown...", flush=True)
