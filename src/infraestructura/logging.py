import datetime
import platform
import socket
import os
import logging
import logging.handlers
import json
from colorama import Fore, Style, init
from abc import ABC, abstractmethod
from typing import Dict, Optional, List

# Inicializar colorama para Windows
init(autoreset=True)


class LogHandler(ABC):
    @abstractmethod
    def log(self, level: str, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        """
        Registra un mensaje de log.
        """
        pass

    def flush(self) -> None:
        """
        Limpia el buffer de logs.
        """
        pass

    def close(self) -> None:
        """
        Cierra y limpia recursos del handler
        """
        pass


class ConsoleLogHandler(LogHandler):
    """
    Escribe los logs en la consola.
    """

    def __init__(self, include_metadata: bool = False):
        self.include_metadata = include_metadata

    # Implementación del método abstracto log (heredado y obligatorio de LogHandler)
    def log(self, level: str, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Mapeo de colores por nivel
        color = ""
        if level == "INFO":
            color = Fore.GREEN
        elif level == "WARNING":
            color = Fore.YELLOW
        elif level == "ERROR":
            color = Fore.RED
        elif level == "DEBUG":
            color = Fore.CYAN
            
        log_message = f"{color}[{timestamp}] - [{level}] - [{method}] - {message}{Style.RESET_ALL}"

        # Agrega metadata si está habilitado
        if self.include_metadata and metadata:
            metadata_str = " | ".join(
                [f"{key}={value}" for key, value in metadata.items()])
            log_message += f" {Fore.BLACK}{Style.BRIGHT}| {metadata_str}{Style.RESET_ALL}"

        print(log_message)


class ApiAnalyticsHandler(LogHandler):
    """
    Placeholder para el handler de API Analytics.
    """

    def __init__(self):
        pass

    def log(self, level: str, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        pass


class RotatingFileLogHandler(LogHandler):
    """
    Escribe logs en archivos con rotación automática.
    """
    def __init__(self, filename: str, max_bytes: int = 5*1024*1024, backup_count: int = 5, include_metadata: bool = True):
        self.include_metadata = include_metadata
        
        # Asegurar que el directorio exista
        log_dir = os.path.dirname(filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        self.logger_internal = logging.getLogger(f"RPA_LOGGER_{filename}")
        self.logger_internal.setLevel(logging.INFO)
        self.logger_internal.propagate = False # Evitar duplicados en root logger
        
        # Evitar agregar handlers múltiples veces si se re-instancia
        if not self.logger_internal.handlers:
            handler = logging.handlers.RotatingFileHandler(
                filename, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
            )
            # Formato simple para el archivo interno, ya que nosotros formateamos el mensaje antes
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger_internal.addHandler(handler)

    def log(self, level: str, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] - [{level}] - [{method}] - {message}"
        
        if self.include_metadata and metadata:
            metadata_str = " | ".join([f"{k}={v}" for k, v in metadata.items()])
            log_line += f" | {metadata_str}"
            
        # Mapeo de niveles
        if level == "DEBUG":
            self.logger_internal.debug(log_line)
        elif level == "WARNING":
            self.logger_internal.warning(log_line)
        elif level == "ERROR":
            self.logger_internal.error(log_line)
        else:
            self.logger_internal.info(log_line)

    def close(self) -> None:
        for h in self.logger_internal.handlers:
            h.close()


class JsonLogHandler(LogHandler):
    """
    Escribe logs en formato JSONL con rotación automática.
    """
    def __init__(self, filename: str, max_bytes: int = 5*1024*1024, backup_count: int = 5):
        # Asegurar directorio
        log_dir = os.path.dirname(filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        self.logger_internal = logging.getLogger(f"RPA_JSON_{filename}")
        self.logger_internal.setLevel(logging.INFO)
        self.logger_internal.propagate = False
        
        if not self.logger_internal.handlers:
            handler = logging.handlers.RotatingFileHandler(
                filename, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
            )
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger_internal.addHandler(handler)

    def log(self, level: str, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": level,
            "method": method,
            "message": message,
            "metadata": metadata or {}
        }
        
        json_line = json.dumps(log_entry, ensure_ascii=False)
        self.logger_internal.info(json_line)

    def close(self) -> None:
        for h in self.logger_internal.handlers:
            h.close()


class Logger:
    @staticmethod
    def get_session_name(base_name: str, extension: str) -> str:
        """
        Genera un nombre de archivo único basado en el PID y el timestamp.
        Ejemplo: app_20240101_120000_1234.log
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = os.getpid()
        return f"{base_name}_{timestamp}_{pid}.{extension}"

    def __init__(self, handlers: Optional[List[LogHandler]] = None):
        # Si no se proporcionan handlers, se usa ConsoleLogHandler por defecto
        self._handlers: List[LogHandler] = handlers if handlers is not None else [
            ConsoleLogHandler()]
        self._metadata: Dict = self._get_metadata()

    def _get_metadata(self) -> Dict:
        """
        Obtiene la metadata base con información del sistema.
        """
        return {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "user": os.getlogin()
        }

    def add_handler(self, handler: LogHandler) -> None:
        """
        Agrega un handler al logger
        """
        if handler not in self._handlers:
            self._handlers.append(handler)

    def remove_handler(self, handler: LogHandler) -> None:
        """
        Remueve un handler del logger
        """
        if handler in self._handlers:
            self._handlers.remove(handler)

    def _log(self, level: str, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        """
        Delega el logging a los handlers
        """
        # Combina metadata base con metadata proporcionada del método
        # Usa el operador **, para crear una copia del diccionario original de metadata
        # De esta manera se mantiene la inmutabilidad del diccionario original
        metadata_combinada = {**self._metadata}
        if metadata:
            metadata_combinada.update(metadata)

        # Delega el log a cada handler, si un handler falla capturamos el error sin afectar a los demás
        for handler in self._handlers:
            try:
                handler.log(level, method, message, metadata_combinada)
            except Exception as e:
                print(
                    f"[Logger] Error en handler {handler.__class__.__name__}: {e}")

    def debug(self, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        self._log("DEBUG", method, message, metadata)

    def info(self, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        self._log("INFO", method, message, metadata)

    def warning(self, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        self._log("WARNING", method, message, metadata)

    def error(self, method: str, message: str, metadata: Optional[Dict] = None) -> None:
        self._log("ERROR", method, message, metadata)

    def close(self) -> None:
        for handler in self._handlers:
            try:
                handler.close()
            except Exception as e:
                print(
                    f"[Logger] Error al cerrar el handler {handler.__class__.__name__}: {e}"
                )
