# Hướng thiết kế: Job Radar

- Sản phẩm: Job Radar tổng hợp tin tuyển dụng từ nhiều trang việc làm cho người tìm việc ở Việt Nam, so sánh lương gross và net trước khi ứng tuyển.
- Tính cách: điềm tĩnh, chính xác, hơi ấm áp
- Thế giới: bảng tin giấy dán trên bảng gỗ buổi sáng, giấy ấm, mực đậm, ánh sáng yên tĩnh
- Khoảnh khắc: thẻ việc làm với dải lương có hai chấm mốc; biểu đồ lương gross và net trên trang công cụ
- Dấu ấn: dải lương, một đường mảnh với hai chấm đánh dấu mức thấp nhất và cao nhất, dùng nhất quán trên thẻ việc làm và trang chi tiết

## Mã dùng chung

- Nền giấy ấm #faf7f1, mặt nổi #fffdf9, viền mờ rgba(58, 48, 34, 0.14), chữ chính #221d16, chữ phụ #6a6156, chữ mờ #8d8478
- Một màu nhấn xanh lá đậm #1b5e4b, tương phản trên nền giấy đạt trên 4.5:1, dùng cho liên kết, nút chính và điểm nhấn biểu đồ
- Phông hệ thống, hai trọng lượng 400 và 500, số dùng tabular-nums, định dạng tiền một kiểu duy nhất theo triệu đồng
- Lưới 4px, bo góc lồng nhau (nút 8, thẻ 12, khung 16), chuyển động lặng chỉ đổi màu và độ mờ
- Biểu tượng đường nét nội tuyến, một cỡ 18px, nét 1.5, cùng màu với chữ
