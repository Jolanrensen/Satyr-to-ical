# Satyr-to-ical
Small Python script to scrape the UGent Satyr website and convert the timetable to an ics file for your calendar.

Requires python packages:
- selenium
- webdriver-manager
- pandas
- icalendar
- tabulate
- lxml
- html5lib
- BeautifulSoup4

Requires Chrome being installed (On Alpine linux
or Home Assistant Appdaemon, this means:
`apk add chromium chromium-chromedriver`)

# How to use
Pull the repo, install all `requirements.txt` with `pip`,
create a `main.py` file that has the import `from satyr_to_ical import update_ical_file_from_satyr` and call the function:
```py
update_ical_file_from_satyr(
    url={{ Satyr URL, probably "https://satyr.ugent.be/#/student" }},
    username={{ your username }},
    password={{ your password }},
    ics_path={{ where to store the ics file, like "satyr.ics" }},
    chrome_driver_path{{ optional path to where chrome/chromedriver is installed }},
)
```

If run on a server, you can automate this to run daily and if you make sure the created `ics` file is visibile to the outside world, you can subscribe your calendar to `webcal://YOUR_URL/.../your_sartir.ics`.
