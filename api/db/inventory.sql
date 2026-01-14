CREATE DATABASE  IF NOT EXISTS `inventory` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `inventory`;
-- MySQL dump 10.13  Distrib 8.0.43, for macos15 (arm64)
--
-- Host: localhost    Database: inventory
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `attachments`
--

DROP TABLE IF EXISTS `attachments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attachments` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `entity_type` varchar(40) NOT NULL,
  `entity_id` bigint NOT NULL,
  `file_url` varchar(255) NOT NULL,
  `note` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `attachments`
--

LOCK TABLES `attachments` WRITE;
/*!40000 ALTER TABLE `attachments` DISABLE KEYS */;
INSERT INTO `attachments` VALUES (1,'ITEM',1,'/files/item1.jpg','Laptop photo'),(2,'ITEM',2,'/files/item2.jpg','Chair photo'),(3,'ITEM',3,'/files/item3.jpg','Switch photo'),(4,'ISSUE',1,'/files/issue1.pdf','Issue doc'),(5,'ISSUE',2,'/files/issue2.pdf','Issue doc'),(6,'ISSUE',3,'/files/issue3.pdf','Approval doc'),(7,'ITEM',4,'/files/item4.jpg','Ink photo'),(8,'ITEM',5,'/files/item5.jpg','Cable photo'),(9,'ISSUE',4,'/files/issue4.pdf','Draft'),(10,'ITEM',6,'/files/item6.jpg','Lamp photo');
/*!40000 ALTER TABLE `attachments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `audit_log`
--

DROP TABLE IF EXISTS `audit_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `actor_user_id` bigint NOT NULL,
  `action` varchar(80) NOT NULL,
  `entity_type` varchar(40) NOT NULL,
  `entity_id` bigint DEFAULT NULL,
  `payload_json` json DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_audit_entity` (`entity_type`,`entity_id`),
  KEY `fk_audit_user` (`actor_user_id`),
  CONSTRAINT `fk_audit_user` FOREIGN KEY (`actor_user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_log`
--

LOCK TABLES `audit_log` WRITE;
/*!40000 ALTER TABLE `audit_log` DISABLE KEYS */;
INSERT INTO `audit_log` VALUES (1,1,'CREATE','ITEM',1,'{\"sku\": \"SKU-001\"}','2025-12-31 04:12:17'),(2,1,'CREATE','ITEM',2,'{\"sku\": \"SKU-002\"}','2025-12-31 04:12:17'),(3,2,'UPDATE','STOCK',1,'{\"qty\": 5}','2025-12-31 04:12:17'),(4,3,'ISSUE','ITEM',3,'{\"qty\": 1}','2025-12-31 04:12:17'),(5,4,'LOGIN','USER',4,'{}','2025-12-31 04:12:17'),(6,5,'CREATE','ISSUE',1,'{\"code\": \"ISS-001\"}','2025-12-31 04:12:17'),(7,6,'APPROVE','ISSUE',2,'{\"approved\": true}','2025-12-31 04:12:17'),(8,7,'CANCEL','ISSUE',8,'{\"reason\": \"error\"}','2025-12-31 04:12:17'),(9,8,'UPDATE','ITEM',9,'{\"min_stock\": 20}','2025-12-31 04:12:17'),(10,9,'LOGIN','USER',9,'{}','2025-12-31 04:12:17');
/*!40000 ALTER TABLE `audit_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (9,'Assets'),(8,'Consumables'),(3,'Electronics'),(4,'Furniture'),(1,'IT Equipment'),(5,'Networking'),(2,'Office Supplies'),(10,'Spare Parts'),(7,'Stationery'),(6,'Tools');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `issue_items`
--

DROP TABLE IF EXISTS `issue_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `issue_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `issue_id` bigint NOT NULL,
  `item_id` bigint NOT NULL,
  `qty` decimal(18,6) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_i_items_issue` (`issue_id`),
  KEY `fk_i_items_item` (`item_id`),
  CONSTRAINT `fk_i_items_issue` FOREIGN KEY (`issue_id`) REFERENCES `issues` (`id`),
  CONSTRAINT `fk_i_items_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `issue_items`
--

LOCK TABLES `issue_items` WRITE;
/*!40000 ALTER TABLE `issue_items` DISABLE KEYS */;
INSERT INTO `issue_items` VALUES (1,1,1,1.000000),(2,2,3,1.000000),(3,3,5,2.000000),(4,4,7,1.000000),(5,5,2,1.000000),(6,6,4,3.000000),(7,7,6,1.000000),(8,8,8,1.000000),(9,9,9,10.000000),(10,10,10,1.000000),(21,11,21,2.000000),(22,12,22,1.000000),(23,13,23,5.000000),(24,14,24,1.000000),(25,15,25,1.000000),(26,16,27,2.000000),(27,17,29,10.000000),(28,18,34,2.000000),(29,19,30,1.000000),(30,20,27,1.000000),(31,21,41,1.000000),(32,21,42,1.000000),(33,21,44,1.000000),(34,22,45,1.000000),(35,21,46,1.000000);
/*!40000 ALTER TABLE `issue_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `issues`
--

DROP TABLE IF EXISTS `issues`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `issues` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(40) NOT NULL,
  `status` enum('DRAFT','APPROVED','ISSUED','CANCELLED') NOT NULL DEFAULT 'DRAFT',
  `requested_by` bigint DEFAULT NULL,
  `approved_by` bigint DEFAULT NULL,
  `issued_at` datetime DEFAULT NULL,
  `note` varchar(255) DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `fk_issue_req` (`requested_by`),
  KEY `fk_issue_app` (`approved_by`),
  CONSTRAINT `fk_issue_app` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_issue_req` FOREIGN KEY (`requested_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `issues`
--

LOCK TABLES `issues` WRITE;
/*!40000 ALTER TABLE `issues` DISABLE KEYS */;
INSERT INTO `issues` VALUES (1,'ISS-001','ISSUED',2,1,'2025-12-31 12:11:35','Office usage','2025-12-31 12:11:35'),(2,'ISS-002','ISSUED',3,1,'2025-12-31 12:11:35','IT maintenance','2025-12-31 12:11:35'),(3,'ISS-003','APPROVED',4,1,'2025-12-31 12:11:35','Pending issue','2025-12-31 12:11:35'),(4,'ISS-004','DRAFT',5,1,'2025-12-31 12:11:35','Draft request','2025-12-31 12:11:35'),(5,'ISS-005','ISSUED',6,1,'2025-12-31 12:11:35','Replacement','2025-12-31 12:11:35'),(6,'ISS-006','ISSUED',7,1,'2025-12-31 12:11:35','Lab usage','2025-12-31 12:11:35'),(7,'ISS-007','APPROVED',8,1,'2025-12-31 12:11:35','Approval stage','2025-12-31 12:11:35'),(8,'ISS-008','CANCELLED',9,1,'2025-12-31 12:11:35','Cancelled','2025-12-31 12:11:35'),(9,'ISS-009','ISSUED',10,1,'2025-12-31 12:11:35','Office setup','2025-12-31 12:11:35'),(10,'ISS-010','DRAFT',2,1,'2025-12-31 12:11:35','New request','2025-12-31 12:11:35'),(11,'ISS-011','ISSUED',3,1,'2025-12-31 12:12:41','New monitor setup','2025-12-31 12:12:41'),(12,'ISS-012','ISSUED',4,1,'2025-12-31 12:12:41','UPS replacement','2025-12-31 12:12:41'),(13,'ISS-013','APPROVED',5,1,'2025-12-31 12:12:41','Cable deployment','2025-12-31 12:12:41'),(14,'ISS-014','DRAFT',6,1,'2025-12-31 12:12:41','Projector request','2025-12-31 12:12:41'),(15,'ISS-015','ISSUED',7,1,'2025-12-31 12:12:41','Meeting room equipment','2025-12-31 12:12:41'),(16,'ISS-016','ISSUED',8,1,'2025-12-31 12:12:41','Storage upgrade','2025-12-31 12:12:41'),(17,'ISS-017','APPROVED',9,1,'2025-12-31 12:12:41','Network expansion','2025-12-31 12:12:41'),(18,'ISS-018','ISSUED',10,1,'2025-12-31 12:12:41','Asset replacement','2025-12-31 12:12:41'),(19,'ISS-019','DRAFT',2,1,'2025-12-31 12:12:41','Tool request','2025-12-31 12:12:41'),(20,'ISS-020','ISSUED',3,1,'2025-12-31 12:12:41','IT onboarding','2025-12-31 12:12:41'),(21,'ISS-021','DRAFT',1,1,'2026-01-05 10:23:10','Starlink device','2026-01-05 10:23:10'),(22,'ISS-022','DRAFT',1,1,'2026-01-05 10:24:00','Laptop leased','2026-01-05 10:24:00');
/*!40000 ALTER TABLE `issues` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `items`
--

DROP TABLE IF EXISTS `items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item_code` varchar(20) NOT NULL,
  `serial_number` varchar(40) DEFAULT NULL,
  `name` varchar(160) NOT NULL,
  `category_id` bigint NOT NULL,
  `unit_id` bigint NOT NULL,
  `owner_user_id` bigint DEFAULT NULL,
  `min_stock` decimal(18,6) NOT NULL DEFAULT '0.000000',
  `description` varchar(500) DEFAULT NULL,
  `image_url` varchar(255) DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`item_code`),
  UNIQUE KEY `item_code` (`item_code`),
  KEY `fk_items_category` (`category_id`),
  KEY `fk_items_unit` (`unit_id`),
  KEY `fk_items_owner` (`owner_user_id`),
  CONSTRAINT `fk_items_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`),
  CONSTRAINT `fk_items_owner` FOREIGN KEY (`owner_user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_items_unit` FOREIGN KEY (`unit_id`) REFERENCES `units` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `items`
--

LOCK TABLES `items` WRITE;
/*!40000 ALTER TABLE `items` DISABLE KEYS */;
INSERT INTO `items` VALUES (1,'SKU-001',NULL,'Laptop Dell Latitude',1,2,1,2.000000,NULL,NULL,1),(2,'SKU-002',NULL,'Office Chair',4,2,1,5.000000,NULL,NULL,1),(3,'SKU-003',NULL,'Network Switch',5,2,1,1.000000,NULL,NULL,1),(4,'SKU-004',NULL,'Printer Ink',8,1,1,10.000000,NULL,NULL,1),(5,'SKU-005',NULL,'HDMI Cable',5,1,1,15.000000,NULL,NULL,1),(6,'SKU-006',NULL,'Desk Lamp',3,2,1,3.000000,NULL,NULL,1),(7,'SKU-007',NULL,'Mouse Wireless',1,1,1,10.000000,NULL,NULL,1),(8,'SKU-008',NULL,'Keyboard Mechanical',1,1,1,5.000000,NULL,NULL,1),(9,'SKU-009',NULL,'Paper A4',7,3,1,20.000000,NULL,NULL,1),(10,'SKU-010',NULL,'Router MikroTik',5,2,1,2.000000,NULL,NULL,1),(21,'SKU-011',NULL,'Monitor 24 Inch',3,2,1,2.000000,NULL,NULL,1),(22,'SKU-012',NULL,'UPS 1200VA',3,2,2,1.000000,NULL,NULL,1),(23,'SKU-013',NULL,'Extension Cord',5,1,3,5.000000,NULL,NULL,1),(24,'SKU-014',NULL,'Projector Epson',3,2,1,1.000000,NULL,NULL,1),(25,'SKU-015',NULL,'Whiteboard',4,2,4,1.000000,NULL,NULL,1),(26,'SKU-016',NULL,'Webcam HD',1,1,5,3.000000,NULL,NULL,1),(27,'SKU-017',NULL,'External HDD 1TB',1,1,6,2.000000,NULL,NULL,1),(28,'SKU-018',NULL,'Flashdisk 32GB',1,1,7,10.000000,NULL,NULL,1),(29,'SKU-019',NULL,'Ethernet Cable CAT6',5,1,8,20.000000,NULL,NULL,1),(30,'SKU-020',NULL,'Power Adapter',3,1,9,5.000000,NULL,NULL,1),(31,'SKU-021',NULL,'Server Rack 42U',4,2,1,1.000000,NULL,NULL,1),(32,'SKU-022',NULL,'Patch Panel',5,2,2,2.000000,NULL,NULL,1),(33,'SKU-023',NULL,'Firewall Appliance',5,2,1,1.000000,NULL,NULL,1),(34,'SKU-024',NULL,'SSD 512GB',1,1,3,3.000000,NULL,NULL,1),(35,'SKU-025',NULL,'RAM 16GB',1,1,4,4.000000,NULL,NULL,1),(36,'SKU-026',NULL,'Laptop Stand',4,1,5,5.000000,NULL,NULL,1),(37,'SKU-027','PR24412','Barcode Scanner',1,1,6,2.000000,'New barcode scanner',NULL,1),(38,'SKU-028',NULL,'Label Printer',3,2,7,1.000000,NULL,NULL,1),(39,'SKU-029',NULL,'Cleaning Kit',8,1,8,10.000000,NULL,NULL,1),(40,'SKU-030',NULL,'Toolbox Set',6,2,9,1.000000,NULL,NULL,1),(41,'SKU-0014512',NULL,'Starlink mini kit',5,1,1,1.000000,NULL,NULL,1),(42,'SKU-04512',NULL,'Starlink mini kit',5,1,1,1.000000,NULL,NULL,1),(44,'SKU-04513',NULL,'Starlink standard kit',5,1,1,1.000000,NULL,NULL,1),(45,'SKU-45',NULL,'Lenovo LED Monitor 27 inch',1,2,1,1.000000,NULL,NULL,1),(46,'SKU-46',NULL,'Lenovo LED Monitor 27 inch, black color',1,2,1,1.000000,NULL,NULL,1);
/*!40000 ALTER TABLE `items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `locations`
--

DROP TABLE IF EXISTS `locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `locations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  `code` varchar(24) NOT NULL,
  `active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `locations`
--

LOCK TABLES `locations` WRITE;
/*!40000 ALTER TABLE `locations` DISABLE KEYS */;
INSERT INTO `locations` VALUES (1,'Main Warehouse','WH-MAIN',1),(2,'IT Room','IT-RM',1),(3,'Office Storage','OFF-ST',1),(4,'Production Floor','PROD-FL',1),(5,'Spare Room','SPARE',1),(6,'Finance Room','FIN-RM',1),(7,'HR Storage','HR-ST',1),(8,'Lab A','LAB-A',1),(9,'Lab B','LAB-B',1),(10,'Temporary Storage','TMP-ST',1);
/*!40000 ALTER TABLE `locations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `settings`
--

DROP TABLE IF EXISTS `settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `settings` (
  `id` int NOT NULL DEFAULT '1',
  `app_name` varchar(100) NOT NULL DEFAULT 'Inventory Management System',
  `items_per_page` int NOT NULL DEFAULT '50',
  `allow_negative_stock` tinyint(1) NOT NULL DEFAULT '0',
  `auto_backup_enabled` tinyint(1) NOT NULL DEFAULT '1',
  `backup_retention_days` int NOT NULL DEFAULT '30',
  `low_stock_threshold` int NOT NULL DEFAULT '10',
  `enable_notifications` tinyint(1) NOT NULL DEFAULT '1',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `updated_by` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `updated_by` (`updated_by`),
  CONSTRAINT `settings_ibfk_1` FOREIGN KEY (`updated_by`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `chk_id` CHECK ((`id` = 1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `settings`
--

LOCK TABLES `settings` WRITE;
/*!40000 ALTER TABLE `settings` DISABLE KEYS */;
INSERT INTO `settings` VALUES (1,'Inventory Management System',50,0,1,30,10,1,'2026-01-05 07:38:07',NULL);
/*!40000 ALTER TABLE `settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_levels`
--

DROP TABLE IF EXISTS `stock_levels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_levels` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item_id` bigint NOT NULL,
  `location_id` bigint NOT NULL,
  `qty_on_hand` decimal(18,6) NOT NULL DEFAULT '0.000000',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_item_location` (`item_id`,`location_id`),
  KEY `fk_sl_loc` (`location_id`),
  CONSTRAINT `fk_sl_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`),
  CONSTRAINT `fk_sl_loc` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_levels`
--

LOCK TABLES `stock_levels` WRITE;
/*!40000 ALTER TABLE `stock_levels` DISABLE KEYS */;
INSERT INTO `stock_levels` VALUES (21,1,1,40.000000,'2026-01-06 05:21:53'),(22,2,1,75.000000,'2026-01-06 05:21:53'),(23,3,2,150.000000,'2026-01-06 05:21:53'),(24,4,3,30.000000,'2025-12-31 03:29:48'),(25,5,1,20.000000,'2025-12-31 03:29:48'),(26,6,4,4.000000,'2025-12-31 03:29:48'),(27,7,5,12.000000,'2025-12-31 03:29:48'),(28,8,6,7.000000,'2025-12-31 03:29:48'),(29,9,7,50.000000,'2025-12-31 03:29:48'),(30,10,1,3.000000,'2025-12-31 03:29:48'),(34,4,1,55.000000,'2026-01-06 05:21:53'),(35,4,2,20.000000,'2026-01-06 05:21:53'),(36,5,2,150.000000,'2026-01-06 05:21:53');
/*!40000 ALTER TABLE `stock_levels` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_tx`
--

DROP TABLE IF EXISTS `stock_tx`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_tx` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `item_id` bigint NOT NULL,
  `location_id` bigint NOT NULL,
  `tx_type` enum('IN','OUT','ADJ','XFER') NOT NULL,
  `qty` decimal(18,6) NOT NULL,
  `ref` varchar(80) DEFAULT NULL,
  `note` varchar(255) DEFAULT NULL,
  `tx_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_tx_item` (`item_id`),
  KEY `fk_tx_loc` (`location_id`),
  KEY `fk_tx_user` (`user_id`),
  CONSTRAINT `fk_tx_item` FOREIGN KEY (`item_id`) REFERENCES `items` (`id`),
  CONSTRAINT `fk_tx_loc` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`),
  CONSTRAINT `fk_tx_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_tx`
--

LOCK TABLES `stock_tx` WRITE;
/*!40000 ALTER TABLE `stock_tx` DISABLE KEYS */;
INSERT INTO `stock_tx` VALUES (11,1,1,'IN',5.000000,'INIT','Initial stock','2025-12-31 03:31:36',1),(12,2,1,'IN',8.000000,'INIT','Initial stock','2025-12-31 03:31:36',1),(13,3,2,'IN',2.000000,'INIT','Initial stock','2025-12-31 03:31:36',1),(14,4,3,'IN',30.000000,'INIT','Initial stock','2025-12-31 03:31:36',1),(15,5,1,'IN',20.000000,'INIT','Initial stock','2025-12-31 03:31:36',1),(16,6,4,'IN',4.000000,'INIT','Initial stock','2025-12-31 03:31:36',1),(17,7,5,'IN',12.000000,'INIT','Initial stock','2025-12-31 03:31:36',1),(18,8,6,'IN',7.000000,'INIT','Initial stock','2025-12-31 03:31:36',1),(19,9,7,'IN',50.000000,'INIT','Initial stock','2025-12-31 03:31:36',1),(20,10,1,'IN',3.000000,'INIT','Initial stock','2025-12-31 03:31:36',1),(21,1,1,'IN',5.000000,'INIT','Initial stock','2025-12-31 04:10:48',1),(22,2,1,'IN',8.000000,'INIT','Initial stock','2025-12-31 04:10:48',1),(23,3,2,'IN',2.000000,'INIT','Initial stock','2025-12-31 04:10:48',1),(24,4,3,'IN',30.000000,'INIT','Initial stock','2025-12-31 04:10:48',1),(25,5,1,'IN',20.000000,'INIT','Initial stock','2025-12-31 04:10:48',1),(26,6,4,'IN',4.000000,'INIT','Initial stock','2025-12-31 04:10:48',1),(27,7,5,'IN',12.000000,'INIT','Initial stock','2025-12-31 04:10:48',1),(28,8,6,'IN',7.000000,'INIT','Initial stock','2025-12-31 04:10:48',1),(29,9,7,'IN',50.000000,'INIT','Initial stock','2025-12-31 04:10:48',1),(30,10,1,'IN',3.000000,'INIT','Initial stock','2025-12-31 04:10:48',1),(31,1,1,'IN',50.000000,'PO-2026-001','Initial stock purchase','2026-01-01 01:00:00',1),(32,1,1,'OUT',10.000000,'ISS-001','Issued to project A','2026-01-02 02:30:00',1),(33,2,1,'IN',100.000000,'PO-2026-002','Bulk purchase for warehouse','2026-01-03 00:15:00',1),(34,2,1,'OUT',25.000000,'ISS-002','Department requisition','2026-01-03 06:20:00',1),(35,3,2,'ADJ',200.000000,'ADJ-001','Inventory count adjustment','2026-01-04 03:00:00',1),(36,3,2,'OUT',50.000000,'ISS-003','Project B allocation','2026-01-04 07:45:00',1),(37,4,1,'IN',75.000000,'RET-001','Returned from project C','2026-01-05 01:30:00',1),(38,4,1,'XFER',-20.000000,'XFER-001','Transfer to Location 2','2026-01-05 08:00:00',1),(39,4,2,'XFER',20.000000,'XFER-001','Transfer from Location 1','2026-01-05 08:00:00',1),(40,5,2,'IN',150.000000,'PO-2026-003','Quarterly stock replenishment','2026-01-05 23:45:00',1);
/*!40000 ALTER TABLE `stock_tx` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `units`
--

DROP TABLE IF EXISTS `units`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `units` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(40) NOT NULL,
  `symbol` varchar(16) NOT NULL,
  `multiplier` decimal(12,6) NOT NULL DEFAULT '1.000000',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `units`
--

LOCK TABLES `units` WRITE;
/*!40000 ALTER TABLE `units` DISABLE KEYS */;
INSERT INTO `units` VALUES (1,'Piece','pcs',1.000000),(2,'Unit','unit',1.000000),(3,'Box','box',1.000000),(4,'Pack','pack',1.000000),(5,'Meter','m',1.000000),(6,'Kilogram','kg',1.000000),(7,'Liter','ltr',1.000000),(8,'Set','set',1.000000),(9,'Roll','roll',1.000000),(10,'Bottle','btl',1.000000);
/*!40000 ALTER TABLE `units` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `email` varchar(160) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('ADMIN','STAFF','AUDITOR') NOT NULL DEFAULT 'STAFF',
  `active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Administrator','it.security@example.com','$2b$12$1hMtzv8paRdHAyXFBuj.Ae5NmqM7YG6PQw2p33xesLmHgRJ49XVle','ADMIN',1,'2025-12-30 19:24:15'),(2,'Rudy Hendrawan','rudy@example.com','$2b$12$19Y4kfmaXclIA9/YNC/uhuGm4rWPoB7jqkEtaf/WJ.nc36LUKAX5i','ADMIN',1,'2025-12-30 20:09:33'),(3,'Dewi Lestari','dewi@example.com','$2b$12$YAor1MrpNlclo5cJgaWYBezHaXlgSdOFKgEmYFburtfkHkJXIe2lO','STAFF',1,'2025-12-30 20:09:33'),(4,'Made Wirawan','made@example.com','$2b$12$8n7XM8CIy5ndiM/Rn6k0m.JU/vyVEg9Uys/lnVdx4z97tkxobFIa2','AUDITOR',1,'2025-12-30 20:09:33'),(5,'Putra Adi','putra@example.com','$2b$12$h9BRP0iYP/5K.Ah/6ZDceOnvDnRpYEX20ivG9i4tP5HP4P4BmvfUS','STAFF',1,'2025-12-30 20:09:33'),(6,'Ayu Puspita','ayu@example.com','$2b$12$lzsJyNGrwnXK20YwVNK8N.52fpOhZLrJCNUTQYpmTLV2fiNhUzfk.','STAFF',1,'2025-12-30 20:09:33'),(7,'Budi Santoso','budi@example.com','$2b$12$NG6uIFhWNQXzIEi7A0Mxhefmq4OeyRsB5uG.EwkD7Wy97vOkLNL5e','STAFF',1,'2025-12-30 20:09:33'),(8,'Sari Wulandari','sari@example.com','$2b$12$6EOncp8rT4sEAKNHVi.dlORk5o4PlsW7WjkUs1817kgEJq2VBULuC','STAFF',1,'2025-12-30 20:09:33'),(9,'Komang Arya','komang@example.com','$2b$12$035Xl9kxPPdceOBxCy/s4.3VfVPfLToMYN0GtYlOOepnvsUUnKP0S','STAFF',1,'2025-12-30 20:09:33'),(10,'Indra Wijaya','indra@example.com','$2b$12$HQySqyJKNzoLOncvXhYYlufsqFIhHIz5k.UbrtrHhiZJruOJWe48i','STAFF',1,'2025-12-30 20:09:33'),(11,'Nina Pratiwi','nina@example.com','$2b$12$1eMnWkN9QCsXKmD.x4Wv1uJw7VPv4LjFLAOMu3.0jkK0qcuSyxbc2','STAFF',1,'2025-12-30 20:09:33');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-06 19:38:39
