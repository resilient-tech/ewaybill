frappe.ui.form.on("Sales Invoice", {
	setup: function(frm) {
		frm.set_query('transporter', function() {
			return {
				filters: {
					'is_transporter': 1
				}
			};
		});

		frm.set_query('driver', function(doc) {
			return {
				filters: {
					'transporter': doc.transporter
				}
			};
		});

		frm.add_fetch('transporter', 'gst_transporter_id', 'gst_transporter_id');
		frm.add_fetch('transporter', 'name', 'transporter_name');
	},

	refresh: function(frm) {
		if(frm.doc.docstatus == 1 && !frm.is_dirty()
			&& !frm.doc.is_return && !frm.doc.ewaybill) {

			frm.add_custom_button('Generate e-Way Bill JSON', () => {
				var w = window.open(
					frappe.urllib.get_full_url(
						"/api/method/ewaybill.generate_ewaybill.generate_ewb_json?"
						+ "dt=" + encodeURIComponent(frm.doc.doctype)
						+ "&dn=" + encodeURIComponent(frm.doc.name)
					)
				);
				if (!w) {
					frappe.msgprint(__("Please enable pop-ups")); return;
				}
			});
		}
	}
});