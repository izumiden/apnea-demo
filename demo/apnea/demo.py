from cgstep import TMC5240
from logging import getLogger
import time
from threading import Thread, Event

from constant import *

from apnea.data import ApneaData
from motor import MotorController, calculate_motor_rpm

logger = getLogger(__name__)

_g_reference_point_event = Event()
_g_stop_event = Event()
_g_thread = None


class StopEvent(Exception):
    pass

def start(motorController: MotorController, apneadata: ApneaData) -> Thread:
    global _g_thread
    if isinstance(_g_thread, Thread):
        if _g_thread.is_alive():
            return
    _g_thread = Thread(
        target=_run, args=(motorController, apneadata)
    )
    _g_thread.start()

    return _g_thread


def stop():
    global _g_stop_event
    global _g_thread
    if isinstance(_g_thread, Thread):
        if _g_thread.is_alive():
            _g_stop_event.set()
    return _g_thread


def get_thread_instance() -> Thread:
    global _g_thread
    return _g_thread


def reached_reference_point() -> None:
    _g_reference_point_event.set()


def moved_away_reference_point() -> None:
    _g_reference_point_event.clear()


def move_to_reference_point(motorController: MotorController) -> None:

    # モーターを停止
    _stop_motor(motorController)
    # モーターの位置を基準点に移動
    if not _g_reference_point_event.is_set():
        motorController.rotate_backwards()
        time_start = time.time()
        time_limit = time_start + MOTER_LIMIT_TIME_OF_DRIVE
        while not _g_reference_point_event.is_set():
            _check_stop_event(0.1)

            if time_limit < time.time():
                logger.error("Reference point not reached.")
                break
            logger.debug(
                f"Motor controller is moving."
                f" xtarget:{motorController.tmc5240.xtarget:9},"
                f" xactual:{motorController.tmc5240.xactual:9},"
                f" vactual:{motorController.tmc5240.vactual:9}"
            )
        # モーターを停止
        _stop_motor(motorController)

    # モーターの基準点を現在位置に設定
    motorController.set_reference_point()


def _check_stop_event(wait:float=0.0) -> None:
    if _g_stop_event.wait(wait):
        raise StopEvent()


def _stop_motor(motorController: MotorController) -> None:
    # モーターを停止
    motorController.stop()
    while motorController.is_running():
        _check_stop_event(0.1)
        
        logger.debug(
            f"Motor controller is stopping."
            f" xtarget:{motorController.tmc5240.xtarget:9},"
            f" xactual:{motorController.tmc5240.xactual:9},"
            f" vactual:{motorController.tmc5240.vactual:9}"
        )


def _run(motorController: MotorController, apneadata: ApneaData):

    logger.info("Apnea demo start.")
    _g_stop_event.clear()
    try:
        sample_interval = apneadata.sampling_interval
        logging_interval = 1.0  # ロギング間隔（秒）

        time_start = time.time()  # 開始時刻を取得
        time_sampling = time_start + sample_interval  # サンプリング時間を初期化

        time_logging = time_start + logging_interval  # ロギング時間を初期化

        rpms = calculate_motor_rpm(
            apneadata.sampling_interval,
            apneadata.usteps_multiplier,
            apneadata.movement_data_list,
            steps_per_rev=STEPS_PER_REV,
        )
        iter_rpms = iter(rpms)

        # モータードライバーを印加
        if not motorController.is_poweron():
            motorController.poweron()

        # モーターを停止
        _stop_motor(motorController)
        
        # モーターの位置を基準点に移動
        move_to_reference_point(motorController)
        
        # モーターの位置をオフセット分移動
        motorController.move_target(MOTER_INITIAL_OFFSET)
        logger.info(f"Motor move to offset position {motorController.tmc5240.xactual} ...")
        while motorController.is_running():
            _check_stop_event(0.1)
        logger.info(f"Motor moved offset position. {motorController.tmc5240.xactual}")
        # モーターの基準点を現在位置に設定
        motorController.set_reference_point()
        # モーターを停止
        _stop_motor(motorController)
        
        # モーターを初期位置に移動
        motorController.move_target(apneadata.initial_position)
        logger.info(f"Motor move to initial position {apneadata.initial_position} ...")
        while motorController.is_running():
            _check_stop_event(0.1)
        logger.info(f"Motor moved initial position. {motorController.tmc5240.xactual}")

        while True:
            _check_stop_event(0.001)
            time_current = time.time()

            if time_sampling <= time_current:
                rpm = 0
                try:
                    rpm = next(iter_rpms)
                except StopIteration:
                    iter_rpms = iter(rpms)
                    rpm = next(iter_rpms)

                if rpm < 0:
                    if _g_reference_point_event.is_set():
                        motorController.stop()
                    else:
                        motorController.rotate_backwards(abs(rpm))
                else:
                    motorController.rotate(rpm)
                logger.debug(f"{time_current:.3f}, {time_sampling:.3f}, {time_current-time_sampling:.3f}, {rpm:.3f}")
                time_sampling += sample_interval
            else:
                if _g_reference_point_event.is_set():
                    if motorController.rampmode == TMC5240.RAMPMODE_VELOCITY_NEGATIVE:
                        motorController.stop()

            if time_logging <= time_current:
                prosess_time = time.time() - time_current
                logger.info(
                    f" x: {motorController.tmc5240.xactual:8,}"
                    f" v/max: {motorController.tmc5240.vactual:8,}/{motorController.tmc5240.vmax:8,}"
                    f" rpm/max: {motorController.tmc5240.vactual_rpm :8,.3f} / {motorController.tmc5240.vmax_rpm:8,.3f}"
                    f" mode: {motorController.rampmode}"
                    f" elapsed: {time_current - time_start:.3f}"
                    f" prosessing time: {prosess_time:.6f}"
                )
                time_logging += logging_interval
    except StopEvent:
        _g_stop_event.clear()
    finally:
        try:
            # モーターの位置を基準点に移動
            move_to_reference_point(motorController)
        except StopEvent:
            _g_stop_event.clear()
        # モータードライバーを停止
        if motorController.is_poweron():
            motorController.poweroff()
        logger.info(f"Apnea demo stop. power is {motorController.is_poweron()}.")