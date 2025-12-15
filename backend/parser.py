import numpy as np

class TelegramParser:
    """
    注射オーダ依頼電文)の電文を解析するパーサー。
    """
    def __init__(self, filepath, encoding='cp932'):
        self.filepath = filepath
        self.encoding = encoding
        self.raw_bytes = b''
        self.offset = 0

    def _slice(self, num_bytes):
        """
        現在のオフセットから指定バイト数をスライスし、オフセットを進める。
        """
        if self.offset + num_bytes > len(self.raw_bytes):
            raise ValueError(f"データが不足しています。{num_bytes} バイトを読み取ろうとしましたが、"
                             f"オフセット {self.offset} でデータが終了しました。")
        data_slice = self.raw_bytes[self.offset:self.offset + num_bytes]
        self.offset += num_bytes
        return data_slice

    def _decode(self, byte_slice):
        """
        バイトスライスをデコードし、stripし、空の場合は np.nan を返す。
        """
        # 不正なSHIFT-JIS文字があってもエラーにならないよう 'replace' を使用
        s = byte_slice.decode(self.encoding, errors='replace').strip()
        # スペース埋めされている項目は np.nan を代入
        return np.nan if not s else s

    def _slice_and_decode(self, num_bytes):
        """
        スライスとデコードを一度に行うヘルパー。
        """
        return self._decode(self._slice(num_bytes))

    def _parse_common_part(self):
        """
        共通部 (64バイト) を解析 [cite: 93, 94]
        """
        common = {
            "message_type": self._slice_and_decode(2),            # 05 電文種別
            "record_continuation": self._slice_and_decode(1),     # 05 レコード継続指示
            "destination_system_code": self._slice_and_decode(2), # 05 送信先システムコード
            "source_system_code": self._slice_and_decode(2),      # 05 発信元システムコード
        }
        # --- 05 処理情報 ---
        common["processing_info"] = {
            "date": self._slice_and_decode(8), # 07 処理年月日
            "time": self._slice_and_decode(6), # 07 処理時刻
        }
        common["client_name"] = self._slice_and_decode(8)      # 05 端末名
        common["d_id"] = self._slice_and_decode(8)             # 05 利用者番号
        common["processing_class"] = self._slice_and_decode(2) # 05 処理区分
        common["response_type"] = self._slice_and_decode(2)    # 05 応答種別
        common["message_length"] = self._slice_and_decode(6)   # 05 電文長
        common["error_code"] = self._slice_and_decode(5)       # 05 エラーコード
        common["reserve"] = self._slice_and_decode(12)         # 05 予備

        return common

    def _parse_content_part(self):
        """
        内容部 (可変長) を解析
        """
        content = {}

        # --- 05 患者情報 ---
        content['patient_info'] = {
            "id": self._slice_and_decode(10),           # 07 患者番号 / 患者ID
            "kanji_name": self._slice_and_decode(30),   # 07 患者漢字氏名
            "kana_name": self._slice_and_decode(60),    # 07 患者カナ氏名
            "sex": self._slice_and_decode(1),           # 07 患者性別
            "birthdate": self._slice_and_decode(8),     # 07 患者生年月日
            "postal_code_1": self._slice_and_decode(3), # 07 郵便番号1
            "postal_code_2": self._slice_and_decode(4), # 07 郵便番号2
            "address": self._slice_and_decode(100),     # 07 患者住所
            "phone_number": self._slice_and_decode(15), # 07 電話番号
        }

        # --- 05 入院情報 ---
        content['inpatient_info'] = {
            "status": self._slice_and_decode(1),    # 07 入外状態
            "dept_code": self._slice_and_decode(3), # 07 入院診療科コード
            "ward_code": self._slice_and_decode(3), # 07 入院中病棟コード
            "room_code": self._slice_and_decode(5), # 07 入院中部屋コード
            "bed_code": self._slice_and_decode(2),  # 07 入院中ベッドコード
        }

        # --- 05 オーダ情報 ---
        order_info = {
            "doc_type": self._slice_and_decode(1),       # 07 文書種別
            "doc_id": self._slice_and_decode(30),        # 07 文書番号
            "version": int(self._slice_and_decode(2)),   # 07 版数
            "parent_doc_id": self._slice_and_decode(30), # 07 親文書番号
            "number": self._slice_and_decode(8),         # 07 オーダ番号
        }

        # 07 関連オーダ番号情報
        order_info['related_order_info'] = {
                "date": self._slice_and_decode(8), # 09 関連オーダ作成日
                "number": self._slice_and_decode(8),   # 09 関連オーダ番号
        }
        
        # 07 実施日時 
        order_info['jisshi_datetime'] = {
            "date": self._slice_and_decode(8), # 09 実施日付
            "time": self._slice_and_decode(6), # 09 実施時間
        }

        # 07 オーダ作成日 
        order_info['sakusei_datetime'] = {
            "date": self._slice_and_decode(8), # 09 オーダ日付
            "time": self._slice_and_decode(6), # 09 オーダ時間
        }
        order_info['hikikaeken_no'] = self._slice_and_decode(8)          # 07 薬引換券番号
        order_info['inpatient_status'] = self._slice_and_decode(1)       # 07 入外区分
        order_info['hakkou_dept_code'] = self._slice_and_decode(3) # 07 オーダ発行診療科コード
        order_info['hakkou_ward_code'] = self._slice_and_decode(3) # 07 オーダ発行病棟コード
        order_info['denpyo_code'] = self._slice_and_decode(4)            # 07 伝票コード
        order_info['denpyo_name'] = self._slice_and_decode(50)           # 07 伝票名称

        # 07 依頼医情報 
        order_info['doctor_info'] = {
            "d_id": self._slice_and_decode(8),        # 09 依頼医番号
            "kanji_name": self._slice_and_decode(20), # 09 依頼医名
            "kana_name": self._slice_and_decode(40),  # 09 依頼医カナ名
        }
        # 07 代行利用者情報 
        order_info['daikoh_info'] = {
            "d_id": self._slice_and_decode(8),        # 09 代行利用者番号
            "kanji_name": self._slice_and_decode(20), # 09 代行利用者名
        }

        # 07 麻薬施用者情報1
        order_info['mayaku_shiyosha_1'] = {
            "id": self._slice_and_decode(10),        # 09 麻薬施用者番号1
            "start_date": self._slice_and_decode(8), # 09 開始日
            "end_date": self._slice_and_decode(8),   # 09 終了日
        }

        # 07 麻薬施用者情報2
        order_info['mayaku_shiyosha_2'] = {
            "id": self._slice_and_decode(10),        # 09 麻薬施用者番号2
            "start_date": self._slice_and_decode(8), # 09 開始日
            "end_date": self._slice_and_decode(8),   # 09 終了日
        }

        content['order_info'] = order_info

        # --- 05 患者プロファイル情報 ---
        patient_profile = {}

        # 07 身長
        patient_profile['height'] = {
            "value": float(self._slice_and_decode(11) or 0), # 09 身長値
            "date": self._slice_and_decode(8),   # 09 身長計測日
        }
        # 07 体重
        patient_profile['weight'] = {
            "value": float(self._slice_and_decode(11) or 0), # 09 体重値
            "date": self._slice_and_decode(8),   # 09 体重計測日
        }
        # 07 体表面積 body surface area
        patient_profile['bsa'] = {
            "value": float(self._slice_and_decode(11) or 0), # 09 体表面積値
        }

        # 07 プロファイル情報
        profile_count_str = self._slice_and_decode(3) # 09 プロファイル数
        profile_count = int(profile_count_str) if profile_count_str is not np.nan else 0 # 数値化
        patient_profile['profile_info'] = {
            "profile_count": profile_count
        }

        ## 09 プロファイル情報群 (可変長)
        patient_profile['profile_info']['profile_group'] = []
        for _ in range(profile_count):
            patient_profile['profile_info']['profile_group'].append({
                "code": self._slice_and_decode(10),  # 11 プロファイルコード
                "name": self._slice_and_decode(50),  # 11 プロファイル名称
                "data": self._slice_and_decode(500), # 11 プロファイルデータ
            })

        content['patient_profile'] = patient_profile

        # --- 05 レジメン情報 ---
        content['regimen_info'] = {
            "code": self._slice_and_decode(8),         # 07 レジメンコード
            "name": self._slice_and_decode(50),        # 07 レジメン名
            "course_count": self._slice_and_decode(3), # 07 コース数
            "drip_order": self._slice_and_decode(4),   # 07 滴下順
            "start_date": self._slice_and_decode(14),  # 07 レジメン適用開始日
            # 07 レジメン適用時の身体情報
            "body_info": { 
                "height": float(self._slice_and_decode(11) or 0), # 09 身長
                "weight": float(self._slice_and_decode(11) or 0), # 09 体重
                "bsa": float(self._slice_and_decode(11) or 0),    # 09 体表面積
            }
        }

        # --- 05 項目数情報 ---
        item_count_str = self._slice_and_decode(4) # 07 項目数
        item_count = int(item_count_str) if item_count_str is not np.nan else 0 # 数値化
        content['item_count_info'] = {"item_count": item_count}

        # --- 05 項目情報群 ---
        item_group = {} 
        # 07 項目情報 (可変長)
        item_group['item_info'] = []
        for _ in range(item_count):
            item = {
                "attribute": self._slice_and_decode(3),         # 09 項目属性
                "code": self._slice_and_decode(8),              # 09 項目コード
                "linked_item_code": self._slice_and_decode(8),  # 09 連結項目コード
                "name": self._slice_and_decode(50),             # 09 項目名称
                "quantity": float(self._slice_and_decode(11) or 0),  # 09 数量
                "unit_flag": self._slice_and_decode(1),         # 09 選択単位フラグ
                "unit_code": self._slice_and_decode(3),         # 09 選択単位コード
                "unit_name": self._slice_and_decode(4),         # 09 選択単位名称
                "max_dose_flag": self._slice_and_decode(1),     # 09 極量フラグ
                "item_row_date": self._slice_and_decode(8),     # 09 項目行日付
                "item_row_time": self._slice_and_decode(6),     # 09 項目行時間
                ## 09 コードグループ
                "code_group": {
                    "buppin_code": self._slice_and_decode(9),     # 11 物品コード
                    "jan_code": self._slice_and_decode(13),       # 11 物品JANコード
                    "iyakuhin_code": self._slice_and_decode(12),  # 11 薬品コード(厚生省コード) / 薬価基準収載医薬品コード
                    "hot_code": self._slice_and_decode(13),       # 11 HOTコード
                    "receden_code": self._slice_and_decode(12),   # 11 レセプト電算コード
                    "jlac10_code": self._slice_and_decode(17),    # 11 JLAC10コード
                    "yj_code": self._slice_and_decode(20),        # 11 標準コード(YJコード)
                    "logi_code": self._slice_and_decode(20),      # 11 物流コード
                    "order_kanri_no": self._slice_and_decode(14), # 11 オーダ管理番号
                    "iji_kanri_no": self._slice_and_decode(10),   # 11 医事管理番号
                }
            }
            item_group['item_info'].append(item)

        content['item_group'] = item_group

        return content

    def parse(self):
        """
        ファイルパスから電文を読み込み、解析を実行する。

        Returns:
            dict: 解析された電文データ。

        Raises:
            FileNotFoundError: ファイルが見つからない場合。
            ValueError: 解析エラーや検証エラーが発生した場合。
        """
        try:
            with open(self.filepath, 'rb') as f:
                self.raw_bytes = f.read()
        except FileNotFoundError:
            print(f"エラー: ファイルが見つかりません: {self.filepath}")
            raise
        except Exception as e:
            print(f"エラー: ファイルを読み込めません: {e}")
            raise

        if not self.raw_bytes:
            raise ValueError("ファイルが空です。")

        self.offset = 0 # オフセットをリセット

        try:
            # --- 1. 共通部 (Common Part) ---
            common_part = self._parse_common_part()

            # --- 2. Validation (電文形式の検証) ---
            if common_part.get('message_type') != 'II' or \
               common_part.get('record_continuation') != 'E' or \
               common_part.get('destination_system_code') != 'HS' or \
               common_part.get('source_system_code') != 'XX':
                # 電文の形式を満たしていない場合、エラーを発報
                raise ValueError(
                    "電文ヘッダーの検証に失敗しました。必須項目 (II, E, HS, XX) "
                    f"が一致しません。 "
                )

            # --- 3. 内容部 (Content Part) ---
            content_part = self._parse_content_part()

            # --- 4. 終端確認 (オプション) ---
            # (前提条件3参照: 終端チェックは省略)
            if self.offset < len(self.raw_bytes):
                remaining = len(self.raw_bytes) - self.offset
                print(f"警告: {remaining} バイトがファイルの終端に残っていますが、"
                      "電文仕様に従い解析を終了しました。")

            # --- 5. 結合 ---
            full_telegram = {
                "common": common_part,
                "content": content_part
            }

            return full_telegram

        except Exception as e:
            print(f"解析エラー: オフセット {self.offset} 付近で問題が発生しました。")
            print(f"エラー詳細: {e}")
            raise