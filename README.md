# NHPinfo WebApp — Hệ Thống Web Tạo Infographic 4K Độc Lập

Hệ thống web độc lập đóng gói 100% quy trình tạo Infographic 4K của kỹ năng **NHPinfo**. Người dùng phổ thông chỉ cần mở trình duyệt trên điện thoại hoặc máy tính, nhập Gmail và dán văn bản để tải ngay ảnh 4K sắc nét.

## 1. Cấu Trúc Thư Mục
```
nhpinfo_webapp/
├── app.py              # Backend Flask tích hợp WeasyPrint + pdftoppm 4K
├── Dockerfile          # Cấu hình đóng gói Docker 1 cú nhấp chuột lên Cloud
├── requirements.txt    # Danh sách thư viện Python
├── whitelist.txt       # Danh sách Gmail được cấp quyền (Admin chỉnh sửa tại đây)
├── templates/
│   └── index.html      # Giao diện Web 1-click thân thiện đại chúng
├── static/
│   └── zalo_qr.png     # Ảnh mã QR nhóm Zalo xác thực
└── output/             # Thư mục lưu trữ file ảnh .PNG và PDF 4K kết xuất
```

## 2. Hướng Dẫn Chạy & Triển Khai
### Cách A: Chạy trực tiếp trên máy tính / VPS (Linux, macOS, Windows)
1. Cài đặt các gói hệ thống:
   - Ubuntu/Debian: `sudo apt update && sudo apt install -y poppler-utils libpango-1.0-0 libpangocairo-1.0-0`
   - macOS: `brew install poppler pango`
2. Cài đặt thư viện Python:
   `pip install -r requirements.txt`
3. Khởi chạy ứng dụng:
   `python app.py`
4. Mở trình duyệt truy cập: `http://localhost:5000`

### Cách B: Triển khai 1 cú nhấp chuột lên Cloud miễn phí (Render.com, Railway.app, Koyeb)
1. Đẩy thư mục `nhpinfo_webapp` lên GitHub của bạn.
2. Đăng ký tài khoản tại [Render.com](https://render.com) hoặc [Railway.app](https://railway.app).
3. Chọn **New Web Service** -> Kết nối Repository GitHub vừa tạo.
4. Nền tảng sẽ tự động nhận diện `Dockerfile`, cài đặt môi trường Linux hoàn chỉnh và tạo ra đường link web công khai dạng: `https://nhpinfo.onrender.com`.

## 3. Cách Quản Lý Cấp Quyền Gmail Khách Hàng
- Mở file `whitelist.txt`, thêm địa chỉ Gmail của khách hàng vào (mỗi email một dòng).
- Khi khách hàng truy cập web và nhập Gmail đã có trong danh sách, hệ thống tự động mở khóa và xuất ảnh ngay.
- Nếu khách hàng chưa có trong danh sách, hệ thống tự động hiển thị mã QR nhóm Zalo để hướng dẫn inbox đăng ký.
