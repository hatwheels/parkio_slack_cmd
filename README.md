# **PARK.IO CMD** #

## **BRIEF** ##

  * Issue commands to track all/specific running auctions and all/specific expiring domains **[park.io](https://park.io)**
  * Commands are issued in **Slack** to **_cmdbot_**, thus makes use of the **Slack API**


## **HOW-TO** ##

  * **Create** a bot with name **_cmdbot_** for your **Slack team**
  * **Run** **`parkio_main.py`** in command line (python 3.x.x) to start **_cmdbot_**
  * **Search if a Domain name is expiring or being auctioned:**
    * Search for a specific domain name with a specific TLD: send to **_cmdbot_** **`search <name> <tld>`**
    * Search for a specific domain name with any TLD: send to **_cmdbot_** **`search <name>`**
  * **Track Auctioned Domains**: 
    * Track all running auctions: send to **_cmdbot_** **`auction all`**
    * Track specific auction: send to **_cmdbot_** **`auction <domain.tld>`**
  * **Track Expiring Domains**:
    * Track all expiring domains: send to **_cmdbot_** **`domain all`**
    * Track expiring domains with specific tld: send to **_cmdbot_** **`domain <tld>`**
  * **Close**: send to **_cmdbot_** **`close <command name>`**, i.e. **`close auction all`**
  * Check which trackers are running: send to **_cmdbot_** **`running?`**
  * Check if **_cmdbot_** is alive (main script is running): send to **_cmdbot_** **`alive?`**
  * For information about all available commands send to **_cmdbot_** **`help`**
