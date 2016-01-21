#!/usr/bin/env python
import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime
import config

this_year = datetime.now().year

headers = {'Authorization': config.params[auth_token]}

for year in range(2014, this_year+1):
    print str(year)
    r = requests.get("http://" + config.params[server_url] + "/api/all_reports/?format=json" + "&year=" + str(year), headers=headers)
    if r.status_code == 200:
        text_file = open("/home/webuser/webapps/tigaserver/static/all_reports" + str(year) + ".json", "w")
        text_file.write(r.text)
        text_file.close()
        print str(year) + ' complete'
    else:
        print 'Warning: report response status code for ' + str(year) + ' is ' + str(r.status_code)

print('Starting coverage month request')
r = requests.get("http://" + config.params[server_url]  + "/api/coverage_month/?format=json", headers=headers)
if r.status_code == 200:
    text_file = open("/home/webuser/webapps/tigaserver/static/coverage_month_data.json", "w")
    text_file.write(r.text)
    text_file.close()
else:
    print 'Warning: coverage month response status code is ' + str(r.status_code)

