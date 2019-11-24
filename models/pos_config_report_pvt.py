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

	pvt_store = fields.Many2one('pos.config', string="Tienda")
	date_begin = fields.Datetime(string="Fecha Inicio")
	date_end = fields.Datetime(string="Fecha Fin", default=lambda self: fields.datetime.now())
	user_ids = fields.Many2many(comodel_name='res.users', relation='rel_config_report_pvt_user', column1='user_id', column2='config_report_id', string='Users')
	filename = fields.Char('Nombre Archivo')
	document = fields.Binary(string = 'Descargar Excel')



	def last_thirty_sales(self, product_id):
		"""
			Funcion que retorna las ventas de los ultimos 30 dias de acuerdo al produto
		"""
		total_sales = 0
		total_qty= 0
		if product_id:
			today = fields.Datetime.from_string(fields.Datetime.now())
			date_last_thirty = today + timedelta(days=-30)

			pos_order_ids =  self.env['pos.order'].search([('date_order', '>=', str(date_last_thirty))])

			
			for x in pos_order_ids:
				if x.lines:
					for order in x.lines:
						if order.product_id.id == product_id:
							total_sales = total_sales + (order.qty * order.price_unit)
							total_qty = total_qty +  order.qty

		total_sales = (total_sales/30)
		total_qty = (total_qty/30)


		data=[]
		data.append({'total_sales': total_sales, 'total_qty':total_qty})


		return data

	def update_vals_sales(self, vals):

		if vals:

			for x in vals:

				x['total_sales'] = x['price_unit'] * x['product_qty']
				x['sale_average_day'] = self.last_thirty_sales(x['product_template_id'])[0]['total_sales']
				x['sold_product_daily_qty']	= self.last_thirty_sales(x['product_template_id'])[0]['total_qty']
				x['cost_product']: x['standard_price'] * x['product_qty']
				x['utility_product']: (x['product_qty'] * x['price_unit']) - (x['product_qty'] * x['standard_price'])

	def return_record_product_report(self, pos_order_ids):
		"""
			Funcion que permite retornar una data con toda la informacion de la orden, con el fin de
			realizar un filtro posteriormente
		"""

		data=[]

		if pos_order_ids:

			for x in pos_order_ids:

				if x.lines:

					for record in x.lines:

						vals = {
							'user_id': x.user_id.id,
							'user_name': x.user_id.name,
							'date_order': x.date_order,
							'product_category_id': record.product_id.categ_id.id,
							'product_category_name': record.product_id.categ_id.name,
							'pvt_store': x.session_id.config_id.id,
							'pvt_store_name': x.session_id.config_id.name,
							'product_template_id': record.product_id.id,
							'product_template_name': record.product_id.name,
							'product_qty': record.qty,
							'price_unit': record.price_unit,
							'total_sales': 0,
							'sale_average_day': 0,
							'sold_product_daily_qty': 0,
							'cost_product': 0,
							'utility_product': 0,
							'standard_price': float(record.product_id.standard_price)
						}
	
						data.append(vals)

		return data


	def search_product_record_exist(self, product_id, pvt_id, user_id, vals):
		"""
			Funcion que permite buscar el producto en vals, (excel)
		"""
		if product_id and vals:
			if len(vals) > 0:
				for x in vals:
					if (x['product_template_id'] == product_id) and (x['pvt_store'] == pvt_id) and (x['user_id'] == user_id):
						return True

		return False


	def update_product_record(self, product_id, product_qty, pvt_id, user_id, vals):
		"""
			Funcion que permite actualizar la data con la cantidad ordenada, (excel)
		"""
		if product_id and vals:
			for x in vals:
				if len(vals) > 0:
					if (x['product_template_id'] == product_id) and (x['pvt_store'] == pvt_id) and (x['user_id'] == user_id):
						x['product_qty'] +=  product_qty


	def return_data_order_report(self, data):
		"""
			Funcion que permite agrupar los datos para el reporte de excel
		"""
		data_order=[]

		if data:
			for x in data:
				if self.search_product_record_exist(x['product_template_id'], x['pvt_store'], x['user_id'], data_order) == False:
					data_order.append(x)
				else:
					self.update_product_record(x['product_template_id'], x['product_qty'], x['pvt_store'], x['user_id'], data_order)


		return data_order



	def create_records_pos_report_pvt(self, data, model_pos_report_pvt):

		data_order = self.return_data_order_report(data)

		print('*******************')
		print(data_order)
		print('*******************')

		self.update_vals_sales(data_order)

		print('------Data Agrupada')
		print(data_order)
		if data_order:
			for x in data_order:

				print(self.env['res.users'].search([('id', '=', x['user_id'])]).name)
				vals={


					'user_id': x['user_id'], 
					'date_order': x['date_order'], 
					'product_category_id': x['product_category_id'], 
					'pvt_store': x['pvt_store'], 
					'product_template_id': x['product_template_id'], 
					'total_sales': x['total_sales'], 
					'sale_average_day': x['sale_average_day'], 
					'product_qty': x['product_qty'], 
					'sold_product_daily_qty': x['sold_product_daily_qty'],
					'cost_product': x['standard_price'] * x['product_qty'],
					'utility_product': (x['product_qty'] * x['price_unit']) - (x['product_qty'] * x['standard_price'])
					#'utility_product': x['utility_product']			
				}
				
				model_pos_report_pvt.create(vals)

	"""
		Funcion permite retornar los datos mas importantes de la compania
	"""
	def return_information_company(self):
		company_id = self.env.user.company_id
		name = company_id.name
		nit = (company_id.partner_id.formatedNit or '')
		street = (company_id.street or '')
		email = (company_id.email or '')
		city = (company_id.partner_id.xcity.name or '')
		state = (company_id.partner_id.state_id.name or '')
		city_state = (state or '') + ' ' + (city or '')
		country_id = (company_id.country_id.name or '')
		phone = (company_id.phone or '')
		website = (company_id.website or '')

		vals = {
			'name': name,
			'nit': ('Nit: ' + nit) or '',
			'street': (street or '') + ' ' + (company_id.street2 or ''),
			'email': email or '',
			'city_state': city_state or '',
			'country_id': country_id or '',
			'phone': phone or '',
			'website': website or ''
		}

		return vals

	def delete_record_pos_report_pvt(self, model_pos_report_pvt):
		"""
			Funcion que permite eliminar los registros que hayan en el modelo, para poder generar el reporte
			con los datos que se han parametrizado
		"""

		pos_ids= model_pos_report_pvt.search([])

		if pos_ids:
			for x in pos_ids:
				x.unlink()

	def return_data(self):

		domain = []
		#model_pos_config = self.env['pos.config']
		model_pos_order = self.env['pos.order']
		model_pos_sesion = self.env['pos.session']
		model_pos_report_pvt = self.env['pos.report_pvt']

		#llenando domain para realizar la busqueda
		if self.date_begin:
			domain.append(('date_order', '>=', self.date_begin))
		if self.date_end:
			domain.append(('date_order', '<=', self.date_end))
		else:
			domain.append(('date_order', '<=', fields.datetime.now()))
		if self.pvt_store:
			#verificando que sesiones tienen el punto de venta seleccionado
			pos_session_ids = model_pos_sesion.search([('config_id', '=', self.pvt_store.id)])
			domain.append(('session_id', 'in', [x.id for x in pos_session_ids]))
		if self.user_ids:
			domain.append(('user_id', 'in', [x.id for x in self.user_ids]))
			

		print(domain)
		pos_order_ids = model_pos_order.search(domain)

		print('-------Las ordenes son: -----')
		print(pos_order_ids)

		#eliminando datos del modelo
		self.delete_record_pos_report_pvt(model_pos_report_pvt)

		#creando data para el informe
		data = self.return_record_product_report(pos_order_ids)

		return data

	def search_data_excel(self, categ_id, pvt_store, vals):

		if len(vals) > 0:
			for x in vals:
				if x['product_category_id'] == categ_id:
					if x['data']:
						for value in x['data']:
							if value['pvt_store'] == pvt_store:
								return True

		return False

	def update_data_excel(self, categ_id, pvt_id, data, vals):

		for x in vals:

			if x['product_category_id'] == categ_id:
				
				if x['data']:
					for value in x['data']:
						#print('la cateogria es: ' + str(x['product_category_id']) + ' el puntode venta es: ' + str(value['pvt_store']))
						if value['pvt_store'] == pvt_id:
							print('entro')

							print('se edita el punto de venta ' + str(pvt_id) + ' con categoria ' + str(x['product_category_id']))
							value['data'].append(data)
					#	else:
							#value['pvt_store'].append(pvt_id)
						#	x['data'].append({'pvt_store': pvt_id, 'data': [data]})


	def update_create_record_excel(self, categ_id, vals):

		for x in vals:

			if x['product_category_id'] == categ_id:
				
				if x['data']:
					if len(x['data']) > 0:
						return True

		return False

	def data_excel(self, vals):

		data_new = []

		for x in vals:

			if self.search_data_excel(x['product_category_id'], x['pvt_store'],  data_new):

				self.update_data_excel(x['product_category_id'],  x['pvt_store'], x, data_new)

			else:



				data_new.append({'product_category_id': x['product_category_id'], 'data': [{'pvt_store': x['pvt_store'], 'data': [x] }]})

		return data_new


	def search_category_pvt(self, model_pos_report_pvt, categ_id, pvt_id):

		record = model_pos_report_pvt.search([('product_category_id', '=', categ_id)])

		iterator = 0

		total_sales = 0
		total_product_qty = 0
		total_cost_product = 0
		total_utility = 0

		#avg
		sale_average_day_avg= 0
		sold_product_daily_qty_avg = 0
		for x in range(len(record)):

			total_sales += record[x].total_sales
			sale_average_day_avg += record[x].sale_average_day
			total_product_qty += record[x].product_qty
			sold_product_daily_qty_avg += record[x].sold_product_daily_qty
			total_cost_product += record[x].cost_product
			total_utility += record[x].utility_product

			iterator+=1



		print('Total iteraciones')
		print(iterator)

		vals = {
		'total_sales': total_sales,
		'sale_average_day': sale_average_day_avg/iterator,
		'product_qty': total_product_qty,
		'sold_product_daily_qty': sold_product_daily_qty_avg/iterator,
		'cost_product': total_cost_product,
		'utility_product': total_utility

		}

		print(vals)
		return vals







	def sortSecond(self, val): 
		return val[1]
	
	@api.multi
	def generate_excel(self):

		data = self.return_data()

		model_pos_report_pvt = self.env['pos.report_pvt']

		self.create_records_pos_report_pvt(data, model_pos_report_pvt)


		record = self.env['pos.report_pvt'].search([])


		for x in record:
			print(x.product_template_id.name)

		categ_ids = []
		data_pvt = []
		for x in record:
			if x.product_category_id.id not in categ_ids:
				categ_ids.append(x.product_category_id.id)
			if x.pvt_store.id not in data_pvt:
				data_pvt.append(x.pvt_store.id)


		print('los datos son')
		print(categ_ids)
		print(data_pvt)




		#sorted(vals, key=lambda x: getattr(x, x['product_category_id']), reverse=True)
		#new_data = sorted(vals, key=lambda x: x['product_category_id'])

		#vals = sorted(new_data, key=lambda x: x['pvt_store'])

		"""

[{'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-20 00:40:26', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 4, 'product_template_name': 'Samung s9 plus', 'product_qty': 4.0, 'price_unit': 10000.0, 'total_sales': 40000.0, 'sale_average_day': 4666.666666666667, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 5000.0},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-20 00:39:59', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 3, 'product_template_name': 'Iphone x', 'product_qty': 5.0, 'price_unit': 100000.0, 'total_sales': 500000.0, 'sale_average_day': 50000.0, 'sold_product_daily_qty': 0.5, 'cost_product': 0, 'utility_product': 0, 'standard_price': 80000.0},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-10-30 23:04:42', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 1, 'product_template_name': 'Propinas', 'product_qty': 6.0, 'price_unit': 1.0, 'total_sales': 6.0, 'sale_average_day': 0.36666666666666664, 'sold_product_daily_qty': 0.36666666666666664, 'cost_product': 0, 'utility_product': 0, 'standard_price': 0.5},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-20 00:40:13', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 5, 'product_template_name': 'Devos', 'product_qty': 8.0, 'price_unit': 50000.0, 'total_sales': 400000.0, 'sale_average_day': 30000.0, 'sold_product_daily_qty': 0.6, 'cost_product': 0, 'utility_product': 0, 'standard_price': 10000.0},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-10-30 23:07:09', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 2, 'product_template_name': 'Varios', 'product_qty': 10.0, 'price_unit': 18.0, 'total_sales': 180.0, 'sale_average_day': 8.4, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 13.0},
 {'user_id': 6, 'user_name': 'Vendedor', 'date_order': '2019-10-18 21:51:11', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 2, 'product_template_name': 'Varios', 'product_qty': 2.0, 'price_unit': 18.0, 'total_sales': 36.0, 'sale_average_day': 8.4, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 13.0},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 3, 'product_template_name': 'Iphone x', 'product_qty': 10.0, 'price_unit': 100000.0, 'total_sales': 1000000.0, 'sale_average_day': 50000.0, 'sold_product_daily_qty': 0.5, 'cost_product': 0, 'utility_product': 0, 'standard_price': 80000.0},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 1, 'product_template_name': 'Propinas', 'product_qty': 5.0, 'price_unit': 1.0, 'total_sales': 5.0, 'sale_average_day': 0.36666666666666664, 'sold_product_daily_qty': 0.36666666666666664, 'cost_product': 0, 'utility_product': 0, 'standard_price': 0.5},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 4, 'product_template_name': 'Samung s9 plus', 'product_qty': 10.0, 'price_unit': 10000.0, 'total_sales': 100000.0, 'sale_average_day': 4666.666666666667, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 5000.0}, 
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 2, 'product_template_name': 'Varios', 'product_qty': 5.0, 'price_unit': 18.0, 'total_sales': 90.0, 'sale_average_day': 8.4, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 13.0}, 
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 5, 'product_template_name': 'Devos', 'product_qty': 10.0, 'price_unit': 50000.0, 'total_sales': 500000.0, 'sale_average_day': 30000.0, 'sold_product_daily_qty': 0.6, 'cost_product': 0, 'utility_product': 0, 'standard_price': 10000.0}]
		"""


		name_report = "Pos Report"

		data_company = self.return_information_company()

		Header_Text = name_report
		file_data = BytesIO()
		workbook = xlsxwriter.Workbook(file_data)
		worksheet = workbook.add_worksheet(name_report)

		#sheet = workbook.add_sheet(order.name)
		
		#Formato de letras y celdas
	
		header_format = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#f9770c', 'font_size': 18 })
		format_tittle = workbook.add_format({'bold': 1,'align':'center', 'valign':'vcenter', 'border':1, 'fg_color':'#f9770c', 'font_size': 25 })
		letter_category = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 16 })
		letter_pvt = workbook.add_format({'bold': 1,'align':'center','valign':'vcenter', 'border':1, 'fg_color':'#ffe8d8', 'font_size': 15 })
		letter_number_total = workbook.add_format({'bold': 1,'align':'right','valign':'vcenter', 'num_format': '$#,##0.00', 'border':1, 'fg_color':'#F9CEA9', 'font_size': 16 })
		
		letter_left = workbook.add_format({'align':'left', 'font_color': 'black', 'font_size': 14})
		letter_number = workbook.add_format({'align':'right', 'font_color': 'black', 'num_format': '$#,##0.00', 'font_size': 14})
		bold = workbook.add_format({'bold': 1,'align':'left','border':1, 'font_size': 14})




		#letter_gray_name = workbook.add_format({'align':'left', 'font_color': 'gray', 'indent':2, 'font_size': 14})
		#letter_gray = workbook.add_format({'align':'right', 'font_color': 'gray', 'num_format': '$#,##0.00', 'font_size': 14})
		#letter_black_name = workbook.add_format({'align':'left', 'font_color': 'black', 'num_format': '$#,##0.00', 'font_size': 14})
		#letter_black = workbook.add_format({'align':'right', 'font_color': 'black', 'num_format': '$#,##0.00', 'font_size': 14})
		

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
			worksheet.write('A1', data_company['name'], bold)
			if data_company['nit']:
				worksheet.write('A2', data_company['nit'], bold)
			if data_company['street']:
				worksheet.write('A3', data_company['street'], bold)
			if data_company['phone']:
				worksheet.write('A4', data_company['phone'], bold)
			if data_company['city_state']:
				worksheet.write('A5', data_company['city_state'], bold)
			if data_company['country_id']:
				worksheet.write('A6', data_company['country_id'], bold)
			if data_company['email']:
				worksheet.write('A7', data_company['email'], bold)
			if data_company['website']:
				worksheet.write('A7', data_company['website'], bold)

			worksheet.merge_range('C3:D4',preview, format_tittle)

			

			fecha_inicial = self.date_begin

			if fecha_inicial ==  False:
				fecha_inicial = 'Sin fecha'
			else:
				fecha_inicial = str(self.date_begin)

			worksheet.merge_range('E9:F9', "Rango de Fechas", header_format)
			worksheet.write('E10', "Fecha Inicial", bold)
			worksheet.write('F10', fecha_inicial, bold)
			worksheet.write('E11', "Fecha Final", bold)
			worksheet.write('F11', str(self.date_end), bold)

			format="%Y-%m-%d %H:%M:00"
			now=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(fields.Datetime.now()))
			
			date_today=str(datetime.strftime(now, format))

			worksheet.write('F1', 'Fecha Impresion', header_format)
			worksheet.write('F2', date_today, bold)

			if len(record) > 0:

				worksheet.write('A13', 'Bodega/PDV', header_format)
				worksheet.write('B13', 'Producto', header_format)
				worksheet.write('C13', 'Vendedor', header_format)
				worksheet.write('D13', 'Ventas', header_format)
				worksheet.write('E13', 'Venta Promedio', header_format)
				worksheet.write('F13', '# Productos Vendidos', header_format)
				worksheet.write('G13', '# Promedio de Productos Vendidos diarios', header_format)
				worksheet.write('H13', 'Costo Total', header_format)
				worksheet.write('I13', 'Utilidad', header_format)
				worksheet.write('J13', 'cantidad Entran', header_format)

				row=14
				col=0


				"""
[{'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-20 00:40:26', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 4, 'product_template_name': 'Samung s9 plus', 'product_qty': 4.0, 'price_unit': 10000.0, 'total_sales': 40000.0, 'sale_average_day': 4666.666666666667, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 5000.0},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-20 00:39:59', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 3, 'product_template_name': 'Iphone x', 'product_qty': 5.0, 'price_unit': 100000.0, 'total_sales': 500000.0, 'sale_average_day': 50000.0, 'sold_product_daily_qty': 0.5, 'cost_product': 0, 'utility_product': 0, 'standard_price': 80000.0},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-10-30 23:04:42', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 1, 'product_template_name': 'Propinas', 'product_qty': 6.0, 'price_unit': 1.0, 'total_sales': 6.0, 'sale_average_day': 0.36666666666666664, 'sold_product_daily_qty': 0.36666666666666664, 'cost_product': 0, 'utility_product': 0, 'standard_price': 0.5},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-20 00:40:13', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 5, 'product_template_name': 'Devos', 'product_qty': 8.0, 'price_unit': 50000.0, 'total_sales': 400000.0, 'sale_average_day': 30000.0, 'sold_product_daily_qty': 0.6, 'cost_product': 0, 'utility_product': 0, 'standard_price': 10000.0},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-10-30 23:07:09', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 2, 'product_template_name': 'Varios', 'product_qty': 10.0, 'price_unit': 18.0, 'total_sales': 180.0, 'sale_average_day': 8.4, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 13.0},
 {'user_id': 6, 'user_name': 'Vendedor', 'date_order': '2019-10-18 21:51:11', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 2, 'product_template_name': 'Varios', 'product_qty': 2.0, 'price_unit': 18.0, 'total_sales': 36.0, 'sale_average_day': 8.4, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 13.0},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 3, 'product_template_name': 'Iphone x', 'product_qty': 10.0, 'price_unit': 100000.0, 'total_sales': 1000000.0, 'sale_average_day': 50000.0, 'sold_product_daily_qty': 0.5, 'cost_product': 0, 'utility_product': 0, 'standard_price': 80000.0},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 1, 'product_template_name': 'Propinas', 'product_qty': 5.0, 'price_unit': 1.0, 'total_sales': 5.0, 'sale_average_day': 0.36666666666666664, 'sold_product_daily_qty': 0.36666666666666664, 'cost_product': 0, 'utility_product': 0, 'standard_price': 0.5},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 4, 'product_template_name': 'Samung s9 plus', 'product_qty': 10.0, 'price_unit': 10000.0, 'total_sales': 100000.0, 'sale_average_day': 4666.666666666667, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 5000.0}, 
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 2, 'product_template_name': 'Varios', 'product_qty': 5.0, 'price_unit': 18.0, 'total_sales': 90.0, 'sale_average_day': 8.4, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 13.0}, 
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 5, 'product_template_name': 'Devos', 'product_qty': 10.0, 'price_unit': 50000.0, 'total_sales': 500000.0, 'sale_average_day': 30000.0, 'sold_product_daily_qty': 0.6, 'cost_product': 0, 'utility_product': 0, 'standard_price': 10000.0}]
		

[{'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-20 00:40:26', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 4, 'product_template_name': 'Samung s9 plus', 'product_qty': 4.0, 'price_unit': 10000.0, 'total_sales': 40000.0, 'sale_average_day': 4666.666666666667, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 5000.0}, 
{'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-20 00:39:59', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 3, 'product_template_name': 'Iphone x', 'product_qty': 5.0, 'price_unit': 100000.0, 'total_sales': 500000.0, 'sale_average_day': 50000.0, 'sold_product_daily_qty': 0.5, 'cost_product': 0, 'utility_product': 0, 'standard_price': 80000.0},
 {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-10-30 23:04:42', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 1, 'product_template_name': 'Propinas', 'product_qty': 6.0, 'price_unit': 1.0, 'total_sales': 6.0, 'sale_average_day': 0.36666666666666664, 'sold_product_daily_qty': 0.36666666666666664, 'cost_product': 0, 'utility_product': 0, 'standard_price': 0.5}, {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-20 00:40:13', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 5, 'product_template_name': 'Devos', 'product_qty': 8.0, 'price_unit': 50000.0, 'total_sales': 400000.0, 'sale_average_day': 30000.0, 'sold_product_daily_qty': 0.6, 'cost_product': 0, 'utility_product': 0, 'standard_price': 10000.0}, {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-10-30 23:07:09', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 2, 'product_template_name': 'Varios', 'product_qty': 10.0, 'price_unit': 18.0, 'total_sales': 180.0, 'sale_average_day': 8.4, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 13.0}, {'user_id': 6, 'user_name': 'Vendedor', 'date_order': '2019-10-18 21:51:11', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 1, 'pvt_store_name': 'Main', 'product_template_id': 2, 'product_template_name': 'Varios', 'product_qty': 2.0, 'price_unit': 18.0, 'total_sales': 36.0, 'sale_average_day': 8.4, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 13.0}, {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 3, 'product_template_name': 'Iphone x', 'product_qty': 10.0, 'price_unit': 100000.0, 'total_sales': 1000000.0, 'sale_average_day': 50000.0, 'sold_product_daily_qty': 0.5, 'cost_product': 0, 'utility_product': 0, 'standard_price': 80000.0}, {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 1, 'product_template_name': 'Propinas', 'product_qty': 5.0, 'price_unit': 1.0, 'total_sales': 5.0, 'sale_average_day': 0.36666666666666664, 'sold_product_daily_qty': 0.36666666666666664, 'cost_product': 0, 'utility_product': 0, 'standard_price': 0.5}, {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 3, 'product_category_name': 'Celulares', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 4, 'product_template_name': 'Samung s9 plus', 'product_qty': 10.0, 'price_unit': 10000.0, 'total_sales': 100000.0, 'sale_average_day': 4666.666666666667, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 5000.0}, {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 2, 'product_template_name': 'Varios', 'product_qty': 5.0, 'price_unit': 18.0, 'total_sales': 90.0, 'sale_average_day': 8.4, 'sold_product_daily_qty': 0.4666666666666667, 'cost_product': 0, 'utility_product': 0, 'standard_price': 13.0}, {'user_id': 1, 'user_name': 'ADMINISTRATOR  ADMINISTRATOR ', 'date_order': '2019-11-22 20:18:43', 'product_category_id': 6, 'product_category_name': 'Esencias', 'pvt_store': 2, 'pvt_store_name': 'Claro', 'product_template_id': 5, 'product_template_name': 'Devos', 'product_qty': 10.0, 'price_unit': 50000.0, 'total_sales': 500000.0, 'sale_average_day': 30000.0, 'sold_product_daily_qty': 0.6, 'cost_product': 0, 'utility_product': 0, 'standard_price': 10000.0}]
				"""	



				for categ in categ_ids:

					flag_categ = True
					flag_pvt = []
					
					for value in record:

						if value.product_category_id.id == categ:
							#es la misma categoria
							#imprimimos la categoria en el excel

							for pvt in data_pvt:

								if value.pvt_store.id == pvt:

									if flag_categ:
										merge= 'A'+str(row)+':B'+str(row)
										print(merge)
										aveg_record = self.search_category_pvt(model_pos_report_pvt, categ, pvt)
										worksheet.merge_range(merge, self.env['product.category'].search([('id', '=', categ)]).name , letter_category)
										worksheet.write('C'+str(row)+':D'+str(row), '', letter_number_total)
										worksheet.write('D'+str(row)+':E'+str(row), (aveg_record['total_sales']), letter_number_total)
										worksheet.write('E'+str(row)+':F'+str(row),  (aveg_record['sale_average_day']), letter_number_total)
										worksheet.write('F'+str(row)+':G'+str(row), aveg_record['product_qty'] or 0, letter_number_total)
										worksheet.write('G'+str(row)+':H'+str(row), aveg_record['sold_product_daily_qty'], letter_number_total)
										worksheet.write('H'+str(row)+':I'+str(row),  aveg_record['cost_product'], letter_number_total)
										worksheet.write('I'+str(row)+':J'+str(row),  aveg_record['utility_product'], letter_number_total)
										worksheet.write('J'+str(row)+':K'+str(row),  str(0), letter_number_total)										

										#row+=1
										flag_categ = False


									if flag_pvt:
										print('entro varias veces')
										for validate_pvt in flag_pvt:
											if value.pvt_store.id not in flag_pvt:
												worksheet.write(row,col, 'PVT. ' +  str(value.pvt_store.name), letter_pvt)
												flag_pvt.append(value.pvt_store.id)
												print('actualizo')
									else:
										worksheet.write(row,col, 'PVT. ' + str(value.pvt_store.name), letter_pvt)
										print('entro una vez')
										flag_pvt.append(value.pvt_store.id)

									worksheet.write(row,col+1 , str(value.product_template_id.name), letter_left)
									worksheet.write(row,col+2 , str(value.user_id.name), letter_left)
									worksheet.write(row,col+3 ,  (value.total_sales), letter_number)
									worksheet.write(row,col+4 ,  (value.sale_average_day), letter_number)
									worksheet.write(row,col+5, (value.product_qty) or 0, letter_number)
									worksheet.write(row,col+6 , (value.sold_product_daily_qty), letter_number)
									worksheet.write(row,col+7 ,  value.cost_product, letter_number)
									worksheet.write(row,col+8 ,  value.utility_product, letter_number)
									worksheet.write(row,col+9 ,  str(0), letter_number)

									row+=1
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

		print('data')
		data = self.return_data()
		print('=====================')
		print(data)
		print('=====================')
		#full

		model_pos_report_pvt = self.env['pos.report_pvt']
		self.create_records_pos_report_pvt(data, model_pos_report_pvt)

		#ctx.update({'default_journal_id': self.id, 'view_no_maturity': True})
		#view_id = self.env.ref('l10n_co_point_of_sale_report.pos_report_pvt_view_tree').id

		searc_view_ref = self.env.ref('l10n_co_point_of_sale_report.doctor_appointment_search_view', False)

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