# coding=utf-8
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE","tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import datetime
from django.db.models import Count
from tigaserver_app.models import Report
from django.contrib.auth.models import User
from tigacrafting.models import ExpertReportAnnotation
from tigaserver_app.models import ReportResponse
from django.db.models import Q

#validation user is super_movelab
auto_validation_user = User.objects.get(pk=24)

reports_imbornal = ReportResponse.objects.filter( Q(question='Selecciona lloc de cria',answer='Embornals') | Q(question='Tipo de lugar de cría', answer='Sumidero o imbornal') | Q(question='Type of breeding site', answer='Storm drain')).exclude(report__creation_time__year=2014).values('report').distinct()
new_reports_unfiltered_sites = Report.objects.exclude(creation_time__year=2014).exclude(type='adult').filter(version_UUID__in=reports_imbornal).exclude(note__icontains='#345').exclude(photos=None).exclude(hidden=True).annotate(n_annotations=Count('expert_report_annotations')).filter(n_annotations=0).order_by('-server_upload_time')

now = datetime.datetime.now()
for report in new_reports_unfiltered_sites:
	naive = report.server_upload_time.replace(tzinfo=None)
	elapsed_days = (now-naive).days
	if elapsed_days > 3:		
		print(report.version_UUID)
		new_annotation = ExpertReportAnnotation(report=report, user=auto_validation_user)
		new_annotation.site_certainty_notes = 'auto'
		new_annotation.validation_complete = True
		new_annotation.revise = True
		new_annotation.save()