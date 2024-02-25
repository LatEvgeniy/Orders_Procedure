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

    @abstractmethod
    def get_field(field_attributes) -> str:
        pass

class i_builder(ABC):
    @abstractmethod
    def build_order() -> None:
        pass

    @abstractmethod
    def get_order() -> Iterable:
        pass

class abstract_creator(ABC):
    @abstractmethod
    def get_field_class(self) -> i_field:
        pass
    
    def get_field(self, field_attributes) -> str:
        field_creator = self.get_field_class()
        field_creator.set_attributes(field_attributes)
        return field_creator.get_field()

class id_creator(abstract_creator):
    def get_field_class(self) -> i_field:
        return id()

class id(i_field):
    def set_attributes(self, field_attributes):
        self.__previous_dec_id = field_attributes

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

class change_date_creator(abstract_creator):
    def get_field_class(self) -> i_field:
        return change_date()
    
class change_date(abstract_date):
    def __init__(self):
        pass

    def set_attributes(self, field_attributes):
        super().__init__(field_attributes[0], field_attributes[1], field_attributes[2])
        self.__multiplier = field_attributes[3]
        self.__increment = field_attributes[4]
        self.__modulo = field_attributes[5]

    def get_field(self) -> str:
        microsecond, second = math.modf(self._seconds * ((self.__multiplier * self._for_random + self.__increment) % self.__modulo))    
        change_date = self._start_time + timedelta(seconds=second, microseconds=microsecond*const.MICROSECONDS_MULTIPLY)
        return change_date.strftime(const.OUTPUT_TIME_FORMAT)     

class creation_date_creator(abstract_creator):
    def get_field_class(self) -> i_field:
        return creation_date()
    
class creation_date(abstract_date):
    def __init__(self):
        pass

    def set_attributes(self, field_attributes):
        super().__init__(field_attributes[0], field_attributes[1], field_attributes[2])
    
    def get_field(self) -> str:
        order_change_date = change_date_creator()
        creation_date_string = order_change_date.get_field([self._start_time, self._seconds, self._for_random,
            const.PSEUDORAND_NUMS_LIST[1][0], const.PSEUDORAND_NUMS_LIST[1][1], const.PSEUDORAND_NUMS_LIST[1][2]])
        creation_date_datetime = datetime.strptime(creation_date_string[:len(creation_date_string)-7], 
            const.INCREMENT_TIME_FORMAT).replace(tzinfo = const.TZ)
        if(creation_date_datetime.hour == const.BREAK_HOUR):    
            creation_date_datetime += timedelta(minutes = const.MINUTES_INCREMENT - creation_date_datetime.minute)        
        return creation_date_datetime.strftime(const.OUTPUT_TIME_FORMAT)

class status_creator(abstract_creator):
    def get_field_class(self) -> i_field:
        return status()

class status(i_field):
    def set_attributes(self, field_attributes):
        self.__prev_status = field_attributes[0]
        self.__for_rand = field_attributes[1]
        self.__zone = field_attributes[2]

    def get_field(self) -> str:
        current_status = const.GET_NEXT_STATUS_DICTIONARY[self.__zone][self.__prev_status]
        if (type(current_status) is list):
            current_status = current_status[0][(const.STATUS_MULTIPLY*self.__for_rand + const.STATUS_INCREMENT) % current_status[1]]   
        return current_status

class initial_price_creator(abstract_creator):
    def get_field_class(self) -> i_field:
        return initial_price()
    
class initial_price(i_field):
    def set_attributes(self, field_attributes):
        self.__instrument = field_attributes

    def get_field(self) -> str:
        top_limit, bottom_limit = const.INSTRUMENT_DICTIONARY[self.__instrument][0], const.INSTRUMENT_DICTIONARY[self.__instrument][1]
        init_price = ((const.PSEUDORAND_NUMS_LIST[3][0]*top_limit + const.PSEUDORAND_NUMS_LIST[3][1]) % 
            const.PSEUDORAND_NUMS_LIST[3][2]) * (top_limit - bottom_limit) + bottom_limit
        return str(init_price)[:const.DIGIT_COUNT_IN_PRICE]

class fill_price_creator(abstract_creator):
    def get_field_class(self) -> i_field:
        return fill_price()
    
class fill_price(i_field):
    def set_attributes(self, field_attributes):
        self.__prev_status = field_attributes[0]
        self.__current_status = field_attributes[1]
        self.__initial_price = field_attributes[2]

    def get_field(self):
        is_fill_pr_not_zero = const.FILL_PRICE_DICTIONARY[self.__current_status]
        consider_prev_reject = False if self.__current_status == const.DONE and self.__prev_status == const.REJECT else is_fill_pr_not_zero
        return self.__initial_price if consider_prev_reject else const.ZERO_FILL_PRICE

class initial_volume_creator(abstract_creator):
    def get_field_class(self) -> i_field:
        return initial_volume()
    
class initial_volume(i_field):
    def set_attributes(self, field_attributes):
        self.__for_random = field_attributes

    def get_field(self) -> str:
        return str(round(round(const.INIT_VOLUME_PARAMS[0] * (((const.INIT_VOLUME_PARAMS[1] * float(self.__for_random) +
            const.INIT_VOLUME_PARAMS[2]) % const.INIT_VOLUME_PARAMS[3]) * (const.INIT_VOLUME_PARAMS[4] - 
                const.INIT_VOLUME_PARAMS[5]) + const.INIT_VOLUME_PARAMS[5])) 
                    / const.INIT_VOLUME_PARAMS[6], 2))[:const.DIGIT_COUNT_IN_VOLUME]

class fill_volume_creator(abstract_creator):
    def get_field_class(self) -> i_field:
        return fill_volume()
    
class fill_volume(i_field):
    def set_attributes(self, field_attributes):
        self.__prev_status = field_attributes[0]
        self.__current_status = field_attributes[1]
        self.__initial_volume = field_attributes[2]
    
    def get_field(self) -> str:
        is_need_coefficient, multiplier = const.FILL_VOLUME_DICIONARY[self.__current_status][self.__prev_status]
        coefficient = (const.FILL_VOLUME_PARAMS[0]*self.__initial_volume + const.FILL_VOLUME_PARAMS[1]) % const.FILL_VOLUME_PARAMS[2]
        return str(coefficient * self.__initial_volume)[:const.DIGIT_COUNT_IN_VOLUME] if is_need_coefficient else str(multiplier 
            * self.__initial_volume)[:const.DIGIT_COUNT_IN_VOLUME]

class order_fields(Iterable):
    def __init__(self, collection: List[Any]):
        self.__fields = collection

    def get_order_field(self, index):
        if(index >= 0):
            return self.__fields[index] if index <= self.__fields.__len__() - 1 else "collection hasn`t enough fields"
        else:
            return "collection hasn`t enough fields"
    
    def add(self, data):
        self.__fields.append(data)

    def __iter__(self):
        return order_iterator(self.__fields)
    
class order_collection(Iterable):
    def __init__(self, collection: List[Any]):
        self.__all_orders = collection

    def __iter__(self):
        return order_iterator(self.__all_orders)
    
    def add(self, data):
        self.__all_orders.append(data)

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

class order_with_first_id_builder(i_builder):
    def __init__(self, start_dec_id):
        self.__start_dec_id = start_dec_id

    def build_order(self):
        order = order_fields([])
        order_id_creator = id_creator()
        order.add(order_id_creator.get_field(self.__start_dec_id))
        self.__order = order

    def get_order(self) -> Iterable:
        return self.__order
        

class order_history_record_builder:
    def __init__(self, red_rows_number, green_rows_number, blue_rows_number):
        self.__red_rows_number = red_rows_number
        self.__green_rows_number = green_rows_number
        self.__blue_rows_number = blue_rows_number

    def get_all_orders(self):
        final_table = order_collection([])
        
        first_orders_list = []
        builder_list = [
            new_order_builder(self.__red_rows_number, const.ID_START_VALUE, const.DONE, const.RED), 
            new_order_builder(self.__green_rows_number, const.ID_START_VALUE + const.ID_INCREMENT *  self.__green_rows_number, const.DONE, const.GREEN),
            new_order_builder(self.__blue_rows_number, const.ID_START_VALUE + const.ID_INCREMENT * (self.__green_rows_number + self.__blue_rows_number), const.FILL, const.BLUE)
            ]
        
        order_director = director()
        for builder in builder_list:
            order_director.builder = builder
            order_director.build_order()
            first_orders_list.append(builder.get_order())

        list = [
            [self.__red_rows_number,   const.RED,   first_orders_list[0]],
            [self.__green_rows_number, const.GREEN, first_orders_list[1]],
            [self.__blue_rows_number,  const.BLUE,  first_orders_list[2]]
            ]                    
        for zone_info in list:
            zone_table = order_collection([])   
            zone_table.add(zone_info[2])
            for index in range(0, zone_info[0] - 1):
                if(const.IS_NEW_ROW_DICT[zone_info[1]][zone_table.get_order(index).get_order_field(6)]):
                    order_builder = new_order_builder(index, int(zone_table.get_order(index).get_order_field(0), 16), zone_table.get_order(index).get_order_field(6), zone_info[1])
                else:
                    order_builder = changed_order_builder(index * int(zone_table.get_order(index).get_order_field(0), 16), zone_table.get_order(index), zone_info[1])
                order_director.builder = order_builder
                order_director.build_order()
                zone_table.add(order_builder.get_order())
            for order in zone_table:
                final_table.add(order)
        return final_table
    
class changed_order_builder(i_builder):
    def __init__(self, index, prev_order, zone):
        self.__prev_order = prev_order
        self.__index = index
        self.__zone = zone
        self.__order = None

    def build_order(self):
        order = order_fields([])
        for i in range(0, 5):      
            order.add(self.__prev_order.get_order_field(i))        
        creation_date_datetime = datetime.strptime(self.__prev_order.get_order_field(5)[:len(self.__prev_order.get_order_field(5))-7], const.INCREMENT_TIME_FORMAT).replace(tzinfo = const.TZ)  
        order_change_date = change_date_creator()
        order.add(order_change_date.get_field([creation_date_datetime, const.MAX_SECONDS_FOR_ONE_ORDER, const.PSEUDORAND_NUMS_LIST[2][0], creation_date_datetime.second, const.PSEUDORAND_NUMS_LIST[2][1], const.PSEUDORAND_NUMS_LIST[2][2]]))
        order_status = status_creator()
        order.add(order_status.get_field([self.__prev_order.get_order_field(6), self.__index, self.__zone]))
        order.add(self.__prev_order.get_order_field(7))
        order_fill_price = fill_price_creator()
        order.add(order_fill_price.get_field([self.__prev_order.get_order_field(6), order.get_order_field(6), order.get_order_field(7)]))
        order.add(self.__prev_order.get_order_field(9))
        order_fill_volume = fill_volume_creator()
        order.add(order_fill_volume.get_field([self.__prev_order.get_order_field(6), order.get_order_field(6), float(order.get_order_field(9))]))
        for index in range(11, 14):
            order.add(self.__prev_order.get_order_field(index))
        self.__order = order

    def get_order(self) -> Iterable:
        return self.__order

class new_order_builder(i_builder):
    def __init__(self, index, prev_dec_id, prev_status, zone):
        self.__index = index
        self.__prev_dec_id = prev_dec_id
        self.__prev_status = prev_status
        self.__zone = zone
        self.__order = None

    def build_order(self):        
        order = order_fields([])
        order_id_creator = id_creator()
        order.add(order_id_creator.get_field(self.__prev_dec_id))
        for index in range(0, 3):
            order.add(const.TEMPLATE_FILLING[index][0][round(const.TEMPLATE_FILLING[index][1] * ((const.TEMPLATE_FILLING[index][2]
                * self.__index + const.TEMPLATE_FILLING[index][3]) % const.TEMPLATE_FILLING[index][4])) % const.TEMPLATE_FILLING[index][5]])
        order_creation_date = creation_date_creator()
        creation_date_string = order_creation_date.get_field([const.GET_START_DATE_DICT[self.__zone][0], const.GET_START_DATE_DICT[self.__zone][1], self.__index])
        order.add(creation_date_string)
        creation_date_datetime = datetime.strptime(creation_date_string[:len(creation_date_string)-7], const.INCREMENT_TIME_FORMAT).replace(tzinfo = const.TZ)                
        order_change_date = change_date_creator()
        order.add(order_change_date.get_field([creation_date_datetime, const.MAX_SECONDS_FOR_ONE_ORDER, const.PSEUDORAND_NUMS_LIST[2][0], creation_date_datetime.second, const.PSEUDORAND_NUMS_LIST[2][1], const.PSEUDORAND_NUMS_LIST[2][2]]))
        order_status = status_creator()
        order.add(order_status.get_field([self.__prev_status, self.__index, self.__zone]))
        order_initial_price = initial_price_creator()
        order.add(order_initial_price.get_field(order.get_order_field(3)))
        order_fill_price = fill_price_creator()
        order.add(order_fill_price.get_field([self.__prev_status, order.get_order_field(6), order.get_order_field(7)]))
        order_initial_volume = initial_volume_creator()
        order.add(order_initial_volume.get_field(self.__index))
        order_fill_volume = fill_volume_creator()
        order.add(order_fill_volume.get_field([self.__prev_status, order.get_order_field(6), float(order.get_order_field(9))]))
        order.add(const.TEMPLATE_FILLING[3][0][round(const.TEMPLATE_FILLING[3][1] * ((const.TEMPLATE_FILLING[3][2]
                * self.__index + const.TEMPLATE_FILLING[3][3]) % const.TEMPLATE_FILLING[3][4])) % const.TEMPLATE_FILLING[3][5]])
        order.add(const.DESCRIPTION_DICTIONARY[order.get_order_field(2)])
        order.add(const.EXTRADATA_DICTIONARY[order.get_order_field(3)])
        self.__order = order

    def get_order(self) -> Iterable:
        return self.__order

class director:
    def __init__(self):
        self.__builder = None

    @property
    def builder(self) -> i_builder:
        return self.__builder
    
    @builder.setter
    def builder(self, builder: builder) -> None:
        self.__builder = builder

    def build_order(self):
        self.__builder.build_order()

def main():
    for order in order_history_record_builder(12, 12, 12).get_all_orders():
        print(tuple(order))

if __name__ == "__main__":
    main()