-- ============================================
-- 迷你商城 — 性能索引（1W 用户量级）
-- 在高频查询字段上建索引，减少全表扫描
-- 执行方式: mysql -u root -p pycharm_test < add_indexes.sql
-- ============================================

-- 用户表：登录查用户名+密码（高频）
ALTER TABLE `user` ADD INDEX IF NOT EXISTS `idx_username_password` (`username`, `password`);

-- 用户表：旧 token 查询（兼容过渡期）
ALTER TABLE `user` ADD INDEX IF NOT EXISTS `idx_token` (`token`);

-- 订单表：用户查自己的订单（高频）
ALTER TABLE `orders` ADD INDEX IF NOT EXISTS `idx_user_id` (`user_id`);
ALTER TABLE `orders` ADD INDEX IF NOT EXISTS `idx_user_status` (`user_id`, `status`);
ALTER TABLE `orders` ADD INDEX IF NOT EXISTS `idx_status` (`status`);

-- 购物车：用户查购物车（高频）
ALTER TABLE `cart` ADD INDEX IF NOT EXISTS `idx_user_id` (`user_id`);

-- 收货地址：用户查地址（高频）
ALTER TABLE `address` ADD INDEX IF NOT EXISTS `idx_user_id` (`user_id`);

-- 商品表：按分类筛选 + 上架状态（高频）
ALTER TABLE `goods` ADD INDEX IF NOT EXISTS `idx_category_onsale` (`category_id`, `is_on_sale`);
ALTER TABLE `goods` ADD INDEX IF NOT EXISTS `idx_onsale` (`is_on_sale`);

-- 商品名称模糊搜索索引（仅 MySQL 5.7+ / 8.0 支持全文索引）
-- ALTER TABLE `goods` ADD FULLTEXT INDEX IF NOT EXISTS `ft_name` (`name`);

-- 订单商品表：按订单查（高频）
ALTER TABLE `order_items` ADD INDEX IF NOT EXISTS `idx_order_id` (`order_id`);

-- 评价表：按商品查（高频）
ALTER TABLE `review` ADD INDEX IF NOT EXISTS `idx_goods_id` (`goods_id`);
ALTER TABLE `review` ADD INDEX IF NOT EXISTS `idx_user_order_goods` (`user_id`, `order_id`, `goods_id`);

-- 售后表：按用户查（高频）
ALTER TABLE `after_sale` ADD INDEX IF NOT EXISTS `idx_user_id` (`user_id`);
ALTER TABLE `after_sale` ADD INDEX IF NOT EXISTS `idx_status` (`status`);

SELECT '索引添加完成！' AS result;
