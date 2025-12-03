import numpy as np
from dotdict import DotDict

class TelegramParser:
    """
    HOPE LifeMark-HX (02 注射オーダ依頼電文) の
    固定長 + 可変長電文を解析するパーサー。
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
            "denbun_shubetsu": self._slice_and_decode(2),       # 電文種別
            "record_keizoku": self._slice_and_decode(1),       # レコード継続指示
            "send_saki_system_code": self._slice_and_decode(2),# 送信先システムコード
            "send_moto_system_code": self._slice_and_decode(2),# 発信元システムコード
            "shori_date": self._slice_and_decode(8),           # 処理年月日
            "shori_time": self._slice_and_decode(6),           # 処理時刻
            "tanmatsu_mei": self._slice_and_decode(8),         # 端末名
            "riyousha_bangou": self._slice_and_decode(8),      # 利用者番号
            "shori_kubun": self._slice_and_decode(2),          # 処理区分
            "outou_shubetsu": self._slice_and_decode(2),       # 応答種別
            "denbun_chou": self._slice_and_decode(6),          # 電文長
            "error_code": self._slice_and_decode(5),           # エラーコード
            "yobi": self._slice_and_decode(12),                # 予備
        }
        return common

    def _parse_content_part(self):
        """
        内容部 (可変長) を解析
        """
        content = {}

        # --- 患者情報 (Patient Info)  ---
        content['patient_info'] = {
            "kanja_bangou": self._slice_and_decode(10),       # 患者番号
            "kanja_kanji_shimei": self._slice_and_decode(30), # 患者漢字氏名
            "kanja_kana_shimei": self._slice_and_decode(60),  # 患者カナ氏名
            "kanja_seibetsu": self._slice_and_decode(1),      # 患者性別
            "kanja_seinengappi": self._slice_and_decode(8),   # 患者生年月日
            "yuubin_bangou_1": self._slice_and_decode(3),    # 郵便番号1
            "yuubin_bangou_2": self._slice_and_decode(4),    # 郵便番号2
            "kanja_juusho": self._slice_and_decode(100),     # 患者住所
            "denwa_bangou": self._slice_and_decode(15),      # 電話番号
        }

        # --- 入院情報 (Inpatient Info)  ---
        content['inpatient_info'] = {
            "nyuugai_joutai": self._slice_and_decode(1),        # 入外状態
            "nyuuin_shinryouka_code": self._slice_and_decode(3),# 入院診療科コード
            "nyuuin_byoutou_code": self._slice_and_decode(3),   # 入院中病棟コード
            "nyuuin_heya_code": self._slice_and_decode(5),      # 入院中部屋コード
            "nyuuin_bed_code": self._slice_and_decode(2),       # 入院中ベッドコード
        }

        # --- オーダ情報 (Order Info) [cite: 94, 99] ---
        order_info = {
            "bunsho_shubetsu": self._slice_and_decode(1),   # 文書種別
            "bunsho_bangou": self._slice_and_decode(30),  # 文書番号
            "bansuu": self._slice_and_decode(2),          # 版数
            "oya_bunsho_bangou": self._slice_and_decode(30), # 親文書番号
            "order_bangou": self._slice_and_decode(8),    # オーダ番号
        }

        # 関連オーダ番号情報 (前提条件2参照: 1回固定で処理) 
        order_info['kanren_order_info'] = [
            {
                "sakusei_date": self._slice_and_decode(8), # 関連オーダ作成日
                "order_bangou": self._slice_and_decode(8), # 関連オーダ番号
            }
        ]
        
        # 実施日時 
        order_info['jisshi_nichiji'] = {
            "date": self._slice_and_decode(8), # 実施日付
            "time": self._slice_and_decode(6), # 実施時間
        }
        
        # オーダ作成日 
        order_info['order_sakusei_date'] = {
            "date": self._slice_and_decode(8), # オーダ日付
            "time": self._slice_and_decode(6), # オーダ時間
        }
        order_info['yakuhiki_ken_bangou'] = self._slice_and_decode(8)   # 薬引換券番号
        order_info['nyuugai_kubun'] = self._slice_and_decode(1)         # 入外区分
        order_info['order_hakkou_shinryouka_code'] = self._slice_and_decode(3) # オーダ発行診療科コード
        order_info['order_hakkou_byoutou_code'] = self._slice_and_decode(3) # オーダ発行病棟コード
        order_info['denpyou_code'] = self._slice_and_decode(4)         # 伝票コード
        order_info['denpyou_meishou'] = self._slice_and_decode(50)     # 伝票名称
        
        # 依頼医情報 
        order_info['irai_i_info'] = {
            "bangou": self._slice_and_decode(8),     # 依頼医番号
            "name": self._slice_and_decode(20),      # 依頼医名
            "kana_name": self._slice_and_decode(40), # 依頼医カナ名
        }
        # 代行利用者情報 
        order_info['daikou_riyousha_info'] = {
            "bangou": self._slice_and_decode(8), # 代行利用者番号
            "name": self._slice_and_decode(20),  # 代行利用者名
        }

        # 麻薬施用者情報1 & 2 (サンプルでは空欄) 
        order_info['mayaku_shiyousha_1'] = {
            "bangou": self._slice_and_decode(10),
            "kaishi_date": self._slice_and_decode(8),
            "shuuryou_date": self._slice_and_decode(8),
        }
        order_info['mayaku_shiyousha_2'] = {
            "bangou": self._slice_and_decode(10),
            "kaishi_date": self._slice_and_decode(8),
            "shuuryou_date": self._slice_and_decode(8),
        }
        content['order_info'] = order_info

        # --- 患者プロファイル情報 (Profile Info)  ---
        profile_info = {}
        profile_info['shinchou'] = { # 身長
            "value": self._slice_and_decode(11), # 身長値
            "date": self._slice_and_decode(8),  # 身長計測日
        }
        profile_info['taijuu'] = { # 体重
            "value": self._slice_and_decode(11), # 体重値
            "date": self._slice_and_decode(8),  # 体重計測日
        }
        profile_info['taihyoumenseki'] = { # 体表面積
            "value": self._slice_and_decode(11), # 体表面積値
        }
        
        # プロファイル情報群 (可変長)
        profile_count_str = self._slice_and_decode(3) # プロファイル数
        profile_count = int(profile_count_str) if profile_count_str is not np.nan else 0
        
        profile_info['profile_count'] = profile_count
        profile_info['profile_group'] = []
        
        for i in range(profile_count):
            profile_info['profile_group'].append({
                "code": self._slice_and_decode(10), # プロファイルコード
                "name": self._slice_and_decode(50), # プロファイル名称
                "data": self._slice_and_decode(500),# プロファイルデータ
            })
        
        content['profile_info'] = profile_info

        # --- レジメン情報 (Regimen Info) (サンプルでは空欄) [cite: 99, 105] ---
        content['regimen_info'] = {
            "code": self._slice_and_decode(8),
            "name": self._slice_and_decode(50),
            "course_suu": self._slice_and_decode(3),
            "tekika_jun": self._slice_and_decode(4),
            "tekiyou_kaishi_date": self._slice_and_decode(14),
            "shintai_info": {
                "shinchou": self._slice_and_decode(11),
                "taijuu": self._slice_and_decode(11),
                "taihyoumenseki": self._slice_and_decode(11),
            }
        }

        # --- 項目情報 (Item Info) (可変長)  ---
        item_count_str = self._slice_and_decode(4) # 項目数
        item_count = int(item_count_str) if item_count_str is not np.nan else 0
        
        item_info = {
            "item_count": item_count,
            "item_group": []
        }

        for _ in range(item_count):
            item = {
                "zokusai": self._slice_and_decode(3),          # 項目属性
                "code": self._slice_and_decode(8),             # 項目コード
                "renketsu_code": self._slice_and_decode(8),    # 連結項目コード
                "name": self._slice_and_decode(50),            # 項目名称
                "suuryou": self._slice_and_decode(11),         # 数量
                "sentaku_tani_flag": self._slice_and_decode(1),# 選択単位フラグ
                "sentaku_tani_code": self._slice_and_decode(3),# 選択単位コード
                "sentaku_tani_name": self._slice_and_decode(4),# 選択単位名称
                "kyokuya_flag": self._slice_and_decode(1),     # 極屋フラグ
                "koumoku_gyou_date": self._slice_and_decode(8),# 項目行日付
                "koumoku_gyou_time": self._slice_and_decode(6),# 項目行時間
                "code_group": { # コードグループ
                    "buppin_code": self._slice_and_decode(9),
                    "jan_code": self._slice_and_decode(13),
                    "yakuhin_code_kouseishou": self._slice_and_decode(12),
                    "hot_code": self._slice_and_decode(13),
                    "receipt_densan_code": self._slice_and_decode(12),
                    "jlac10_code": self._slice_and_decode(17),
                    "hyoujun_code_yj": self._slice_and_decode(20),
                    "butsuryuu_code": self._slice_and_decode(20),
                    "order_kanri_bangou": self._slice_and_decode(14),
                    "iji_kanri_bangou": self._slice_and_decode(10),
                }
            }
            item_info['item_group'].append(item)
        
        content['item_info'] = item_info
        
        return content

    def parse(self):
        """
        ファイルパスから電文を読み込み、解析を実行する。
        
        Returns:
            DotDict: 解析された電文データ。
        
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
            if common_part.get('denbun_shubetsu') != 'II' or \
               common_part.get('record_keizoku') != 'E' or \
               common_part.get('send_saki_system_code') != 'HS' or \
               common_part.get('send_moto_system_code') != 'XX':
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
                      "PDFレイアウトに従い解析を終了しました。")

            # --- 5. 結合と DotDict への変換 ---
            full_telegram = {
                "common": common_part,
                "content": content_part
            }
            
            return DotDict(full_telegram)

        except Exception as e:
            print(f"解析エラー: オフセット {self.offset} 付近で問題が発生しました。")
            print(f"エラー詳細: {e}")
            raise