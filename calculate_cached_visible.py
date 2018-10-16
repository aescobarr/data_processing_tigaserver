# !/usr/bin/env python

# This is a process which populates the report field called cached_visible. It evaluates the value of show_on_map for each report on the app except for:
# - 2014 reports --> These are always show_on_map = True
# - Reports from current year --> These are considered dynamic data and subject to revision, so show_on_map is calculated dynamically

from tigaserver_app.models import Report
from tigacrafting.models import ExpertReportAnnotation
from datetime import datetime

all_reports = Report.objects.all()
this_year = datetime.now().year

for report in all_reports:
  if report.creation_time.year < this_year and report.creation_time.year != 2014:
    show_on_map = (not report.photos.all().exists()) or ((ExpertReportAnnotation.objects.filter(report=report, user__groups__name='expert', validation_complete=True).count() >= 3 or ExpertReportAnnotation.objects.filter(report=report, user__groups__name='superexpert', validation_complete=True, revise=True).exists()) and report.get_final_expert_status() == 1)
    report.cached_visible = show_on_map
    report.save()