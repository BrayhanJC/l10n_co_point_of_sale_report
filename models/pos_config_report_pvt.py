# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    Autor: Brayhan Andres Jaramillo Castaño
#    Correo: brayhanjaramillo@hotmail.com
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

import logging
from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)

import xlsxwriter
#from io import StringIO
from io import BytesIO
import base64

import time
from datetime import datetime, timedelta, date
import sys


class PosConfigReportPDV(models.TransientModel):
	
	_name = 'pos.config_report_pvt'

	pvt_ids = fields.Many2many(comodel_name='pos.config', relation='rel_config_report_pos_config', column1='pos_config_id', column2='pos_report_id', string='Tienda')
	date_begin = fields.Datetime(string="Fecha Inicio")
	date_end = fields.Datetime(string="Fecha Fin", default=lambda self: fields.datetime.now())
	user_ids = fields.Many2many(comodel_name='res.users', relation='rel_config_report_pvt_user', column1='user_id', column2='config_report_id', string='Users')
	filename = fields.Char('Nombre Archivo')
	document = fields.Binary(string = 'Descargar Excel')


	def load_information_report_pvt(self):
		"""
			Funcion que nos permite ejecutar una consulta para eliminar y crear el reporte del punto de venta
		"""
		domain = []
		#model_pos_config = self.env['pos.config']
		model_pos_order = self.env['pos.order']
		model_pos_sesion = self.env['pos.session']
		model_pos_report_pvt = self.env['pos.report_pvt']


		user_ids = ""
		if self.user_ids:
			for x in self.user_ids:
				user_ids+= str(x.id) + ','
			user_ids = user_ids[:len(user_ids)-1]
		

		pvt_ids = ""
		if self.pvt_ids:
			#verificando que sesiones tienen el punto de venta seleccionado
			pos_session_ids = model_pos_sesion.search([('config_id', '=', [x.id for x in self.pvt_ids])])
			for x in pos_session_ids:
				pvt_ids+= str(x.id) + ','
			pvt_ids = pvt_ids[:len(pvt_ids)-1]


		today = fields.Datetime.from_string(fields.Datetime.now())
		date_last_thirty = today + timedelta(days=-50)

		sql_delete = "DELETE FROM pos_report_pvt"
		self.env.cr.execute(sql_delete)

		sql = """
INSERT INTO pos_report_pvt (user_id, product_category_id, pvt_store, product_template_id, total_sales, sale_average_day, product_qty, sold_product_daily_qty)
SELECT r_user.id, product_tmpl.categ_id, pvt.id, product_tmpl.id, SUM(order_line.qty * order_line.price_unit), 
((SELECT SUM(ts_order_line.qty * ts_order_line.price_unit)
FROM pos_order ts_pos_or, pos_order_line ts_order_line, pos_session ts_pos_se, 
product_product ts_product, product_template ts_product_tmpl, res_users ts_r_user, 
res_partner ts_partner, pos_config ts_pvt, product_category ts_product_categ

WHERE ts_pos_or.date_order <= '%(date_today)s'
AND ts_pos_or.date_order >= '%(date_last_thirty)s'

AND ts_order_line.order_id = ts_pos_or.id

AND ts_pos_or.session_id = ts_pos_se.id

AND ts_order_line.product_id = ts_product.id
AND ts_product.product_tmpl_id = ts_product_tmpl.id
AND ts_product_tmpl.id = product_tmpl.id
AND ts_product.product_tmpl_id = product_tmpl.id

AND ts_r_user.id = ts_pos_or.user_id
AND ts_r_user.partner_id = ts_partner.id


AND ts_pvt.id = ts_pos_se.config_id

AND ts_product_categ.id = ts_product_tmpl.categ_id

AND ts_product_tmpl.categ_id = product_tmpl.categ_id)/30)::float,
SUM(order_line.qty), 
((SELECT SUM(sp_order_line.qty)
FROM pos_order sp_pos_or, pos_order_line sp_order_line, pos_session sp_pos_se, 
product_product sp_product, product_template sp_product_tmpl, res_users sp_r_user, 
res_partner sp_partner, pos_config sp_pvt, product_category sp_product_categ
WHERE sp_pos_or.date_order <= '%(date_today)s'
AND sp_pos_or.date_order >= '%(date_last_thirty)s'

AND sp_order_line.order_id = sp_pos_or.id

AND sp_pos_or.session_id = sp_pos_se.id

AND sp_order_line.product_id = sp_product.id
AND sp_product.product_tmpl_id = sp_product_tmpl.id
AND sp_product_tmpl.id = product_tmpl.id
AND sp_product.product_tmpl_id = product_tmpl.id

AND sp_r_user.id = sp_pos_or.user_id
AND sp_r_user.partner_id = sp_partner.id


AND sp_pvt.id = sp_pos_se.config_id

AND sp_product_categ.id = sp_product_tmpl.categ_id
AND sp_product_tmpl.categ_id = product_tmpl.categ_id)/30)::float


FROM pos_order pos_or, pos_order_line order_line, pos_session pos_se, 
product_product product, product_template product_tmpl, res_users r_user, 
res_partner partner, pos_config pvt, product_category product_categ
WHERE pos_or.date_order <= '%(date_today)s'

AND order_line.order_id = pos_or.id

AND pos_or.session_id = pos_se.id

AND order_line.product_id = product.id
AND product.product_tmpl_id = product_tmpl.id

AND r_user.id = pos_or.user_id
AND r_user.partner_id = partner.id

AND pvt.id = pos_se.config_id

AND product_categ.id = product_tmpl.categ_id
		"""%{
			'date_today': today,
			'date_last_thirty': date_last_thirty,
		}
		
		if self.date_begin:
			sql+= " AND pos_or.date_order >= '" + self.date_begin +  "' " + "\n"

		if self.pvt_ids:
			#verificando que sesiones tienen el punto de venta seleccionado
			sql+= " AND pos_or.session_id in (" + pvt_ids + ") "  + "\n"

		if self.user_ids:
			sql+= " AND pos_or.user_id in (" + user_ids + ") "  + "\n"

		sql+=""" GROUP BY r_user.id, product_tmpl.id, pvt.id, pvt.name, product_tmpl.categ_id;
		"""

		self.env.cr.execute( sql )


	@api.multi
	def generate_excel(self):

		self.load_information_report_pvt()

		model_pos_report_pvt= self.env['pos.report_pvt']

		record = model_pos_report_pvt.search([], order="pvt_store asc")

		categ_ids = []
		data_pvt = []
		for x in record:
			if x.product_category_id.id not in categ_ids:
				categ_ids.append(x.product_category_id.id)
			if x.pvt_store.id not in data_pvt:
				data_pvt.append(x.pvt_store.id)

		#sorted(vals, key=lambda x: getattr(x, x['product_category_id']), reverse=True)
		#new_data = sorted(vals, key=lambda x: x['product_category_id'])

		#vals = sorted(new_data, key=lambda x: x['pvt_store'])


		name_report = "Pos Report - " + str(fields.Datetime.from_string(fields.Datetime.now()))

		Header_Text = name_report
		file_data = BytesIO()
		workbook = xlsxwriter.Workbook(file_data)
		worksheet = workbook.add_worksheet(name_report)
	
		header_format = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#f9770c', 'font_size': 18 })
		format_tittle = workbook.add_format({'bold': 1,'align':'center', 'valign':'vcenter', 'border':1, 'fg_color':'#f9770c', 'font_size': 25 })
		letter_category = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 16 })
		letter_pvt = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#ffe8d8', 'font_size': 15 })
		letter_number_total = workbook.add_format({'bold': 1,'align':'right','valign':'vcenter', 'num_format': '$#,##0.00', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 16 })
		
		letter_left = workbook.add_format({'align':'left', 'font_color': 'black', 'font_size': 14})
		letter_number = workbook.add_format({'align':'right', 'font_color': 'black', 'num_format': '$#,##0.00', 'font_size': 14})
		bold = workbook.add_format({'bold': 1,'align':'left','border':1, 'font_size': 14})


		worksheet.set_column('A1:A1',35)
		worksheet.set_column('B1:B1',35)
		worksheet.set_column('C1:C1',35)
		worksheet.set_column('D1:C1',35)
		worksheet.set_column('E1:E1',35)
		worksheet.set_column('F1:F1',35)
		worksheet.set_column('G1:G1',55)
		worksheet.set_column('H1:H1',35)
		worksheet.set_column('I1:I1',35)
		worksheet.set_column('J1:J1',35)
		worksheet.set_column('K1:K1',35)
		worksheet.set_column('L1:L1',35)

		preview = name_report 

		for i in range(1):
			
			if len(record) > 0:

				worksheet.write('A1', 'Bodega/PDV', header_format)
				worksheet.write('B1', 'Producto', header_format)
				worksheet.write('C1', 'Vendedor', header_format)
				worksheet.write('D1', 'Ventas', header_format)
				worksheet.write('E1', 'Venta Promedio', header_format)
				worksheet.write('F1', '# Productos Vendidos', header_format)
				worksheet.write('G1', '# Promedio de Productos Vendidos diarios', header_format)
				worksheet.write('H1', 'Costo Total', header_format)
				worksheet.write('I1', 'Utilidad', header_format)
				worksheet.write('J1', 'Cantidad a la Mano', header_format)

				row=1
				col=0

				for value in record:

					worksheet.write(row,col , str(value.pvt_store.name), letter_left)
					worksheet.write(row,col+1 , str(value.product_template_id.name), letter_left)
					worksheet.write(row,col+2 , str(value.user_id.name), letter_left)
					worksheet.write(row,col+3 ,  (value.total_sales), letter_number)
					worksheet.write(row,col+4 ,  (value.sale_average_day), letter_number)
					worksheet.write(row,col+5, (value.product_qty) or 0, letter_number)
					worksheet.write(row,col+6 , (value.sold_product_daily_qty), letter_number)
					worksheet.write(row,col+7 ,  value.cost_product, letter_number)
					worksheet.write(row,col+8 ,  value.utility_product, letter_number)
					worksheet.write(row,col+9 ,  value.product_qty_stock, letter_number)

					row+=1


			workbook.close()
			file_data.seek(0)

			self.write({'document':base64.encodestring(file_data.read()), 'filename':Header_Text+'.xlsx'})


		return {
			'name': _(u'Configuración Pos Report'),
			'res_model':'pos.config_report_pvt',
			'type':'ir.actions.act_window',
			'view_type':'form',
			'view_mode':'form',
			'target':'new',
			'nodestroy': True,
			'res_id': self.id
		}


	@api.multi
	def button_return_report(self):

		self.load_information_report_pvt()

		return {
			'name': _('Reporte Punto de Venta'),
			'res_model':'pos.report_pvt',
			'type':'ir.actions.act_window',
			#'view_id': self.env.ref('l10n_co_point_of_sale_report.doctor_appointment_search_view').id,
			'view_mode': 'tree',
			'view_type': 'form',
			#'target':'inline',
			#'nodestroy': True,
			#'search_view_id': self.env.ref('l10n_co_point_of_sale_report.doctor_appointment_search_view').id
		#	 'views': [(searc_view_ref and searc_view_ref.id or False, 'search') ],
			
			#'view_id': view_id,
			#'context': self._context
		}	







PosConfigReportPDV()