"""新北市 API 整合測試"""

import pytest
from src.clients.ntpc_api import NTPCApiClient, NTPCApiError
from src.models.truck import TruckLine


class TestNTPCApiIntegration:
    """新北市 API 整合測試"""

    @pytest.fixture
    def client(self):
        """建立 API 客戶端"""
        return NTPCApiClient()

    def test_get_around_points_success(self, client):
        """測試成功查詢附近的垃圾車"""
        # 使用板橋區的座標
        lat, lng = 25.0199, 121.4705

        result = client.get_around_points(lat, lng)

        # 驗證基本結果
        assert isinstance(result, list), "結果應該是列表"

        # 如果有找到垃圾車，進行更詳細的驗證
        if len(result) > 0:
            truck = result[0]

            # 驗證資料類型
            assert isinstance(truck, TruckLine), "結果應該是 TruckLine 物件"

            # 驗證必要欄位存在
            assert truck.line_id, "line_id 不應為空"
            assert truck.line_name, "line_name 不應為空"
            assert truck.car_no, "car_no 不應為空"
            assert truck.area, "area 不應為空"

            # 驗證數值欄位
            assert isinstance(truck.arrival_rank, int), "arrival_rank 應為整數"
            assert isinstance(truck.diff, int), "diff 應為整數"
            assert truck.arrival_rank >= 0, "arrival_rank 應為非負數"
            assert len(truck.points) > 0, "應該有清運點資料"

            # 驗證座標合理性（新北市範圍）
            assert 24.0 < truck.location_lat < 26.0, "緯度應在合理範圍內"
            assert 121.0 < truck.location_lon < 122.0, "經度應在合理範圍內"

            print(f"\n✅ 找到 {len(result)} 台垃圾車")
            print(f"第一台: {truck.line_name} ({truck.car_no})")
            print(f"目前位置: {truck.location}")
            print(f"停靠點: {truck.arrival_rank}/{len(truck.points)}")
            print(f"延遲狀態: {truck.diff} 分鐘")

    def test_get_around_points_data_consistency(self, client):
        """測試資料一致性"""
        lat, lng = 25.0199, 121.4705

        result = client.get_around_points(lat, lng)

        if len(result) > 0:
            for truck in result:
                # 驗證 arrival_rank 不超過總清運點數
                assert truck.arrival_rank <= len(truck.points), \
                    f"{truck.line_name}: arrival_rank 不應超過清運點總數"

                # 驗證清運點的 point_rank 連續且唯一
                point_ranks = [p.point_rank for p in truck.points]
                assert len(point_ranks) == len(set(point_ranks)), \
                    f"{truck.line_name}: point_rank 應該唯一"

                # 驗證目前清運點存在
                current_point = truck.get_current_point()
                if truck.arrival_rank > 0:
                    assert current_point is not None, \
                        f"{truck.line_name}: 應該要有目前清運點"

    def test_get_around_points_upcoming_logic(self, client):
        """測試即將到達清運點的邏輯"""
        lat, lng = 25.0199, 121.4705

        result = client.get_around_points(lat, lng)

        if len(result) > 0:
            for truck in result:
                upcoming = truck.get_upcoming_points()

                # 驗證所有即將到達的清運點的 rank 都大於目前 rank
                for point in upcoming:
                    assert point.point_rank > truck.arrival_rank, \
                        f"{truck.line_name}: 即將到達的清運點 rank 應大於目前 rank"

                # 驗證排序正確（由小到大）
                ranks = [p.point_rank for p in upcoming]
                assert ranks == sorted(ranks), \
                    f"{truck.line_name}: 即將到達的清運點應按 rank 排序"

                print(f"\n{truck.line_name}:")
                print(f"  目前停靠點序號: {truck.arrival_rank}")
                print(f"  剩餘清運點數: {len(upcoming)}")
                if upcoming:
                    print(f"  下一個清運點: {upcoming[0].point_name} (rank: {upcoming[0].point_rank})")

    def test_get_around_points_point_status(self, client):
        """測試清運點狀態邏輯"""
        lat, lng = 25.0199, 121.4705

        result = client.get_around_points(lat, lng)

        if len(result) > 0:
            truck = result[0]

            # 測試已經過的清運點
            passed_points = [p for p in truck.points if p.has_passed()]
            for point in passed_points:
                assert point.arrival is not None, "已經過的清運點應該有 arrival 時間"

            # 測試未經過的清運點
            upcoming = truck.get_upcoming_points()
            for point in upcoming:
                # 未經過的清運點應該沒有 arrival 時間，或 arrival 為空字串
                assert not point.arrival or point.arrival == "", \
                    "未經過的清運點不應該有 arrival 時間"

            print(f"\n{truck.line_name} 清運點狀態統計:")
            print(f"  已經過: {len(passed_points)} 個")
            print(f"  未到達: {len(upcoming)} 個")

    def test_get_around_points_invalid_coordinates(self, client):
        """測試無效座標"""
        # 使用海上的座標（應該找不到垃圾車）
        lat, lng = 25.0, 120.0

        result = client.get_around_points(lat, lng)

        # 應該返回空列表而不是錯誤
        assert isinstance(result, list), "即使沒有結果也應返回列表"

    def test_api_retry_mechanism(self):
        """測試 API 重試機制"""
        # 使用錯誤的 base_url 來測試重試
        client = NTPCApiClient(
            base_url="https://invalid-url-for-testing.example.com",
            retry_count=2,
            retry_delay=1
        )

        with pytest.raises(NTPCApiError) as exc_info:
            client.get_around_points(25.0199, 121.4705)

        # 驗證錯誤訊息包含重試資訊
        assert "重試" in str(exc_info.value)
        print(f"\n✅ 重試機制正常: {exc_info.value}")

    def test_concurrent_requests(self, client):
        """測試併發請求"""
        import concurrent.futures

        lat, lng = 25.0199, 121.4705

        # 同時發送 3 個請求
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(client.get_around_points, lat, lng)
                for _ in range(3)
            ]

            results = [future.result() for future in futures]

        # 驗證所有請求都成功
        for result in results:
            assert isinstance(result, list), "每個請求都應返回列表"

        print(f"\n✅ 併發請求測試通過，共 {len(results)} 個請求")

    def test_response_time(self, client):
        """測試回應時間"""
        import time

        lat, lng = 25.0199, 121.4705

        start_time = time.time()
        result = client.get_around_points(lat, lng)
        elapsed_time = time.time() - start_time

        # 驗證回應時間在合理範圍內（10秒內）
        assert elapsed_time < 10, f"回應時間過長: {elapsed_time:.2f} 秒"

        print(f"\n✅ API 回應時間: {elapsed_time:.2f} 秒")
        print(f"   找到 {len(result)} 台垃圾車")
