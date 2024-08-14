# imap-daemon-notifier
IMAP **listener** to send instant **push notifications** when a new email is received using **IMAP-IDLE**.
This Python Script was made for my private use, as my Universities email service does not provide push notifications, and constand Fetching on Mobile devices caused huge battery drain issue, while still being not instantaneous. 

![Screenshot](https://github.com/user-attachments/assets/afe3921f-50d9-4dbf-9a52-982fbec88f15)

## Features
- Push notifications (current implementation through PushOver)
- Sleep and Wind down during weekends
- Clean CLI interface and logging.

## Possible Additions
- Own custom push notification platform/ other third-party services like IFTT
- Sender/Subject line logic for priority checking

  
## Usage
```
python3 -m venv pyenv

.\pyenv\Scripts\Activate.ps1 (Powershell)
source pyenvwsl/bin/activate (Bash)

python3 -m pip install -r requirements.txt
```
Please fill the `.env` with your credentials. A template has been provided.


## Tips and Tricks
**No Output to tty:**
nohup python3 imap.py > /dev/shm/imap-idle-output.log &

**Blend output to tty:**
nohup python3 imap.py | tee /dev/shm/imap-idle-output.log &

**Kill the background task:**
ps aux | grep imap
kill PID

**To read the log:**
tail -f /dev/shm/imap-idle-output.log
cat /dev/shm/imap-idle-output.log

## Note
I no longer use this script, so I am making it public, use at your own discretion. No Warranty is provided.



