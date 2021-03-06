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

from odoo import api, fields, models, _
import time
from datetime import datetime, timedelta, date
import logging
_logger = logging.getLogger(__name__)
from odoo import modules
from odoo.addons import decimal_precision as dp


class PosReportPVT(models.TransientModel):
	
	_name = 'pos.report_pvt'
	_description= "Pos Report PVT"


	


	#product
	product_template_id = fields.Many2one('product.template', string="Producto")
	#costo producto
	standard_price_product = fields.Float(string='Costo Unitario', related='product_template_id.standard_price', digits=dp.get_precision('Product Unit of Measure'))
	#costo producto
	barcode_product = fields.Char(string=u'Código de Barras', related='product_template_id.barcode', digits=dp.get_precision('Product Unit of Measure'))
	#vendedor
	user_id = fields.Many2one('res.users', string="Vendedor")
	#categoria del producto
	product_category_id = fields.Many2one('product.category', string=u"Categoría")
	#punto de venta
	pvt_store = fields.Many2one('pos.config', string="Tienda")
	#ventas
	total_sales = fields.Float(string="Total Ventas", default=0)
	#venta promedio dia
	sale_average_day = fields.Float(string=u"Venta Promedio Día", default=0)
	#productos vendidos
	product_qty = fields.Float(string="Productos Vendidos", default=0)
	#promedio de productos vendidos diarios
	sold_product_daily_qty = fields.Float(string="Productos Vendidos Diarios", default=0, store=True)
	#costo del producto
	cost_product = fields.Float(string="Costo Total", compute="_compute_cost_product", default=0)
	#Utilidad del producto
	utility_product = fields.Float(string="Utilidad Total", compute="_compute_utility_product", default=0)
	#cantidad virtual
	product_qty_stock = fields.Float(string='A la Mano', related='product_template_id.qty_available', digits=dp.get_precision('Product Unit of Measure'))
	#cantidad virtual
	product_virtual_available = fields.Float(string='Cantidad Virtual', related='product_template_id.virtual_available', digits=dp.get_precision('Product Unit of Measure'))
	#cantidad de entrada
	product_incoming_qty = fields.Float(string='Cantidad Entrante', related='product_template_id.incoming_qty', digits=dp.get_precision('Product Unit of Measure'))
	#cantidad de entrada
	product_outgoing_qty = fields.Float(string='Cantidad Saliente', related='product_template_id.outgoing_qty', digits=dp.get_precision('Product Unit of Measure'))
	#Reglas de Reordenamiento
	product_nbr_reordering_rules = fields.Integer(string= 'Reglas de Abastecimiento', related='product_template_id.nbr_reordering_rules', digits=dp.get_precision('Product Unit of Measure'))
	#Regla minima
	product_reordering_min_qty = fields.Float(string= u'Reabastecimiento Mínimo', related='product_template_id.reordering_min_qty', digits=dp.get_precision('Product Unit of Measure'))
	#Regla maxima
	product_reordering_max_qty = fields.Float(string= u'Reabastecimiento Máximo', related='product_template_id.reordering_max_qty', digits=dp.get_precision('Product Unit of Measure'))
	#descuentos realizados
	discounts = fields.Float(string="Descuentos", default=0)
	#ventas totales - descuentos
	total = fields.Float(string="Total", default=0)

	def _compute_barcode_product(self):

		_logger.info('##########')
		for x in self:
			_logger.info(x.id)
			_logger.info(x.name)
			product =  self.env['product.product'].search([('product_tmpl_id', '=', x.id)])
			print(product)
			x.barcode_product = product.barcode  or ''


	def _compute_cost_product(self):
		for x in self:
			x.cost_product = x.product_template_id.standard_price * x.product_qty

	def _compute_utility_product(self):
		for x in self:
			x.utility_product = (x.product_qty * x.product_template_id.list_price) - (x.product_qty * x.product_template_id.standard_price)
					
PosReportPVT()