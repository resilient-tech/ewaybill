# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "ewaybill"
app_title = "e-Way Bill JSON Generation"
app_publisher = "Resilient Tech"
app_description = "Functionality to generate e-Way Bill JSON for v10 Users"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@resilient.tech"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/ewaybill/css/ewaybill.css"
# app_include_js = "/assets/js/ewaybill.min.js"

# include js, css files in header of web template
# web_include_css = "/assets/ewaybill/css/ewaybill.css"
# web_include_js = "/assets/ewaybill/js/ewaybill.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Sales Invoice" : "public/js/si.js"}
doctype_list_js = {"Sales Invoice" : "public/js/si_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "ewaybill.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "ewaybill.install.before_install"
after_install = "ewaybill.custom_fields.make_custom_fields"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ewaybill.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"ewaybill.tasks.all"
# 	],
# 	"daily": [
# 		"ewaybill.tasks.daily"
# 	],
# 	"hourly": [
# 		"ewaybill.tasks.hourly"
# 	],
# 	"weekly": [
# 		"ewaybill.tasks.weekly"
# 	]
# 	"monthly": [
# 		"ewaybill.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "ewaybill.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "ewaybill.event.get_events"
# }

