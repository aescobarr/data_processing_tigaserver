#!/usr/bin/env python
import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime
import config
import psycopg2
from django.utils.dateparse import parse_datetime

this_year = datetime.now().year

headers = {'Authorization': config.params['auth_token']}


for year in range(2014, this_year+1):
    print str(year)
    r = requests.get("http://" + config.params['server_url'] + "/api/all_reports/?format=json" + "&year=" + str(year), headers=headers)
    if r.status_code == 200:
        text_file = open("/home/webuser/webapps/tigaserver/static/all_reports" + str(year) + ".json", "w")
        text_file.write(r.text)
        text_file.close()
        print str(year) + ' complete'
    else:
        print 'Warning: report response status code for ' + str(year) + ' is ' + str(r.status_code)

print('Starting coverage month request')
r = requests.get("http://" + config.params['server_url']  + "/api/coverage_month/?format=json", headers=headers)
if r.status_code == 200:
    text_file = open("/home/webuser/webapps/tigaserver/static/coverage_month_data.json", "w")
    text_file.write(r.text)
    text_file.close()
else:
    print 'Warning: coverage month response status code is ' + str(r.status_code)

#open connection to database
# conn_string = "host='" + config.params['db_host'] + "' dbname='" + config.params['db_name'] + "' user='" + config.params['db_user'] + "' password='" + config.params['db_password'] + "'"
# print "Connecting to database"
# conn = psycopg2.connect(conn_string)
# cursor = conn.cursor()
# cursor.execute("DROP TABLE IF EXISTS map_aux_reports;")
# cursor.execute("CREATE TABLE map_aux_reports (id serial primary key,version_uuid character varying(36),observation_date timestamp with time zone,lon double precision,lat double precision,ref_system character varying(36),type character varying(7),breeding_site_answers character varying(100),mosquito_answers character varying(100),expert_validated boolean,expert_validation_result character varying(100),photo_url character varying(255),photo_license character varying(100),dataset_license character varying(100));")
# conn.commit()

# for year in range(2014, this_year+1):
#     print "Reading year %s json file to database" % year
#     json_data = open("/home/webuser/webapps/tigaserver/static/all_reports" + str(year) + ".json")
#     data = json.load(json_data)
#     for bit in data:
#         creation_date_str = bit['creation_time']
#         creation_date = parse_datetime(creation_date_str)
#         site_responses_str = ''
#         tiger_responses_str = ''
#         movelab_annotation_str = ''        
#         expert_validation_result = ''
#         photo_html_str = ''
#         validated = False
#         if bit['movelab_annotation'] != None and bit['movelab_annotation'] and bit['movelab_annotation'] != 'None' and bit['movelab_annotation'] != '':
#             validated = True
#             if bit['type'] == 'adult':
#                 if year == 2014:
#                     if bit['movelab_annotation']['tiger_certainty_category'] != None and bit['movelab_annotation']['tiger_certainty_category'] and bit['movelab_annotation']['tiger_certainty_category'] != 'None' and bit['movelab_annotation']['tiger_certainty_category'] != '':
#                         if bit['movelab_annotation']['tiger_certainty_category'] <= 0:                            
#                             expert_validation_result = 'none#' + str(bit['movelab_annotation']['tiger_certainty_category'])
#                         else:       
#                             expert_validation_result = 'albopictus#' + str(bit['movelab_annotation']['tiger_certainty_category'])
#                     else:
#                         validated = False
#                         expert_validation_result = 'none#none'

#                     if bit['movelab_annotation']['photo_html'] != None and bit['movelab_annotation']['photo_html'] and bit['movelab_annotation']['photo_html'] != 'None' and bit['movelab_annotation']['photo_html'] != '':
#                         photo_html_str = bit['movelab_annotation']['photo_html']
#                 else:                    
#                     if bit['movelab_annotation']['classification'] and bit['movelab_annotation']['classification'] != 'None' and bit['movelab_annotation']['classification'] != '':
#                         if bit['movelab_annotation']['classification'] == 'albopictus':
#                             expert_validation_result = bit['movelab_annotation']['classification'] + '#' + str(bit['movelab_annotation']['tiger_certainty_category'])
#                         elif bit['movelab_annotation']['classification'] == 'aegypti':
#                             expert_validation_result = bit['movelab_annotation']['classification'] + '#' + str(bit['movelab_annotation']['aegypti_certainty_category'])
#                         else:
#                             expert_validation_result = bit['movelab_annotation']['classification'] + '#' + str(bit['movelab_annotation']['score'])                    
#                     try:
#                         if bit['movelab_annotation']['photo_html'] != None and bit['movelab_annotation']['photo_html'] and bit['movelab_annotation']['photo_html'] != 'None' and bit['movelab_annotation']['photo_html'] != '':
#                             photo_html_str = bit['movelab_annotation']['photo_html']                    
#                     except KeyError:
#                         pass            
#             elif bit['type'] == 'site':
#                 expert_validation_result = 'site#' + str(bit['movelab_annotation']['site_certainty_category'])
#                 try:
#                     if bit['movelab_annotation']['photo_html'] != None and bit['movelab_annotation']['photo_html'] and bit['movelab_annotation']['photo_html'] != 'None' and bit['movelab_annotation']['photo_html'] != '':
#                         photo_html_str = bit['movelab_annotation']['photo_html']
#                 except KeyError:
#                     pass
#             else:
#                 pass        
#         if bit['site_responses'] and bit['site_responses'] != 'None' and bit['site_responses'] != '':            
#             #site_responses_str = bit['site_responses']['q1_response_new'] + '#' + bit['site_responses']['q2_response_new'] + '#' + bit['site_responses']['q3_response_new']
#             try:
#                 #site_responses_str = str(bit['site_responses']['q1_response']) + '#' + str(bit['site_responses']['q2_response']) + '#' + str(bit['site_responses']['q3_response'])                
#                 site_responses_str = str(bit['site_responses']['q1_response']) + '#' + str(bit['site_responses']['q2_response'])
#             except KeyError:
#                 pass
#             try:
#                 site_responses_str = str(bit['site_responses']['q1_response_new']) + '#' + str(bit['site_responses']['q2_response_new']) + '#' + str(bit['site_responses']['q3_response_new'])
#             except KeyError:
#                 pass
#         if bit['tiger_responses'] and bit['tiger_responses'] != 'None' and bit['tiger_responses'] != '':
#             tiger_responses_str = str(bit['tiger_responses']['q1_response']) + '#' + str(bit['tiger_responses']['q2_response']) + '#' + str(bit['tiger_responses']['q3_response'])
#         #if bit['movelab_annotation'] and bit['movelab_annotation'] != 'None' and bit['movelab_annotation'] != '':
#             #movelab_annotation_str = str(bit['movelab_annotation'])
#         cursor.execute("""INSERT INTO map_aux_reports(version_uuid, observation_date,lon,lat,ref_system,type,breeding_site_answers,mosquito_answers,expert_validated,expert_validation_result,photo_url) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);""",(bit['version_UUID'], creation_date, bit['lon'], bit['lat'],'WGS84', bit['type'], site_responses_str, tiger_responses_str, validated, expert_validation_result, photo_html_str))
# conn.commit()

# cursor.close()
# conn.close()
