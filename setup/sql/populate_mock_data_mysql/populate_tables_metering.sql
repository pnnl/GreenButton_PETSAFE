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

--
-- You'll need to add subscriptions; I was told to avoid touching that table for now
-- I'll assume there's an ID of 1 that already exists; adjust that if needed
--

--
-- Time zones:
-- https://www.greenbuttonalliance.org/daylight-savings-time
--
INSERT INTO time_configurations (`id`, `description`, `published`, `self_link_href`, `self_link_rel`, `up_link_href`, `up_link_rel`, `updated`, `uuid`, `dstEndRule`, `dstOffset`, `dstStartRule`, `tzOffset`) VALUES (1, "PST", 1737536400000, "/speedes/1_0/timezones/1", "self", "/speedes/1_0/timezones", "up", 1737536400000, "08502cf0dd3a404ea4e848c42", "B40E2000", -25200, "360E2000", -28800);
INSERT INTO time_configurations (`id`, `description`, `published`, `self_link_href`, `self_link_rel`, `up_link_href`, `up_link_rel`, `updated`, `uuid`, `dstEndRule`, `dstOffset`, `dstStartRule`, `tzOffset`) VALUES (1, "MST", 1737536400000, "/speedes/1_0/timezones/2", "self", "/speedes/1_0/timezones", "up", 1737536400000, "800052880df6466f9f3a3229a", "B40E2000", -21600, "360E2000", -25200);

--
-- Retail customers
--
INSERT INTO retail_customers (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `enabled`, `username`, `first_name`, `last_name`, `password`, `role`) VALUES (0, '', '2014-01-02 05:00:00', '/speedes/1_0/RetailCustomer/1','self','/speedes/1_0/RetailCustomer','up','2014-01-02 05:00:00','F06E8B03-0299-467E-972A-A883ECDCC575', TRUE, 'grace', 'Grace', 'Hopper', 'koala', 'ROLE_CUSTODIAN');
INSERT INTO retail_customers (`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `enabled`, `username`, `first_name`, `last_name`, `password`, `role`) VALUES ('', '2014-01-02 05:00:00', '/speedes/1_0/RetailCustomer/1','self','/speedes/1_0/RetailCustomer','up','2014-01-02 05:00:00','106E8B03-0299-467E-972A-A883ECDCC575', TRUE, 'alan', 'Alan', 'Turing', 'koala', 'ROLE_USER');
INSERT INTO retail_customers (`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `enabled`, `username`, `first_name`, `last_name`, `password`, `role`) VALUES ('', '2014-01-02 05:00:00', '/speedes/1_0/RetailCustomer/1','self','/speedes/1_0/RetailCustomer','up','2014-01-02 05:00:00','206E8B03-0299-467E-972A-A883ECDCC575', TRUE, 'donald', 'Donald', 'Knuth','koala', 'ROLE_USER');
INSERT INTO retail_customers (`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `enabled`, `username`, `first_name`, `last_name`, `password`, `role`) VALUES ('', '2014-01-02 05:00:00', '/speedes/1_0/RetailCustomer/1','self','/speedes/1_0/RetailCustomer','up','2014-01-02 05:00:00','306E8B03-0299-467E-972A-A883ECDCC575', TRUE, 'paul', 'Paul', 'Dirac', 'koala', 'ROLE_USER');

--
-- Service delivery points
--
INSERT INTO service_delivery_points (`id`, `customerAgreement`, `name`, `tariffProfile`) VALUES (1, "", "123 Street External Meter Socket", "");
INSERT INTO service_delivery_points (`id`, `customerAgreement`, `name`, `tariffProfile`) VALUES (2, "", "West Point Housing Meter Socket", "");
INSERT INTO service_delivery_points (`id`, `customerAgreement`, `name`, `tariffProfile`) VALUES (3, "", "Sample Avenue Aggregate Socket", "");

--
-- Usage points
--
INSERT INTO usage_points (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `roleFlags`, `status`, `uri`, `localTimeParameters_id`, `retail_customer_id`, `serviceCategory_kind`, `serviceDeliveryPoint_id`, `subscription_id`) VALUES (1, "", 1737536400000, "/speedes/1_0/usagepoints/1", "self", "/speedes/1_0/usagepoints", "up", 1737536400000, "38265a2d-9dd3-4310-a49d-cc871747aefc", 0100000000000000, 1, "https://example.com?meter=1", 1, 1, "bigint for service category kind", 1, 1);
INSERT INTO usage_points (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `roleFlags`, `status`, `uri`, `localTimeParameters_id`, `retail_customer_id`, `serviceCategory_kind`, `serviceDeliveryPoint_id`, `subscription_id`) VALUES (2, "", 1737536400000, "/speedes/1_0/usagepoints/2", "self", "/speedes/1_0/usagepoints", "up", 1737536400000, "5b97f042-ba7f-48f7-839f-9bec433c9e50", 0100000000000000, 1, "https://example.com?meter=2", 2, 2, "bigint for service category kind", 1, 2);
INSERT INTO usage_points (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `roleFlags`, `status`, `uri`, `localTimeParameters_id`, `retail_customer_id`, `serviceCategory_kind`, `serviceDeliveryPoint_id`, `subscription_id`) VALUES (3, "", 1737536400000, "/speedes/1_0/usagepoints/3", "self", "/speedes/1_0/usagepoints", "up", 1737536400000, "4ca086cd-541a-4550-8a6e-2193371baab5", 0100000000000000, 0, "https://example.com?meter=3", 1, 1, "bigint for service category kind", 1, 1);

--
-- Reading types
--

INSERT INTO reading_types (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`,`accumulationBehavior`,`rational_denominator`,`rational_numerator`,`commodity`,`consumptionTier`,`cpp`,`dataQualifier`,`defaultQuality`,`flowDirection`,`interharmonic_denominator`,`interharmonic_numerator`,`intervalLength`,`kind`,`measuringPeriod`,`phase`,`powerOfTenMultiplier`,`timeAttribute`,`tou`,`uom`) VALUES (1, "15 Minute Electrical Consumption North America", 1737536400000, "/speedes/1_0/readingTypes/1", self, "/speedes/1_0/readingTypes", "up", 1737536400000, "d49c35cf-49f7-441b-82e3-3a4209de1c77", "4", "", "", "1", "", "", "12", "", "1", "", "", "", "12", "", "769", "3", "3", "", "72");

--
-- Meter readings
--
INSERT INTO meter_readings (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `reading_type_id`, `usage_point_id`) VALUES (1, "", 1737536400000, "/speedes/1_0/meterreadings/1", "self", "/speedes/1_0/meterreadings", "up", 1737536400000, "060ab976-8aed-409a-92c3-892b255e3916", 1, 1);
INSERT INTO meter_readings (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `reading_type_id`, `usage_point_id`) VALUES (2, "", 1737536400000, "/speedes/1_0/meterreadings/2", "self", "/speedes/1_0/meterreadings", "up", 1737536400000, "1e2f6930-6719-47be-800f-4d48637e960e", 1, 2);
INSERT INTO meter_readings (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `reading_type_id`, `usage_point_id`) VALUES (3, "", 1737536400000, "/speedes/1_0/meterreadings/3", "self", "/speedes/1_0/meterreadings", "up", 1737536400000, "9dc2fdd9-f139-4feb-a706-8ee661560448", 1, 3);

--
-- Interval blocks
-- duration is in seconds; 900 = 15 minute interval
--
INSERT INTO interval_blocks (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `duration`, `start`, `meter_reading_id`) VALUES (1, "", 1737536400000, "/speedes/1_0/intervalblocks/1", "self", "/speedes/1_0/intervalblocks", "up", 1737536400000, "754ce232-9ab2-4cd4-977d-272abfd01a71", 900, 1737536400000, 1);
INSERT INTO interval_blocks (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `duration`, `start`, `meter_reading_id`) VALUES (2, "", 1737536400900, "/speedes/1_0/intervalblocks/2", "self", "/speedes/1_0/intervalblocks", "up", 1737536400900, "ec435711-ae04-47d2-9202-e933bddfdccf", 900, 1737536400900, 1);

INSERT INTO interval_blocks (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `duration`, `start`, `meter_reading_id`) VALUES (3, "", 1737536400000, "/speedes/1_0/intervalblocks/3", "self", "/speedes/1_0/intervalblocks", "up", 1737536400000, "856e9517-9d8e-43a6-a3d8-a04e4b37fcfb", 900, 1737536400000, 2);
INSERT INTO interval_blocks (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `duration`, `start`, `meter_reading_id`) VALUES (4, "", 1737536400900, "/speedes/1_0/intervalblocks/4", "self", "/speedes/1_0/intervalblocks", "up", 1737536400900, "c81717d1-74ff-40d1-bb89-6ff8eb24df68", 900, 1737536400900, 2);

INSERT INTO interval_blocks (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `duration`, `start`, `meter_reading_id`) VALUES (5, "", 1737536400000, "/speedes/1_0/intervalblocks/5", "self", "/speedes/1_0/intervalblocks", "up", 1737536400000, "01a3cd40-b575-4e06-8b19-39ca2882a427", 900, 1737536400000, 3);
INSERT INTO interval_blocks (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `duration`, `start`, `meter_reading_id`) VALUES (6, "", 1737536400900, "/speedes/1_0/intervalblocks/6", "self", "/speedes/1_0/intervalblocks", "up", 1737536400900, "0d61be09-5c1d-400a-8548-8fad95f329a2", 900, 1737536400900, 3);