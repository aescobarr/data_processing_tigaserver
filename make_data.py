# coding=utf-8
#!/usr/bin/env python
import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime
import config
import psycopg2
from django.utils.dateparse import parse_datetime

def add_photo_to_unfiltered_sites(cursor):
    cursor.execute("""SELECT m.version_uuid,p.photo FROM map_aux_reports m,tigaserver_app_photo p WHERE p.report_id = m.version_uuid and ( private_webmap_layer='breeding_site_not_yet_filtered' or private_webmap_layer='storm_drain_water' or private_webmap_layer='storm_drain_dry' or private_webmap_layer='breeding_site_other' or private_webmap_layer='trash_layer') and n_photos > 0 and photo_url='' and p.hide=false;""")
    result = cursor.fetchall()
    last_uuid = '-1'
    for row in result:
        current_uuid = row[0]
        if current_uuid != last_uuid:
            #do stuff
            cursor.execute("""UPDATE map_aux_reports set photo_url=%s WHERE version_uuid=%s;""",('/media/' + row[1],row[0],))
        last_uuid=current_uuid;

def adjust_coarse_filter(cursor,file,webmap_layer):
    json_data = open(file)    
    data = json.load(json_data)
    for bit in data:
        version_UUID = bit["version_UUID"]
        cursor.execute("""UPDATE map_aux_reports set private_webmap_layer=%s WHERE version_uuid=%s""",(webmap_layer,version_UUID,))

def get_nota_usuari_de_report(cursor, version_UUID):
    cursor.execute("""SELECT note from tigaserver_app_report WHERE "version_UUID"=%s;""",(version_UUID,))
    result = cursor.fetchone()
    if not result is None and len(result) > 0:
        return result[0]
    return ''

def actualitza_nota_usuari(cursor, version_UUID, note):
    cursor.execute("""UPDATE map_aux_reports set note=%s WHERE version_uuid=%s;""",(note,version_UUID,))

def clean_photo_str(photo_str):
    if photo_str == '' or photo_str == 'None' or photo_str == None:
        return ''
    splitted_str = photo_str.split(' ')
    if len(splitted_str) > 0:
        str_href = splitted_str[1]
        str_href_nocomma = str_href.replace('"','')
        str_clean = str_href_nocomma.replace('href=','')
        return str_clean
    return ''

def get_storm_drain_status(questions,answers):
	index = 0
	for question in questions:
		if question.startswith(u'Does it contain stagnant water') or question.startswith(u'Contiene agua estancada') or question.startswith(u'Cont\xe9 aigua estancada') or \
			question.startswith(u'Does it have stagnant water') or question.startswith(u'\xbfContiene agua estancada') or question.startswith(u'Cont\xe9 aigua estancada'):
			if answers[index].startswith(u'Yes') or answers[index].startswith(u'S\xed') or answers[index].startswith(u'Has stagnant water') or answers[index].startswith(u'Hay agua') or answers[index].startswith(u'Hi ha aigua'):
				return 'storm_drain_water'
			elif answers[index].startswith(u'No') or answers[index].startswith(u'Does not'):
				return 'storm_drain_dry'
			else:
				return 'other'
		index = index + 1
	return 'other'

this_year = datetime.now().year

headers = {'Authorization': config.params['auth_token']}

server_url = config.params['server_url']

filenames = []

# #####################################################################################################
# This block should only be uncommented running the script locally and with pregenerated map data files
# #####################################################################################################
'''
filenames.append("/home/webuser/webapps/tigaserver/static/all_reports2014.json")
filenames.append("/home/webuser/webapps/tigaserver/static/all_reports2015.json")
filenames.append("/home/webuser/webapps/tigaserver/static/all_reports2016.json")
filenames.append("/home/webuser/webapps/tigaserver/static/all_reports2017.json")
filenames.append("/tmp/hidden_reports2014.json")
filenames.append("/tmp/hidden_reports2015.json")
filenames.append("/tmp/hidden_reports2016.json")
filenames.append("/tmp/hidden_reports2017.json")
'''

r = requests.get("http://" + config.params['server_url'] + "/api/cfa_reports/?format=json", headers=headers)
if r.status_code == 200:
    file = "/tmp/cfa.json"
    text_file = open(file, "w")
    text_file.write(r.text)
    text_file.close()
    print 'Coarse filter adults complete'

r = requests.get("http://" + config.params['server_url'] + "/api/cfs_reports/?format=json", headers=headers)
if r.status_code == 200:
    file = "/tmp/cfs.json"
    text_file = open(file, "w")
    text_file.write(r.text)
    text_file.close()
    print 'Coarse filter sites complete'

for year in range(2014, this_year+1):
    print str(year)
    r = requests.get("http://" + config.params['server_url'] + "/api/all_reports/?format=json" + "&year=" + str(year), headers=headers)
    if r.status_code == 200:
        file = "/home/webuser/webapps/tigaserver/static/all_reports" + str(year) + ".json"
        text_file = open(file, "w")
        text_file.write(r.text)
        text_file.close()
        print str(year) + ' complete'
        filenames.append(file)
    else:
        print 'Warning: report response status code for ' + str(year) + ' is ' + str(r.status_code)

for year in range(2014, this_year+1):
    print str(year)
    r = requests.get("http://" + config.params['server_url'] + "/api/hidden_reports/?format=json" + "&year=" + str(year), headers=headers)
    if r.status_code == 200:
        file = "/tmp/hidden_reports" + str(year) + ".json"
        text_file = open(file, "w")
        text_file.write(r.text)
        text_file.close()
        print str(year) + ' complete'
        filenames.append(file)
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

conn_string = "host='" + config.params['db_host'] + "' dbname='" + config.params['db_name'] + "' user='" + config.params['db_user'] + "' password='" + config.params['db_password'] + "'"
print "Connecting to database"
conn = psycopg2.connect(conn_string)
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS map_aux_reports CASCADE;")
cursor.execute("CREATE TABLE map_aux_reports (id serial primary key,version_uuid character varying(36), "\
	"observation_date timestamp with time zone,lon double precision,lat double precision,ref_system character varying(36),"\
	"type character varying(7),breeding_site_answers character varying(100),mosquito_answers character varying(100),"\
	"expert_validated boolean,expert_validation_result character varying(100),simplified_expert_validation_result character varying(100),"\
	"site_cat integer, storm_drain_status character varying(50),edited_user_notes character varying(4000), "\
	"photo_url character varying(255),photo_license character varying(100),dataset_license character varying(100), "\
	"single_report_map_url character varying(255), n_photos integer, visible boolean, final_expert_status integer, note text, "\
	"private_webmap_layer character varying(255), "\
	"t_q_1 character varying(255), t_q_2 character varying(255), t_q_3 character varying(255), "\
	"t_a_1 character varying(255), t_a_2 character varying(255), t_a_3 character varying(255), "\
	"s_q_1 character varying(255), s_q_2 character varying(255), s_q_3 character varying(255), s_q_4 character varying(255),"\
	"s_a_1 character varying(255), s_a_2 character varying(255), s_a_3 character varying(255), s_a_4 character varying(255)"\
	");")
conn.commit()

#for year in range(2014, this_year+1):
for file in filenames:
    print "Writing file %s  to database" % file
    json_data = open(file)
    data = json.load(json_data)
    for bit in data:        
        creation_date_str = bit['creation_time']
        creation_date = parse_datetime(creation_date_str)
        site_responses_str = ''
        tiger_responses_str = ''
        movelab_annotation_str = ''
        edited_user_notes = ''
        expert_validation_result = 'none#none'
        simplified_expert_validation_result = 'nosesabe'
        single_report_map_url = ''
        storm_drain_status = ''
        t_q_1, t_q_2, t_q_3 = '','',''
        tiger_questions = [t_q_1, t_q_2, t_q_3]
        t_a_1, t_a_2, t_a_3 = '','',''
        tiger_answers = [t_a_1, t_a_2, t_a_3]
        s_q_1, s_q_2, s_q_3, s_q_4 = '','','',''
        site_questions = [s_q_1, s_q_2, s_q_3, s_q_4]
        s_a_1, s_a_2, s_a_3, s_a_4 = '','','',''
        site_answers = [s_a_1, s_a_2, s_a_3, s_a_4]
        #new_storm_drain_status = ''
        photo_html_str = ''

        if bit['tiger_responses_text'] is not None:
            index_t = 0
            for key in bit['tiger_responses_text'].keys():
                tiger_questions[index_t] = key
                tiger_answers[index_t] = bit['tiger_responses_text'][key]
                index_t = index_t+1
        if bit['site_responses_text'] is not None:
            index_s = 0
            for key in bit['site_responses_text'].keys():
                site_questions[index_s] = key
                site_answers[index_s] = bit['site_responses_text'][key]
                index_s = index_s+1

        validated = False                
        if bit['movelab_annotation'] != None and bit['movelab_annotation'] and bit['movelab_annotation'] != 'None' and bit['movelab_annotation'] != '':
            validated = True
            if bit['type'] == 'adult':                
                if file.find("2014") >= 0:
                    if bit['movelab_annotation']['tiger_certainty_category'] != None and bit['movelab_annotation']['tiger_certainty_category'] and bit['movelab_annotation']['tiger_certainty_category'] != 'None' and bit['movelab_annotation']['tiger_certainty_category'] != '':
                        if bit['movelab_annotation']['tiger_certainty_category'] <= 0:                            
                            expert_validation_result = 'none#' + str(bit['movelab_annotation']['tiger_certainty_category'])
                        else:       
                            expert_validation_result = 'albopictus#' + str(bit['movelab_annotation']['tiger_certainty_category'])
                    else:
                        validated = False
                        expert_validation_result = 'none#none'

		    try:
                        if bit['movelab_annotation']['photo_html'] != None and bit['movelab_annotation']['photo_html'] and bit['movelab_annotation']['photo_html'] != 'None' and bit['movelab_annotation']['photo_html'] != '':
                            photo_html_str = clean_photo_str(bit['movelab_annotation']['photo_html'])
                    except KeyError:
                        pass
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
                            photo_html_str = clean_photo_str(bit['movelab_annotation']['photo_html'])
                    except KeyError:
                        pass            
            elif bit['type'] == 'site':
                expert_validation_result = 'site#' + str(bit['movelab_annotation']['site_certainty_category'])
                try:
                    if bit['movelab_annotation']['photo_html'] != None and bit['movelab_annotation']['photo_html'] and bit['movelab_annotation']['photo_html'] != 'None' and bit['movelab_annotation']['photo_html'] != '':
                        photo_html_str = clean_photo_str(bit['movelab_annotation']['photo_html'])
                except KeyError:
                    pass
            else:
                pass
            if bit['movelab_annotation']['edited_user_notes'] != None and bit['movelab_annotation']['edited_user_notes'] and bit['movelab_annotation']['edited_user_notes'] != 'None' and bit['movelab_annotation']['edited_user_notes'] != '':
                edited_user_notes = bit['movelab_annotation']['edited_user_notes']
        if bit['site_responses'] and bit['site_responses'] != 'None' and bit['site_responses'] != '':                        
            try:                
                site_responses_str = str(bit['site_responses']['q1_response']) + '#' + str(bit['site_responses']['q2_response'])
            except KeyError:
                pass
            try:
                site_responses_str = str(bit['site_responses']['q1_response_new']) + '#' + str(bit['site_responses']['q2_response_new']) + '#' + str(bit['site_responses']['q3_response_new'])
            except KeyError:
                pass        
        if bit['tiger_responses'] and bit['tiger_responses'] is not None and bit['tiger_responses'] != 'None' and bit['tiger_responses'] != '':
            try:
                tiger_responses_str = str(bit['tiger_responses']['q1_response']) + '#' + str(bit['tiger_responses']['q2_response']) + '#' + str(bit['tiger_responses']['q3_response'])
            except KeyError:
                print "Error evaluating responses " 
                print bit['tiger_responses']
                tiger_responses_str = "0#0#" + str(bit['tiger_responses']['q3_response'])

        if expert_validation_result != '':
            if expert_validation_result == 'albopictus#1' or expert_validation_result == 'albopictus#2':
                simplified_expert_validation_result = 'albopictus'
            elif expert_validation_result == 'aegypti#1' or expert_validation_result == 'aegypti#2':
                simplified_expert_validation_result = 'aegypti'            
            elif expert_validation_result == 'albopictus#-1' or expert_validation_result == 'albopictus#-2' or expert_validation_result == 'aegypti#-1' or expert_validation_result == 'aegypti#-2' or expert_validation_result == 'none#-1' or expert_validation_result == 'none#-2':
                simplified_expert_validation_result = 'noseparece'            
            elif expert_validation_result == 'albopictus#0' or expert_validation_result == 'aegypti#0' or expert_validation_result == 'none#0' or expert_validation_result == 'none#none':
                simplified_expert_validation_result = 'nosesabe'
            elif expert_validation_result.startswith('site#'):
                simplified_expert_validation_result = 'site'

        if simplified_expert_validation_result != '' and simplified_expert_validation_result == 'site':
            if bit['site_cat'] != 0:
                storm_drain_status = 'other'                
                simplified_expert_validation_result = simplified_expert_validation_result + "#" + storm_drain_status
            else:
                # if site_responses_str == '':
                #     storm_drain_status = 'other'                    
                #     simplified_expert_validation_result = simplified_expert_validation_result + "#" + storm_drain_status
                # else:
                #     site_responses_l = site_responses_str.split('#')                    
                if bit['site_responses_text'] is not None:
                    storm_drain_status = get_storm_drain_status(site_questions, site_answers)
                else:
                    storm_drain_status = 'other'

        single_report_map_url = 'http://' + server_url + '/es/single_report_map/' + bit['version_UUID']        

        
        #kill conditions
        if bit['latest_version'] == True:
            cursor.execute("""INSERT INTO map_aux_reports(version_uuid, observation_date,lon,lat,ref_system,type,breeding_site_answers,mosquito_answers,expert_validated,expert_validation_result,simplified_expert_validation_result,site_cat,storm_drain_status,edited_user_notes,photo_url,single_report_map_url,n_photos,visible,final_expert_status,t_q_1, t_q_2, t_q_3, t_a_1, t_a_2, t_a_3, s_q_1, s_q_2, s_q_3, s_q_4, s_a_1, s_a_2, s_a_3, s_a_4) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);""",(bit['version_UUID'], creation_date, bit['lon'], bit['lat'],'WGS84', bit['type'], site_responses_str, tiger_responses_str, validated, expert_validation_result, simplified_expert_validation_result,bit['site_cat'],storm_drain_status, edited_user_notes, photo_html_str, single_report_map_url,bit['n_photos'],bit['visible'],bit['final_expert_status_text'],tiger_questions[0], tiger_questions[1], tiger_questions[2], tiger_answers[0], tiger_answers[1], tiger_answers[2], site_questions[0], site_questions[1], site_questions[2], site_questions[3], site_answers[0], site_answers[1], site_answers[2], site_answers[3]))
            note = get_nota_usuari_de_report(cursor,bit['version_UUID'])
            actualitza_nota_usuari(cursor, bit['version_UUID'], note)        
            conn.commit()

print "Updating database"
#special points -> site#-4 are auto validated
cursor.execute("""UPDATE map_aux_reports set expert_validation_result = 'site#-4' where version_uuid in (select report_id from tigacrafting_expertreportannotation where site_certainty_notes='auto');""")
#end of special classification for 2014 sites
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='mosquito_tiger_confirmed' where type='adult' and expert_validated=True and expert_validation_result='albopictus#2' and n_photos > 0 and final_expert_status=1;""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='mosquito_tiger_probable' where type='adult' and expert_validated=True and expert_validation_result='albopictus#1' and n_photos > 0 and final_expert_status=1;""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='yellow_fever_confirmed' where type='adult' and expert_validated=True and expert_validation_result='aegypti#2' and n_photos > 0 and final_expert_status=1;""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='yellow_fever_probable' where type='adult' and expert_validated=True and expert_validation_result='aegypti#1' and n_photos > 0 and final_expert_status=1;""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='other_species' where type='adult' and expert_validated=True and (expert_validation_result='none#-1' or expert_validation_result='none#-2') and n_photos > 0 and final_expert_status=1;""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='unidentified' where (type='adult' and n_photos = 0) or (type='adult' and expert_validated=True and expert_validation_result='none#0' and n_photos > 0 and final_expert_status=1);""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='not_yet_validated' where type='adult' and expert_validated=False and n_photos > 0 and visible=True;""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='storm_drain_water' where type='site' and expert_validated=True and ( expert_validation_result='site#1' or expert_validation_result='site#2' or expert_validation_result='site#-4') and storm_drain_status='storm_drain_water'  and final_expert_status=1;""")
#old
#cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='storm_drain_dry' where type='site' and expert_validated=True and ( expert_validation_result='site#0' or expert_validation_result='site#1' or expert_validation_result='site#2'  or expert_validation_result='site#-4') and storm_drain_status='storm_drain_dry' and final_expert_status=1;""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='storm_drain_dry' where type='site' and expert_validated=True and ( expert_validation_result='site#0' or expert_validation_result='site#-4') and storm_drain_status='storm_drain_dry' and final_expert_status=1;""")
#Move site#0 to breeding_site_other
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='breeding_site_other' where type='site' and expert_validated=True and ( expert_validation_result='site#0' or expert_validation_result='site#1' or expert_validation_result='site#2') and storm_drain_status='other' and final_expert_status=1;""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='breeding_site_not_yet_filtered' where type='site' and expert_validated=False;""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='trash_layer' where ( visible = False and final_expert_status<>0 ) or (expert_validated = True and (expert_validation_result='none#-3' or expert_validation_result='site#-3' or expert_validation_result='site#0' or expert_validation_result='none#none') and (final_expert_status = 1 or final_expert_status = -1)) or (type='site' and expert_validated=True and (expert_validation_result='site#-2' or expert_validation_result='site#-1') and final_expert_status = 0);""")
#Move site#0 to breeding_site_other
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='breeding_site_other' where expert_validation_result = 'site#-4' and private_webmap_layer IS NULL;""")
#we remove unclassified points from 2014 -> go to trash_layer
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='trash_layer' where private_webmap_layer='not_yet_validated' and to_char(observation_date,'YYYY')='2014';""")
# Currently 3 points - in this case the user says it's a dry storm drain while the expert says there's water. We lean toward the expert
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='storm_drain_water' where private_webmap_layer IS NULL and expert_validation_result = 'site#1';""")
#add photos to unfiltered sites. They don't have photo because there is no movelab_annotation
#special classification for 2014 sites
#2014 auto-validated sites don't have movelab_annotation, therefore they are always labeled as expert_validated = false
#they have to be manually classified in storm drain (water/dry) and other manually
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='storm_drain_water' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat = 0 and expert_validated = FALSE and ((s_q_1 = 'Tipo de lugar de cría' or s_q_1 = 'Type of breeding site') and (((s_q_1 = 'Tipo de lugar de cría' or s_q_1 = 'Type of breeding site') and (s_a_1 = 'Sumideros' or s_a_1 = 'Storm drain')) or ((s_q_2 = '¿Contiene agua estancada?' or s_q_2 = 'Does it have stagnant water inside?') and (s_a_2 = 'Sí' or s_a_2 = 'Yes'))));""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='storm_drain_dry' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat = 0 and expert_validated = FALSE and (((s_q_1 = 'Tipo de lugar de cría' or s_q_1 = 'Type of breeding site') and (s_a_1 = 'Sumideros' or s_a_1 = 'Storm drain')) or ((s_q_2 = '¿Contiene agua estancada?' or s_q_2 = 'Does it have stagnant water inside?') and s_a_2 = 'No'));""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='storm_drain_water' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat = 0 and expert_validated = FALSE and (((s_q_3 = 'Tipo de lugar de cría' or s_q_3 = 'Type of breeding site') and (s_a_3 = 'Sumideros' or s_a_3 = 'Storm drain')) or ((s_q_2 = '¿Contiene agua estancada?' or s_q_2 = 'Does it have stagnant water inside?') and (s_a_2 = 'Sí' or s_a_2 = 'Yes')));""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='storm_drain_dry' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat = 0 and expert_validated = FALSE and (((s_q_3 = 'Tipo de lugar de cría' or s_q_3 = 'Type of breeding site') and (s_a_3 = 'Sumideros' or s_a_3 = 'Storm drain')) or ((s_q_2 = '¿Contiene agua estancada?' or s_q_2 = 'Does it have stagnant water inside?') and s_a_2 = 'No'));""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='storm_drain_water' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat = 0 and expert_validated = FALSE and (s_q_3 = 'Selecciona lloc de cria' and s_a_3 = 'Embornals' and s_q_1 = 'Conté aigua estancada?' and s_a_1 = 'Sí');""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='storm_drain_dry' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat = 0 and expert_validated = FALSE and (s_q_3 = 'Selecciona lloc de cria' and s_a_3 = 'Embornals' and s_q_1 = 'Conté aigua estancada?' and s_a_1 = 'No');""")
cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='breeding_site_other' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat <> 0 and expert_validated = FALSE;""")
add_photo_to_unfiltered_sites(cursor)

print "Adjusting coarse filter adults"
adjust_coarse_filter(cursor,"/tmp/cfa.json","not_yet_validated")
print "Adjusting coarse filter sites"
adjust_coarse_filter(cursor,"/tmp/cfs.json","breeding_site_not_yet_filtered")

#regenerate map view (drop table destroys it)
print "Regenerating views"
cursor.execute("""CREATE MATERIALIZED VIEW reports_map_data AS WITH validated_data AS (SELECT map_aux_reports.private_webmap_layer AS category,map_aux_reports.id,map_aux_reports.observation_date,map_aux_reports.lat,map_aux_reports.lon,map_aux_reports.expert_validation_result FROM map_aux_reports WHERE map_aux_reports.final_expert_status <> 0 AND map_aux_reports.lon IS NOT NULL AND map_aux_reports.lat IS NOT NULL AND map_aux_reports.lat <> (-1)::double precision AND map_aux_reports.lon <> (-1)::double precision) SELECT foo2.id,foo2.c,foo2.expert_validation_result,foo2.category,foo2.month,st_x(foo2.geom) AS lon,st_y(foo2.geom) AS lat,2 AS geohashlevel,st_setsrid(foo2.geom, 4326) AS geom FROM ( SELECT count(*) AS c,validated_data.category,validated_data.expert_validation_result,to_char(validated_data.observation_date, 'YYYYMM'::text) AS month,CASE WHEN count(*)::integer = 1 THEN st_setsrid(st_makepoint(min(validated_data.lon), min(validated_data.lat)), 4326) ELSE st_centroid(st_geomfromgeohash(st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 2))) END AS geom, CASE WHEN count(*)::integer = 1 THEN string_agg(validated_data.id::character varying::text, ','::text)::integer ELSE NULL::integer END AS id FROM validated_data GROUP BY validated_data.category, st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 2), to_char(validated_data.observation_date, 'YYYYMM'::text), validated_data.expert_validation_result) foo2 UNION SELECT foo3.id,foo3.c,foo3.expert_validation_result,foo3.category,foo3.month,st_x(foo3.geom) AS lon,st_y(foo3.geom) AS lat,3 AS geohashlevel,st_setsrid(foo3.geom, 4326) AS geom FROM ( SELECT count(*) AS c,validated_data.category,validated_data.expert_validation_result,to_char(validated_data.observation_date, 'YYYYMM'::text) AS month,CASE WHEN count(*)::integer = 1 THEN st_setsrid(st_makepoint(min(validated_data.lon), min(validated_data.lat)), 4326) ELSE st_centroid(st_geomfromgeohash(st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 3))) END AS geom, CASE WHEN count(*)::integer = 1 THEN string_agg(validated_data.id::character varying::text, ','::text)::integer ELSE NULL::integer END AS id FROM validated_data GROUP BY validated_data.category, st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 3), to_char(validated_data.observation_date, 'YYYYMM'::text), validated_data.expert_validation_result) foo3 UNION SELECT foo4.id,foo4.c,foo4.expert_validation_result,foo4.category,foo4.month,st_x(foo4.geom) AS lon,st_y(foo4.geom) AS lat,4 AS geohashlevel,st_setsrid(foo4.geom, 4326) AS geom FROM ( SELECT count(*) AS c, validated_data.category, validated_data.expert_validation_result, to_char(validated_data.observation_date, 'YYYYMM'::text) AS month, CASE WHEN count(*)::integer = 1 THEN st_setsrid(st_makepoint(min(validated_data.lon), min(validated_data.lat)), 4326) ELSE st_centroid(st_geomfromgeohash(st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 4))) END AS geom, CASE WHEN count(*)::integer = 1 THEN string_agg(validated_data.id::character varying::text, ','::text)::integer ELSE NULL::integer END AS id FROM validated_data GROUP BY validated_data.category, st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 4), to_char(validated_data.observation_date, 'YYYYMM'::text), validated_data.expert_validation_result) foo4 UNION SELECT foo5.id,foo5.c,foo5.expert_validation_result,foo5.category,foo5.month,st_x(foo5.geom) AS lon,st_y(foo5.geom) AS lat,5 AS geohashlevel,st_setsrid(foo5.geom, 4326) AS geom FROM ( SELECT count(*) AS c, validated_data.category,validated_data.expert_validation_result,to_char(validated_data.observation_date, 'YYYYMM'::text) AS month, CASE WHEN count(*)::integer = 1 THEN st_setsrid(st_makepoint(min(validated_data.lon), min(validated_data.lat)), 4326) ELSE st_centroid(st_geomfromgeohash(st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 5))) END AS geom, CASE WHEN count(*)::integer = 1 THEN string_agg(validated_data.id::character varying::text, ','::text)::integer ELSE NULL::integer END AS id FROM validated_data GROUP BY validated_data.category, st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 5), to_char(validated_data.observation_date, 'YYYYMM'::text), validated_data.expert_validation_result) foo5 UNION SELECT foo7.id, foo7.c,foo7.expert_validation_result,foo7.category,foo7.month,st_x(foo7.geom) AS lon,st_y(foo7.geom) AS lat,7 AS geohashlevel,st_setsrid(foo7.geom, 4326) AS geom FROM ( SELECT count(*) AS c, validated_data.category,validated_data.expert_validation_result,to_char(validated_data.observation_date, 'YYYYMM'::text) AS month, CASE WHEN count(*)::integer = 1 THEN st_setsrid(st_makepoint(min(validated_data.lon), min(validated_data.lat)), 4326) ELSE st_centroid(st_geomfromgeohash(st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 7))) END AS geom, CASE WHEN count(*)::integer = 1 THEN string_agg(validated_data.id::character varying::text, ','::text)::integer ELSE NULL::integer END AS id FROM validated_data GROUP BY validated_data.category, st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 7), to_char(validated_data.observation_date, 'YYYYMM'::text), validated_data.expert_validation_result) foo7 UNION SELECT foo8.id,foo8.c,foo8.expert_validation_result,foo8.category,foo8.month,foo8.lon,foo8.lat,8 AS geohashlevel,st_setsrid(st_makepoint(foo8.lon, foo8.lat), 4326) AS geom FROM ( SELECT 1 AS c,validated_data.category,validated_data.expert_validation_result,to_char(validated_data.observation_date, 'YYYYMM'::text) AS month,validated_data.lon,validated_data.lat,validated_data.id FROM validated_data) foo8 ORDER BY 7 WITH DATA;""")

conn.commit()

cursor.close()
conn.close()
