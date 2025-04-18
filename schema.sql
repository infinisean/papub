CREATE TABLE `system_resources` (

  `devid` int NOT NULL,

  `updated` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  `bu` enum('corp','retail') NOT NULL DEFAULT 'retail',

  `retail_store` int(10) UNSIGNED ZEROFILL DEFAULT NULL,

  `hostname` varchar(30) NOT NULL,

  `last_boot` datetime DEFAULT NULL,

  `one_min_load` float UNSIGNED DEFAULT NULL,

  `cpu_usage` float UNSIGNED DEFAULT NULL,

  `mem_used` float UNSIGNED DEFAULT NULL,

  `mem_free` float UNSIGNED DEFAULT NULL,

  `mem_total` float UNSIGNED GENERATED ALWAYS AS ((`mem_used` + `mem_free`)) VIRTUAL

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;