import csv 
import pandas as pd 
from pathlib import Path

CSV_FOLDER = 'setup/exports_imports/building_aggregation/processor/powerfolders'
CSV_OUTPUT_FOLDER = 'setup/exports_imports/building_aggregation/processor/new-powerfolders/'
POINTS_CSV = 'setup/exports_imports/building_aggregation/processor/points.csv'

def get_csv_list(csv_folder):
    directory = Path(csv_folder) 
    csv_file_list = [] 

    for entry in directory.iterdir():
        if entry.is_file() and 'POWER' in entry.name:
            csv_file_list.append(entry.resolve())

    return csv_file_list

def process_chunk(chunk, subset_list, column_map):
    chunk['duration'] = (pd.to_datetime(chunk['max_t']) - pd.to_datetime(chunk['min_t'])).dt.total_seconds() / 60  
    subset_chunk = chunk[subset_list]
    renamed_chunk = subset_chunk.rename(columns=column_map)
    return renamed_chunk 



    csv_files = get_csv_list(CSV_FOLDER)
    for file in csv_files:
        chunk_iterator = pd.read_csv(file, chunksize = 10000)
        first_chunk = next(chunk_iterator) 

        print(first_chunk.info)
        print()


def main():
    csv_files = get_csv_list(CSV_FOLDER)
    column_map = {
        'ee_site_id' : 'ee_site_id',
        'regname' : 'regname',
        'min_t' : 'timestamp',  
        'duration' : 'duration',
        'power' : 'P REAL', 
        'apparent_power' : 'Q REAL',
        'pf' : 'PF REAL'
    }
    column_list = list(column_map.keys())
    columns_to_read = list(column_list)
    columns_to_read.append('max_t')
    columns_to_read.remove('duration')

    points_column = ['ee_site_id', 'regname', 'point_id']
    filter_list = ['ee_site_id', 'regname']
    points_df = pd.read_csv(POINTS_CSV, usecols = points_column)


    try:
        for file in csv_files:
            filename, extension = file.name.split('.') 
            new_filename = filename + '_new'
            new_filename = '.'.join([new_filename, extension])
            output = CSV_OUTPUT_FOLDER + new_filename 
        
            chunk_iterator = pd.read_csv(file, chunksize = 100000, usecols = columns_to_read)
            is_first_chunk = True

            print(f'Processing file: {file.name}')

            for chunk in chunk_iterator:
                processed_chunk = process_chunk(chunk, column_list, column_map)
                # chunk_joined = pd.merge(processed_chunk, points_df, on = filter_list, how = 'left')
                # chunk_joined['point_id'] = chunk_joined['point_id'].astype('Int64')
                processed_chunk['duration'] = processed_chunk['duration'].astype('Int64')
                processed_chunk['timestamp'] = processed_chunk['timestamp'].apply(lambda x: x[:-4])

                processed_chunk.insert(loc = 3, column = 'dummy', value = 0)
                
                # Old 

                # processed_chunk = process_chunk(chunk, column_list, column_map)
                # chunk_joined = pd.merge(processed_chunk, points_df, on = filter_list, how = 'left')
                # chunk_joined['point_id'] = chunk_joined['point_id'].astype('Int64')
                # chunk_joined['duration'] = chunk_joined['duration'].astype('Int64')
                # chunk_joined['timestamp'] = chunk_joined['timestamp'].apply(lambda x: x[:-4])

                # chunk_joined.insert(loc = 3, column = 'dummy', value = 0)

                # point_id_column = chunk_joined['point_id'] 
                # chunk_joined = chunk_joined.drop(columns = ['point_id'])
                # chunk_joined.insert(loc = 1, column = 'point_id', value = point_id_column)

                if is_first_chunk:
                    processed_chunk.to_csv(output, index = False, mode = 'w', header = True)
                    is_first_chunk = False
                else:
                    processed_chunk.to_csv(output, index = False, mode = 'a', header = False)
            
            print(f'Finished processing file : {file.name}\n')
    except Exception as e: 
        print(f'Failed to process files : {e}')




if __name__ == '__main__':
    main()
