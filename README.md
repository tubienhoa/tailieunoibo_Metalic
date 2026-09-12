# Hệ Thống Quản Trị Quy Trình & Biểu Mẫu Theo Cây Thư Mục Nội Bộ

Hệ thống được thiết kế theo cấu trúc thư mục động (Dynamic Directory Architecture):
- Thư mục tổng: `HE_THONG_PHONG_BAN/`
- Mỗi phòng ban là 1 thư mục con (ví dụ: `01_Khoi_San_Xuat/`, `02_Khoi_Ke_Toan/`...).
- Trong mỗi phòng ban có 2 thư mục con chuẩn:
  - `Quy_Trinh_SOP/`: Chứa các tài liệu quy trình, hướng dẫn thao tác chuẩn.
  - `Bieu_Mau_Form/`: Chứa các biểu mẫu Excel, Word, PDF để nhân viên tải về dùng.
  - `metadata.json`: Tự động ghi nhận thông tin quản lý và lịch sử cập nhật.

## 🚀 Thêm phòng ban mới:
Có 2 cách:
1. Thao tác trên giao diện: Vào tab **"➕ Quản Lý & Tạo Phòng Ban Mới"** -> Điền tên -> Hệ thống tự động tạo thư mục và phân loại.
2. Thao tác vật lý trên máy chủ/GitHub: Chỉ cần tạo thêm 1 folder mới trong `HE_THONG_PHONG_BAN/`, hệ thống sẽ tự động quét và đưa lên website.
