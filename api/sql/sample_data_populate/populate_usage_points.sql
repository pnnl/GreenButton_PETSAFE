USE `datacustodian`;
-- MySQL dump 10.13  Distrib 5.5.35, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: datacustodian
-- ------------------------------------------------------
-- Server version	5.5.35-0ubuntu0.12.04.2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- SET GLOBAL default_table_encryption=ON;

---
--- Bare minimum inserts for usage_points to work
---

---
--- You'll need to add subscriptions; I was told to avoid touching that table for now
--- I'll assume there's an ID of 1 that already exists; adjust that accordingly
---

---
--- Time zones:
--- https://www.greenbuttonalliance.org/daylight-savings-time
---
INSERT INTO time_configurations (`id`, `description`, `published`, `self_link_href`, `self_link_rel`, `up_link_href`, `up_link_rel`, `updated`, `uuid`, `dstEndRule`, `dstOffset`, `dstStartRule`, `tzOffset`) VALUES (1, "PST", 1737536400000, "/speedes/1_0/timezones/1", "self", "/speedes/1_0/timezones", "up", 1737536400000, "08502cf0dd3a404ea4e848c42", "B40E2000", -25200, "360E2000", -28800);
INSERT INTO time_configurations (`id`, `description`, `published`, `self_link_href`, `self_link_rel`, `up_link_href`, `up_link_rel`, `updated`, `uuid`, `dstEndRule`, `dstOffset`, `dstStartRule`, `tzOffset`) VALUES (1, "MST", 1737536400000, "/speedes/1_0/timezones/2", "self", "/speedes/1_0/timezones", "up", 1737536400000, "800052880df6466f9f3a3229a", "B40E2000", -21600, "360E2000", -25200);

---
--- Retail customers:
---
INSERT INTO retail_customers (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `enabled`, `username`, `first_name`, `last_name`, `password`, `role`) VALUES (0, '', '2014-01-02 05:00:00', '/RetailCustomer/1','self','/RetailCustomer','up','2014-01-02 05:00:00','F06E8B03-0299-467E-972A-A883ECDCC575', TRUE, 'grace', 'Grace', 'Hopper', 'koala', 'ROLE_CUSTODIAN');
INSERT INTO retail_customers (`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `enabled`, `username`, `first_name`, `last_name`, `password`, `role`) VALUES ('', '2014-01-02 05:00:00', '/RetailCustomer/1','self','/RetailCustomer','up','2014-01-02 05:00:00','106E8B03-0299-467E-972A-A883ECDCC575', TRUE, 'alan', 'Alan', 'Turing', 'koala', 'ROLE_USER');
INSERT INTO retail_customers (`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `enabled`, `username`, `first_name`, `last_name`, `password`, `role`) VALUES ('', '2014-01-02 05:00:00', '/RetailCustomer/1','self','/RetailCustomer','up','2014-01-02 05:00:00','206E8B03-0299-467E-972A-A883ECDCC575', TRUE, 'donald', 'Donald', 'Knuth','koala', 'ROLE_USER');
INSERT INTO retail_customers (`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `enabled`, `username`, `first_name`, `last_name`, `password`, `role`) VALUES ('', '2014-01-02 05:00:00', '/RetailCustomer/1','self','/RetailCustomer','up','2014-01-02 05:00:00','306E8B03-0299-467E-972A-A883ECDCC575', TRUE, 'paul', 'Paul', 'Dirac', 'koala', 'ROLE_USER');

---
--- Service delivery points TODO
---
INSERT INTO service_delivery_points (`id`, `customerAgreement`, `name`, `tariffProfile`) VALUES ();


---
--- Usage points
---
INSERT INTO usage_points (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `roleFlags`, `status`, `uri`, `localTimeParameters_id`, `retail_customer_id`, `serviceCategory_kind`, `serviceDeliveryPoint_id`, `subscription_id`) VALUES (1, "description goes here", 1737536400000, "/speedes/1_0/usagepoints/1", "self", "/speedes/1_0/usagepoints", "up", 1737536400000, "uuid goes here", "roleflags blob", "status goes here", "uri goes here", 1, 1, "bigint for service category kind", 1, 1);
INSERT INTO usage_points (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `roleFlags`, `status`, `uri`, `localTimeParameters_id`, `retail_customer_id`, `serviceCategory_kind`, `serviceDeliveryPoint_id`, `subscription_id`) VALUES (1, "description goes here", 1737536400000, "/speedes/1_0/usagepoints/1", "self", "/speedes/1_0/usagepoints", "up", 1737536400000, "uuid goes here", "roleflags blob", "status goes here", "uri goes here", 1, 1, "bigint for service category kind", 1, 1);
INSERT INTO usage_points (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `roleFlags`, `status`, `uri`, `localTimeParameters_id`, `retail_customer_id`, `serviceCategory_kind`, `serviceDeliveryPoint_id`, `subscription_id`) VALUES (1, "description goes here", 1737536400000, "/speedes/1_0/usagepoints/1", "self", "/speedes/1_0/usagepoints", "up", 1737536400000, "uuid goes here", "roleflags blob", "status goes here", "uri goes here", 1, 1, "bigint for service category kind", 1, 1);