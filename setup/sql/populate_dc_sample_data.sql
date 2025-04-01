/* Add application_information */
SET sql_mode = 'PIPES_AS_CONCAT';

SET @dcbaseurl = 'http://localhost:8080';
SET @tpbaseurl = 'http://localhost:9090';

USE datacustodian;


/* 
Insert known time zones 
For format, see https://www.greenbuttonalliance.org/daylight-savings-time

Example for United States DST as of 2024-01-22:
---
dstStartRule:
2nd Sunday of March at 2:00 AM (skips directly to 3 AM)
Decimal: 3 3 0 7 2 0
Binary: 0011 011 00000 111 00010 000000000000
Hexadecimal (stored value): 360E2000
---
dstEndRule:
1st Sunday of November at 2:00 AM (skips back and repeats 1 AM)
Decimal: 11 2 0 7 2 0
Binary: 1011 010 00000 111 00010 000000000000
Hexadecimal (stored value): B40E2000
*/
START TRANSACTION;
/* Pacific Standard Time */
INSERT INTO time_configurations (`id`, `description`, `published`, `self_link_href`, `self_link_rel`, `up_link_href`, `up_link_rel`, `updated`, `uuid`, `dstEndRule`, `dstOffset`, `dstStartRule`, `tzOffset`) VALUES (1, "PST", "2025-01-22 09:00:00", "/speedes/1_0/timezones/1", "self", "/speedes/1_0/timezones", "up", "2025-01-22 09:00:00", "af11dcbb-f7c4-4898-b298-8d791de4bd98", "B40E2000", -25200, "360E2000", -28800);
/* Mountain Standard Time */
INSERT INTO time_configurations (`id`, `description`, `published`, `self_link_href`, `self_link_rel`, `up_link_href`, `up_link_rel`, `updated`, `uuid`, `dstEndRule`, `dstOffset`, `dstStartRule`, `tzOffset`) VALUES (2, "MST", "2025-01-22 09:00:00", "/speedes/1_0/timezones/2", "self", "/speedes/1_0/timezones", "up", "2025-01-22 09:00:01", "9a5e3e99-9263-425e-b47e-9eb67366c084","B40E2000", -21600, "360E2000", -25200);
COMMIT;

START TRANSACTION;
/* Retail customers... */
INSERT INTO retail_customers (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `first_name`, `last_name`, `role`) VALUES (0, '', '2014-01-02 05:00:00', '/speedes/1_0/RetailCustomer/1','self','/speedes/1_0/RetailCustomer','up','2014-01-02 05:00:00','F06E8B03-0299-467E-972A-A883ECDCC575', 'Grace', 'Hopper', 'ROLE_CUSTODIAN');
INSERT INTO retail_customers (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `first_name`, `last_name`, `role`) VALUES (1, '', '2014-01-02 05:00:00', '/speedes/1_0/RetailCustomer/2','self','/speedes/1_0/RetailCustomer','up','2014-01-02 05:00:00','106E8B03-0299-467E-972A-A883ECDCC575', 'Alan', 'Turing', 'ROLE_USER');
INSERT INTO retail_customers (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `first_name`, `last_name`, `role`) VALUES (2, '', '2014-01-02 05:00:00', '/speedes/1_0/RetailCustomer/3','self','/speedes/1_0/RetailCustomer','up','2014-01-02 05:00:00','206E8B03-0299-467E-972A-A883ECDCC575', 'Donald', 'Knuth', 'ROLE_USER');
INSERT INTO retail_customers (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `first_name`, `last_name`, `role`) VALUES (3, '', '2014-01-02 05:00:00', '/speedes/1_0/RetailCustomer/4','self','/speedes/1_0/RetailCustomer','up','2014-01-02 05:00:00','306E8B03-0299-467E-972A-A883ECDCC575', 'Paul', 'Dirac', 'ROLE_USER');
/* ...and their logins */
/* passwords are argon2id hashes of "koala" salted with "himalayan" */
INSERT INTO logins (`customer_id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `enabled`, `username`, `password`) VALUES (0, '', '2014-01-02 05:00:00', '/speedes/1_0/RetailCustomer/1','self','/speedes/1_0/RetailCustomer','up','2014-01-02 05:00:00','F06E8B03-0299-467E-972A-A883ECDCC575', TRUE, 'grace', '$argon2id$v=19$m=64,t=2,p=1$aGltYWxheWFu$FvHHYCq/ud3DOnW+uRHMVw');
INSERT INTO logins (`customer_id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `enabled`, `username`, `password`) VALUES (1, '', '2014-01-02 05:00:00', '/speedes/1_0/RetailCustomer/2','self','/speedes/1_0/RetailCustomer','up','2014-01-02 05:00:00','106E8B03-0299-467E-972A-A883ECDCC575', TRUE, 'alan', '$argon2id$v=19$m=64,t=2,p=1$aGltYWxheWFu$FvHHYCq/ud3DOnW+uRHMVw');
INSERT INTO logins (`customer_id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `enabled`, `username`, `password`) VALUES (2, '', '2014-01-02 05:00:00', '/speedes/1_0/RetailCustomer/3','self','/speedes/1_0/RetailCustomer','up','2014-01-02 05:00:00','206E8B03-0299-467E-972A-A883ECDCC575', TRUE, 'donald', '$argon2id$v=19$m=64,t=2,p=1$aGltYWxheWFu$FvHHYCq/ud3DOnW+uRHMVw');
INSERT INTO logins (`customer_id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `enabled`, `username`, `password`) VALUES (3, '', '2014-01-02 05:00:00', '/speedes/1_0/RetailCustomer/4','self','/speedes/1_0/RetailCustomer','up','2014-01-02 05:00:00','306E8B03-0299-467E-972A-A883ECDCC575', TRUE, 'paul', '$argon2id$v=19$m=64,t=2,p=1$aGltYWxheWFu$FvHHYCq/ud3DOnW+uRHMVw');
COMMIT;

START TRANSACTION;
/* Subscriptions and authorizations */
INSERT INTO `application_information` (`id`, `kind`, `description`, `published`, `self_link_href`, `self_link_rel`, `up_link_href`, `up_link_rel`, `updated`, `uuid`, `authorizationServerAuthorizationEndpoint`, `authorizationServerRegistrationEndpoint`, `authorizationServerTokenEndpoint`, `authorizationServerUri`, `clientId`, `clientIdIssuedAt`, `clientName`, `clientSecret`, `clientSecretExpiresAt`, `clientUri`, `contacts`, `dataCustodianApplicationStatus`, `dataCustodianBulkRequestURI`, `dataCustodianDefaultBatchResource`, `dataCustodianDefaultSubscriptionResource`, `dataCustodianId`, `dataCustodianResourceEndpoint`, `dataCustodianThirdPartySelectionScreenURI`, `logoUri`, `policyUri`, `redirectUri`, `registrationAccessToken`, `registrationClientUri`, `responseTypes`, `softwareId`, `softwareVersion`, `thirdPartyApplicationDescription`, `thirdPartyApplicationName`, `thirdPartyApplicationStatus`, `thirdPartyApplicationType`, `thirdPartyApplicationUse`, `thirdPartyDataCustodianSelectionScreenURI`, `thirdPartyLoginScreenURI`, `thirdPartyNotifyUri`, `thirdPartyPhone`, `thirdPartyScopeSelectionScreenURI`, `thirdPartyUserPortalScreenURI`, `tokenEndpointAuthMethod`, `tosUri`, `dataCustodianScopeSelectionScreenURI`) VALUES
(1, 'DATA_CUSTODIAN_ADMIN', 'Green Button Alliance OpenESPI Data Custodian Admin Application', '2014-01-02 05:00:00', '/espi/1_1/resource/DataCustodian/ApplicationInformation/1', 'self', '/espi/1_1/resource/DataCustodian/ApplicationInformation', 'up', '2014-01-02 05:00:00', '185C9C3F-5B4A-44A9-8959-3AE79E60A9F5', @dcbaseurl || '/DataCustodian/oauth/authorize', @dcbaseurl || '/DataCustodian/espi/1_1/register', @dcbaseurl || '/DataCustodian/oauth/token', @dcbaseurl || '/DataCustodian/', 'data_custodian', 1403190000, 'Green Button DataCustodian Admin', 'secret', 0, @dcbaseurl || '/DataCustodian','john.teeter@energyos.org,martin.burns@nist.gov,donald.coffin@reminetworks.com', '1', @dcbaseurl || '/DataCustodian/espi/1_1/resource/Batch/Bulk', @dcbaseurl || '/DataCustodian/espi/1_1/resource/Batch', @dcbaseurl || '/DataCustodian/espi/1_1/resource/Batch/Subscription', 'data_custodian', @dcbaseurl || '/DataCustodian/espi/1_1/resource', @dcbaseurl || '/DataCustodian/RetailCustomer/{retailCustomerId}/ThirdPartyList', NULL, NULL, NULL, NULL, @dcbaseurl || '/DataCustodian/espi/1_1/resource/ApplicationInformation/1', 0, 'EnergyOS OpenESPI', '1.2', 'EnergyOS OpenESPI Example DataCustodian Admin', 'Data Custodian Admin (localhost)', '1', '1', '1', NULL, NULL, NULL, NULL, NULL, NULL, 'client_secret_basic', NULL, @dcbaseurl || '/DataCustodian/RetailCustomer/ScopeSelection/'),
(2, 'THIRD_PARTY', 'Green Button Alliance OpenESPI Third Party Application', '2014-01-02 05:00:00', '/espi/1_1/resource/DataCustodian/ApplicationInformation/2', 'self', '/espi/1_1/resource/DataCustodian/ApplicationInformation', 'up', '2014-01-02 05:00:00', 'AF6E8B03-0299-467E-972A-A883ECDCC575', @dcbaseurl || '/DataCustodian/oauth/authorize', @dcbaseurl || '/DataCustodian/espi/1_1/register', @dcbaseurl || '/DataCustodian/oauth/token', @dcbaseurl || '/DataCustodian/', 'third_party', 1403190000, 'Green Button Third Party', 'secret', 0, @tpbaseurl || '/ThirdParty', 'john.teeter@energyos.org,martin.burns@nist.gov,donald.coffin@reminetworks.com', '1', @dcbaseurl || '/DataCustodian/espi/1_1/resource/Batch/Bulk', @dcbaseurl || '/DataCustodian/espi/1_1/resource/Batch', @dcbaseurl || '/DataCustodian/espi/1_1/resource/Batch/Subscription', 'data_custodian', @dcbaseurl || '/DataCustodian/espi/1_1/resource', @dcbaseurl || '/DataCustodian/RetailCustomer/1/ThirdPartyList', @tpbaseurl || '/ThirdParty/resources/ico/favicon.png', NULL, @tpbaseurl || '/ThirdParty/espi/1_1/OAuthCallBack', 'd89bb056-0f02-4d47-9fd2-ec6a19ba8d0c', @dcbaseurl || '/DataCustodian/espi/1_1/resource/ApplicationInformation/2', 0, 'EnergyOS OpenESPI Example Third Party', '1.2', 'EnergyOS OpenESPI Example Third Party', 'Third Party (localhost)', '1', '1', '1', @tpbaseurl || '/ThirdParty/RetailCustomer/{retailCustomerId}/DataCustodianList', @tpbaseurl || '/ThirdParty/login', @tpbaseurl || '/ThirdParty/espi/1_1/Notification', NULL, @tpbaseurl || '/ThirdParty/RetailCustomer/ScopeSelection', @tpbaseurl || '/ThirdParty', 'client_secret_basic', NULL, @dcbaseurl || '/DataCustodian/RetailCustomer/ScopeSelectionList?ThirdPartyID=third_party'),
(3, 'UPLOAD_ADMIN', 'Green Button Alliance OpenESPI MDM Upload Application', '2014-01-02 05:00:00', '/espi/1_1/resource/DataCustodian/ApplicationInformation/3', 'self', '/espi/1_1/resource/DataCustodian/ApplicationInformation', 'up', '2014-01-02 05:00:00', '185C9C3F-5B4A-44A9-8959-3AE79E60A9F7', @dcbaseurl || '/DataCustodian/oauth/authorize', @dcbaseurl || '/DataCustodian/espi/1_1/register', @dcbaseurl || '/DataCustodian/oauth/token', @dcbaseurl || '/DataCustodian/', 'upload', 1403190000, 'Green Button DMD Upload Service', 'secret', 0, NULL, 'john.teeter@energyos.org,martin.burns@nist.gov,donald.coffin@reminetworks.com', '1', @dcbaseurl || '/DataCustodian/espi/1_1/resource/Batch/Bulk', @dcbaseurl || '/DataCustodian/espi/1_1/resource/Batch', @dcbaseurl || '/DataCustodian/espi/1_1/resource/Batch/Subscription', 'data_custodian', @dcbaseurl || '/DataCustodian/espi/1_1/resource', @dcbaseurl || '/DataCustodian/RetailCustomer/1/ThirdPartyList', NULL, NULL, NULL, NULL, @dcbaseurl || '/DataCustodian/espi/1_1/resource/ApplicationInformation/3', 0, 'EnergyOS OpenESPI DMD Upload Service', '1.2', 'EnergyOS OpenESPI DMD Upload Service', 'MDM Upload (localhost)', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'client_secret_basic', NULL, NULL);

/* Add application_information_scopes */ 
INSERT INTO application_information_scopes (application_information_id, scope) VALUES (1, 'FB=1_3_4_5_13_14_19_32_33_34_35_36_37_38_41_44_45');
INSERT INTO application_information_scopes (application_information_id, scope) VALUES (2, 'FB=1_3_4_5_13_14_39;IntervalDuration=3600;BlockDuration=monthly;HistoryLength=13');
INSERT INTO application_information_scopes (application_information_id, scope) VALUES (2, 'FB=1_3_4_5_13_14_15_39;IntervalDuration=900;BlockDuration=monthly;HistoryLength=13');
INSERT INTO application_information_scopes (application_information_id, scope) VALUES (2, 'FB=1_3_4_5_13_14_39;IntervalDuration=3600;BlockDuration=monthly;HistoryLength=13');
INSERT INTO application_information_scopes (application_information_id, scope) VALUES (2, 'FB=1_3_4_5_6_7_8_9_10_11_29_12_13_14_15_16_17_18_19_27_28_32_33_34_35_37_38_39_40_41_44;IntervalDuration=3600;BlockDuration=monthly;HistoryLength=13');
INSERT INTO application_information_scopes (application_information_id, scope) VALUES (3, 'FB=45');

/* Add application_information_grant_types */
INSERT INTO application_information_grant_types (application_information_id, grantTypes) VALUES (1, 'CLIENT_CREDENTIALS');
INSERT INTO application_information_grant_types (application_information_id, grantTypes) VALUES (2, 'AUTHORIZATION_CODE');
INSERT INTO application_information_grant_types (application_information_id, grantTypes) VALUES (2, 'REFRESH_TOKEN');
INSERT INTO application_information_grant_types (application_information_id, grantTypes) VALUES (2, 'CLIENT_CREDENTIALS');
INSERT INTO application_information_grant_types (application_information_id, grantTypes) VALUES (3, 'CLIENT_CREDENTIALS');

/* Add predefined authorizations */
INSERT INTO `authorizations` VALUES (1,NULL,'2015-05-15 15:02:39',NULL,'self',NULL,'up','2015-05-15 15:02:40','A1635478-76A7-449D-8AE9-EBB191352C25','2a85f4bd-30db-4b7d-8f41-b046b0566cb3',@dcbaseurl || '/DataCustodian/espi/1_1/resource/Authorization/1',0,0,NULL,NULL,NULL,NULL,1747076559,NULL,0,0,NULL,@dcbaseurl || '/DataCustodian/espi/1_1/resource/',NULL,'FB=3_19_32_33_34_35_36_37_38_41_44_45',NULL,'1','data_custodian',0,1,0,1),
(2,NULL,'2015-05-15 15:02:53',NULL,'self',NULL,'up','2015-05-15 15:02:53','63463495-7D32-4E45-8775-3B35AC60E13F','03909715-b0ca-4797-9a9a-601fff1d2848',@dcbaseurl || '/DataCustodian/espi/1_1/resource/Authorization/2',0,0,NULL,NULL,NULL,NULL,1747076572,NULL,0,0,NULL,@dcbaseurl || '/DataCustodian/espi/1_1/resource/Batch/RetailCustomer/**/UsagePoint',NULL,'FB=45',NULL,'1','upload',0,3,0,2),
(3,NULL,'2015-05-15 15:02:56',NULL,'self',NULL,'up','2015-05-15 15:02:56','766A7FBC-BB0B-41D1-801F-0E91EA0A3A64','53520584-d640-4812-a721-8a1afa459ff7',@dcbaseurl || '/DataCustodian/espi/1_1/resource/Authorization/3',0,0,NULL,NULL,NULL,NULL,1747076575,NULL,0,0,NULL,@dcbaseurl || '/DataCustodian/espi/1_1/resource/Batch/Bulk/**',NULL,'FB=34_35',NULL,'1','third_party_admin',0,2,0,3),
(4,NULL,'2015-05-15 15:03:02',NULL,'self',NULL,'up','2015-05-15 15:03:02','403CBA0C-46F5-4E64-816C-5D11C06DEB7A','c66b0854-ea1f-4e24-afb7-afab9e0f6c5e',@dcbaseurl || '/DataCustodian/espi/1_1/resource/Authorization/4',0,0,NULL,NULL,NULL,NULL,1747076581,NULL,0,0,NULL,@dcbaseurl || '/DataCustodian/espi/1_1/resource/ApplicationInformation/2',NULL,'FB=36_40',NULL,'1','REGISTRATION_third_party',0,2,0,4);

/* Add predefined subscriptions */
INSERT INTO `subscriptions` VALUES (1,NULL,'2015-05-15 15:02:40',NULL,'self',NULL,'up','2015-05-15 15:02:40','BE830DC5-3F21-4967-AA35-EFDF8C61A914','4e625c48-3ec2-4571-9e21-d1da0c57516d','2015-05-15 15:02:40',1,1,0),
(2,NULL,'2015-05-15 15:02:53',NULL,'self',NULL,'up','2015-05-15 15:02:53','55AE97C3-2DD4-4762-B7BF-11AED8D7AE58','7a60b601-f2c0-41aa-8e71-8dbe42c028d9','2015-05-15 15:02:53',3,2,0),
(3,NULL,'2015-05-15 15:02:56',NULL,'self',NULL,'up','2015-05-15 15:02:56','991C0B49-97BA-48C2-BE30-7545C027F72E','82e034de-0812-4c8f-879a-fc367e7fe224','2015-05-15 15:02:56',2,3,0),
(4,NULL,'2015-05-15 15:03:02',NULL,'self',NULL,'up','2015-05-15 15:03:02','99F1F395-8883-44F7-8D1D-1DBABDCB7C1F','38a6bea3-cdad-4ab6-af81-2034ad112b0e','2015-05-15 15:03:02',2,4,0);
COMMIT;

/* Service delivery points and usage points */
START TRANSACTION;
INSERT INTO service_delivery_points (`id`, `customerAgreement`, `name`, `tariffProfile`) VALUES (1, "", "123 Street External Meter Socket", "");
INSERT INTO service_delivery_points (`id`, `customerAgreement`, `name`, `tariffProfile`) VALUES (2, "", "West Point Housing Meter Socket", "");
INSERT INTO service_delivery_points (`id`, `customerAgreement`, `name`, `tariffProfile`) VALUES (3, "", "Sample Avenue Aggregate Socket", "");

INSERT INTO usage_points (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `roleFlags`, `status`, `uri`, `localTimeParameters_id`, `retail_customer_id`, `serviceCategory_kind`, `serviceDeliveryPoint_id`, `subscription_id`) VALUES (1, "", 1737536400000, "/speedes/1_0/usagepoints/1", "self", "/speedes/1_0/usagepoints", "up", 1737536400000, "38265a2d-9dd3-4310-a49d-cc871747aefc", 0100000000000000, 1, "https://example.com?meter=1", 1, 1, "bigint for service category kind", 1, 1);
INSERT INTO usage_points (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `roleFlags`, `status`, `uri`, `localTimeParameters_id`, `retail_customer_id`, `serviceCategory_kind`, `serviceDeliveryPoint_id`, `subscription_id`) VALUES (2, "", 1737536400000, "/speedes/1_0/usagepoints/2", "self", "/speedes/1_0/usagepoints", "up", 1737536400000, "5b97f042-ba7f-48f7-839f-9bec433c9e50", 0100000000000000, 1, "https://example.com?meter=2", 2, 2, "bigint for service category kind", 1, 2);
INSERT INTO usage_points (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `roleFlags`, `status`, `uri`, `localTimeParameters_id`, `retail_customer_id`, `serviceCategory_kind`, `serviceDeliveryPoint_id`, `subscription_id`) VALUES (3, "", 1737536400000, "/speedes/1_0/usagepoints/3", "self", "/speedes/1_0/usagepoints", "up", 1737536400000, "4ca086cd-541a-4550-8a6e-2193371baab5", 0100000000000000, 0, "https://example.com?meter=3", 1, 1, "bigint for service category kind", 1, 1);
COMMIT;

/* Reading types and meter readings */
START TRANSACTION;
INSERT INTO reading_types (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`,`accumulationBehaviour`,`rational_denominator`,`rational_numerator`,`commodity`,`consumptionTier`,`cpp`,`dataQualifier`,`defaultQuality`,`flowDirection`,`interharmonic_denominator`,`interharmonic_numerator`,`intervalLength`,`kind`,`measuringPeriod`,`phase`,`powerOfTenMultiplier`,`timeAttribute`,`tou`,`uom`) VALUES (1, "15 Minute Electrical Consumption North America", 1737536400000, "/speedes/1_0/readingTypes/1", "self", "/speedes/1_0/readingTypes", "up", 1737536400000, "d49c35cf-49f7-441b-82e3-3a4209de1c77", "4", "", "", "1", "", "", "12", "", "1", "", "", "", "12", "", "769", "3", "3", "", "72");

INSERT INTO meter_readings (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `reading_type_id`, `usage_point_id`) VALUES (1, "", 1737536400000, "/speedes/1_0/meterreadings/1", "self", "/speedes/1_0/meterreadings", "up", 1737536400000, "060ab976-8aed-409a-92c3-892b255e3916", 1, 1);
INSERT INTO meter_readings (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `reading_type_id`, `usage_point_id`) VALUES (2, "", 1737536400000, "/speedes/1_0/meterreadings/2", "self", "/speedes/1_0/meterreadings", "up", 1737536400000, "1e2f6930-6719-47be-800f-4d48637e960e", 1, 2);
INSERT INTO meter_readings (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `reading_type_id`, `usage_point_id`) VALUES (3, "", 1737536400000, "/speedes/1_0/meterreadings/3", "self", "/speedes/1_0/meterreadings", "up", 1737536400000, "9dc2fdd9-f139-4feb-a706-8ee661560448", 1, 3);
COMMIT;

/* Interval blocks; duration is in seconds; 900 = 15 minute interval */
START TRANSACTION;
INSERT INTO interval_blocks (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `duration`, `start`, `meter_reading_id`) VALUES (1, "", 1737536400000, "/speedes/1_0/intervalblocks/1", "self", "/speedes/1_0/intervalblocks", "up", 1737536400000, "754ce232-9ab2-4cd4-977d-272abfd01a71", 900, 1737536400000, 1);
INSERT INTO interval_blocks (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `duration`, `start`, `meter_reading_id`) VALUES (2, "", 1737536400900, "/speedes/1_0/intervalblocks/2", "self", "/speedes/1_0/intervalblocks", "up", 1737536400900, "ec435711-ae04-47d2-9202-e933bddfdccf", 900, 1737536400900, 1);

INSERT INTO interval_blocks (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `duration`, `start`, `meter_reading_id`) VALUES (3, "", 1737536400000, "/speedes/1_0/intervalblocks/3", "self", "/speedes/1_0/intervalblocks", "up", 1737536400000, "856e9517-9d8e-43a6-a3d8-a04e4b37fcfb", 900, 1737536400000, 2);
INSERT INTO interval_blocks (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `duration`, `start`, `meter_reading_id`) VALUES (4, "", 1737536400900, "/speedes/1_0/intervalblocks/4", "self", "/speedes/1_0/intervalblocks", "up", 1737536400900, "c81717d1-74ff-40d1-bb89-6ff8eb24df68", 900, 1737536400900, 2);

INSERT INTO interval_blocks (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `duration`, `start`, `meter_reading_id`) VALUES (5, "", 1737536400000, "/speedes/1_0/intervalblocks/5", "self", "/speedes/1_0/intervalblocks", "up", 1737536400000, "01a3cd40-b575-4e06-8b19-39ca2882a427", 900, 1737536400000, 3);
INSERT INTO interval_blocks (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `duration`, `start`, `meter_reading_id`) VALUES (6, "", 1737536400900, "/speedes/1_0/intervalblocks/6", "self", "/speedes/1_0/intervalblocks", "up", 1737536400900, "0d61be09-5c1d-400a-8548-8fad95f329a2", 900, 1737536400900, 3);
COMMIT;

/* Addresses; 1 and 3 lack fullAddress, 2 and 4 have it */
/* 1 and 2 have no unit number. 3 and 4 do. */
START TRANSACTION;
INSERT INTO addresses (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `houseFractionNumber`, `unit`, `building`, `streetName`, `streetNumber`, `streetPrefix`, `streetSuffix`, `streetType`, `city`, `county`, `state`, `zipcode`, `zipFour`, `fullAddress`, `latitude`, `longitude`) VALUES (1, "mailing", 1737536400000, "/speedes/1_0/addresses/1", "self", "/speedes/1_0/addresses", "up", 1737536400000, "bcec381a-5e5b-4022-aa09-d17108bfae07", "", "", "123", "Test", "", "West", "", "Street", "Testown", "Koala", "WA", "00000", "0000", "", "", "");
INSERT INTO addresses (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `houseFractionNumber`, `unit`, `building`, `streetName`, `streetNumber`, `streetPrefix`, `streetSuffix`, `streetType`, `city`, `county`, `state`, `zipcode`, `zipFour`, `fullAddress`, `latitude`, `longitude`) VALUES (2, "mailing", 1737536400000, "/speedes/1_0/addresses/2", "self", "/speedes/1_0/addresses", "up", 1737536400000, "bc609426-15a6-4497-88df-3f99c1b88985", "", "", "321", "Test", "", "West", "", "Street", "Testown", "Koala", "WA", "00000", "0000", "321 West Test Street, Testown WA 00000", "", "");

INSERT INTO addresses (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `houseFractionNumber`, `unit`, `building`, `streetName`, `streetNumber`, `streetPrefix`, `streetSuffix`, `streetType`, `city`, `county`, `state`, `zipcode`, `zipFour`, `fullAddress`, `latitude`, `longitude`) VALUES (3, "mailing", 1737536400000, "/speedes/1_0/addresses/3", "self", "/speedes/1_0/addresses", "up", 1737536400000, "2ec98e31-4da1-4270-9554-c3bee6e9f68c", "1/2", "8", "500", "Test", "", "", "", "Street", "Testown", "Koala", "WA", "00000", "0000", "", "", "");
INSERT INTO addresses (`id`,`description`,`published`,`self_link_href`,`self_link_rel`,`up_link_href`,`up_link_rel`,`updated`,`uuid`, `houseFractionNumber`, `unit`, `building`, `streetName`, `streetNumber`, `streetPrefix`, `streetSuffix`, `streetType`, `city`, `county`, `state`, `zipcode`, `zipFour`, `fullAddress`, `latitude`, `longitude`) VALUES (4, "mailing", 1737536400000, "/speedes/1_0/addresses/4", "self", "/speedes/1_0/addresses", "up", 1737536400000, "95e753b1-3e78-4b13-8b6e-fa219abf4529", "2/2", "5", "600", "Test", "", "", "", "Street", "Testown", "Koala", "WA", "00000", "0000", "2/2 Unit 5, 600 Test Street, Testown WA 00000", "", "");
COMMIT;

/* TODO:
- usage_summaries
- electric_power_quality_summaries
- usage_point_related_links
- reading_qualities
- meter_reading_related_links
- line_item
- resources
- addresses
- relationships

- (subscriptions_usage_points)
- (BatchList)
*/