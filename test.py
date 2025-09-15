import pandas as pd 

CSV_FILE = 'POWER15_wide.csv' 
OUTPUT = 'POWER15_wide_new.csv'
NEW_OUTPUT = 'POWER15_wide_filtered.csv'

columns = ['ee_site_id', 'timestamp_end', 'timestamp_start', 'duration', 'Mains', 'Mains With Solar']
chunk_iterator = pd.read_csv(OUTPUT, usecols = columns, chunksize= 100000)

main_counter = 0 
main_solar_counter = 0 
distinct_duration_value = 0 
distinct_row = []
row_count = 0 
filter_count = 0
is_first_chunk = True

try:
    print('Processing file')
    for chunk in chunk_iterator:
        main_counter += chunk['Mains'].isnull().sum()
        main_solar_counter += chunk['Mains With Solar'].isnull().sum()
        
        duration_mask = chunk['duration'] != 14 
        distinct_duration_value += duration_mask.sum()

        if duration_mask.any():
            distinct_row.extend(chunk[duration_mask].to_dict('records'))
        # duration_mask = chunk['duration'] == 14
        # filtered_chunk = chunk[duration_mask]

        if distinct_row:
            for row in distinct_row:
                print(row)

        row_count += len(chunk)


    print('Finished processing file\n\n') 
    print(f'Mains null counter : {main_counter}')
    print(f'Mains solar null counter : {main_solar_counter}')
    print(f'Distinct duration values : {distinct_duration_value}')
    print(f'Distinct row : {distinct_row}\n\n')
    print(f'Row count: {row_count}')

        # if is_first_chunk:
        #     filtered_chunk.to_csv(NEW_OUTPUT, mode = 'w', index = False, header = True)
        #     is_first_chunk = False 
        # else: 
        #     filtered_chunk.to_csv(NEW_OUTPUT, mode = 'a', index = False, header = False) 

        

        # row_count += len(chunk)
        # filter_count += len(filtered_chunk)
    
    print(row_count)
    print(filter_count)

except Exception as e: 
    print(f'Failed to process file for nulls : {e}')


# is_first_chunk = True
# column_map = {
#     'min_t' : 'timestamp_end',
#     'max_t' : 'timestamp_start',
# }

# try:
#     print(f'Processing file : {CSV_FILE}')
#     for chunk in chunk_iterator: 
#         chunk['duration'] = (pd.to_datetime(chunk['max_t']) - pd.to_datetime(chunk['min_t'])).dt.total_seconds() / 60  
#         chunk['ee_site_id'] = chunk['ee_site_id'].astype('Int64')
#         chunk['duration'] = chunk['duration'].astype('Int64')
#         chunk['min_t'] = chunk['min_t'].str.replace('.000', '')
#         chunk['max_t'] = chunk['max_t'].str.replace('.000', '')

#         duration = chunk['duration'] 
#         chunk = chunk.drop(columns = ['duration'])
#         chunk.insert(loc = 3, column = 'duration', value = duration)
        


#         if is_first_chunk: 
#             chunk.rename(columns=column_map, inplace = True) 
#             chunk.to_csv(OUTPUT, index = False, mode = 'w', header = True)
#             is_first_chunk = False
#         else:
#             chunk.to_csv(OUTPUT, index = False, mode = 'a', header = False)

#     print(f'Finished processing file : {CSV_FILE}')
# except Exception as e:
#     print(f'Failed to process file: {e}')
