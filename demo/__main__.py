from dotenv import load_dotenv
load_dotenv(".env")

import configparser
import logging
import logging.config
from logging import getLogger
import os
import yaml

import constant

try:
    val = os.getenv("LOGGING_CONFIG_FILE")
    if val is not None:
        if os.path.exists(val):
            constant.LOGGING_CONFIG_FILE = val

    try:
        logging.config.fileConfig(constant.LOGGING_CONFIG_FILE)
    except (configparser.MissingSectionHeaderError, KeyError) as e:
        try:
            with open(constant.LOGGING_CONFIG_FILE) as f:
                yaml_conf = yaml.safe_load(f)
                logging.config.dictConfig(yaml_conf)
        except FileNotFoundError as e:
            logging.basicConfig(level="WARNING")
            logging.error(f"log config FileNotFoundError.: {e}")
        except (yaml.parser.ParserError, KeyError, ValueError) as e:
            logging.basicConfig(level="WARNING")
            logging.error(f"log config yaml parse error: {e}")

    # create logger
    logger = getLogger(__name__)

    val = os.getenv("STEPS_PER_REV")
    if val is not None:
        try :
            val = int(val)
            constant.STEPS_PER_REV = val
        except ValueError :
            pass

    val = os.getenv("MOTOR_RATED_VOLTAGE")
    if val is not None:
        try :
            val = float(val)
            constant.MOTOR_RATED_VOLTAGE = val
        except ValueError :
            pass

    val = os.getenv("MOTOR_WINDING_RESISTANCE")
    if val is not None:
        try :
            val = float(val)
            constant.MOTOR_WINDING_RESISTANCE = val
        except ValueError :
            pass

    val = os.getenv("MOTER_AMAX")
    if val is not None:
        try :
            val = int(val)
            constant.MOTER_AMAX = val
        except ValueError :
            pass

    val = os.getenv("MOTER_DMAX")
    if val is not None:
        try :
            val = int(val)
            constant.MOTER_DMAX = val
        except ValueError :
            pass

    val = os.getenv("MOTER_V1")
    if val is not None:
        try :
            val = int(val)
            constant.MOTER_V1 = val
        except ValueError :
            pass

    val = os.getenv("MOTER_A1")
    if val is not None:
        try :
            val = int(val)
            constant.MOTER_A1 = val
        except ValueError :
            pass

    val = os.getenv("MOTER_D1")
    if val is not None:
        try :
            val = int(val)
            constant.MOTER_D1 = val
        except ValueError :
            pass

    val = os.getenv("MOTER_V2")
    if val is not None:
        try :
            val = int(val)
            constant.MOTER_V2 = val
        except ValueError :
            pass

    val = os.getenv("MOTER_A2")
    if val is not None:
        try :
            val = int(val)
            constant.MOTER_A2 = val
        except ValueError :
            pass

    val = os.getenv("MOTER_D2")
    if val is not None:
        try :
            val = int(val)
            constant.MOTER_D2 = val
        except ValueError :
            pass

    val = os.getenv("MOTER_LIMIT_TIME_OF_DRIVE")
    if val is not None:
        try :
            val = float(val)
            constant.MOTER_LIMIT_TIME_OF_DRIVE = val
        except ValueError :
            pass

    val = os.getenv("MOTER_DEFAULT_SPEED")
    if val is not None:
        try :
            val = float(val)
            constant.MOTER_DEFAULT_SPEED = val
        except ValueError :
            pass

    val = os.getenv("MOTER_EXTRAQ_STOP_TIME")
    if val is not None:
        try :
            val = float(val)
            constant.MOTER_EXTRAQ_STOP_TIME = val
        except ValueError :
            pass

    val = os.getenv("MOTER_INITIAL_OFFSET")
    if val is not None:
        try :
            val = int(val)
            constant.MOTER_INITIAL_OFFSET = val
        except ValueError :
            pass

    val = os.getenv("APNEA_DATA_CSV_PATH")
    if val is not None:
        constant.APNEA_DATA_CSV_PATH = val

    val = os.getenv("START_SW_PIN")
    if val is not None:
        try :
            val = int(val)
            constant.START_SW_PIN = val
        except ValueError :
            pass

    val = os.getenv("STOP_SW_PIN")
    if val is not None:
        try :
            val = int(val)
            constant.STOP_SW_PIN = val
        except ValueError :
            pass

    val = os.getenv("LIMIT_SW_PIN")
    if val is not None:
        try :
            val = int(val)
            constant.LIMIT_SW_PIN = val
        except ValueError :
            pass

    val = os.getenv("DEBOUNCE_INTERVAL")
    if val is not None:
        try :
            val = float(val)
            constant.DEBOUNCE_INTERVAL = val
        except ValueError :
            pass


    import device
    device.start()

except KeyboardInterrupt:
    print("")

