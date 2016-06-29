Стенд panda-fsc-cosmics
=======================
Программы, созданные для автоматической обработки данных с испытательного стенда калоримтера типа "Шашлык" для эксперимента ПАНДА. 
Их можно использовать и на других экспериментальных стендах, за исключением декодирования сырых данных, формат которых специфичен для АЦП SIS3316.
  
Обработка
---------
Сырые данные (.raw) -- это данные, вычитанные из модулей АЦП, по одному файлу на каждый канал. 
  
Последовательность обработки:
  1. **sis3316/tools/integrate.py** -- декодирование сырых форм сигналов и их интегрирование *(data1.raw -> data1.txt)*;
  1. **coinc.py** -- поиск совпадающих событий *({trig.conf, data1.txt, data2.txt, ...} -> data.coinc)*;
  1. **root-hist.py** -- построение гистограмм для комбинации каждого исходного файла и примененного триггера совпадений *(data.coinc -> data1\_trig1.hist, data2\_trig2.hist)*;
  1. **root-fit.py** -- автоматическое фитирование гистограмм заданным распределением *(data1\_trig1.hist -> \<fit\_parameters\>)*.
  
Установка
---------
  
Запуск
------
  1. Обработка сырых данных:
    ```Shell
    # Processing one file at a time.
    # Baseline is average of 30 first samples, next 20 samples are a signal waveform.
    ~/SIS3316/tools/integrate.py -b 30 -n 20 data0.dat -o data0.txt --progress
    
    # Processing all *.dat in folder at once with GNU Parallel (data0.dat -> data0.txt)
    time parallel ~/SIS3316/tools/integrate.py -b 30 -n 20 {} -o {.}.txt  ::: *.dat
    
    # It's clever to gzip processed data files.
    pigz -v *.dat
    ```
  1. 
  
Особенности
-----------
