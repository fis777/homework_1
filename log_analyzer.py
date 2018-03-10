#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import logging
import datetime
import configparser
import argparse
import math
import gzip

import os

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

# Проверка на повторный запуск парсера
def already_parsed(report_dir):
    full_path = os.path.join(report_dir, 'timestamp.ts')
    if os.path.exists(full_path):
        stat = os.stat(full_path)
        #Если совпадают дата файла и текущая дата
        if datetime.date.fromtimestamp(stat.st_ctime) == datetime.date.today():
            return True
    return False

def parsing(log_dir,report_size):

    file_name = 'nginx-access-ui.log-' + datetime.date.today().strftime('%Y%m%d')
    full_path = os.path.join(log_dir, file_name)
    
    log = None
    if os.path.exists(full_path + '.gz'):
        log = gzip.open(full_path + '.gz','r')
    if os.path.exists(full_path):
        log = open(full_path)
    if log is None:
        # Если нечего обрабатывать выходим
        return log

    # Kоличество записей в логе
    counter = sum(1 for line in log)
    log.seek(0)

    # Счетчик необработанных записей
    line_counter_error = 0
    #Сумма request_time всех запросов
    request_time_sum = 0

    # В результате обработки получаем справочник вида:
    # table_log = {'URL1':[request_time1,request_time2,,,,],'URL2':[request_time1,request_time2,,,,],,,}
    # для последующего рассчета необходимых данных
    table_log = {}

    for line in log:
        try:
            # Если обрабатываем '.gz'
            if type(line) is bytes:
                line = line.decode('utf-8')
            current_url = line.split(' ')[7]
            request_time = float(line.split(' ')[-1])
        except:
            line_counter_error += 1
            #Если количество ошибочных записей больше 20% от общего числа выходим с ошибкой
            if line_counter_error > counter/5:
                logging.error('Too many errors')
                return None
        else:
            #Добавляем в справочник
            try:
                table_log[current_url].append(request_time)
            except KeyError:
                #Если еще не встречался такой URL добавляем
                table_log[current_url] = [request_time]
            request_time_sum += request_time
    log.close()

    #Заполняем расчетные поля
    table = [{'count': len(table_log[item]),
              'time_avg': sum(table_log[item]) / float(len(table_log[item])),
              'time_max': max(table_log[item]),
              'time_sum': sum(table_log[item]),
              'url': item,
              'time_med': median(table_log[item]),
              'time_perc': sum(table_log[item])/(request_time_sum/100),
              'count_perc': len(table_log[item])/(counter/100)} for item in table_log]
    #Сортируем
    table.sort(key=lambda item : item['time_sum'],reverse=True)
    #Возвращаем REPORT_SIZE строк
    return table[:report_size]

#Вычисляем медиану
def median(list_request_time):

    list_request_time.sort()
    quantity = len(list_request_time)

    if quantity == 1:
        return list_request_time[0]

    half_quantity = math.floor(quantity / 2)
    if quantity % 2 == 0:
        # Если данные содержат четное число различных значений, упорядоченных в ряд, например 3, 8, 16, 17,
        # то медианой является значение, лежащее посередине между двумя центральными значениями: $М_{d}$ = (8 + 16) : 2 = 12.
        return (list_request_time[half_quantity-1] + list_request_time[half_quantity])/2
    else:
        # Если данные содержат нечетное число различных значений и они представляют упорядоченный ряд,
        # то медианой является среднее значение ряда. Например, в ряду 5, 8, 12, 25, 30 медиана $М_{d }$= 12
        return list_request_time[half_quantity]

def report_generate(report_dir,report_data):

    substr = '$table_json'
    full_path_template = os.path.join(report_dir, 'report.html')
    try:
        report_template = open(full_path_template, 'r')
    except FileNotFoundError:
        logging.error('No HTML template in %s' % report_dir)
        return False

    full_path_report =  os.path.join(report_dir, 'report-' + datetime.date.today().strftime('%Y%m%d') + '.html')
    daily_report = open(full_path_report,'w')
    for line in report_template:
        if line.find(substr):
            line = line.replace(substr, report_data)
        daily_report.writelines(line)

    report_template.close()
    daily_report.close()
    return True

def make_timestamp(report_dir):
    try:
        datetime_stamp = open(os.path.join(report_dir, 'timestamp.ts'), 'w')
    except FileNotFoundError:
        logging.error('Path %s is not exist. Timestamp is not created.', report_dir)
        return False
    datetime_stamp.write(str(datetime.datetime.now()))
    datetime_stamp.close()
    return True

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="settings.ini")
    return parser.parse_args()

def main():

    # Получаем путь к конфигу из параметра командной строки (если указан, если не указан то 'settings.ini' в текущей директории)
    args = parse_args()
    # Парсим конфиг
    conf_file = configparser.ConfigParser()
    conf_file.read(args.config)
    for name,value in conf_file.items("Settings"):
        config[name.upper()] = value

    # Платформонезависимый полный путь
    log_dir = os.path.realpath(config['LOG_DIR'])
    report_dir = os.path.realpath(config['REPORT_DIR'])

    #Настраиваем логирование для нашего парсера
    try:
        logging.basicConfig(format= u'[%(asctime)s] %(levelname)-6s %(message)s',
                                filename = os.path.join(log_dir, 'log_analyzer.log'),level = logging.INFO)
    except FileNotFoundError:
            logging.basicConfig(format=u'[%(asctime)s] %(levelname)-6s %(message)s', filename=None, level=logging.INFO)
    
    try:
        #Если лог за сегодня обработан ничего не делаем
        if already_parsed(report_dir):
            logging.error("Today log already parced")
            return

        #Непосредственно сам парсинг
        logging.info("Start")
        table = parsing(log_dir,int(config['REPORT_SIZE']))
        if table is None:
            logging.error("Log or path %s is not exist",log_dir)
            return

        report_generate(report_dir,str(table))

        # Timestamp
        make_timestamp(report_dir)
        logging.info('Successfull parsed')

    except:
        # Все остальные ошибки с трейсбеком пишем в лог
        logging.exception('Undefines error')

if __name__ == "__main__":
    main()
