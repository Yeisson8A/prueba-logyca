import logging
import sys

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Formato: Tiempo - Nombre - Nivel - Mensaje
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para archivo (opcional, útil para persistencia local)
    file_handler = logging.FileHandler("worker_activity.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger