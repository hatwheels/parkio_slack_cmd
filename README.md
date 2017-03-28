# **PARK.IO CMD** #

## **BRIEF** ##

  * Issue commands to track all/specific running auctions and all/specific soon-to-expire domains @park.io
  * Commands are issued in **Slack** to **_cmdbot_**, thus makes use of the **Slack API**


## **HOW-TO** ##

  * **Create** a bot with name **cmdbot** for your **Slack team**
  * **Run** **`parkio_main.py`** in command line (python 3.x.x) to start **_cmdbot_**
  * **Auctions**: 
    * Track all running auctions: send to **_cmdbot_** **`auction all`**
    * Track specific auction: send to **_cmdbot_** **`auction <domain.tld>`**
  * **Domains**:
    * Track all soon-to-be expiring domains: send to **_cmdbot_** **`domain all`**
    * track soon-to-be expiring domains with specific tld: send to **_cmdbot_** **`domain <tld>`**
  * **Close**: send to **_cmdbot_** **`close <command name>`**, i.e. **`close auction all`**
  * Check which trackers are running: send to **_cmdbot_** **`running?`**
  * Check if **_cmdbot_** is alive (main script is running): send to **_cmdbot_** **`alive?`**
  * For information about all available commands send to **_cmdbot_** **`help`**
