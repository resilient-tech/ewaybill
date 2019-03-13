from __future__ import unicode_literals

import frappe, os, json
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def make_custom_fields():
	si_ewaybill_fields = [
		{
			'fieldname': 'transporter_info',
 			'label': 'Transporter Info',
 			'fieldtype': 'Section Break',
 			'insert_after': 'terms',
 			'collapsible': 1,
 			'collapsible_depends_on': 'transporter',
 			'print_hide': 1
		},
		{
			'fieldname': 'transporter',
			'label': 'Transporter',
			'fieldtype': 'Link',
			'insert_after': 'transporter_info',
			'options': 'Supplier',
			'print_hide': 1
		},
		{
			'fieldname': 'gst_transporter_id',
			'label': 'GST Transporter ID',
			'fieldtype': 'Data',
			'insert_after': 'transporter',
			'print_hide': 1
		},
		{
			'fieldname': 'lr_no',
			'label': 'Transport Receipt No',
			'fieldtype': 'Data',
			'insert_after': 'gst_transporter_id',
			'print_hide': 1,
			'translatable': 0
		},
		{
			'fieldname': 'vehicle_no',
			'label': 'Vehicle No',
			'fieldtype': 'Data',
			'insert_after': 'lr_no',
			'print_hide': 1
		},
		{
			'fieldname': 'distance',
			'label': 'Distance (in km)',
			'fieldtype': 'Float',
			'insert_after': 'vehicle_no',
			'print_hide': 1
		},
		{
			'fieldname': 'transporter_col_break',
			'fieldtype': 'Column Break',
			'insert_after': 'distance'
		},
		{
			'fieldname': 'transporter_name',
			'label': 'Transporter Name',
			'fieldtype': 'Data',
			'insert_after': 'transporter_col_break',
			'read_only': 1,
			'print_hide': 1
		},
		{
			'fieldname': 'mode_of_transport',
			'label': 'Mode of Transport',
			'fieldtype': 'Select',
			'options': '\nRoad\nAir\nRail\nShip',
			'default': 'Road',
			'insert_after': 'transporter_name',
			'print_hide': 1
		},
		{
			'fieldname': 'lr_date',
			'label': 'Transport Receipt Date',
			'fieldtype': 'Date',
			'insert_after': 'mode_of_transport',
			'default': 'Today',
			'print_hide': 1
		},
		{
			'fieldname': 'driver_name',
			'label': 'Driver Name',
			'fieldtype': 'Data',
			'insert_after': 'lr_date',
			'print_hide': 1
		},
		{
			'fieldname': 'gst_vehicle_type',
			'label': 'GST Vehicle Type',
			'fieldtype': 'Select',
			'options': 'Regular\nOver Dimensional Cargo (ODC)',
			'depends_on': 'eval:(doc.mode_of_transport === "Road")',
			'default': 'Regular',
			'insert_after': 'driver_name',
			'print_hide': 1
		},
		{
			'fieldname': 'ewaybill',
			'label': 'e-Way Bill No.',
			'fieldtype': 'Data',
			'depends_on': 'eval:(doc.docstatus === 1)',
			'allow_on_submit': 1,
			'insert_after': 'project'
		}
	]

	custom_fields = {
		'Sales Invoice': si_ewaybill_fields,
		'Supplier': [
			{
				'fieldname': 'gst_transporter_id',
				'label': 'GST Transporter ID',
				'fieldtype': 'Data',
				'insert_after': 'supplier_type',
				'depends_on': 'eval:doc.is_transporter'
			},
			{
				"fieldname": "is_transporter",
				"fieldtype": "Check",
				"label": "Is Transporter",
				'insert_after': 'disabled'
			}
		]
	}

	create_custom_fields(custom_fields)
	create_custom_fields(custom_fields)
