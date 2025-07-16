<div align="center">


  <pre>Асинхронный пинг + логгирование</pre>
  <br>
  <div>
    <a href="https://github.com/ValentinBELYN/icmplib">Сделано на основе библиотеки icmplib</a>&nbsp;&nbsp;&nbsp;
  </div>
  <br>
</div>

## Features

- :deciduous_tree: **async-ping + logging** Выполняет пинг к различным клиентам и логгирует результаты ping в файлы c разбивкой по месяцам

## Usage

- **Settings async-ping**

  Изменяем файл config.json под нужные ip-адреса, интервал, и количество запросов:

  ```shell
    {
    "hosts": [
        "8.8.8.8",
        "7.7.7.7"
    ],
    "ping_interval": 300,
    "ping_timeout": 2,
    "ping_count": 2
    }
  ```

- **Run async-ping**

  После создания образа, например "async-ping:1.0", запуск через docker: 

  ```shell
  docker run -d --name async-ping-1.0-container -v /home/user/logs:/app/logs --restart always async-ping:1.0
  ```

  Логи будут храниться в операционной системе по адресу: /home/user/logs
