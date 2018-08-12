"""
This bot analyzes job listings that are no older than the JOBS_MAX_AGE and creates
a digest of the highest paying ones.

The digest is formatted with Markdown and posted to Reddit.
"""

import threading
from datetime import datetime, timedelta

import lxml.html
import praw

import config

MIN_SALARY_THRESHOLD = 8000


def load_files():
    """Reads the log file and discards the files that are older than the JOB_MAX_AGE."""

    now = datetime.now() - timedelta(hours=config.DELTA_HOURS)
    now_timestamp = now.timestamp()

    with open("log.txt", "r", encoding="utf-8") as temp_file:

        files_list = list()

        for item in temp_file.read().split("\n"):

            try:
                file_name, file_date = item.split(",")

                file_timestamp = datetime.strptime(
                    file_date, "%Y-%m-%d %H:%M:%S.%f").timestamp()

                if (now_timestamp - file_timestamp) <= config.JOBS_MAX_AGE:
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

        # Very few times the HTML is corrupted and can't be fixed.
        try:
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

            master_list.append((clean_salary, name, location, url))

        except:
            pass


def prepare_post():
    """Filters jobs listings from the master_list and prepares a Markdown message."""

    message = "Las ofertas aqui presentes no son mayores a 3 días.\n\n"
    message += "Se actualiza cada 15 minutos. Ordenado por Salario Neto Mensual (MXN).\n\n"
    message += "Oferta | Empresa | Salario Neto Mensual | Ubicación\n--|--|--|--\n"

    # We sort from highest to lowest salary.
    master_list.sort(reverse=True, key=lambda tup: tup[0])

    for salary, name, location, url in master_list:

        # We discard jobs that don't meet the minimum salary threshold.
        if salary >= MIN_SALARY_THRESHOLD:

            # We avoid hitting the Reddit 40,000 characters limit.
            if len(message) <= 39000:

                # We then separate and clean the job name and the company name.
                offer = name.split("-")[0].title().strip()
                company = name.split("-")[-1].strip()

                if "sin nombre" in company.lower():
                    company = "S/N"
                else:
                    company = company.title()

                message += "[{}]({}) | {} | ${:,} | {}\n".format(
                    offer, url, company, salary, location)

    # We finalize the mssage with the footer.
    now = datetime.now() - timedelta(hours=config.DELTA_HOURS)

    message += """\n*****\n^Última ^actualización: ^{:%d-%m-%Y ^a ^las ^%H:%M:%S} ^|
        ^[Ayuda](https://redd.it/93au4i) ^|
        ^[Contacto](https://www.reddit.com/message/compose/?to=agent_phantom) ^|
        ^[GitHub](https://git.io/fNoyw)""".format(now)

    update_post(message)


def update_post(message):
    """Updates the Reddit post with the specified Markdown message.

    Parameters
    ----------

    message : str
        The Markdown formatted message.

    """

    # We initialize Reddit.
    reddit = praw.Reddit(client_id=config.APP_ID, client_secret=config.APP_SECRET,
                         user_agent=config.USER_AGENT, username=config.REDDIT_USERNAME,
                         password=config.REDDIT_PASSWORD)

    # We update the Reddit theads.
    for post_id in config.POST_IDS:
        reddit.submission(post_id).edit(message)


if __name__ == "__main__":

    # We use multithreading to accelerate the reading of all files.
    master_list = list()
    threads = list()

    for file in load_files():
        t = threading.Thread(target=parse_file, args=(file, ))
        t.start()
        threads.append(t)

    [t.join() for t in threads]

    prepare_post()
