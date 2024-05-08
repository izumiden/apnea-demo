#
# モーターの設定
#
STEPS_PER_REV = 45                  # ステップ数
MOTOR_RATED_VOLTAGE = 4.4           # モーターの定格電圧
MOTOR_WINDING_RESISTANCE = 15       # モーターの巻線抵抗
MOTER_AMAX = 1000                   # 最大加速度 (usteps/s²)
MOTER_DMAX = 1000                   # 最大減速度 (usteps/s²)

MOTER_V1 = 0                        # 速度 (usteps/s)
MOTER_A1 = 0                        # 加速度 (usteps/s²)
MOTER_D1 = 0                        # 加速度 (usteps/s²)

MOTER_V2 = 0                        # 速度 (usteps/s)
MOTER_A2 = 0                        # 加速度 (usteps/s²)
MOTER_D2 = 0                        # 加速度 (usteps/s²)

#
# モーター制御設定
#
MOTER_LIMIT_TIME_OF_DRIVE = 10.0    # モーターの駆動時間の上限（秒）
MOTER_DEFAULT_SPEED = 300.0        # モーターの通常速度（RPM）
MOTER_EXTRAQ_STOP_TIME = 1.0        # モーター停止時の余分な時間（秒）
MOTER_INITIAL_OFFSET = 100          # モーターの初期位置オフセット
APNEA_DATA_CSV_PATH = "data.csv"    # 睡眠時無呼吸データのCSVファイルパス

#
# ピン設定
#
START_SW_PIN = 23                   # スタートスイッチのピン番号
STOP_SW_PIN = 27                    # ストップスイッチのピン番号
LIMIT_SW_PIN = 22                   # リミットスイッチのピン番号
DEBOUNCE_INTERVAL = 0.01            # デバウンス間隔（秒）

#
# ロギング設定
#
LOGGING_CONFIG_FILE = "logging.yaml"
