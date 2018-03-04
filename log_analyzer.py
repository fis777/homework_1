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


def nginx_log_file_descrptor(log_dir):
    full_path = log_dir+'/nginx-access-ui.log-'+datetime.date.today().strftime('%Y%m%d')
    if os.path.exists(full_path + '.gz'):
        return gzip.open(full_path + '.gz','r')
    if os.path.exists(full_path):
        return open(full_path)
    return None

# Проверка на повторный запуск парсера
def already_parsed(timestamp_dir):
    if os.path.exists(timestamp_dir + '/log_analizer.ts'):
        stat = os.stat(timestamp_dir + '/log_analizer.ts')
        #Если совпадают дата файла и текущая дата
        if datetime.date.fromtimestamp(stat.st_ctime) == datetime.date.today():
            return True
    return False

# Возвращает количество строк в логе
def line_counter(log_dir):
    log = nginx_log_file_descrptor(log_dir)
    if log is not None:
        counter = len(log.readlines())
        log.close()
    else:
        counter = 0
    return counter

def parsing(log_dir,report_size):
    # Счетчик необработанных записей
    line_counter_error = 0
    #Сумма request_time всех запросов
    request_time_sum = 0
    # Kоличество записей в логе
    counter = line_counter(log_dir)
    if counter == 0:
        logging.error("Log file is empty or not exist")
        return None

    # В результате обработки получаем справочник вида:
    # table_log = {'URL1':[request_time1,request_time2,,,,],'URL2':[request_time1,request_time2,,,,],,,}
    # для последующего рассчета необходимых данных
    table_log = {}
    nginx_log = nginx_log_file_descrptor(log_dir)
    if nginx_log is None:
        logging.error("Log is not exist")
        return None

    for line in nginx_log:
        try:
            # Если обрабатываем '.gz'
            if type(line) is bytes:
                line = line.decode('utf-8')
            current_url = line.split(' ')[7]
            request_time = float(line.split(' ')[-1])
        except:
            logging.error(u'Is not added: %s' % line)
            line_counter_error += 1
            #Если количество ошибочных записей больше 20% от общего числа выходим с ошибкой
            if line_counter_error > counter/5:
                logging.error(u'Too many errors')
                return None
        else:
            #Добавляем в справочник
            try:
                table_log[current_url].append(request_time)
            except KeyError:
                #Если еще не встречался такой URL добавляем
                table_log[current_url] = [request_time]
            request_time_sum += request_time
    nginx_log.close()

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
    try:
        report_template = open(report_dir + '/report.html', 'r')
    except FileNotFoundError:
        logging.error('No HTML template in %s' % report_dir)
        return False
    daily_report = open(report_dir + '/report-' + datetime.date.today().strftime('%Y%m%d') + '.html','w')
    for line in report_template:
        if line.find(substr):
            line = line.replace(substr, report_data)
        daily_report.writelines(line)

    report_template.close()
    daily_report.close()
    return True

def make_timestamp(timestamp_dir):
    try:
        datetime_stamp = open(timestamp_dir + '/log_analizer.ts', 'w')
    except FileNotFoundError:
        logging.error('No timestamp file stamped')
        return False
    datetime_stamp.write(str(datetime.datetime.now()))
    datetime_stamp.close()
    return True


def main():

    # Дефолтное значение пути к конфигу
    config_path = 'settings.ini'
    # Получаем путь к конфигу из параметра командной строки (если указан)
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str)
    arg = parser.parse_args()
    if arg.config:
        config_path = arg.config
    # Если не найден конфиг завершаем работу
    if not os.path.exists(config_path):
        return
    # Парсим конфиг
    config_file = configparser.ConfigParser()
    config_file.read(config_path)
    if config_file.has_option("Settings","report_size"):
        config['REPORT_SIZE'] = config_file.getint("Settings","report_size")
    if config_file.has_option("Settings", "report_dir"):
        config['REPORT_DIR'] = config_file.get("Settings", "report_dir")
    if config_file.has_option("Settings", "log_dir"):
        config['LOG_DIR'] = config_file.get("Settings", "log_dir")
    if config_file.has_option("Settings", "analyzer_log_dir"):
        config['ANALYZER_LOG_DIR'] = config_file.get("Settings", "analyzer_log_dir")
    if config_file.has_option("Settings", "timestamp_dir"):
        config['TIMESTAMP_DIR'] = config_file.get("Settings", "timestamp_dir")


    #Настраиваем логирование для нашего парсера
    if "ANALYZER_LOG_DIR" in config:
        try:
            logging.basicConfig(format= u'[%(asctime)s] %(levelname)-6s %(message)s',
                                filename = config['ANALYZER_LOG_DIR'] + '/log_analiser.log',level = logging.INFO)
        except FileNotFoundError:
            logging.basicConfig(format=u'[%(asctime)s] %(levelname)-6s %(message)s', filename=None, level=logging.INFO)
            logging.error('ANALYZER_LOG_DIR defined but not exist')
            return
    else:
        logging.basicConfig(format= u'[%(asctime)s] %(levelname)-6s %(message)s',filename = None,level = logging.INFO)
    logging.info('Started')

    try:
        #Если лог за сегодня обработан ничего не делаем
        if already_parsed(config['TIMESTAMP_DIR']):
            logging.error("Today log already parced")
            return

        # Если лог за сегодня пустой или его нет ничего не делаем
        if line_counter(config['LOG_DIR']) == 0:
            logging.error("Today log empty or not exist")
            return

        #Непосредственно сам парсинг
        table = parsing(config['LOG_DIR'],config['REPORT_SIZE'])

        report_generate(config["REPORT_DIR"],str(table))

        # Timestamp
        make_timestamp(config['TIMESTAMP_DIR'])
        logging.info('Successfull parsed')

    except:
        # Все остальные ошибки с трейсбеком пишем в лог
        logging.exception('Undefines error')

if __name__ == "__main__":
    main()
