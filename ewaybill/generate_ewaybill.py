from __future__ import unicode_literals
import frappe, re, json
from frappe import _
from frappe.utils import cstr, flt, date_diff, getdate
from erpnext.regional.india import states, state_numbers
from erpnext.controllers.taxes_and_totals import get_itemised_taxable_amount


@frappe.whitelist()
def generate_ewb_json(dt, dn):
	if dt != 'Sales Invoice':
		frappe.throw(_('e-Way Bill JSON can only be generated from Sales Invoice'))

	dn = dn.split(',')

	ewaybills = []
	for doc_name in dn:
		doc = frappe.get_doc(dt, doc_name)
		if doc.docstatus != 1:
			frappe.throw(_('e-Way Bill JSON can only be generated from submitted document'))

		if doc.is_return:
			frappe.throw(_('e-Way Bill JSON cannot be generated for Sales Return as of now'))

		if doc.ewaybill:
			frappe.throw(_('e-Way Bill already exists for this document'))

		reqd_fields = ['company_gstin', 'company_address', 'customer_address',
			'shipping_address_name', 'mode_of_transport', 'distance']

		for fieldname in reqd_fields:
			if not doc.get(fieldname):
				frappe.throw(_('{} is required to generate e-Way Bill JSON'.format(
					doc.meta.get_label(fieldname)
				)))

		if len(doc.company_gstin) < 15:
			frappe.throw(_('You must be a registered supplier to generate e-Way Bill'))

		data = frappe._dict({
			"transporterId": "",
			"TotNonAdvolVal": 0,
		})

		data.userGstin = data.fromGstin = doc.company_gstin
		data.supplyType = 'O'

		if doc.invoice_type in ['Regular', 'SEZ']:
			data.subSupplyType = 1
		elif doc.invoice_type in ['Export', 'Deemed Export']:
			data.subSupplyType = 3
		else:
			frappe.throw(_('Unsupported Invoice Type for e-Way Bill JSON generation'))

		data.docType = 'INV'
		data.docDate = frappe.utils.formatdate(doc.posting_date, 'dd/mm/yyyy')

		company_address = frappe.get_doc('Address', doc.company_address)
		data.fromPincode = validate_pincode(company_address.pincode, 'Company Address')
		data.fromStateCode = data.actualFromStateCode = validate_state_code(
			company_address.gst_state_number, 'Company Address')

		billing_address = frappe.get_doc('Address', doc.customer_address)
		if not doc.billing_address_gstin or len(doc.billing_address_gstin) < 15:
			data.toGstin = 'URP'
			set_gst_state_and_state_number(billing_address)
		else:
			data.toGstin = doc.billing_address_gstin

		data.toPincode = validate_pincode(billing_address.pincode, 'Customer Address')
		data.toStateCode = validate_state_code(billing_address.gst_state_number, 'Customer Address')

		if doc.customer_address != doc.shipping_address_name:
			data.transType = 2
			shipping_address = frappe.get_doc('Address', doc.shipping_address_name)
			set_gst_state_and_state_number(shipping_address)
			data.toPincode = validate_pincode(shipping_address.pincode, 'Shipping Address')
			data.actualToStateCode = validate_state_code(shipping_address.gst_state_number, 'Shipping Address')
		else:
			data.transType = 1
			data.actualToStateCode = data.toStateCode
			shipping_address = billing_address

		data.itemList = []
		data.totalValue = doc.total
		for attr in ['cgstValue', 'sgstValue', 'igstValue', 'cessValue', 'OthValue']:
			data[attr] = 0

		gst_accounts = get_gst_accounts(doc.company, account_wise=True)
		tax_map = {
			'sgst_account': ['sgstRate', 'sgstValue'],
			'cgst_account': ['cgstRate', 'cgstValue'],
			'igst_account': ['igstRate', 'igstValue'],
			'cess_account': ['cessRate', 'cessValue']
		}
		item_data_attrs = ['sgstRate', 'cgstRate', 'igstRate', 'cessRate', 'cessNonAdvol']
		hsn_wise_charges, hsn_taxable_amount = get_itemised_tax_breakup_data(doc, account_wise=True)
		for hsn_code, taxable_amount in hsn_taxable_amount.items():
			item_data = frappe._dict()
			if not hsn_code:
				frappe.throw(_('GST HSN Code does not exist for one or more items'))
			item_data.hsnCode = int(hsn_code)
			item_data.taxableAmount = taxable_amount
			item_data.qtyUnit = ""
			for attr in item_data_attrs:
				item_data[attr] = 0

			for account, tax_detail in hsn_wise_charges.get(hsn_code, {}).items():
				account_type = gst_accounts.get(account, '')
				for tax_acc, attrs in tax_map.items():
					if account_type == tax_acc:
						item_data[attrs[0]] = tax_detail.get('tax_rate')
						data[attrs[1]] += tax_detail.get('tax_amount')
						break
				else:
					data.OthValue += tax_detail.get('tax_amount')

			data.itemList.append(item_data)

		for attr in ['sgstValue', 'cgstValue', 'igstValue', 'cessValue']:
			data[attr] = flt(data[attr], 2)

		disable_rounded = frappe.db.get_single_value('Global Defaults', 'disable_rounded_total')
		data.totInvValue = doc.grand_total if disable_rounded else doc.rounded_total

		if doc.distance > 4000:
			frappe.throw(_('Distance cannot be greater than 4000 kms'))

		data.transDistance = int(round(doc.distance))

		transport_modes = {
			'Road': 1,
			'Rail': 2,
			'Air': 3,
			'Ship': 4
		}

		vehicle_types = {
			'Regular': 'R',
			'Over Dimensional Cargo (ODC)': 'O'
		}

		data.transMode = transport_modes.get(doc.mode_of_transport)

		if doc.mode_of_transport == 'Road':
			if not doc.gst_transporter_id and not doc.vehicle_no:
				frappe.throw(_('Either GST Transporter ID or Vehicle No is required if Mode of Transport is Road'))
			if doc.vehicle_no:
				data.vehicleNo = doc.vehicle_no.replace(' ', '')
			if not doc.gst_vehicle_type:
				frappe.throw(_('Vehicle Type is required if Mode of Transport is Road'))
			else:
				data.vehicleType = vehicle_types.get(doc.gst_vehicle_type)
		else:
			if not doc.lr_no or not doc.lr_date:
				frappe.throw(_('Transport Receipt No and Date are mandatory for your chosen Mode of Transport'))

		if doc.lr_no:
			data.transDocNo = doc.lr_no

		if doc.lr_date:
			data.transDocDate = frappe.utils.formatdate(doc.lr_date, 'dd/mm/yyyy')

		if doc.gst_transporter_id:
			validate_gstin_check_digit(doc.gst_transporter_id, label='GST Transporter ID')
			data.transporterId  = doc.gst_transporter_id

		fields = {
			"/. -": {
				'docNo': doc.name,
				'fromTrdName': doc.company,
				'toTrdName': doc.customer_name,
				'transDocNo': doc.lr_no,
			},
			"@#/,&. -": {
				'fromAddr1': company_address.address_line1,
				'fromAddr2': company_address.address_line2,
				'fromPlace': company_address.city,
				'toAddr1': shipping_address.address_line1,
				'toAddr2': shipping_address.address_line2,
				'toPlace': shipping_address.city,
				'transporterName': doc.transporter_name
			}
		}

		for allowed_chars, field_map in fields.items():
			for key, value in field_map.items():
				if not value:
					data[key] = ''
				else:
					data[key] = re.sub(r'[^\w' + allowed_chars + ']', '', value)

		ewaybills.append(data)

	data = {
		'version': '1.0.1118',
		'billLists': ewaybills
	}

	frappe.local.response.filecontent = json.dumps(data, indent=4, sort_keys=True)
	frappe.local.response.type = 'download'

	if len(ewaybills) > 1:
		doc_name = 'Bulk'

	frappe.local.response.filename = '{0}_e-WayBill_Data_{1}.json'.format(doc_name, frappe.utils.random_string(5))

def validate_pincode(pincode, address):
	pin_not_found = "Pin Code doesn't exist for {}"
	incorrect_pin = "Pin Code for {} is incorrecty formatted. It must be 6 digits (without spaces)"

	if not pincode:
		frappe.throw(_(pin_not_found.format(address)))

	pincode = pincode.replace(' ', '')
	if not pincode.isdigit() or len(pincode) != 6:
		frappe.throw(_(incorrect_pin.format(address)))
	else:
		return int(pincode)

def validate_state_code(state_code, address):
	no_state_code = "GST State Code not found for {0}. Please set GST State in {0}"
	if not state_code:
		frappe.throw(_(no_state_code.format(address)))
	else:
		return int(state_code)

def get_gst_accounts(company, account_wise=False):
	gst_accounts = frappe._dict()
	gst_settings_accounts = frappe.get_all("GST Account",
		filters={"parent": "GST Settings", "company": company},
		fields=["cgst_account", "sgst_account", "igst_account", "cess_account"])

	if not gst_settings_accounts:
		frappe.throw(_("Please set GST Accounts in GST Settings"))

	for d in gst_settings_accounts:
		for acc, val in d.items():
			if not account_wise:
				gst_accounts.setdefault(acc, []).append(val)
			elif val:
				gst_accounts[val] = acc


	return gst_accounts

def set_gst_state_and_state_number(doc):
	if not doc.gst_state:
		if not doc.state:
			return
		state = doc.state.lower()
		states_lowercase = {s.lower():s for s in states}
		if state in states_lowercase:
			doc.gst_state = states_lowercase[state]
		else:
			return

	doc.gst_state_number = state_numbers[doc.gst_state]


def validate_gstin_check_digit(gstin, label='GSTIN'):
	''' Function to validate the check digit of the GSTIN.'''
	factor = 1
	total = 0
	code_point_chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
	mod = len(code_point_chars)
	input_chars = gstin[:-1]
	for char in input_chars:
		digit = factor * code_point_chars.find(char)
		digit = (digit // mod) + (digit % mod)
		total += digit
		factor = 2 if factor == 1 else 1
	if gstin[-1] != code_point_chars[((mod - (total % mod)) % mod)]:
		frappe.throw(_("Invalid {0}! The check digit validation has failed. " +
			"Please ensure you've typed the {0} correctly.".format(label)))

def get_itemised_tax(taxes, with_tax_account=False):
	itemised_tax = {}
	for tax in taxes:
		if getattr(tax, "category", None) and tax.category=="Valuation":
			continue

		item_tax_map = json.loads(tax.item_wise_tax_detail) if tax.item_wise_tax_detail else {}
		if item_tax_map:
			for item_code, tax_data in item_tax_map.items():
				itemised_tax.setdefault(item_code, frappe._dict())

				tax_rate = 0.0
				tax_amount = 0.0

				if isinstance(tax_data, list):
					tax_rate = flt(tax_data[0])
					tax_amount = flt(tax_data[1])
				else:
					tax_rate = flt(tax_data)

				itemised_tax[item_code][tax.description] = frappe._dict(dict(
					tax_rate = tax_rate,
					tax_amount = tax_amount
				))

				if with_tax_account:
					itemised_tax[item_code][tax.description].tax_account = tax.account_head

	return itemised_tax

def get_itemised_tax_breakup_data(doc, account_wise=False):
	itemised_tax = get_itemised_tax(doc.taxes, with_tax_account=account_wise)

	itemised_taxable_amount = get_itemised_taxable_amount(doc.items)

	if not frappe.get_meta(doc.doctype + " Item").has_field('gst_hsn_code'):
		return itemised_tax, itemised_taxable_amount

	item_hsn_map = frappe._dict()
	for d in doc.items:
		item_hsn_map.setdefault(d.item_code or d.item_name, d.get("gst_hsn_code"))

	hsn_tax = {}
	for item, taxes in itemised_tax.items():
		hsn_code = item_hsn_map.get(item)
		hsn_tax.setdefault(hsn_code, frappe._dict())
		for tax_desc, tax_detail in taxes.items():
			key = tax_desc
			if account_wise:
				key = tax_detail.get('tax_account')
			hsn_tax[hsn_code].setdefault(key, {"tax_rate": 0, "tax_amount": 0})
			hsn_tax[hsn_code][key]["tax_rate"] = tax_detail.get("tax_rate")
			hsn_tax[hsn_code][key]["tax_amount"] += tax_detail.get("tax_amount")

	# set taxable amount
	hsn_taxable_amount = frappe._dict()
	for item in itemised_taxable_amount:
		hsn_code = item_hsn_map.get(item)
		hsn_taxable_amount.setdefault(hsn_code, 0)
		hsn_taxable_amount[hsn_code] += itemised_taxable_amount.get(item)

	return hsn_tax, hsn_taxable_amount
