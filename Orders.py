import math
import os
import logging
import configparser
import Constant_values_for_orders as const
from getpass import getpass
# from mysql.connector import connect, Error
from datetime import datetime, timedelta

def get_config_data():
    if(not os.path.exists(os.path.join(os.path.dirname(os.path.realpath(__file__)), const.CONFIG_FILE_NAME ))):
        print(const.FILE_NOT_FOUND_MESSAGE % const.CONFIG_FILE_NAME)
        exit(1)
    config_data = configparser.ConfigParser()
    try:     
        config_data.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), const.CONFIG_FILE_NAME ))  
    except:
        print(const.INCORRECT_CONFIG_DATA_MESSAGE % const.CONFIG_FILE_NAME)
        exit(1)
    try: 
        logger_data = [config_data['LOG']['LEVEL'], config_data['LOG']['LOG_FILE_NAME']]
        row_count_data = [
            int(config_data['NUMBER_OF_ROWS']['RED_ZONE_ROWS']), 
            int(config_data['NUMBER_OF_ROWS']['GREEN_ZONE_ROWS']),
            int(config_data['NUMBER_OF_ROWS']['BLUE_ZONE_ROWS'])
            ]            
        database_data = [
            config_data['DATABASE']['DATABASE_HOST'], config_data['DATABASE']['DATABASE_USER'], 
            config_data['DATABASE']['DATABASE_PASSWORD'], config_data['DATABASE']['DATABASE_NAME'],
            config_data['DATABASE']['TABLE_NAME']
            ]
        for number in row_count_data:
            if (number <= 0):
                print(const.INCORRECT_CONFIG_ROW_NUMBERS % const.CONFIG_FILE_NAME)
                exit(1)   
    except:
        print(const.INCORRECT_OR_NO_CONFIG_DATA_MESSAGE % const.CONFIG_FILE_NAME)
        exit(1)
    return row_count_data, logger_data, database_data

def set_logger(logger_level, logger_file_name):  
    logger = logging.getLogger(__name__)  
    try:
        logger.setLevel(logger_level)
    except:
        print(const.BAD_LOGGING_LEVEL_MESSAGE)
        exit(1)
    file_handler = logging.FileHandler(os.path.join(os.path.dirname(os.path.realpath(__file__)), logger_file_name))
    file_handler.setFormatter(logging.Formatter(const.LOGGER_OUTPUT_FORMAT))
    logger.addHandler(file_handler)
    return logger

def get_hex_id(prev_dec_id):
    prev_dec_id += const.ID_INCREMENT * ((const.PSEUDORAND_NUMS_LIST[0][0]*prev_dec_id + 
        const.PSEUDORAND_NUMS_LIST[0][1]) % const.PSEUDORAND_NUMS_LIST[0][2])
    return hex(round(prev_dec_id)).lstrip(const.ID_LEFT_STRIP).upper().zfill(const.DIGIT_COUNT_IN_HEX_ID)

def get_change_date(start_time, max_seconds, multiplier, rand_num, increment, modulo):
    microsecond, second = math.modf(max_seconds * ((multiplier * rand_num + increment) % modulo))    
    change_date = start_time + timedelta(seconds=second, microseconds=microsecond*const.MICROSECONDS_MULTIPLY)
    return change_date.strftime(const.OUTPUT_TIME_FORMAT)

def get_creation_date(start_time, seconds, for_rand):
    creation_date_string = get_change_date(start_time, seconds, const.PSEUDORAND_NUMS_LIST[1][0],
        float(for_rand), const.PSEUDORAND_NUMS_LIST[1][1], const.PSEUDORAND_NUMS_LIST[1][2])
    creation_date_datetime = datetime.strptime(creation_date_string[:len(creation_date_string)-7], 
        const.INCREMENT_TIME_FORMAT).replace(tzinfo = const.TZ)
    if(creation_date_datetime.hour == const.BREAK_HOUR):    
        creation_date_datetime += timedelta(minutes = const.MINUTES_INCREMENT - creation_date_datetime.minute)        
    return creation_date_datetime.strftime(const.OUTPUT_TIME_FORMAT)

def get_status(prev_status, for_rand, zone): 
    status = const.GET_NEXT_STATUS_DICTIONARY[zone][prev_status]
    if (type(status) is list):
        status = status[0][(const.STATUS_MULTIPLY*for_rand + const.STATUS_INCREMENT) % status[1]]   
    return status

def get_initial_price(instrument):
    top_limit, bottom_limit = const.INSTRUMENT_DICTIONARY[instrument][0], const.INSTRUMENT_DICTIONARY[instrument][1]
    init_price = ((const.PSEUDORAND_NUMS_LIST[3][0]*top_limit + const.PSEUDORAND_NUMS_LIST[3][1]) % 
        const.PSEUDORAND_NUMS_LIST[3][2]) * (top_limit - bottom_limit) + bottom_limit
    return str(init_price)[:const.DIGIT_COUNT_IN_PRICE]

def get_fill_price(prev_status, curr_status, init_price):
    is_fill_pr_not_zero = const.FILL_PRICE_DICTIONARY[curr_status]
    consider_prev_reject = False if curr_status == const.DONE and prev_status == const.REJECT else is_fill_pr_not_zero
    return init_price if consider_prev_reject else const.ZERO_FILL_PRICE

def get_initial_volume(for_rand):
    return str(round(round(const.INIT_VOLUME_PARAMS[0] * (((const.INIT_VOLUME_PARAMS[1] * float(for_rand) +
        const.INIT_VOLUME_PARAMS[2]) % const.INIT_VOLUME_PARAMS[3]) * (const.INIT_VOLUME_PARAMS[4] - 
            const.INIT_VOLUME_PARAMS[5]) + const.INIT_VOLUME_PARAMS[5])) 
                / const.INIT_VOLUME_PARAMS[6], 2))[:const.DIGIT_COUNT_IN_VOLUME]

def get_fill_volume(prev_status, current_status, init_volume):
    is_need_coefficient, multiplier = const.FILL_VOLUME_DICIONARY[current_status][prev_status]
    coefficient = (const.FILL_VOLUME_PARAMS[0]*init_volume + const.FILL_VOLUME_PARAMS[1]) % const.FILL_VOLUME_PARAMS[2]
    return str(coefficient * init_volume)[:const.DIGIT_COUNT_IN_VOLUME] if is_need_coefficient else str(multiplier 
        * init_volume)[:const.DIGIT_COUNT_IN_VOLUME]

# def output_in_MySQL(orders_table, logger, database_host, database_user, database_password, database_name, table_name):
#     try:
#         with connect(
#             host = database_host,            
#             user = database_user, 
#             password = database_password,
#             database = database_name  
#             ) as connection:  
#             all_orders_string_for_output_in_database = str(tuple(orders_table[0]))
#             for index in range(1, len(orders_table)):
#                 all_orders_string_for_output_in_database += ', ' + str(tuple(orders_table[index]))
#             orders_insert_query = const.INSTER_QUERY % table_name + all_orders_string_for_output_in_database
#             connection._execute_query(orders_insert_query)
#             connection.commit()
#             connection.close()           
#     except Error:
#         logger.critical(Error)

def get_orders_table(red_rows, green_rows, blue_rows):
    final_table = []
    prev_string_id = get_hex_id(const.ID_START_VALUE)
    list = [
        [red_rows,   const.RED,   get_row(red_rows * round(int(prev_string_id, 16)), int(prev_string_id, 16),                             const.DONE, const.RED)],
        [green_rows, const.GREEN, get_row(green_rows, int(prev_string_id, 16) + const.ID_INCREMENT *  green_rows,             const.DONE, const.GREEN)],
        [blue_rows,  const.BLUE,  get_row(blue_rows,  int(prev_string_id, 16) + const.ID_INCREMENT * (green_rows + blue_rows), const.FILL, const.BLUE)]
        ]            
    for zone_info in list:
        zone_table = []
        row = zone_info[2]
        zone_table.append(row)
        for index in range(0, zone_info[0] - 1):
            if(const.IS_NEW_ROW_DICT[zone_info[1]][zone_table[index][6]]):
                row = get_row(index*round(int(zone_table[index][0], 16)), int(zone_table[index][0], 16), zone_table[index][6], zone_info[1])
            else:
                current_status = get_status(zone_table[index][6], index*round(int(zone_table[index][0], 16)), zone_info[1])
                prev_datatime_change_date = datetime.strptime(zone_table[index][5][:len(zone_table[index][5])-7],
                    const.INCREMENT_TIME_FORMAT).replace(tzinfo = const.TZ)
                change_date = get_change_date(prev_datatime_change_date, const.MAX_SECONDS_FOR_ONE_ORDER,
                    const.PSEUDORAND_NUMS_LIST[2][0], prev_datatime_change_date.second, const.PSEUDORAND_NUMS_LIST[2][1],
                        const.PSEUDORAND_NUMS_LIST[2][2])
                fill_price =  get_fill_price(zone_table[index][6],  current_status, zone_table[index][7])
                fill_volume = get_fill_volume(zone_table[index][6], current_status, float(zone_table[index][9]))
                row = zone_table[index][0:len(zone_table[index])]
                row[5], row[6], row[8], row[10] = change_date, current_status, fill_price, fill_volume
            zone_table.append(row)
        final_table += zone_table
    for index in range(0, len(final_table)):
        final_table[index].insert(0, str(index + 1))
    return final_table

def get_row(index, prev_dec_id, prev_status, zone):
    row, iter = first_template_filling(index)
    row[0] = get_hex_id(prev_dec_id)
    creation_date_string = get_creation_date(const.GET_START_DATE_DICT[zone][0], const.GET_START_DATE_DICT[zone][1], index)
    creation_date_datetime = datetime.strptime(creation_date_string[:len(creation_date_string)-7],
        const.INCREMENT_TIME_FORMAT).replace(tzinfo = const.TZ)
    row[5] = get_change_date(creation_date_datetime, const.MAX_SECONDS_FOR_ONE_ORDER, const.PSEUDORAND_NUMS_LIST[2][0], 
        creation_date_datetime.second, const.PSEUDORAND_NUMS_LIST[2][1], const.PSEUDORAND_NUMS_LIST[2][2]) 
    row = second_template_filling(prev_status, index, int(row[0], 16), zone, row, creation_date_string, iter)
    row[8] = get_fill_price(prev_status, row[6], row[7])
    row[10] = get_fill_volume(prev_status, row[6], float(row[9]))
    return row

def first_template_filling(index):
    row = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    iter = const.TEMPLATE_FILLING_START_INDEX
    for i in range(0,len(const.TEMPLATE_FILLING)):
        row[iter] = const.TEMPLATE_FILLING[i][0][round(const.TEMPLATE_FILLING[i][1] * ((const.TEMPLATE_FILLING[i][2]
            * index + const.TEMPLATE_FILLING[i][3]) % const.TEMPLATE_FILLING[i][4])) % const.TEMPLATE_FILLING[i][5]]
        iter += const.TEMPLATE_FILLING[i][6]
    return row, iter

def second_template_filling(prev_status, index, prev_dec_id, zone, row, creation_date_string, iter):
    template_filling_list = [
        [creation_date_string, 2], [get_status(prev_status, index * round(prev_dec_id), zone), 1], [get_initial_price(row[3]), 2],
        [get_initial_volume(index), 3], [const.DESCRIPTION_DICTIONARY[row[2]], 1], [const.EXTRADATA_DICTIONARY[row[3]], 0]    
        ]
    for function in template_filling_list:
        row[iter] = function[0]
        iter += function[1]
    return row

def main():
    row_count_data, logger_data, database_data = get_config_data()
    logger = set_logger(logger_data[0], logger_data[1])
    logger.info(const.INFO_TASK_MESSAGE, row_count_data[0], row_count_data[1], row_count_data[2]) 

    orders_table = get_orders_table(row_count_data[0], row_count_data[1], row_count_data[2])
    for index in range(0, len(orders_table)):
        print(orders_table[index])    
    logger.info(const.INFO_TABLE_DONE_MESSAGE)  

    # output_in_MySQL(orders_table, logger, database_data[0], database_data[1], database_data[2], database_data[3], database_data[4]) 

if __name__ == "__main__":
    main()