# Mexican Jobs

This project contains several scripts used for the analysis of job listings posted in the official Mexican Job Board (https://www.empleos.gob.mx).

A secondary use for this project were the creation of 2 Reddit bots that help users to quickly filter job listings with their desired parameters, including salary range, location and a keyword.

## Scripts

Name | Brief Description
--|--
`scraper.py` | A web scraper made with `Requests` and `BeautifulSoup` that continously keeps saving new job listings.
`post_bot.py` | A Reddit bot made with `PRAW` and `lxml` that creates a digest with the highest paying jobs country wide.
`comments_bot.py` | A Reddit bot made with `PRAW` and `lxml` that creates a customized digest with the parameters given by the user.

All of these scripts were written in Python 3, they were deployed on a VPS and were scheduled with the following crontab.

```
*/5 * * * * cd /home/scripts/ && python3 scraper.py
15,30,45,0 cd /home/scripts/ && python3 post_bot.py
* * * * * cd /home/scripts/ && python3 comments_bot.py
```

### Web Scraper

Creating the web scraper required to study the structure of the website. Searching for job listings can be achieved only with `GET` requests. Not providing any keyword returns all the available jobs for the desired state.

All states urls were hardcoded and added to a list. The script iterates over this list and requests the contents of each state.

The script detects if the available job listings are not already saved and if there are new job listings it saves them to their respective state folders and updates a log file with the current timestamp.

This is run every 5 minutes to ensure that almost all job listings are saved and to avoid making too many requests to the server.

While debugging this script I noticed that I constantly got timed out from the server. I was able to fix this by reusing a Session object while making all requests and also adding a retry capability.

### Reddit Bots

Both Reddit bots share most of their functionality. They first load the log file created by the web scraper and discard all items that are older than 3 days.

With the remaining items it uses multithreading and `lxml` to quickly extract the relevant data from the .html files and adds it to a master list as tuples. The master list is then sorted by the salary value.

After the master list is sorted, the script starts creating the `Markdown` message that will be posted on Reddit.

The `post_bot.py` script only grabs the highest paying jobs and keeps concatenating them to the message string until it reaches 39,000 characters.

Reddit has a 40,000 character limit on posts. The ramaining 1000 characters are used for the footer where I added some links and the timestamp.

The `comments_bot.py` script is much more complex than the previous one. After the master list is sorted it then connects to the Reddit API and checks for new comments with the `!empleos` command.

The `!empleos` command can have up to 4 parameters.

Parameter | Required or Optional | Type
--|--|--
Location | Required | 1 String
Minimum Salary | Optional | Integer
Maximum Salary | Optional | Integer
Keyword | Optional | 1 String

The script splits the message body and verifies each of the parameters to be the correct type, cleans them and adds them to a dictionary.

This dictionary is then sent to a function where the values are compared against the values of the master list.

In this new function we start a counter and for each job listing that fulfills our parameters we increase it by 1.

The first check is the location, if the provided location isn't available in the master list, it is then instantly discarded.

If the script detects that a minimum salary was provided it then discards all jobs where the salary is lower than the one specified.

Similar rules apply for the other 2 parameters. Once our counter hits 10 we stop filtering job listings, this is due to Reddit's comment limit of 10,000 characters.

Finally we add the footer to the message and reply to the original comment.

## Analysis

The analysis, figures and scripts that will be used for it will be available early September.