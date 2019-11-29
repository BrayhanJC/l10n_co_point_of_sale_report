SELECT pvt.name AS pvt, pvt.id as pvt_store, r_user.login AS user_name, r_user.id AS user_id,
product_tmpl.id as product_template_id, product_tmpl.name AS product_name, product_tmpl.categ_id as product_category_id,
SUM(order_line.qty) AS product_qty, product_tmpl.list_price, SUM(order_line.qty * order_line.price_unit) AS total_sales
FROM pos_order pos_or, pos_order_line order_line, pos_session pos_se, 
product_product product, product_template product_tmpl, res_users r_user, 
res_partner partner, pos_config pvt, product_category product_categ
WHERE pos_or.date_order <= '2019-12-31 20:18:11.887'


--Relacionando ordenes
AND order_line.order_id = pos_or.id

--Relacionando sesiones
AND pos_or.session_id = pos_se.id

--Relacionando produtos
AND order_line.product_id = product.id
AND product.product_tmpl_id = product_tmpl.id

--Relacion usuario
AND r_user.id = pos_or.user_id
AND r_user.partner_id = partner.id

--Relacion punto de venta
AND pvt.id = pos_se.config_id

--Relacion categoria
AND product_categ.id = product_tmpl.categ_id

GROUP BY r_user.id, product_tmpl.id, pvt.id, pvt.name, product_tmpl.categ_id




--Subconsulta venta totales

(SELECT SUM(order_line.qty * order_line.price_unit) AS venta_promedio_dia
FROM pos_order pos_or, pos_order_line order_line, pos_session pos_se, 
product_product product, product_template product_tmpl, res_users r_user, 
res_partner partner, pos_config pvt, product_category product_categ
WHERE pos_or.date_order <= '2019-12-31 20:18:11.887'
pos_or.date_order >= '2019-10-01 20:18:11.887'

--Relacionando ordenes
AND order_line.order_id = pos_or.id

--Relacionando sesiones
AND pos_or.session_id = pos_se.id

--Relacionando produtos
AND order_line.product_id = product.id
AND product.product_tmpl_id = product_tmpl.id

--Relacion usuario
AND r_user.id = pos_or.user_id
AND r_user.partner_id = partner.id

--Relacion punto de venta
AND pvt.id = pos_se.config_id

--Relacion categoria
AND product_categ.id = product_tmpl.categ_id)

GROUP BY r_user.id, product_tmpl.id, pvt.id, pvt.name, product_tmpl.categ_id



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
			

		pos_order_ids = model_pos_order.search(domain)


