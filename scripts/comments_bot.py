"""
This is a Reddit bot that answers to users who use the !empleos command.
It keeps track of which comments it has answered.
"""

import threading
from datetime import datetime, timedelta

import lxml.html
import praw

import config

# The file path where the log is saved.
COMMENTS_LOG_FILE = "comments_log.txt"

# The next 2 lists must have the same length, since one will replace the other.
ACCENT_MARKS = ["á", "Á", "é", "É", "í", "Í", "ó", "Ó", "ú", "Ú"]
FRIENDLY_MARKS = ["a", "A", "e", "E", "i", "I", "o", "O", "u", "U"]

# Error messages
NO_JOBS_MESSAGE = "Lo siento. No pude encontrar ofertas con los parámetros especificados."

# To avoid hitting the 10,000 charater limit in comments we only return up to 10 jobs.
MAX_JOBS = 10

DELTA_HOURS = 0  # 0 for local time, -5 for Mexico Central Time.
JOBS_MAX_AGE = 86400 * 3  # Seconds in a day multiplied for the number of days.


def load_files():
    """Reads the log file and discards the files that are older than the JOB_MAX_AGE."""

    now = datetime.now() - timedelta(hours=DELTA_HOURS)
    now_timestamp = now.timestamp()

    with open("log.txt", "r", encoding="utf-8") as temp_file:

        files_list = list()

        for item in temp_file.read().split("\n"):

            try:
                file_name, file_date = item.split(",")

                file_timestamp = datetime.strptime(
                    file_date, "%Y-%m-%d %H:%M:%S.%f").timestamp()

                if (now_timestamp - file_timestamp) <= JOBS_MAX_AGE:
                    files_list.append(file_name)

            except:
                pass

        return files_list


def parse_file(file_name):
    """Parses a .html file and extracts values of interest using lxml.

    Parameters
    ----------
    file_name : str
        The name of the file to be parsed.

    """

    with open(file_name, "r", encoding="utf-8") as temp_file:

        html = lxml.html.fromstring(temp_file.read())

        salary = html.xpath(
            "/html/body/div[1]/div[8]/div[4]/div/div[2]/div/div[1]/div/div/span")[0].text

        clean_salary = int(float(salary.replace("$", "").replace(",", "")))

        name = html.xpath(
            "/html/body/div[1]/div[8]/div[1]/div/h3/small")[0].text

        location = html.xpath(
            "/html/body/div[1]/div[8]/div[4]/div/div[2]/div/div[2]/div/div/span")[0].text

        url = html.xpath(
            "//meta[@property='og:url']/@content")[0].replace("x//", "x/")

        # We add all the fields to the master_list as a tuple.
        master_list.append((clean_salary, name, location, url))


def load_comments():
    """Loads the latest comments and replies to those who
    include the !empleos command and valid parameters.
    """

    # We initialize Reddit.
    reddit = praw.Reddit(client_id=config.APP_ID, client_secret=config.APP_SECRET,
                         user_agent=config.USER_AGENT, username=config.REDDIT_USERNAME,
                         password=config.REDDIT_PASSWORD)

    processed_comments = load_log()

    for post_id in config.SUBMISSION_IDS:
        for comment in reddit.submission(id=post_id).comments:

            if comment.id not in processed_comments:

                # For a comment to be valid we start by checking that the command !empleos is in the comment body.
                if "!empleos" in comment.body:

                    # We split the comment body into a list and remove white space chunks.
                    parameters_list = comment.body.split(" ")
                    parameters_list = [x for x in parameters_list if x != ""]

                    parameters = dict()

                    # The parameters list can have up to 5 items, including the command.
                    # We check for each escneario and clean the data accordingly.
                    if len(parameters_list) == 2:
                        parameters["location"] = clean_word(
                            str(parameters_list[1])).lower()

                    elif len(parameters_list) == 3:
                        parameters["location"] = clean_word(
                            str(parameters_list[1])).lower()
                        parameters["minimum_salary"] = int(parameters_list[2])

                    elif len(parameters_list) == 4:
                        parameters["location"] = clean_word(
                            str(parameters_list[1])).lower()
                        parameters["minimum_salary"] = int(parameters_list[2])

                        try:
                            parameters["maximum_salary"] = int(
                                parameters_list[3])
                        except:
                            parameters["tag"] = clean_word(
                                str(parameters_list[3])).lower()

                    elif len(parameters_list) == 5:
                        parameters["location"] = clean_word(
                            str(parameters_list[1])).lower()
                        parameters["minimum_salary"] = int(parameters_list[2])
                        parameters["maximum_salary"] = int(parameters_list[3])
                        parameters["tag"] = clean_word(
                            str(parameters_list[4])).lower()

                    message, job_counter = filter_posts(parameters)

                    # If there were no jobs we reply with an error message.
                    if job_counter == 0:
                        comment.reply(NO_JOBS_MESSAGE)
                        update_log(comment.id)
                    else:
                        comment.reply(message)
                        update_log(comment.id)


def filter_posts(parameters):
    """Creates a folder if it doesn't exist.

    Parameters
    ----------
    parameters : dict
        A dictionary containing the parameters to filter the master list.

    Returns
    -------
    str
        The Reddit reply message formatted with Markdown.   

    int
        The number of jobs that satisfied all parameters.

    """

    # We initialize the message with the table header.
    message = "Oferta | Empresa | Salario Neto Mensual | Ubicación\n--|--|--|--\n"
    job_counter = 0

    # We unpack the tuples from the master_list.
    for salary, name, location, url in master_list:

        # We set the job_match flag to false. This is used to avoid duplicating code.
        job_match = False

        # Keep reading from the master_list only if we don't have reached the limit.
        if job_counter < MAX_JOBS:

            # The first check is to know if our location is available in the master_list.
            if parameters["location"] in clean_word(location.lower()):

                # We then separate and clean the job name and the company name.
                offer = name.split("-")[0].title().strip()
                company = name.split("-")[-1].strip()

                if "sin nombre" in company.lower():
                    company = "S/N"
                else:
                    company = company.title()

                # This is where things start getting messy. Since we don't know which parameters
                # are available, we first check for the escenario where we get all of them and
                # Keep falling back until the one where we only have the location.
                if parameters.get("minimum_salary") and parameters.get("maximum_salary") and parameters.get("tag"):
                    if salary >= parameters["minimum_salary"] and salary <= parameters["maximum_salary"] and parameters["tag"] in clean_word(name.lower()):
                        job_match = True

                elif parameters.get("minimum_salary") and parameters.get("tag"):
                    if salary >= parameters["minimum_salary"] and parameters["tag"] in clean_word(name.lower()):
                        job_match = True

                elif parameters.get("minimum_salary") and parameters.get("maximum_salary"):
                    if salary >= parameters["minimum_salary"] and salary <= parameters["maximum_salary"]:
                        job_match = True

                elif parameters.get("minimum_salary"):
                    if salary >= parameters["minimum_salary"]:
                        job_match = True

                else:
                    job_match = True

            # If the current listing satisfies our parameters we add it to the table.
            if job_match:
                message += "[{}]({}) | {} | ${:,} | {}\n".format(
                    offer, url, company, salary, location)

                job_counter += 1

    # We finalize the mssage with the footer.
    now = datetime.now() - timedelta(hours=DELTA_HOURS)

    message += """\n*****\n^Ofertas ^obtenidas ^el: ^{:%d-%m-%Y ^a ^las ^%H:%M:%S} ^|
        [^Ayuda](https://redd.it/93au4i) ^|
        [^Contacto](https://www.reddit.com/message/compose/?to=agent_phantom) ^|
        [^GitHub](https://git.io/fNoyw)""".format(now)

    return (message, job_counter)


def load_log():
    """Loads the comments log. If it doesn't exist it creates it and returns an empty list.

    Returns
    -------

    list
        A list containing all the processed comments.

    """

    try:
        with open(COMMENTS_LOG_FILE, "r", encoding="utf-8") as temp_file:
            return [x for x in temp_file.read().split("\n")]

    except:
        with open(COMMENTS_LOG_FILE, "w", encoding="utf-8") as temp_file:
            return list()


def update_log(comment_id):
    """Updates the log file with the specified comment_id.

    Parameters
    ----------
    post_id : str
        The specified Reddit comment id.

    """

    with open(COMMENTS_LOG_FILE, "a", encoding="utf-8") as temp_file:
        temp_file.write("{}\n".format(comment_id))


def clean_word(word):
    """Cleans the word by replacing non-friendly characters.

    Parameters
    ----------
    word : str
        The word to be cleaned.

    Returns
    -------
    str
        The cleaned word.

    """

    for index, char in enumerate(ACCENT_MARKS):
        word = word.replace(char, FRIENDLY_MARKS[index])

    return word


if __name__ == "__main__":

    # We use multithreading to accelerate the reading of all files.
    master_list = list()
    threads = list()

    for file in load_files():
        t = threading.Thread(target=parse_file, args=(file, ))
        t.start()
        threads.append(t)

    [t.join() for t in threads]

    # We sort from highest to lowest salary.
    master_list.sort(reverse=True, key=lambda tup: tup[0])

    load_comments()
