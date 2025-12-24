import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {"level": record.levelname, "msg": record.getMessage(), "time": self.formatTime(record)}
        if hasattr(record, "props"):
            log.update(record.props)
        return json.dumps(log)


logger = logging.getLogger("rag_service")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
