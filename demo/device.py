from cgstep import TMC5240
from logging import getLogger
import pigpio
import time
from threading import Thread, Event

from constant import *

from apnea.data import ApneaData
from apnea import demo as ApneaDemo
from motor import MotorController
from switch import Switch

logger = getLogger(__name__)

_g_demo_event = Event()
_g_demo_start_event = Event()
_g_demo_sop_event = Event()


def _demo_start():
    _g_demo_start_event.set()
    _g_demo_event.set()

def _demo_stop():
    _g_demo_sop_event.set()
    _g_demo_event.set()

def _start_sw_pin_cbf(gpio, level, tick):
    global _g_motorController
    global _g_apneadata
    logger.info(f"start sw gpio:{gpio}, level:{level}, tick:{tick}")
    _demo_start()


def _stop_sw_pin_cbf(gpio, level, tick):
    logger.info(f"stop sw gpio:{gpio}, level:{level}, tick:{tick}")
    _demo_stop()


def _limit_sw_pin_cbf(gpio, level, tick):
    logger.info(f"limit sw gpio:{gpio}, level:{level}, tick:{tick}")
    if level == pigpio.HIGH:
        ApneaDemo.moved_away_reference_point()
    else:
        ApneaDemo.reached_reference_point()


def start():
    global _g_motorController
    global _g_apneadata
    

    _g_apneadata = ApneaData(APNEA_DATA_CSV_PATH)

    _g_motorController = MotorController(steps_per_rev=STEPS_PER_REV)
    _g_motorController.poweron()
    try:
        logger.info(f"Motor enabled. xtarget:{_g_motorController.tmc5240.xtarget}")
        while _g_motorController.is_running():
            time.sleep(1.0)
            logger.info(
                f"Motor controller is running."
                f" xtarget:{_g_motorController.tmc5240.xtarget:9},"
                f" xactual:{_g_motorController.tmc5240.xactual:9},"
                f" vactual:{_g_motorController.tmc5240.vactual:9}"
            )
        pi = pigpio.pi()
        try:
            limit_sw = Switch(
                LIMIT_SW_PIN, pi, debounce_interval=0.2, edge=pigpio.EITHER_EDGE
            )
            logger.info(f"limit sw({limit_sw.pin}) level:{limit_sw.level}")
            try:
                limit_sw.callback = _limit_sw_pin_cbf

                if limit_sw.level == pigpio.HIGH:
                    _g_motorController.rotate_backwards()
                    while limit_sw.level == pigpio.HIGH:
                        time.sleep(0.1)
                        logger.info(f"Motor position reset. {_g_motorController.tmc5240.xactual}.")
                else:
                    ApneaDemo.reached_reference_point()

                _g_motorController.rotate_backwards(0)
                while _g_motorController.is_running():
                    time.sleep(0.1)
                    logger.info(f"Motor stop. {_g_motorController.tmc5240.xactual}.")

                # モーターの位置をリセット
                _g_motorController.set_reference_point()
                logger.info(f"Motor position reseted. {_g_motorController.tmc5240.xactual}.")

                start_sw = Switch(
                    START_SW_PIN, pi, debounce_interval=0.2, edge=pigpio.RISING_EDGE
                )
                logger.info(f"start sw({start_sw.pin}) level:{start_sw.level}")
                try:
                    start_sw.callback = _start_sw_pin_cbf

                    stop_sw = Switch(
                        STOP_SW_PIN, pi, debounce_interval=0.2, edge=pigpio.RISING_EDGE
                    )
                    logger.info(f"stop sw({stop_sw.pin}) level:{stop_sw.level}")
                    try:
                        stop_sw.callback = _stop_sw_pin_cbf

                        while True:
                            _g_demo_event.wait()
                            _g_demo_event.clear()

                            if _g_demo_sop_event.is_set():
                                _g_demo_sop_event.clear()
                                ApneaDemo.stop()
                            
                            if _g_demo_start_event.is_set():
                                _g_demo_start_event.clear()
                                ApneaDemo.start(_g_motorController, _g_apneadata)
                    finally:
                        stop_sw.cancel()
                finally:
                    start_sw.cancel()
            finally:
                limit_sw.cancel()
        finally:
            pi.stop()
    finally:
        thread = ApneaDemo.stop()
        if isinstance(thread, Thread):
            if thread.is_alive():
                thread.join()
        if _g_motorController.is_poweron():
            _g_motorController.poweroff()
            logger.info(f"motor power off.")
        logger.info(f"device stopped. motor power is {_g_motorController.is_poweron()}")

