#### Скрипт для парсинга лога nginx за текущую дату.

Служебная информация для работы скрипта задается в файле конфигурации,по умолчанию это _settings.ini_

Можно передать скрипту другой файл конфигурации запустив скрипт с опцией *--config "полный путь до файла"*.

В файле конфигурации можно указать:
* `report_size`  Количество строк в отчете
* `log_dir`  путь до лога
* `analyzer_log_dir`  путь до лога самого скрипта
* `timestamp_dir`  путь до файла timestamp

 Результатом работы является файл с именем *report-YYYYMMDD.html*

 Запуск скрипта: python **log_analyzer.py [--config config]**

 Запуск тестов: **python -m unittest test.py -v**