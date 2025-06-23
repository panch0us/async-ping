import asyncio
from icmplib import async_ping
import logging
from logging.handlers import TimedRotatingFileHandler
import datetime
import json
import os
from typing import List, Dict

# ==============================================
# КОНСТАНТЫ И НАСТРОЙКИ
# ==============================================

CONFIG_FILE = 'config.json'     # Путь к конфигурационному файлу
LOG_DIR     = 'logs'            # Директория для хранения логов

# ==============================================
# НАСТРОЙКА ЛОГГИРОВАНИЯ С РОТАЦИЕЙ ПО МЕСЯЦАМ
# ==============================================

def setup_logging():
    """Настраивает систему логирования с ротацией по месяцам"""
    
    # Создаем директорию для логов, если ее нет
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Формат записей в лог-файле
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Создаем обработчик с ротацией по месяцам
    # Файлы будут называться типа 'ping_monitor_2025-05.log'
    log_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, 'ping_monitor.log'),
        when='M',          # Ротация в начале каждого месяца
        interval=1,        # Каждый месяц
        backupCount=24,    # Хранить логи за 12 месяцев
        encoding='utf-8'
    )
    
    # Устанавливаем суффикс для архивных файлов (по году и месяцу)
    log_handler.suffix = "%Y-%m.log"
    
    # Настраиваем базовую конфигурацию логирования
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            log_handler,            # Запись в файл с ротацией
            #logging.StreamHandler() # Вывод в консоль
        ]
    )

# ==============================================
# РАБОТА С КОНФИГУРАЦИОННЫМ ФАЙЛОМ
# ==============================================

def load_config() -> Dict:
    """
    Загружает конфигурацию из JSON-файла.
    Возвращает словарь с настройками.
    """
    
    # Стандартные настройки, если файл не найден или поврежден
    default_config = {
        "hosts": [
            "8.8.8.8", 
            "1.1.1.1",
            "10.18.7.1",
            "10.18.7.2",
            "10.18.7.3",
            ],
        "ping_interval": 60,
        "ping_timeout": 2,
        "ping_count": 2
    }
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            
            # Проверяем, что все необходимые поля есть в конфиге
            if not all(key in config for key in default_config):
                logger.warning("Config file is missing some settings. Using defaults.")
                config = {**default_config, **config}
                
            return config
            
    except FileNotFoundError:
        logger.warning(f"Config file {CONFIG_FILE} not found. Using default settings.")
        return default_config
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file {CONFIG_FILE}. Using default settings.")
        return default_config

# ==============================================
# ФУНКЦИИ ДЛЯ ПИНГОВАНИЯ ХОСТОВ
# ==============================================

async def ping_host(host: str, timeout: int = 2, count: int = 2) -> Dict:
    """
    Асинхронно пингует указанный хост и возвращает результат в виде словаря.
    
    Параметры:
        host (str): IP-адрес или доменное имя хоста
        timeout (int): Таймаут ожидания ответа в секундах
        count (int): Количество отправляемых пакетов
        
    Возвращает:
        Dict: Результат пинга с информацией о доступности и времени ответа
    """
    
    try:
        # Выполняем асинхронный ping
        result = await async_ping(host, count=count, timeout=timeout)
        
        return {
            'host':        host,
            'is_alive':    result.is_alive,
            'packet_loss': result.packet_loss,
            'avg_rtt':     result.avg_rtt,
            'min_rtt':     result.min_rtt,
            'max_rtt':     result.max_rtt,
            'error':       None
        }
    except Exception as e:
        # В случае ошибки возвращаем информацию о недоступности
        return {
            'host':        host,
            'is_alive':    False,
            'packet_loss': 100,
            'error':       str(e)
        }

async def check_all_hosts(hosts: List[str], timeout: int, count: int) -> List[Dict]:
    """
    Пингует все указанные хосты параллельно и возвращает результаты.
    
    Параметры:
        hosts (List[str]): Список хостов для проверки
        timeout (int): Таймаут ожидания ответа в секундах
        count (int): Количество отправляемых пакетов
        
    Возвращает:
        List[Dict]: Список результатов проверки для каждого хоста
    """
    
    # Создаем задачи для каждого хоста
    tasks = [ping_host(host, timeout, count) for host in hosts]
    
    # Выполняем все задачи параллельно
    return await asyncio.gather(*tasks)

# ==============================================
# ОСНОВНАЯ ФУНКЦИЯ МОНИТОРИНГА
# ==============================================

async def monitor_hosts():
    """
    Основная функция мониторинга, которая периодически проверяет хосты
    и записывает результаты в лог-файл.
    """
    
    # Загружаем конфигурацию
    config = load_config()
    
    # Извлекаем параметры из конфига
    hosts    = config['hosts']
    interval = config['ping_interval']
    timeout  = config['ping_timeout']
    count    = config['ping_count']
    
    logger.info(f"Старт теста! Количество хостов = {len(hosts)}, интервал = {interval} сек.")
    
    while True:
        try:
            # Получаем текущую дату для лога
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"=== Начало проверки ping в {current_time} ===")
            
            # Пингуем все хосты
            results = await check_all_hosts(hosts, timeout, count)
            
            # Обрабатываем результаты
            for result in results:
                if result['is_alive']:
                    logger.info(
                        f"Хост {result['host']} доступен. "
                        f"Пакетов потеряно: {result['packet_loss']}%, "
                        f"RTT: min={result['min_rtt']}ms, "
                        f"avg={result['avg_rtt']}ms, "
                        f"max={result['max_rtt']}ms"
                    )
                else:
                    error_msg = f" (Ошибка: {result['error']})" if result['error'] else ""
                    logger.error(
                        f"Хост {result['host']} недоступен! "
                        f"Потеря пакетов: 100%{error_msg}"
                    )
            
            # Ждем указанный интервал перед следующей проверкой
            logger.info(f"Проверка ping завершена. Следующая проверка через {interval} сек.")
            await asyncio.sleep(interval)
            
        except asyncio.CancelledError:
            # Корректно обрабатываем остановку программы
            logger.info("Мониторинг остановлен пользователем")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            await asyncio.sleep(10)  # Ждем перед повторной попыткой

# ==============================================
# ТОЧКА ВХОДА
# ==============================================

if __name__ == "__main__":
    # Инициализируем систему логирования
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Запускаем мониторинг
        asyncio.run(monitor_hosts())
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")