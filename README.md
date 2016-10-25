Стенд panda-fsc-cosmics
=======================
Программы, созданные для обработки и фитирования данных с испытательного стенда калоримтера типа "Шашлык" для эксперимента ПАНДА. Формат сырых данных специфичен для АЦП SIS3316, всё остальное можно использовать и на других стендах.
  
Обработка
---------
Сырые данные (.raw) -- это бинарные данные, вычитанные из модулей АЦП, по одному файлу на каждый канал. Формат определяется настройками АЦП.
  
Последовательность обработки данных:
  1. **sis3316/tools/integrate.py** -- декодирование сырых форм сигналов и их интегрирование *(data1.raw -> data1.txt)*;
  1. **coinc.py** -- поиск совпадающих по времени записей с отбором определенных комбинаций каналов *({trig.conf, data1.txt, data2.txt, ...} -> data_trigA.txt, data_trigB.txt, ...)*;
  1. \* **monsys/monsys_adjust.py** -- скорректировать амплитуды сигналов на основе данных мониторной системы;
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
    # Baseline is average of 30 first samples, all next samples are signal waveform,
    # also for each record save found baseline.
    ~/SIS3316/tools/integrate.py -b 20 data0.dat -o data0.txt --progress  --save-bl
    
    # Processing all *.dat in folder at once with GNU Parallel (data0.dat -> data0.txt)
    time parallel ~/SIS3316/tools/integrate.py -b 30 {} -o {.}.txt  ::: *.dat
    
    # It's clever to gzip processed data files.
    pigz -v *.dat
    ````
        
  2. Поиск совпадающих событий:
    ```Shell
    # Check that timestamps in files are consequent:
    for file in `ls data*.txt`; do  echo $file; sort -cn $file ; done
    
    # Sometimes first timestamps in files are not conequent.
    # Remove first 10 lines of each text file with:
    for file in `ls data_*.txt`; do  echo $file; sed -i -e 1,10d $file ;done
    
    # Join several data files:
    sort --numeric-sort --merge data1.txt data2.txt ... > sorted.txt
    
    # Process one file at a time (display progress and statistics for event lengths),
    # find coincidences for channels 8-11 and 12-15 with jitter no more than 2 timestamp units,
    # write coincidential events to ./out/trig_A.txt and ./out/trigB.txt 
    pv -c ../sorted.txt | ./coinc.py -t A:8,9,10,11 -t B:12,13,14,15 --stats --progress -o ./out/trig_
    
    # Process all files:
    sort --numeric-sort --merge data*.txt | ./coinc.py -p triggers.txt --jitter=2.0 -o ./trig_j2/
    ```
     
  3. Коррекция по данным мониторной системы:
  Если набор данных проводился утилитой readout_monsys.py, то раз в несколько секунд на выход UI АЦП подавались импульсы для запуска источника света мониторной системы. Таким образом, в каналах, подсвеченной мониторной системой, будет два типа событий: космика и мониторная система. Отделить одни от других можно по амплитуде, либо отобрав события мониторной системы по совпадению во всех подсвеченных каналах.
    
  На предыдущем этапе в триггере "mon" задаем совпадение во всех каналах, подсвечиваемых мониторной системой.
  В дальнейшем усредняем данные для каждой последовательности мониторных импульсов (считаем, что между последовательностями импульсов проходит несколько секунд).
  
      ./monsys_avg.py ./trig_j2/mon.txt > mon_avg.txt
      
  Уменьшаем количество данных (усредняем до 1000 точек):
  
      ./monsys_reduce.py mon_avg.txt  > mon_reduced1000.txt
  
  Обрабатываем данные: устраняем "уплывание" сигнала в каждом канале:
  ```Shell
    for file in `ls data/??.txt`; do ./monsys_adjust.py  $file  mon_reduced1000.txt > data_adj/$(basename $file); echo $file; done
  ```
  
  4. Строим гистограмму:
  
  
  5. Фитируем данные вручную (пакетом ROOT):
  
  6. Находим максимум в автоматическом режиме ([усреднением с KDE](https://en.wikipedia.org/wiki/Kernel_density_estimation)):
  
  
Особенности
-----------
