from cgstep import TMC5240

from logging import getLogger
import time
from threading import Thread

from constant import *

# create logger
logger = getLogger(__name__)


class MotorEnabledError(Exception):
    """
    Exception raised when attempting to perform motor operations without enabling the motor.
    """

    def __init__(self, *args: object):
        super().__init__(*args)
        if not args["message"]:
            self.message = args["message"]
        else:
            self.message = "Motor is enabled."


class MotorNotEnabledError(Exception):
    """
    Exception raised when attempting to perform motor operations without enabling the motor.
    """

    def __init__(self, *args: object):
        super().__init__(*args)
        if 0 < len(args):
            self.message = args[0]
        else:
            self.message = "Motor is not enabled."


class MotorRunningError(Exception):
    """
    Exception raised when attempting to make configuration changes while the motor is running.
    """

    def __init__(self, *args: object):
        super().__init__(*args)
        logger.info(f"args:{args}")
        if 0 < len(args):
            self.message = args[0]
        else:
            self.message = "Motor is running."


class MotorController:
    def __init__(self, steps_per_rev=200):

        ifs = round(MOTOR_RATED_VOLTAGE / MOTOR_WINDING_RESISTANCE, 3)

        self._tmc5240 = TMC5240(steps_per_rev=steps_per_rev)
        self._poweron_flag = bool(self._tmc5240.toff != 0)
        self._tmc5240.disable()

        self._tmc5240.ifs = ifs  # 電流値ifs (A)
        self._tmc5240.amax = (
            MOTER_AMAX if 0 < MOTER_AMAX else 0
        )  # 最大加速度 (usteps/s²)
        self._tmc5240.dmax = (
            MOTER_DMAX if 0 < MOTER_DMAX else 0
        )  # 最大減速度 (usteps/s²)

        v = a = d = 0
        if 0 < MOTER_V1:
            if 0 < MOTER_A1:
                v = MOTER_V1
                a = MOTER_A1
            if 0 < MOTER_D1:
                d = MOTER_D1
                v = MOTER_V1
        if 0 < v:
            self._tmc5240.v1 = v
            self._tmc5240.a1 = a
            self._tmc5240.d1 = d

        v = a = d = 0
        if 0 < MOTER_V2:
            if 0 < MOTER_A2:
                v = MOTER_V2
                a = MOTER_A2
            if 0 < MOTER_D2:
                d = MOTER_D2
                v = MOTER_V2
        if 0 < v:
            self._tmc5240.v1 = v
            self._tmc5240.a1 = a
            self._tmc5240.d1 = d

        self._tmc5240.vmax = 0  # 最大速度を0rpmに設定
        self._tmc5240.xtarget = 0
        self._tmc5240.xactual = 0

        self._rampmode = TMC5240.RAMPMODE_VELOCITY_POSITIVE  # 速度制御モード (正回転)
        self._tmc5240.rampmode = self._rampmode

        if self._poweron_flag:
            self.poweron()

        self._thread = None
        self._sample_interval = 0
        self._rpms = []
        self._stop_flag = False

        logger.info(f"ifs:{ifs}")

    @property
    def tmc5240(self):
        return self._tmc5240

    @property
    def rampmode(self):
        return self._rampmode

    def is_poweron(self):
        return self._poweron_flag

    def poweron(self):
        self._tmc5240.enable()
        self._poweron_flag = True
        return self

    def poweroff(self):
        self._tmc5240.disable()
        self._poweron_flag = False
        return self

    def set_rampmode(self, rampmode):
        if self._rampmode != rampmode:
            self._tmc5240.rampmode = rampmode
            self._rampmode = rampmode
        return self

    def set_reference_point(self):
        if self.is_running():
            raise MotorRunningError()
        self._tmc5240.xactual = 0
        return self

    def move_target(self, target: int, rpm: float = MOTER_DEFAULT_SPEED):
        if not self.is_poweron():
            raise MotorNotEnabledError()
        if self.is_running():
            raise MotorRunningError()

        self.set_rampmode(TMC5240.RAMPMODE_POSITIONING)  # 速度制御モード (位置制御)
        self._tmc5240.xtarget = target
        self._tmc5240.vmax_rpm = rpm
        return self

    def rotate(self, rpm: float = MOTER_DEFAULT_SPEED):
        if not self.is_poweron():
            raise MotorNotEnabledError()
        self.set_rampmode(TMC5240.RAMPMODE_HOLD)
        self._tmc5240.vmax_rpm = rpm
        self.set_rampmode(TMC5240.RAMPMODE_VELOCITY_POSITIVE)

    def rotate_backwards(self, rpm: float = MOTER_DEFAULT_SPEED):
        if not self.is_poweron():
            raise MotorNotEnabledError()
        self.set_rampmode(TMC5240.RAMPMODE_HOLD)
        self._tmc5240.vmax_rpm = rpm
        self.set_rampmode(TMC5240.RAMPMODE_VELOCITY_NEGATIVE)

    def stop(self):
        self._tmc5240.vmax = 0

    def is_running(self):
        return self._tmc5240.vactual != 0


def calculate_motor_rpm(
    sample_interval_secondes: float,
    microstep_ratio: float,
    movements: list[float, float],
    steps_per_rev: float = 200,
):
    """
    各時間点でのモーターの回転速度をRPMで計算する。

    :param sample_interval_secondes: サンプル間隔（秒）
    :param microstep_ratio: マイクロステップ倍率
    :param movements: 移動量のリスト（各サンプルでの±移動量）
    :param steps_per_rev: モーターの一回転あたりのステップ数（フルステップ）
    :return: 各サンプルでのモーターの回転速度（RPM）のリスト
    """
    rpms = []  # RPMを格納するリスト
    index = 0
    rpm_sum = 0

    logger.info(f"sample_interval_secondes:{sample_interval_secondes:.3f}.")
    logger.info(f"microstep_ratio:{microstep_ratio:.3f}.")
    logger.info(f"steps_per_rev:{steps_per_rev:.3f}.")

    for movement in movements:
        val = 0
        if 1 < len(movement):
            val = movement[1]
        # ステップ/サンプル間隔（秒）
        speed_steps_per_sample_interval = val * microstep_ratio
        # ステップ/秒
        speed_steps_per_second = (
            speed_steps_per_sample_interval / sample_interval_secondes
        )

        rpm = (speed_steps_per_second * 60) / steps_per_rev
        rpm = round(rpm, 2)
        rpms.append(rpm)
        rpm_sum += rpm

        if index < 100:
            logger.debug(
                f"[{index:2}]val:{val:3} rpm:{rpm:10,.3f}. speed_steps_per_second:{speed_steps_per_second:10,.3f}"
            )
        index += 1

    logger.info(f"len:{len(rpms)} sum:{rpm_sum}")

    return rpms


if __name__ == "__main__":
    motor_controller = MotorController()
    motor_controller.run()

# このスクリプトは、モータドライバを有効化し、10rpmの速度で回転させます。また、0.5秒ごとに現在の位置、速度、経過時間を表示し、1秒ごとに最大速度を10rpmずつ増加させます。Ctrl+Cを押すと、元の位置に戻ります。
# 以下のコマンドを実行して、モータを回転させます。
# $ python motor.py
#
# 以下のような出力が表示されます。
# 現在の位置:        0 現在の速度:        0/0 経過時間:    0.000
