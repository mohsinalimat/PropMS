from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import today
from erpnext.utilities.product import get_price

def make_sales_invoice(doc, method):
    is_grouped = frappe.db.get_value("Property Management Settings", None, "group_maintenance_job_items")
    if not is_grouped:
        is_grouped =0
    is_grouped =int(is_grouped)
    company = frappe.db.get_value("Property Management Settings", None, "company")
    if not company:
        company = frappe.db.get_single_value('Global Defaults', 'default_company')
    cost_center = frappe.db.get_value("Property", doc.property_name, "cost_center")
    submit_maintenance_invoice = frappe.db.get_value("Property Management Settings", None, "submit_maintenance_invoice")
    if not submit_maintenance_invoice:
        submit_maintenance_invoice =0
    submit_maintenance_invoice =int(submit_maintenance_invoice)
    user_remarks= "Sales invoice for Maintenance Job Card {0}".format(doc.name)

    def _make_sales_invoice(items_list = None): 
        if not len(items_list) > 0 or not doc.customer:
            return      
        invoice_doc = frappe.get_doc(dict(
            doctype = "Sales Invoice",
            customer = doc.customer,
            company = company,
            posting_date = today(),
            due_date = today(),
            ignore_pricing_rule = 1,
            items = items_list,
            update_stock = 1,
            remarks = user_remarks,
            cost_center = cost_center,
            )).insert(ignore_permissions=True)
        if invoice_doc:
            frappe.flags.ignore_account_permission = True
            if submit_maintenance_invoice == 1:
                invoice_doc.submit()
            frappe.msgprint(str("Sales invoice Created {0}".format(invoice_doc.name)))
            for item_row in doc.materials_required:
                if item_row.item and item_row.quantity and item_row.invoiced == 1 and not item_row.sales_invoice:
                    item_row.sales_invoice = invoice_doc.name
                    

    if is_grouped == 1:
        items = []
        for item_row in doc.materials_required:
            if item_row.item and item_row.quantity and item_row.material_status =="Fulfilled"and not item_row.sales_invoice:
                item_dict = dict(
                    item_code = item_row.item,
                    qty = item_row.quantity,
                    rate = item_row.rate,
                    cost_center = cost_center,
                )
                items.append(item_dict)
                item_row.invoiced = 1
        _make_sales_invoice(items)

    else :
        for item_row in doc.materials_required:
            if item_row.item and item_row.quantity and item_row.material_status =="Fulfilled"and not item_row.sales_invoice:
                items = []
                item_dict = dict(
                    item_code = item_row.item,
                    qty = item_row.quantity,
                    rate = item_row.rate,
                )
                items.append(item_dict)
                item_row.invoiced = 1
                _make_sales_invoice(items)   


@frappe.whitelist()
def get_item_rate(item,customer):
    price_list = frappe.db.get_value("Customer", customer, "default_price_list")
    customer_group = frappe.db.get_value("Customer", customer, "customer_group")
    company = frappe.db.get_single_value('Global Defaults', 'default_company')
    rate = get_price(item,price_list,customer_group,company)
    if rate:
        return rate["price_list_rate"]


@frappe.whitelist()
def get_items_group():
    property_doc = frappe.get_doc("Property Management Settings")
    items_group_list = []
    for items_group in property_doc.maintenance_item_group:
        items_group_list.append(items_group.item_group)
    return items_group_list