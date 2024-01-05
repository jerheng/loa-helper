## About loa-helper
Python script/app to easily download and merge spotify playlists, albums and single tracks to local mp4 files.
Discord bot to assist with visualizing raid members' schedules from time of reset ( wednesday - tuesday ) 

## To-Do
* Keep track of live schedules by adding in a duration since last active before marking the message_id as completed
  * Utilizing a database system to keep track of servers/channels the bot is present in along with command call statistics
* Allowing for server admins to customize the bot settings, i.e auto-deleting of commands called, 
  
## Getting Started

### Prerequisites
* Python >= 3.8.5
* All requirements in requirements.txt
* Getting your own bot secret key

### Installation
1.Clone the repository
```
git clone https://github.com/jerheng/loa-helper/tree/main
```

2.Install required packages (If you're not using docker)
```
pip3 install -r requirements.txt
```

3. Updating .env with your secret key and settings.py with your respective emote id's
* I recommend deploying the bot to a test server belonging to you first, then uploading the emoji assets to the server and reanming them, obtaining the emoji ids and updating .settings accordingly!
* The way to get your emoji id is to insert \ before your emoji (e.g \:helloworld_emoji:), then it'll output in the format of <:helloworld_emoji_id>, which is what you want to replace .settings with.

### Deploying the bot locally
1. Docker deployment
Recommended if you experience issues with 2. to avoid the need to replicate my development environment!
```
docker build -t loa-helper .
docker run loa-helper
```

2. Python3 local deployment
```
python3 app/main.py
```

### Commands usage
/schedule [role] 
* Calls upon the bot to schedule a raid, pinging members who are either part of the role if a valid role is passed as an argument with the command call, otherwise pinging everyone who is able to view the channel/thread
* Auto-pins the schedule message for members to keep track easily.

/gen 
* Looks up the latest schedule message called in the channel/thread where /gen is called, and tabulates the availability of all raid members as shown below, while reminding members who have yet to react to the message.


