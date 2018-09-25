"""
This script contains several functions that creates plots or get statistical information from the dataset.
The reader will require to manually call the functions with the main dataframe as the only argument.
"""

import csv

import geopandas
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns

sns.set()

ACCENT_MARKS = ["á", "Á", "é", "É", "í", "Í", "ó", "Ó", "ú", "Ú"]
FRIENDLY_MARKS = ["a", "A", "e", "E", "i", "I", "o", "O", "u", "U"]


def get_basic_stats(df):
    """Gets the basic salary stats.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """

    print(df["salary"].describe())
    print("median", np.median(df["salary"]))


def generate_lineplot(df):
    """Generates a lineploot with the website activity.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """

    df.set_index("date", inplace=True)
    b = df.resample("D").count().reset_index()

    plt.figure(figsize=(10, 5))
    plt.plot(b["date"], b["offer"], marker="o")
    plt.title("Site Activity")
    plt.xlabel("August 2018")
    plt.tight_layout()
    plt.savefig("line1.png")


def generate_monthly_salaries_hist(df):
    """Generates an histogram of monthly salary distribution.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """

    plt.figure(figsize=(15, 10))

    filtered = df[df["salary"].between(0, 20000, inclusive=True)]["salary"]
    hist = sns.distplot(filtered, kde=False, bins=20,
                        axlabel="Monthly Salary (MXN)")
    plt.title("Salary Distribution")
    hist.xaxis.set_major_locator(ticker.MultipleLocator(2000))
    plt.savefig("hist1.png")


def generate_work_hours_hist(df):
    """Generates an histogram of hours worked distribution.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """

    plt.figure(figsize=(15, 10))

    sns.distplot(df["hours_worked"], kde=False,
                 bins=24, axlabel="Hours")
    plt.title("Labour Hours Distribution")
    plt.savefig("hist2.png")


def generate_work_days_hist(df):
    """Generates an histogram of days worked distribution.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """

    plt.figure(figsize=(15, 10))

    sns.distplot(df["days_worked"], kde=False,
                 bins=7, axlabel="Days")
    plt.title("Labour Days Distribution")
    plt.savefig("hist3.png")


def generate_work_hours_scatter(df):
    """Generates a scatter plot of hours worked and salary.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """

    plt.figure(figsize=(15, 10))
    filtered = df[df["salary"].between(0, 20000, inclusive=True)]

    sns.scatterplot(x="hours_worked", y="salary", data=filtered, alpha=0.5)
    plt.xlabel("Hours")
    plt.ylabel("Salary")
    plt.title("Salary vs Hours Worked")
    plt.savefig("scatter1.png")


def generate_state_bars(df):
    """Generates a bar plot with the job offers counts for each state.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """

    states = list()
    counts = list()

    for item in df["state"].value_counts().items():
        states.append(item[0])
        counts.append(item[1])

    plt.rcParams["figure.figsize"] = [11, 11]
    bar_plot = sns.barplot(x=counts, y=states)

    for patch in bar_plot.patches:
        width = patch.get_width()
        bar_plot.text(width + 170, patch.get_y() + patch.get_height() /
                      2 + 0.2, "{}".format(int(width)), ha="center")

    plt.title("Job Offers by State")
    plt.savefig("states_counts.png")


def daily_hours():
    """Prints the percentage of each worked_hours count.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """

    for index, item in df["hours_worked"].value_counts().iteritems():

        perc = (item / total) * 100
        print("Hours:", index)
        print("Percentage:", perc)
        print("-------------------")


def create_donut():
    """Generates a donut plot from specified salary ranges.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """

    labels = ["< $4,000", "$4001.00 a $6000.00",
              "$6001.00 a $8000.00", "$8001.00 a $10,000.00", "$10,000.00 a $15,000.00", "> $15,000.00"]

    a = (len(df[df["salary"].between(
        0, 4000, inclusive=True)]) * 100) / total

    b = (len(df[df["salary"].between(
        4001, 6000, inclusive=True)]) * 100) / total

    c = (len(df[df["salary"].between(
        6001, 8000, inclusive=True)]) * 100) / total

    d = (len(df[df["salary"].between(
        8001, 10000, inclusive=True)]) * 100) / total

    e = (len(df[df["salary"].between(
        10001, 15000, inclusive=True)]) * 100) / total

    f = (len(df[df["salary"].between(
        15001, 100000, inclusive=True)]) * 100) / total

    values = [a, b, c, d, e, f]
    explode = (0, 0, 0, 0, 0, 0)  # explode a slice if required

    plt.rcParams["figure.figsize"] = [8, 8]
    plt.rcParams["figure.facecolor"] = "#282A36"
    plt.rcParams["text.color"] = "#FFFFFF"
    plt.rcParams["font.size"] = 14

    plt.pie(values, explode=explode, labels=None,
            autopct='%1.1f%%', shadow=False)

    centre_circle = plt.Circle(
        (0, 0), 0.75, color="#282A36", fc="#282A36", linewidth=0)
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)

    plt.axis('equal')
    plt.savefig("donut1.png")


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


def generate_maps(df):
    """Generates 2 maps using geopandas, one for median salaries and one for offers count.

    The shape file used for this project was downloaded from:

    https://www.arcgis.com/home/item.html?id=ac9041c51b5c49c683fbfec61dc03ba8

    """

    # First we read the shape file from its unzipped folder.
    mexico_df = geopandas.read_file("./mexicostates")

    # We will get the median salary for each state and add it into its new column.
    for item in df.groupby("state")["salary"].median().items():

        # We remove accent marks and rename Ciudad de Mexico to its former name.
        clean_name = clean_word(item[0])

        if clean_name == "Ciudad de Mexico":
            clean_name = "Distrito Federal"

        mexico_df.loc[mexico_df["ADMIN_NAME"] ==
                      clean_name, "median_salary"] = item[1]

    # Now we will get the amount of offers for each state.
    for item in df["state"].value_counts().items():
        clean_name = clean_word(item[0])

        if clean_name == "Ciudad de Mexico":
            clean_name = "Distrito Federal"

        mexico_df.loc[mexico_df["ADMIN_NAME"] ==
                      clean_name, "offers_count"] = item[1]

    plt.rcParams["figure.figsize"] = [12, 8]

    # To generate the other map you only require to change the column parameter and set another title.
    mexico_df.plot(column="median_salary", cmap="viridis", legend=True)
    plt.title("Monthly Median Salary from Job Offers (MXN)")

    plt.axis("off")
    plt.tight_layout()
    plt.savefig("map1.png")


def generate_median_by_profession(df):
    """Generates a csv file with the most popular professions.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to be plotted.

    """

    with open("medians.csv", "w", encoding="utf-8", newline="") as temp_file:
        temp_list = list()
        temp_list.append(["offer", "median_salary", "count"])

        for item, count in df["offer"].value_counts()[:].items():
            median_salary = df[df["offer"] == item]["salary"].median()
            temp_list.append([item, int(median_salary), count])

        csv.writer(temp_file).writerows(temp_list)


if __name__ == "__main__":

    main_df = pd.read_csv("data.csv", parse_dates=["date"])
    total = len(main_df)

    generate_median_by_profession(main_df)
