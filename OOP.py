import math
import os
import logging
import configparser
import Constant_values_for_orders as const
from collections import namedtuple
from _collections_abc import Iterator, Iterable
from datetime import datetime, timedelta
from getpass import getpass
from abc import ABC, abstractmethod

class i_field(ABC):
    @abstractmethod
    def get_field(self) -> str:
        pass

class abstract_date(ABC):    
    def __init__(self, start_time, seconds, for_random):
        self._start_time = start_time
        self._seconds = seconds
        self._for_random = for_random

    @abstractmethod
    def get_field(self) -> str:
        pass
    
class id(i_field):
    def __init__(self, previous_dec_id):
        self.__previous_dec_id = previous_dec_id

    def get_field(self) -> str:
        self.__previous_dec_id += const.ID_INCREMENT * ((const.PSEUDORAND_NUMS_LIST[0][0]*self.__previous_dec_id + 
            const.PSEUDORAND_NUMS_LIST[0][1]) % const.PSEUDORAND_NUMS_LIST[0][2])
        return hex(round(self.__previous_dec_id)).lstrip(const.ID_LEFT_STRIP).upper().zfill(const.DIGIT_COUNT_IN_HEX_ID)
    
class change_date(abstract_date):
    def __init__(self, start_time, seconds, for_random, multiplier, increment, modulo):
        super().__init__(start_time, seconds, for_random)
        self.__multiplier = multiplier
        self.__increment = increment
        self.__modulo = modulo

    def get_field(self) -> str:
        microsecond, second = math.modf(self._seconds * ((self.__multiplier * self._for_random + self.__increment) % self.__modulo))    
        change_date = self._start_time + timedelta(seconds=second, microseconds=microsecond*const.MICROSECONDS_MULTIPLY)
        return change_date.strftime(const.OUTPUT_TIME_FORMAT)     

class creation_date(abstract_date):
    def __init__(self, start_time, seconds, for_random):
        super().__init__(start_time, seconds, for_random)
    
    def get_field(self) -> str:
        change_date_field = change_date(self._start_time, self._seconds, self._for_random,
            const.PSEUDORAND_NUMS_LIST[1][0], const.PSEUDORAND_NUMS_LIST[1][1], const.PSEUDORAND_NUMS_LIST[1][2])
        creation_date_string = change_date_field.get_field()
        creation_date_datetime = datetime.strptime(creation_date_string[:len(creation_date_string)-7], 
            const.INCREMENT_TIME_FORMAT).replace(tzinfo = const.TZ)
        if(creation_date_datetime.hour == const.BREAK_HOUR):    
            creation_date_datetime += timedelta(minutes = const.MINUTES_INCREMENT - creation_date_datetime.minute)        
        return creation_date_datetime.strftime(const.OUTPUT_TIME_FORMAT)

class status(i_field):
    def __init__(self, prev_status, for_rand, zone):
        self.__prev_status = prev_status
        self.__for_rand = for_rand
        self.__zone = zone

    def get_field(self) -> str:
        current_status = const.GET_NEXT_STATUS_DICTIONARY[self.__zone][self.__prev_status]
        if (type(current_status) is list):
            current_status = current_status[0][(const.STATUS_MULTIPLY*self.__for_rand + const.STATUS_INCREMENT) % current_status[1]]   
        return current_status

class initial_price(i_field):
    def __init__(self, instrument):
        self.__instrument = instrument

    def get_field(self) -> str:
        top_limit, bottom_limit = const.INSTRUMENT_DICTIONARY[self.__instrument][0], const.INSTRUMENT_DICTIONARY[self.__instrument][1]
        init_price = ((const.PSEUDORAND_NUMS_LIST[3][0]*top_limit + const.PSEUDORAND_NUMS_LIST[3][1]) % 
            const.PSEUDORAND_NUMS_LIST[3][2]) * (top_limit - bottom_limit) + bottom_limit
        return str(init_price)[:const.DIGIT_COUNT_IN_PRICE]

class fill_price(i_field):
    def __init__(self, prev_status, current_status, initial_price):
        self.__prev_status = prev_status
        self.__current_status = current_status
        self.__initial_price = initial_price

    def get_field(self):
        is_fill_pr_not_zero = const.FILL_PRICE_DICTIONARY[self.__current_status]
        consider_prev_reject = False if self.__current_status == const.DONE and self.__prev_status == const.REJECT else is_fill_pr_not_zero
        return self.__initial_price if consider_prev_reject else const.ZERO_FILL_PRICE
        
class initial_volume(i_field):
    def __init__(self, for_random):
        self.__for_random = for_random

    def get_field(self) -> str:
        return str(round(round(const.INIT_VOLUME_PARAMS[0] * (((const.INIT_VOLUME_PARAMS[1] * float(self.__for_random) +
            const.INIT_VOLUME_PARAMS[2]) % const.INIT_VOLUME_PARAMS[3]) * (const.INIT_VOLUME_PARAMS[4] - 
                const.INIT_VOLUME_PARAMS[5]) + const.INIT_VOLUME_PARAMS[5])) 
                    / const.INIT_VOLUME_PARAMS[6], 2))[:const.DIGIT_COUNT_IN_VOLUME]

class fill_volume(i_field):
    def __init__(self, prev_status, current_status, initial_volume):
        self.__prev_status = prev_status
        self.__current_status = current_status
        self.__initial_volume = float(initial_volume)
    
    def get_field(self) -> str:
        is_need_coefficient, multiplier = const.FILL_VOLUME_DICIONARY[self.__current_status][ self.__prev_status]
        coefficient = (const.FILL_VOLUME_PARAMS[0]*self.__initial_volume + const.FILL_VOLUME_PARAMS[1]) % const.FILL_VOLUME_PARAMS[2]
        return str(coefficient * self.__initial_volume)[:const.DIGIT_COUNT_IN_VOLUME] if is_need_coefficient else str(multiplier 
            * self.__initial_volume)[:const.DIGIT_COUNT_IN_VOLUME]

class order_fields(Iterable):
    def __init__(self):
        self.__fields = [" ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " "]

    def get_field(self, index):
        if(index >= 0):
            return self.__fields[index] if index <= self.__fields.__len__() - 1 else "collection hasn`t enough fields"
        else:
            return "collection hasn`t enough fields"
    
    def set_field(self, index, field_data):
        self.__fields[index] = field_data

    def __iter__(self):
        return order_iterator(self.__fields)
    
class order_collection(Iterable):
    def __init__(self):
        self.__all_orders = []

    def __iter__(self):
        return order_iterator(self.__all_orders)
    
    def add(self, order_field):
        self.__all_orders.append(order_field)

    def get_order(self, order_index):
        if(order_index >= 0):
            return self.__all_orders[order_index] if order_index <= self.__all_orders.__len__() - 1 else "collection hasn`t enough orders"
        else:
            return "collection hasn`t enough orders"

class order_iterator(Iterator):
    def __init__(self, collection):
        self.__collection = collection
        self.__position = 0

    def __next__(self):
        try:
            value = self.__collection[self.__position]
            self.__position += 1
        except IndexError:
            raise StopIteration()
        return value

class order_builder:
    def __init__(self, index, prev_dec_id, prev_status, zone):
        self.__index = index
        self.__prev_dec_id = prev_dec_id
        self.__zone = zone
        self.__prev_status = prev_status

    def build_order(self):
        order, iter = self.__first_template_filling()
        order.set_field(0, id(self.__prev_dec_id).get_field())
        creation_date_string = creation_date(const.GET_START_DATE_DICT[self.__zone][0], const.GET_START_DATE_DICT[self.__zone][1], self.__index).get_field()
        creation_date_datetime = datetime.strptime(creation_date_string[:len(creation_date_string)-7], const.INCREMENT_TIME_FORMAT).replace(tzinfo = const.TZ)        
        order.set_field(5, change_date(creation_date_datetime, const.MAX_SECONDS_FOR_ONE_ORDER, const.PSEUDORAND_NUMS_LIST[2][0], creation_date_datetime.second, const.PSEUDORAND_NUMS_LIST[2][1], const.PSEUDORAND_NUMS_LIST[2][2]).get_field())
        order = self.__second_template_filling(order, creation_date_string, iter)
        order.set_field(8, fill_price(self.__prev_status, order.get_field(6), order.get_field(7)).get_field())
        order.set_field(10, fill_volume(self.__prev_status, order.get_field(6), float(order.get_field(9))).get_field())
        return order

    def __first_template_filling(self):
        order = order_fields()
        iter = const.TEMPLATE_FILLING_START_INDEX
        for i in range(0,len(const.TEMPLATE_FILLING)):
            order.set_field(iter, const.TEMPLATE_FILLING[i][0][round(const.TEMPLATE_FILLING[i][1] * ((const.TEMPLATE_FILLING[i][2]
                * self.__index + const.TEMPLATE_FILLING[i][3]) % const.TEMPLATE_FILLING[i][4])) % const.TEMPLATE_FILLING[i][5]])
            iter += const.TEMPLATE_FILLING[i][6]
        return order, iter
    
    def __second_template_filling(self, order, creation_date_string, iter):
        template_filling_list = [
            [creation_date_string, 2], [status(self.__prev_status, self.__index * round(self.__prev_dec_id), self.__zone).get_field(), 1],
            [initial_price(order.get_field(3)).get_field(), 2], [initial_volume(self.__index).get_field(), 3],
            [const.DESCRIPTION_DICTIONARY[order.get_field(2)], 1], [const.EXTRADATA_DICTIONARY[order.get_field(3)], 0]    
            ]
        for function in template_filling_list:
            order.set_field(iter, function[0])
            iter += function[1]
        return order

class build_changed_order:
    def __init__(self, order_for_change, index, zone):
        self.__order_for_change = order_for_change
        self.__index = index
        self.__zone = zone

    def build_order(self):
        current_status = status(self.__order_for_change.get_field(6), self.__index*round(int(self.__order_for_change.get_field(0), 16)), self.__zone).get_field()
        prev_datatime_change_date = datetime.strptime(self.__order_for_change.get_field(5)[:len(self.__order_for_change.get_field(5))-7],
            const.INCREMENT_TIME_FORMAT).replace(tzinfo = const.TZ)
        order_change_date = change_date(prev_datatime_change_date, const.MAX_SECONDS_FOR_ONE_ORDER,
            const.PSEUDORAND_NUMS_LIST[2][0], prev_datatime_change_date.second, const.PSEUDORAND_NUMS_LIST[2][1],
                const.PSEUDORAND_NUMS_LIST[2][2]).get_field()
        order_fill_price =  fill_price(self.__order_for_change.get_field(6),  current_status, self.__order_for_change.get_field(7)).get_field()
        order_fill_volume = fill_volume(self.__order_for_change.get_field(6), current_status, float(self.__order_for_change.get_field(9))).get_field()
        template_filling = [[5, order_change_date], [6, current_status], [8, order_fill_price], [10, order_fill_volume]]
        for filling in template_filling:
            self.__order_for_change.set_field(filling[0], filling[1])
        return self.__order_for_change

class all_orders():
    def __init__(self, red_rows_num, green_zone_num, blue_rows_num):
        self.__red_rows_num = red_rows_num
        self.__green_zone_num = green_zone_num
        self.__blue_zone_num = blue_rows_num

    def create_order_collection(self):
        final_table = order_collection()
        start_string_id = id(const.ID_START_VALUE).get_field()
        list = [
            [self.__red_rows_num,   const.RED,   order_builder(self.__red_rows_num * round(int(start_string_id, 16)), int(start_string_id, 16), const.DONE, const.RED).build_order()],
            [self.__green_zone_num, const.GREEN, order_builder(self.__green_zone_num, int(start_string_id, 16) + const.ID_INCREMENT *  self.__green_zone_num, const.DONE, const.GREEN).build_order()],
            [self.__blue_zone_num,  const.BLUE,  order_builder(self.__blue_zone_num,  int(start_string_id, 16) + const.ID_INCREMENT * (self.__green_zone_num + self.__blue_zone_num), const.FILL, const.BLUE).build_order()]
            ]            
        for zone_info in list:
            zone_table = order_collection()
            order = zone_info[2]
            zone_table.add(order)
            for index in range(0, zone_info[0] - 1):
                if(const.IS_NEW_ROW_DICT[zone_info[1]][zone_table.get_order(index).get_field(6)]):
                    order = order_builder(index**13, int(zone_table.get_order(index).get_field(0), 16), zone_table.get_order(index).get_field(6), zone_info[1]).build_order()
                else:
                    order = build_changed_order(zone_table.get_order(index), index**13, zone_info[1]).build_order()
                zone_table.add(order)
            for order in zone_table:
                final_table.add(order)
        return final_table

def main():
    for order in all_orders(5, 5, 5).create_order_collection():
        print(tuple(order))
    # order = order_builder(3123, 42145, "part fill", "green").build_order()
    # print(tuple(order))
    # new_order = build_changed_order(order, 2131, "green").build_order()
    # print(tuple(new_order))
if __name__ == "__main__":
    main()