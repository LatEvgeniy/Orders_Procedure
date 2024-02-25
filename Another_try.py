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
from typing import Any, List

class i_field(ABC):
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

class abstract_date(ABC):    
    def __init__(self, start_time, seconds, for_random):
        self._start_time = start_time
        self._seconds = seconds
        self._for_random = for_random

    @abstractmethod
    def get_field(self) -> str:
        pass

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
    def __init__(self, collection: List[Any] = []):
        self.__fields = collection

    def get_order_field(self, index):
        if(index >= 0):
            return self.__fields[index] if index <= self.__fields.__len__() - 1 else "collection hasn`t enough fields"
        else:
            return "collection hasn`t enough fields"
    
    def add(self, field_data):
        self.__fields.append(field_data)

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

class green_zone_builder:
    def __init__(self, green_zone_nums, zone):
        self.__green_zone_nums = green_zone_nums
        self.__zone = zone

    def get_green_orders(self):
        zone_table = order_collection()

        green_order_builder = green_new_order_builder(self.__green_zone_nums, const.ID_START_VALUE, const.FILL, self.__zone)
        
        zone_table.add(green_order_builder.get_order())
        for index in range(0, self.__green_zone_nums - 1):
            if(const.IS_NEW_ROW_DICT[self.__zone][zone_table.get_order(index).get_order_field(6)]):
                green_order_builder = green_new_order_builder(index, int(zone_table.get_order(index).get_order_field(0), 16), zone_table.get_order(index).get_order_field(6), self.__zone)
            else:
                green_order_builder = green_changed_order_builder(index * int(zone_table.get_order(index).get_order_field(0), 16), zone_table.get_order(index), self.__zone)
            zone_table.add(green_order_builder.get_order())
        return zone_table
    
class green_changed_order_builder:
    def __init__(self, index, prev_order, zone):
        self.__prev_order = prev_order
        self.__index = index
        self.__zone = zone

    def get_order(self):
        order = order_fields()
        for i in range(0, 5):      
            order.add(self.__prev_order.get_order_field(i))        
        creation_date_datetime = datetime.strptime(self.__prev_order.get_order_field(5)[:len(self.__prev_order.get_order_field(5))-7], const.INCREMENT_TIME_FORMAT).replace(tzinfo = const.TZ)        
        template_filling_list = [
            change_date(creation_date_datetime, const.MAX_SECONDS_FOR_ONE_ORDER, const.PSEUDORAND_NUMS_LIST[2][0], creation_date_datetime.second, const.PSEUDORAND_NUMS_LIST[2][1], const.PSEUDORAND_NUMS_LIST[2][2]).get_field(),
            status(self.__prev_order.get_order_field(6), self.__index, self.__zone).get_field(), self.__prev_order.get_order_field(7) 
            ]
        for field in template_filling_list:
            order.add(field)
        order.add(fill_price(self.__prev_order.get_order_field(6), order.get_order_field(6), order.get_order_field(7)).get_field())
        order.add(self.__prev_order.get_order_field(9))
        order.add(fill_volume(self.__prev_order.get_order_field(6), order.get_order_field(6), float(order.get_order_field(9))).get_field())
        for index in range(11, 14):
            order.add(self.__prev_order.get_order_field(index))
        return order

class green_new_order_builder:
    def __init__(self, index, prev_dec_id, prev_status, zone):
        self.__index = index
        self.__prev_dec_id = prev_dec_id
        self.__prev_status = prev_status
        self.__zone = zone

    def get_order(self):
        order = order_fields()
        order.add(id(self.__prev_dec_id).get_field())
        for index in range(0, 3):
            order.add(const.TEMPLATE_FILLING[index][0][round(const.TEMPLATE_FILLING[index][1] * ((const.TEMPLATE_FILLING[index][2]
                * self.__index + const.TEMPLATE_FILLING[index][3]) % const.TEMPLATE_FILLING[index][4])) % const.TEMPLATE_FILLING[index][5]])
        creation_date_string = creation_date(const.GET_START_DATE_DICT[self.__zone][0], const.GET_START_DATE_DICT[self.__zone][1], self.__index).get_field()
        order.add(creation_date_string)
        creation_date_datetime = datetime.strptime(creation_date_string[:len(creation_date_string)-7], const.INCREMENT_TIME_FORMAT).replace(tzinfo = const.TZ)                
        order.add(change_date(creation_date_datetime, const.MAX_SECONDS_FOR_ONE_ORDER, const.PSEUDORAND_NUMS_LIST[2][0], creation_date_datetime.second, const.PSEUDORAND_NUMS_LIST[2][1], const.PSEUDORAND_NUMS_LIST[2][2]).get_field())
        order.add(status(self.__prev_status, self.__index, self.__zone).get_field())
        order.add(initial_price(order.get_order_field(3)).get_field())
        order.add(fill_price(self.__prev_status, order.get_order_field(6), order.get_order_field(7)).get_field())
        order.add(initial_volume(self.__index).get_field())
        order.add(fill_volume(self.__prev_status, order.get_order_field(6), float(order.get_order_field(9))).get_field())
        order.add(const.TEMPLATE_FILLING[3][0][round(const.TEMPLATE_FILLING[3][1] * ((const.TEMPLATE_FILLING[3][2]
                * self.__index + const.TEMPLATE_FILLING[3][3]) % const.TEMPLATE_FILLING[3][4])) % const.TEMPLATE_FILLING[3][5]])
        order.add(const.DESCRIPTION_DICTIONARY[order.get_order_field(2)])
        order.add(const.EXTRADATA_DICTIONARY[order.get_order_field(3)])
        return order

def main():
    # for order in all_orders(5, 5, 5).create_order_collection():
    #     print(tuple(order))
    # order = order_builder(3123, 42145, "part fill", "green").build_order()
    # print(tuple(order))
    # new_order = build_changed_order(order, 2131, "green").build_order()
    # print(tuple(new_order))
    # for order in green_zone_builder(15, const.RED).get_green_orders():
    #     print(tuple(order))
    col = order_fields()
    col.add("something")
    col.add("someth13413ing")
    print(col.get_order_field(0))
    for item in col:
        print(item)


if __name__ == "__main__":
    main()