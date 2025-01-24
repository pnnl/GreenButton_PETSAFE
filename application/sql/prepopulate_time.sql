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

These are sample records made to test understanding of the format.
Build the self link:
CONCAT("/speedes/1_0/timezones/", last_insert_id() + 1);

MAY have a race condition; if so, update the new entry immediately after,
but this may be the one solution I found without that issue.
Needs testing to see if that's actually the case. 
SET @self_path = CONCAT("/speedes/1_0/timezones/", last_insert_id() + 1)

Consider a trigger instead?
eg. https://stackoverflow.com/questions/17266442/in-mysql-how-can-i-use-the-autoincrement-value-in-another-column-at-the-time-of?rq=3

DELIMITER //    
    CREATE TRIGGER buildSelfLinkHrefFromID BEFORE INSERT ON time_configurations FOR EACH ROW
    BEGIN
        DECLARE next_ai INT;
        SELECT auto_increment INTO next_ai
          FROM information_schema.tables
          WHERE table_schema = DATABASE() AND table_name = 'time_configurations';
        SET NEW.self_link_href = CONCAT("/speedes/1_0/timezones/", next_ai);
    END //
DELIMITER ;
*/

/*
DELIMITER //    
    CREATE TRIGGER buildSelfLinkHrefFromID BEFORE INSERT ON time_configurations FOR EACH ROW
    BEGIN
        DECLARE next_ai INT;
        SELECT auto_increment INTO next_ai
          FROM information_schema.tables
          WHERE table_schema = DATABASE() AND table_name = 'time_configurations';
        SET NEW.self_link_href = CONCAT("/speedes/1_0/timezones/", next_ai + 1);
    END //
DELIMITER ;
*/

START TRANSACTION;
INSERT INTO time_configurations (id, description, published, self_link_href, self_link_rel, up_link_href, up_link_rel, updated, uuid, dstEndRule, dstOffset, dstStartRule, tzOffset) 
VALUES 
/* Pacific Standard Time */
(1, "PST", "2025-01-22 09:00:00", "/speedes/1_0/timezones/1", "self", "/speedes/1_0/timezones", "up", "2025-01-22 09:00:00", "af11dcbb-f7c4-4898-b298-8d791de4bd98", "B40E2000", -25200, "360E2000", -28800);
/* Mountain Standard Time */
(2, "MST", "2025-01-22 09:00:00", "/speedes/1_0/timezones/2", "self", "/speedes/1_0/timezones", "up", "2025-01-22 09:00:01", "9a5e3e99-9263-425e-b47e-9eb67366c084","B40E2000", -21600, "360E2000", -25200);
SELECT self_link_href FROM time_configurations;
COMMIT;