/*
 *
 *    Copyright (c) 2018-2021 Green Button Alliance, Inc.
 *
 *    Portions (c) 2013-2018 EnergyOS.org
 *
 *     Licensed under the Apache License, Version 2.0 (the "License");
 *     you may not use this file except in compliance with the License.
 *     You may obtain a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 *     Unless required by applicable law or agreed to in writing, software
 *     distributed under the License is distributed on an "AS IS" BASIS,
 *     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *     See the License for the specific language governing permissions and
 *     limitations under the License.
 *
 */

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
INSERT INTO time_configurations (id, description, published, self_link_href, self_link_rel, up_link_href, up_link_rel, updated, dstEndRule, dstOffset, dstStartRule, tzOffset) 
VALUES 
/* Pacific Standard Time */
("PST", "2025-01-22 09:00:00", "/speedes/1_0/timezones/1", "self", "/speedes/1_0/timezones", "up", "2025-01-22 09:00:00", "B40E2000", -25200, "360E2000", -28800)
/* Mountain Standard Time */
("MST", "2025-01-22 09:00:00", "/speedes/1_0/timezones/2", "self", "/speedes/1_0/timezones", "up", "2025-01-22 09:00:00", "B40E2000", -21600, "360E2000", -25200)