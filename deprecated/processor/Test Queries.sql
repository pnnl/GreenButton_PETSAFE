CREATE INDEX idx_labels_point_id ON LABELS(point_id);

 SELECT * FROM POWER  
        INNER JOIN LABELS 
        ON POWER.point_id = LABELS.point_id 
        WHERE LABELS.circuit_label_type_id=15
        limit 10;        
        

-- Check that records have started collection
select LABELS.point_id,*,datetime(day_zero_dt, 'unixepoch', 'localtime') as start_ts FROM LABELS where (LABELS.circuit_label_type_id=15 or LABELS.circuit_label_type_id=16) and LABELS.day_zero_dt <unixepoch("2021-01-01") order by day_zero_dt   ;



select *,datetime(timestamp, 'unixepoch', 'localtime') as ts from ( SELECT * FROM POWER
WHERE POWER.point_id IN (25492,2637)   and POWER.timestamp >=unixepoch("2021-01-01") limit 100) P 
join LABELS 
on LABELS.point_id=P.point_id;


select *,datetime(timestamp, 'unixepoch', 'localtime') as ts from ( SELECT * FROM POWER
WHERE POWER.point_id IN (
Select LABELS.point_id from LABELS where LABELS.circuit_label_type_id=15 or LABELS.circuit_label_type_id=16
)  and POWER.ee_site_id=491 and POWER.timestamp >unixepoch("2020-01-01") limit 100) P 
join LABELS 
on LABELS.point_id=P.point_id;
