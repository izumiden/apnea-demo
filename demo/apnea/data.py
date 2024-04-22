import csv
from logging import getLogger

# create logger
logger = getLogger(__name__)


class ApneaData:
    def __init__(self, csv_file):
        self.csv_file = csv_file

        self._name = ""
        # サンプリング間隔
        self._sampling_interval = 0
        # マイクロステップ倍率
        self._usteps_multiplier = 0.0
        # 初期待機位置
        self._initial_position = 0
        # 位置データと移動量データのリスト
        self._movement_data_list = []

        self.load_csv()

    @property
    def name(self):
        return self._name

    @property
    def sampling_interval(self):
        return self._sampling_interval

    @property
    def usteps_multiplier(self):
        return self._usteps_multiplier

    @property
    def initial_position(self):
        return int(self._initial_position * self._usteps_multiplier)

    @property
    def movement_data_list(self):
        return self._movement_data_list

    def load_csv(self):
        try:
            logger.info(f"csv_file:{self.csv_file}")
            try:
                with open(self.csv_file, mode="r", encoding="utf-8") as file:
                    csv_reader = csv.reader(file)

                    self._name = next(csv_reader)[1]

                    try:
                        self._sampling_interval = float(next(csv_reader)[1])/1000
                    except ValueError:
                        pass

                    try:
                        self._usteps_multiplier = float(next(csv_reader)[1])
                    except ValueError:
                        pass

                    try:
                        self._initial_position = int(next(csv_reader)[1])
                    except ValueError:
                        pass

                    for row in csv_reader:
                        # logger.debug(f"位置: {row[0]} 移動量: {row[1]}")
                        # (モーター位置データ, 移動量) のタプルをリストに追加
                        pos = 0
                        diff = 0
                        count = len(row)
                        if 0 < count:
                            try:
                                pos = int(row[0])
                            except ValueError:
                                pass

                            if 1 < count:
                                try:
                                    diff = int(row[1])
                                except ValueError:
                                    pass

                        self._movement_data_list.append((pos, diff))
            except StopIteration:
                pass

            # CSVファイルから読み込んだ内容を確認
            logger.info(f"制御間隔: {self._sampling_interval}")
            logger.info(f"マイクロステップ: {self._usteps_multiplier}")
            logger.info(f"初期待機位置: {self._initial_position}")
            logger.info(f"移動データ数: {len(self._movement_data_list)}")

            # for movement_data in self.movement_data:
            #   logger.debug(f"位置: {movement_data[0]} 移動量: {movement_data[1]}")
        except FileNotFoundError:
            logger.error(f"csv file not found {self.csv_file}")
            raise
        except:
            logger.error(f"csv file read error {len(self._movement_data_list)}")
            raise
