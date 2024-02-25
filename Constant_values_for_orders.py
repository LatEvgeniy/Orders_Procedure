import pytz
from datetime import datetime 

#---------------------------------------------- CONFIG FILE ----------------------------------------------------

# File name where config params are
CONFIG_FILE_NAME = "Orders.ini"

#------------------------------------------- ALL STATUSES AND ZONES --------------------------------------------

# All available zones
RED = "red"
GREEN = "green"
BLUE = "blue"

# All available statuses
NEW = "new"
IN_PROGRESS = "in progress"
FILL = "fill"
PART_FILL = "part fill"
REJECT = "reject"
DONE = "done"

#-------------------------------------------------- TIME -------------------------------------------------------

# Order's time zone
TZ = pytz.timezone('Etc/GMT-2')
# Output date format
OUTPUT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f%Z:00"
# Time format without time zone for correctly create datetime.datetime object 
INCREMENT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

# Red zone starts at 28.11.2022 12:00
START_TIME_FOR_RED_ZONE = datetime  (2022, 11, 28, 12, 0, 0, 0, tzinfo=TZ)
# Green zone starts at 28.11.2022 13:00
START_TIME_FOR_GREEN_ZONE = datetime(2022, 11, 29, 13, 0, 0, 0, tzinfo=TZ)
# Blue zone starts at 28.11.2022 11:00
START_TIME_FOR_BLUE_ZONE = datetime (2022, 11, 29, 11, 0, 0, 0, tzinfo=TZ)

# [23:00..00:00) break time
BREAK_HOUR = 23
# When order generate time 23:40 we have to add 60 minutes - 40 minutes  = 20 minutes to avoid break time
MINUTES_INCREMENT = 60

# To use not microseconds but milliseconds for example
MICROSECONDS_MULTIPLY = 100000
# 5 minutes * 60 seconds / 4 statuses - one order should take about 5 minutes, one order max 4 statuses
MAX_SECONDS_FOR_ONE_ORDER = 75

#------------------------------------- CONSTANT VALUES FOR ORDER CREATION -------------------------------------

# Min order ID in dec
ID_START_VALUE = 3224152124
# Max increment for order id that multiply by a coefficient
ID_INCREMENT = 92832629

# Max count of digits in hex id, volume, price
DIGIT_COUNT_IN_HEX_ID = 10
DIGIT_COUNT_IN_VOLUME = 5
DIGIT_COUNT_IN_PRICE = 6

# After in progress could be only 3 statuses: fill, part fill, reject
AVAILABLE_STATUSES_AFTER_IN_PROGRESS_COUNT = 3
# RED_STATUSES_LIST has 5 status
ALL_AVAILABLE_STATUSES_FOR_RED_ZONE_CONUNT = 5

# When fill price = 0 programm have to write this in database as ZERO_FILL_PRICE
ZERO_FILL_PRICE = "0"

# When we get hex number using hex() it gets string with format 0xFFFF and we have to strip left part to get correct id format
ID_LEFT_STRIP = "0x"

# While template filling firstly should get order`s provider value that has index 1 (Order_ID index 0, id_pk hasn`t yet so Provider - index 1)
TEMPLATE_FILLING_START_INDEX = 1

# To improve preudorandom
STATUS_MULTIPLY = 98774137 
STATUS_INCREMENT = 6689524

#----------------------------------- LISTS AND DICTIONARIES FOR ORDER CREATION ---------------------------------

# Start time and max incement for each zone
GET_START_DATE_DICT = {
    GREEN: [START_TIME_FOR_GREEN_ZONE, 78900], # 78 900 seconds = ((22 hours * 60) - 5 minutes) * 60
    RED:   [START_TIME_FOR_RED_ZONE,   3300], # 3300 seconds = 55 minutes * 60
    BLUE:  [START_TIME_FOR_BLUE_ZONE,  3300]
    }

# All available providers
PROVIDER_LIST = ["FXCM", "SQM"]

# All available directions
DIRECTION_LIST = ["sell", "buy"]

# All available instruments
INSTRUMENT_LIST = [
    'EURUSD', 'USDJPY', 'GBPUSD', 'USDTRY',
    'USDCHF', 'USDCAD', 'EURJPY', 'AUDUSD',
    'NZDUSD', 'EURGBP', 'EURCHF'
    ]

# Max and min prices for instrument
INSTRUMENT_DICTIONARY  = {
    'EURUSD': [1.1, 0.9],   'USDJPY': [145, 135],   'GBPUSD': [1.3, 1.1],   'USDTRY': [20, 16],
    'USDCHF': [1.05, 0.85], 'USDCAD': [1.1, 0.9],   'EURJPY': [1.45, 1.25], 'AUDUSD': [155, 135],
    'NZDUSD': [0.75, 0.55], 'EURGBP': [0.75, 0.55], 'EURCHF': [1.08, 0.88]
    }

# True when we have to generate new row, False - only modify previous row
IS_NEW_ROW_DICT = {
    RED:   {DONE: True, IN_PROGRESS: False, FILL: False, PART_FILL: False, REJECT: False},
    GREEN: {NEW: False, IN_PROGRESS: False, FILL: False, PART_FILL: False, REJECT: False, DONE: True},
    BLUE:  {NEW: False, IN_PROGRESS: False, FILL: True,  PART_FILL: True,  REJECT: True}
    }

# All available statuses for red zone
RED_STATUSES_LIST =   [FILL, PART_FILL, REJECT, IN_PROGRESS, DONE]
# All available statuses for green zone
GREEN_STATUSES_LIST = [FILL, PART_FILL, REJECT, IN_PROGRESS, DONE, NEW]
# All available statuses for blue zone
BLUE_STATUSES_LIST =  [FILL, PART_FILL, REJECT, IN_PROGRESS, NEW]

# Format: order's zone: prev status: next status or list with modulo
# example with next status: status = GET_NEXT_STATUS_DICTIONARY[GREEN][DONE] -> status = NEW
# example with list and modulo: status = GET_NEXT_STATUS_DICTIONARY[RED][DONE] -> status = status[0][(1 * 2 + 3) % status[1]]   
GET_NEXT_STATUS_DICTIONARY = {
    RED:  {DONE: [RED_STATUSES_LIST, 5], IN_PROGRESS: [RED_STATUSES_LIST, 3],   FILL: DONE, PART_FILL: DONE, REJECT: DONE},
    GREEN: {NEW: IN_PROGRESS, DONE: NEW, IN_PROGRESS: [GREEN_STATUSES_LIST, 3], FILL: DONE, PART_FILL: DONE, REJECT: DONE},
    BLUE:  {NEW: IN_PROGRESS,            IN_PROGRESS: [BLUE_STATUSES_LIST, 3],  FILL: NEW,  PART_FILL: NEW,  REJECT: NEW }
    }

# If status is new, in progress or reject -> fill price have to be 0 else have to be equal to initial price
FILL_PRICE_DICTIONARY = {NEW: False, IN_PROGRESS: False, REJECT: False, FILL: True, PART_FILL: True, DONE: True}

# first dictionary key checks order's current status, second dictionary key - previous status.
# False, True - do we need to use coefficient to multiply it by initial volume?
# If we dont need to use coefficient as multiplier - we use 0, 1 as multiplier for initial volume
FILL_VOLUME_DICIONARY = {
    NEW: {IN_PROGRESS:  [False, 0], FILL: [False, 0],   REJECT: [False, 0], PART_FILL: [False, 0], DONE: [False, 0]}, 
    IN_PROGRESS: {NEW:  [False, 0], DONE: [False, 0]},  REJECT: {IN_PROGRESS: [False, 0], DONE: [False, 0]},  
    FILL: {IN_PROGRESS: [False, 1], DONE: [False, 1]},  PART_FILL: {IN_PROGRESS: [True, 0], DONE: [True, 0]},  
    DONE: {
        IN_PROGRESS: [False, 1], REJECT: [False, 0], FILL: [False, 1], PART_FILL: [True, 0], NEW: [False, 1],
        DONE: [False, 1]
        }
    }

# Format: (27 * random_number + 31) % 0.99
FILL_VOLUME_PARAMS = [27, 31, 0.99]

# Format: round(100 * (<- to get number 0..99) ((19 * rand_number + 23) % 0.99) (<- to get random coefficient) * 
# (1 - 0.1) + 0.1 (<- to get value 0.1..1)) / 20 (<- to get a number that looks like it was written by a human)
#
# example: round(100 * (((19*float(for_rand) + 23) % 0.99) * (1 - 0.1) + 0.1)) / 20
INIT_VOLUME_PARAMS  = [100, 19, 23, 0.99, 1, 0.1, 20]

# All available extratada that depends on instrument
EXTRADATA_DICTIONARY = {
    'EURUSD': 'Euro/US Dollar',  'USDJPY': 'US Dollar/ Yen',  'GBPUSD': 'Pound/US Dollar',
    'USDTRY': 'US Dollar/ Lira', 'USDCHF': 'US Dollar/Franc', 'USDCAD': 'US Dollar/ Canada Dollar',
    'EURJPY': 'Euro/Yen',        'EURGBP': 'Euro/Pound',      'EURCHF': 'Euro/Franc',
    'NZDUSD': 'newZealand Dollar/US Dollar',                  'AUDUSD': 'Australian Dollar/ US Dollar'
    }

# All available tags
TAG_LIST = ["Work", "Salary", "Business", "Entertainm", "Trade", "Family", "Service", "Self"]

# All available descriptions
DESCRIPTION_DICTIONARY = {"sell": "I`m just selling", "buy": "I`m just buying"}

# example: PROVIDER_LIST[round(100 * ((5.507552 * index + 9.2580) % 0.99)) % 2]
TEMPLATE_FILLING = [ 
#    values list    | mul after round | mul before round | increment | coeff modulo | list modulo |  row index increment 
    [PROVIDER_LIST,   100,              5.507552,          9.2580,     0.99,          2,             1],
    [DIRECTION_LIST,  100,              7.529218,          11.85216,   0.99,          2,             1],
    [INSTRUMENT_LIST, 100,              9.141212,          13.722534,  0.99,          11,            8],
    [TAG_LIST,        1,                21,                25,         0.99,          8,            -7]
    ]

# example: (3 * random_number + 7) % 0.99
PSEUDORAND_NUMS_LIST = [ 
#    multiply  | increment  | modulo
    [3,          7,           0.99], # For hex_id
    [13.6541235, 17.75423023, 0.99], # For creation_date
    [27.908783,  39.974,      0.99], # For change_date
    [17,         21,          0.99]  # For initial_price
    ]

#------------------------------------------ LOGGER AND PRINT MESSAGES' ------------------------------------------

# Format for logger messages
LOGGER_OUTPUT_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# Print output messages in console
BAD_LOGGING_LEVEL_MESSAGE = "Некорректно задан уровень логирования. Программа досрочно завершена"
FILE_NOT_FOUND_MESSAGE = f"Файл %s не найден. Программа досрочно завершена"
INCORRECT_CONFIG_DATA_MESSAGE = f"В файле %s некорректные данные. Программа досрочно завершена"
INCORRECT_OR_NO_CONFIG_DATA_MESSAGE = f"В файле %s отсутствуют данные или они некорректны. Программа досрочно завершена"
INCORRECT_CONFIG_ROW_NUMBERS  = f"В файле %s количество строк может быть только целым положительным числом больше нуля. Программа досрочно завершена"

# Logger output messages in file
INFO_TASK_MESSAGE = f"Нужно сформировать таблицу где красная зона занимает %s строк, зеленая - %s, синяя - %s"
INFO_TABLE_DONE_MESSAGE = "Итоговая таблица успешно сформирована!"

INSTER_QUERY = f"insert into %s(id_pk, Order_ID, Provider, Direction, Instrument, Creation_date, Change_date,\
    Status, Initial_price, Fill_price, Initial_volume, Fill_volume, Tags, Description, Extradata) values "