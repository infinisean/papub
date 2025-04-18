CREATE TABLE system_resources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    uptime VARCHAR(255),
    load_averages VARCHAR(255),
    cpu_usage FLOAT,
    mem_total FLOAT,
    mem_used FLOAT,
    mem_free FLOAT
);