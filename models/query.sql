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
AND ts_r_user.id = r_user.id

AND ts_pvt.id = ts_pos_se.config_id
AND ts_pvt.id = pvt.id

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
AND sp_r_user.id = r_user.id

AND sp_pvt.id = sp_pos_se.config_id
AND sp_pvt.id = pvt.id

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

GROUP BY r_user.id, product_tmpl.id, pvt.id, pvt.name, product_tmpl.categ_id;