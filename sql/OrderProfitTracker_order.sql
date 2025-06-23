drop table order_profit_tracker_db.orders;
CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer_name` text NOT NULL,
  `project_name` text NOT NULL,
  `sales_amount` numeric default 0,
  `order_amount` numeric default 0,
  `invoiced_amount` numeric default 0,
  `order_date` date NOT NULL,
  `contract_type` varchar(16),
  `sales_stage` varchar(16),
  `billing_month` date,
  `work_in_progress` boolean default false,
  `description` text,
  `created_at` datetime DEFAULT now(),
  `updated_at` datetime DEFAULT now(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;