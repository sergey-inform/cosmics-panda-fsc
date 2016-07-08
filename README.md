Стенд panda-fsc-cosmics
=======================
Программы, созданные для автоматической обработки данных с испытательного стенда калоримтера типа "Шашлык" для эксперимента ПАНДА. 
Их можно использовать и на других экспериментальных стендах, за исключением декодирования сырых данных, формат которых специфичен для АЦП SIS3316.
  
Обработка
---------
Сырые данные (.raw) -- это данные, вычитанные из модулей АЦП, по одному файлу на каждый канал. 
  
Последовательность обработки:
  1. **sis3316/tools/integrate.py** -- декодирование сырых форм сигналов и их интегрирование *(data1.raw -> data1.txt)*;
  1. **coinc.py** -- поиск совпадающих по времени записей с отбором определенных комбинаций каналов *({trig.conf, data1.txt, data2.txt, ...} -> data_trigA.txt, data_trigB.txt, ...)*;
  1. **root-hist.py** -- построение гистограмм для выбранного канала *(data_trigA.txt, data_trigB.txt... -> \<histogram\>)*;
  1. **root-fit.py** -- автоматическое фитирование гистограмм заданным распределением *(\<histogram\> -> \<fit\_parameters\>)*.
  
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
    ````
        
  2. Поиск совпадающих событий:
    ```Shell
    # Join several data files:
    sort --numeric-sort --merge data1.txt data2.txt ... > sorted.txt
    
    # Process one file at a time (display progress and event counts)
    pv -c ../sorted.txt | ./coinc.py -t A:1,2,3,8,9 -t B:4,5,6,8,9 --stats --progress -o ./out/trig_
    
    # Process all files:
    sort --numeric-sort --merge data*.txt | ./coinc.py -p triggers.txt --jitter=2.0 -o ./out/trig_
    
    ```
     
  3. 
  
Особенности
-----------
