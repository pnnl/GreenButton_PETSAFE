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


INSERT INTO reading_types (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`,`accumulationBehavior`,`rational_denominator`,`rational_numerator`,`commodity`,`consumptionTier`,`cpp`,`dataQualifier`,`defaultQuality`,`flowDirection`,`interharmonic_denominator`,`interharmonic_numerator`,`intervalLength`,`kind`,`measuringPeriod`,`phase`,`powerOfTenMultiplier`,`timeAttribute`,`tou`,`uom`) VALUES ();
                            1, "base electrical", 1737536400000, "/speedes/1_0/readingTypes/1", self, "/speedes/1_0/readingTypes", "up", 1737536400000, "d49c35cf-49f7-441b-82e3-3a4209de1c77", "", "", "", "electricity", "", "", "", "", "", "", "", 15, "", "", "", 1, "", "", "");