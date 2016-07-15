import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime
import config
from django.utils.dateparse import parse_datetime
import csv

year = 2016

headers = {'Authorization': config.params['auth_token']}

BCN_BB = {'min_lat': 41.321049, 'min_lon': 2.052380, 'max_lat': 41.468609, 'max_lon': 2.225610}

def is_in_bcn(bit):
	f_lon = float(bit['lon'])
	f_lat = float(bit['lat'])
	check_lat = BCN_BB['min_lat'] <= f_lat and f_lat <= BCN_BB['max_lat']
	check_lon = BCN_BB['min_lon'] <= f_lon and f_lon <= BCN_BB['max_lon']
	return check_lat and check_lon

print "Reading year %s json file to database" % year
json_data = open("/home/webuser/webapps/tigaserver/static/all_reports" + str(year) + ".json")
csv_file = open("data_ASPB.csv","wb")
csv_writer = csv.writer(csv_file,delimiter=';')
csv_writer.writerow(['version_UUID','creation_date','lon', 'lat','ref_sys','type','site_response_1','site_response_2','site_response_1_new','site_response_2_new','site_response_3_new', 'tiger_response_1','tiger_response_2','tiger_response_3','validated','expert_validation_result','map_url'])
data = json.load(json_data)
for bit in data:
    creation_date_str = bit['creation_time']
    creation_date = parse_datetime(creation_date_str)
    site_responses_str = ''
    tiger_responses_str = ''
    movelab_annotation_str = ''        
    expert_validation_result = ''
    photo_html_str = ''
    tiger_response_1 = ''
    tiger_response_2 = ''
    tiger_response_3 = ''
    site_response_1_new = ''
    site_response_2_new = ''
    site_response_3_new = ''
    site_response_1 = ''
    site_response_2 = ''
    map_url = ''
    validated = False
    if is_in_bcn(bit):
	    if bit['movelab_annotation'] != None and bit['movelab_annotation'] and bit['movelab_annotation'] != 'None' and bit['movelab_annotation'] != '':
	        validated = True
	        if bit['type'] == 'adult':
	            if year == 2014:
	                if bit['movelab_annotation']['tiger_certainty_category'] != None and bit['movelab_annotation']['tiger_certainty_category'] and bit['movelab_annotation']['tiger_certainty_category'] != 'None' and bit['movelab_annotation']['tiger_certainty_category'] != '':
	                    if bit['movelab_annotation']['tiger_certainty_category'] <= 0:                            
	                        expert_validation_result = 'none#' + str(bit['movelab_annotation']['tiger_certainty_category'])
	                    else:       
	                        expert_validation_result = 'albopictus#' + str(bit['movelab_annotation']['tiger_certainty_category'])
	                else:
	                    validated = False
	                    expert_validation_result = 'none#none'

	                if bit['movelab_annotation']['photo_html'] != None and bit['movelab_annotation']['photo_html'] and bit['movelab_annotation']['photo_html'] != 'None' and bit['movelab_annotation']['photo_html'] != '':
	                    photo_html_str = bit['movelab_annotation']['photo_html']
	            else:                    
	                if bit['movelab_annotation']['classification'] and bit['movelab_annotation']['classification'] != 'None' and bit['movelab_annotation']['classification'] != '':
	                    if bit['movelab_annotation']['classification'] == 'albopictus':
	                        expert_validation_result = bit['movelab_annotation']['classification'] + '#' + str(bit['movelab_annotation']['tiger_certainty_category'])
	                    elif bit['movelab_annotation']['classification'] == 'aegypti':
	                        expert_validation_result = bit['movelab_annotation']['classification'] + '#' + str(bit['movelab_annotation']['aegypti_certainty_category'])
	                    else:
	                        expert_validation_result = bit['movelab_annotation']['classification'] + '#' + str(bit['movelab_annotation']['score'])                    
	                try:
	                    if bit['movelab_annotation']['photo_html'] != None and bit['movelab_annotation']['photo_html'] and bit['movelab_annotation']['photo_html'] != 'None' and bit['movelab_annotation']['photo_html'] != '':
	                        photo_html_str = bit['movelab_annotation']['photo_html']                    
	                except KeyError:
	                    pass            
	        elif bit['type'] == 'site':
	            expert_validation_result = 'site#' + str(bit['movelab_annotation']['site_certainty_category'])
	            try:
	                if bit['movelab_annotation']['photo_html'] != None and bit['movelab_annotation']['photo_html'] and bit['movelab_annotation']['photo_html'] != 'None' and bit['movelab_annotation']['photo_html'] != '':
	                    photo_html_str = bit['movelab_annotation']['photo_html']
	            except KeyError:
	                pass
	        else:
	            pass        
	    if bit['site_responses'] and bit['site_responses'] != 'None' and bit['site_responses'] != '':            
	        try:            
	            site_responses_str = str(bit['site_responses']['q1_response']) + '#' + str(bit['site_responses']['q2_response'])
	            site_response_1 = 'ns' if bit['site_responses']['q1_response'] == 0 else ('si' if bit['site_responses']['q1_response'] == 1 else 'no')
	            site_response_2 = 'ns' if bit['site_responses']['q2_response'] == 0 else ('si' if bit['site_responses']['q2_response'] == 1 else 'no')
	        except KeyError:
	            pass
	        try:
	            site_responses_str = str(bit['site_responses']['q1_response_new']) + '#' + str(bit['site_responses']['q2_response_new']) + '#' + str(bit['site_responses']['q3_response_new'])
	            site_response_1_new = 'no' if bit['site_responses']['q1_response_new'] == -1 else 'si'
	            site_response_2_new = 'no' if bit['site_responses']['q2_response_new'] == -1 else 'si'
	            site_response_3_new = 'no' if bit['site_responses']['q3_response_new'] == -1 else 'si'
	        except KeyError:
	            pass
	    if bit['tiger_responses'] and bit['tiger_responses'] != 'None' and bit['tiger_responses'] != '':
	        tiger_responses_str = str(bit['tiger_responses']['q1_response']) + '#' + str(bit['tiger_responses']['q2_response']) + '#' + str(bit['tiger_responses']['q3_response'])
	        tiger_response_1 = 'ns' if bit['tiger_responses']['q1_response'] == 0 else ('si' if bit['tiger_responses']['q1_response'] == 1 else 'no')
	        tiger_response_2 = 'ns' if bit['tiger_responses']['q2_response'] == 0 else ('si' if bit['tiger_responses']['q2_response'] == 1 else 'no')
	        tiger_response_3 = 'ns' if bit['tiger_responses']['q3_response'] == 0 else ('si' if bit['tiger_responses']['q3_response'] == 1 else 'no')
	    map_url = "http://" + config.params['server_url'] + "/single_report_map/" + bit['version_UUID']
	    csv_writer.writerow([bit['version_UUID'],creation_date,bit['lon'], bit['lat'],'WGS84',bit['type'],site_response_1,site_response_2,site_response_1_new,site_response_2_new,site_response_3_new,tiger_response_1,tiger_response_2,tiger_response_3,validated,expert_validation_result,map_url])