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
| 1   | point_id                  | Primary key         |
| 2   | timestamp                 | Int                 |
| 3   | duration                  | Int                 |
| 4   | P REAL                    | float?              |
| 5   | Q REAL                    | float?              |
| 6   | PF REAL                   | float               |
| 7   | point_id (FK, Labels)     | Int                 |
