"""新北市垃圾車 API 客戶端"""

import time
import requests
from typing import Optional, Dict, Any, List
from src.utils.logger import logger
from src.models.truck import TruckLine


class NTPCApiError(Exception):
    """新北市 API 錯誤"""
    pass


class NTPCApiClient:
    """新北市垃圾車 API 客戶端"""

    def __init__(
        self,
        base_url: str = "https://crd-rubbish.epd.ntpc.gov.tw/WebAPI",
        timeout: int = 10,
        retry_count: int = 3,
        retry_delay: int = 2
    ):
        """
        初始化 API 客戶端

        Args:
            base_url: API 基礎 URL
            timeout: 請求逾時時間（秒）
            retry_count: 重試次數
            retry_delay: 重試延遲（秒）
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.session = requests.Session()

    def get_around_points(self, lat: float, lng: float) -> Optional[List[TruckLine]]:
        """
        查詢附近的垃圾車

        Args:
            lat: 查詢位置的緯度
            lng: 查詢位置的經度

        Returns:
            List[TruckLine]: 垃圾車路線列表，失敗時返回 None

        Raises:
            NTPCApiError: 當所有重試都失敗時
        """
        url = f"{self.base_url}/GetAroundPoints"
        payload = {"lat": lat, "lng": lng}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        last_error = None

        for attempt in range(self.retry_count):
            try:
                logger.debug(
                    f"呼叫新北市 API (嘗試 {attempt + 1}/{self.retry_count}): "
                    f"lat={lat}, lng={lng}"
                )

                response = self.session.post(
                    url,
                    data=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                # 檢查 HTTP 狀態碼
                response.raise_for_status()

                # 解析 JSON
                data = response.json()

                # 驗證回應格式
                if not isinstance(data, dict):
                    raise NTPCApiError(f"API 回應格式錯誤: 不是字典類型")

                if 'Line' not in data:
                    logger.warning("API 回應中無 'Line' 欄位，可能沒有垃圾車在附近")
                    return []

                # 轉換為 TruckLine 物件
                lines = []
                for line_data in data.get('Line', []):
                    try:
                        truck_line = TruckLine.from_dict(line_data)
                        lines.append(truck_line)
                    except Exception as e:
                        logger.warning(f"解析路線資料失敗: {e}")
                        continue

                logger.info(
                    f"成功查詢新北市 API: 找到 {len(lines)} 條路線 "
                    f"(TimeStamp: {data.get('TimeStamp')})"
                )

                return lines

            except requests.exceptions.Timeout:
                last_error = "請求逾時"
                logger.warning(f"API 請求逾時 (嘗試 {attempt + 1}/{self.retry_count})")

            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP 錯誤: {e.response.status_code}"
                logger.warning(
                    f"API 回傳錯誤狀態碼 {e.response.status_code} "
                    f"(嘗試 {attempt + 1}/{self.retry_count})"
                )

            except requests.exceptions.RequestException as e:
                last_error = f"網路錯誤: {str(e)}"
                logger.warning(
                    f"API 請求失敗: {e} "
                    f"(嘗試 {attempt + 1}/{self.retry_count})"
                )

            except ValueError as e:
                last_error = f"JSON 解析失敗: {str(e)}"
                logger.error(f"API 回應無法解析為 JSON: {e}")
                # JSON 解析失敗不重試
                break

            except Exception as e:
                last_error = f"未知錯誤: {str(e)}"
                logger.error(f"API 請求發生未預期的錯誤: {e}")
                break

            # 如果還有重試機會，等待後重試
            if attempt < self.retry_count - 1:
                logger.info(f"等待 {self.retry_delay} 秒後重試...")
                time.sleep(self.retry_delay)

        # 所有重試都失敗
        error_msg = f"新北市 API 請求失敗 (重試 {self.retry_count} 次): {last_error}"
        logger.error(error_msg)
        raise NTPCApiError(error_msg)

    def __del__(self):
        """清理資源"""
        if hasattr(self, 'session'):
            self.session.close()
