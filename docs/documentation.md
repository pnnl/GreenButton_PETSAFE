# Database Structure

## Label

| num | Column name               | Datatype            |
|-----|---------------------------|---------------------|
| 0   | ee_site_id                | Int                 |
| 1   | point_id (PK)             | Int                 |
| 2   | regname                   | Char(32) NOT NULL   |
| 3   | circuit_label_type_id     | Int                 |
| 4   | circuit_label_type_desc   | Char(32)            |
| 5   | circuit_label             | Char(32)            |
| 6   | equipment_type_desc       | Char(32)            |
| 7   | day_zero_dt               | Int                 |

## Power

| num | Column name               | Datatype            |
|-----|---------------------------|---------------------|
| 0   | ee_site_id                | Int                 |
| 1   | point_id (FK Labels)      | Int, indexed        |
| 2   | timestamp                 | Int (unix timestamp)|
| 3   | duration                  | Int                 |
| 4   | P REAL                    | float               |
| 5   | Q REAL                    | float               |
| 6   | PF REAL                   | float               |

## PRAGMA Settings

- **foreign_keys = ON:** Enforce foreign key constraints.
- **journal_mode = WAL:** Write-ahead log, improves performance. Primarily affects behavior of writers; readers should not be significantly affected.
- **synchronous = normal:** Asks WAL to wait for FSYNC, but readers don't have to wait. Because WAL is journal_mode, database will not be corrupted on power loss, but uncommitted transactions may be rolled back.
- **mmap_size = 15000000000:** Enables memory mapping up to 15,000,000,000 bytes (15GB), improves performance. I/O errors need to be caught by application and vaccuum may fail silently, but vaccuum isn't in use at present (2024-09-13), making this less of a concern.
- **threads = 3:** enables threads to assist with queries, letting them run much faster. 3 was chosen as a relatively safe number for portability; adjust if needed for your device.
- **analysis_limit = 400:** limits duration of pragma optimize, which is run when closing as per [SQLite documentation's suggested best practice](https://www.sqlite.org/pragma.html#pragma_optimize).

# Building Frame Output

| num | Column name               | Datatype            |
|-----|---------------------------|---------------------|
| 0   | building_id               | Int                 |
| 1   | point_id (list of sites)  | Str "(tuple of int)"|
| 2   | timestamp (index)         | Datetime            |
| 3   | duration                  | Int                 |
| 4   | real_power                | float               |
| 5   | apparent_power            | float               |
| 6   | PF                        | float               |
