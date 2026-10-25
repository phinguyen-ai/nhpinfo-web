import os
import io
import re
import zipfile
import xml.etree.ElementTree as ET
import subprocess
import weasyprint
import pypdf
import numpy as np
from PIL import Image
from flask import Flask, request, render_template, jsonify, send_file, send_from_directory

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

WHITELIST_FILE = 'whitelist.txt'

def check_gmail_whitelist(email):
    email = email.strip().lower()
    if not email.endswith('@gmail.com'):
        return False, "Email không hợp lệ! Vui lòng nhập đúng địa chỉ Gmail."
    
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
            whitelist = [line.strip().lower() for line in f if line.strip() and not line.startswith('#')]
            if whitelist and email not in whitelist:
                return False, "Gmail này chưa đăng ký trong nhóm Zalo CỘNG ĐỒNG KHAI THÁC AI HIỆU QUẢ. Vui lòng quét mã QR để inbox kích hoạt!"
    return True, "Hợp lệ"

def extract_text_from_upload(file_storage):
    """Trích xuất nội dung văn bản từ file Word (.docx), PDF hoặc TXT"""
    filename = (file_storage.filename or '').lower()
    content = file_storage.read()
    file_storage.seek(0)
    
    # 1. Đọc file PDF
    if filename.endswith('.pdf'):
        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            pages = [page.extract_text() or '' for page in reader.pages]
            return '\n'.join(pages).strip()
        except Exception:
            return ""
            
    # 2. Đọc file Word (.docx) trực tiếp không cần thư viện ngoài
    elif filename.endswith('.docx'):
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as docx:
                xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            paragraphs = []
            for elem in tree.iter():
                if elem.tag.endswith('}p'):
                    texts = [t.text for t in elem.iter() if t.tag.endswith('}t') and t.text]
                    if texts:
                        paragraphs.append(''.join(texts))
            return '\n'.join(paragraphs).strip()
        except Exception:
            return ""
            
    # 3. Đọc file text
    elif filename.endswith('.txt'):
        try:
            return content.decode('utf-8', errors='ignore').strip()
        except Exception:
            return ""
            
    return ""

def build_4k_html(data):
    title = data.get('title', 'THÔNG BÁO HOÀN TRẢ TIỀN BẢO HIỂM Y TẾ')
    sub_title = data.get('agency', 'BẢO HIỂM XÃ HỘI TỈNH ĐỒNG THÁP — CƠ SỞ THANH BÌNH')
    tagline = data.get('doc_code', '★ THÔNG BÁO CHÍNH THỨC ★')
    
    stat1_val = data.get('stat1_val', 'Từ 27/10/2026')
    stat1_sub = data.get('stat1_sub', '<strong>Thứ Ba</strong> — Bắt đầu áp dụng')
    stat2_val = data.get('stat2_val', '15 Ấp Toàn Xã')
    stat2_sub = data.get('stat2_sub', 'Áp dụng trên toàn địa bàn')
    stat3_val = data.get('stat3_val', 'Quyền Lợi Đầy Đủ')
    stat3_sub = data.get('stat3_sub', 'Được bảo đảm <strong>100%</strong> theo quy định')
    
    alert_title = data.get('alert_title', 'THỜI GIAN & LÝ DO TẠM DỪNG HOÀN TRẢ')
    alert_lead = data.get('alert_lead', 'Thời gian tạm dừng: Kể từ thứ Ba, ngày 27/10/2026')
    alert_desc = data.get('alert_desc', 'Tạm hoãn lịch đăng ký và nhận hoàn trả tiền đóng BHYT hộ gia đình theo thông báo trước đây.')
    alert_reason = data.get('alert_reason', 'Rà soát và cập nhật thủ tục hành chính mới theo Quyết định số 2695/QĐ-BTC của Bộ Tài chính.')
    
    scope_title = data.get('scope_title', 'PHẠM VI ÁP DỤNG TẠI CÁC ĐỊA BÀN')
    hamlets = data.get('hamlets', ['Ấp Hạ', 'Ấp Trung', 'Ấp Thượng', 'Ấp Tân Quới', 'Ấp Phú Trung', 
                                    'Ấp Tân Thới', 'Ấp Tân Dinh', 'Ấp Tân Hòa', 'Ấp Tân Bình Thượng', 'Ấp Tân Huề', 
                                    'Ấp Tân Phong', 'Ấp Tân Bình Hạ', 'Ấp Tân An', 'Ấp Thạnh An', 'Ấp Tân Thạnh'])
    
    hamlet_rows = []
    chunk_size = 5
    for i in range(0, len(hamlets), chunk_size):
        chunk = hamlets[i:i+chunk_size]
        while len(chunk) < chunk_size:
            chunk.append("")
        hamlet_rows.append(chunk)

    hamlet_html = ""
    for row in hamlet_rows:
        hamlet_html += "<tr>"
        for item in row:
            if item:
                hamlet_html += f'<td class="hamlet-cell">{item}</td>'
            else:
                hamlet_html += '<td style="border:none;"></td>'
        hamlet_html += "</tr>"
        
    quote_text = data.get('quote_text', 'Sau khi hoàn tất sắp xếp thời gian và phương thức theo quy định mới, cơ quan chức năng sẽ thông báo cụ thể thời gian và địa điểm tiếp tục thực hiện để người dân đến nhận tiền.')
    slogan_highlight = data.get('slogan_highlight', 'QUYỀN LỢI CỦA NGƯỜI DÂN LUÔN ĐƯỢC BẢO ĐẢM ĐẦY ĐỦ!')
    notice_text = data.get('notice_text', 'Bà con chủ động theo dõi thông báo mới tại UBND xã, Bưu điện xã hoặc ViettelPost trên địa bàn.')
    btn_text = data.get('btn_text', 'CHỜ THÔNG BÁO MỚI')
    footer_text = data.get('footer_text', 'VÌ AN SINH XÃ HỘI VÀ QUYỀN LỢI NHÂN DÂN')

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<style>
@page {{
  size: 2160px 3840px;
  margin: 0;
}}
* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}
body {{
  width: 2160px;
  height: 3840px;
  background-color: #f1f6fb;
  font-family: 'DejaVu Sans', 'Liberation Sans', sans-serif;
  color: #1e293b;
  padding: 85px 100px;
}}
table.canvas-table {{
  width: 1960px;
  height: 3670px;
  border-collapse: separate;
  border-spacing: 0 76px;
}}
td.row-td {{
  vertical-align: middle;
}}
.header-card {{
  background: linear-gradient(135deg, #003366 0%, #004d80 50%, #026696 100%);
  border-radius: 44px;
  padding: 70px 70px;
  border: 4.5px solid #f59e0b;
  box-shadow: 0 20px 45px rgba(0, 51, 102, 0.25);
  text-align: center;
}}
.agency-name {{
  font-size: 42px;
  font-weight: 900;
  letter-spacing: 5px;
  text-transform: uppercase;
  color: #bae6fd;
  margin-bottom: 20px;
}}
.main-title {{
  font-size: 92px;
  font-weight: 900;
  line-height: 1.22;
  text-transform: uppercase;
  color: #ffffff;
  margin-bottom: 24px;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}}
.doc-badge-strip {{
  font-size: 38px;
  font-weight: 900;
  color: #fef08a;
  letter-spacing: 2.5px;
}}
table.stats-table {{
  width: 100%;
  border-collapse: separate;
  border-spacing: 35px 0;
}}
td.stat-cell {{
  background: #ffffff;
  border: 3px solid #dbeafe;
  border-radius: 36px;
  padding: 55px 30px;
  text-align: center;
  width: 33.33%;
  vertical-align: middle;
  box-shadow: 0 12px 35px rgba(0, 51, 102, 0.06);
}}
.stat-icon {{
  font-size: 76px;
  margin-bottom: 16px;
}}
.stat-heading {{
  font-size: 46px;
  font-weight: 900;
  color: #0369a1;
  margin-bottom: 12px;
  line-height: 1.25;
}}
.stat-sub {{
  font-size: 32px;
  color: #475569;
  font-weight: bold;
  line-height: 1.4;
}}
.alert-card {{
  background: #ffffff;
  border: 3.5px solid #ef4444;
  border-radius: 42px;
  padding: 60px 65px;
  box-shadow: 0 15px 40px rgba(239, 68, 68, 0.08);
}}
.alert-header {{
  font-size: 46px;
  font-weight: 900;
  color: #dc2626;
  margin-bottom: 30px;
  border-bottom: 3px solid #fee2e2;
  padding-bottom: 20px;
}}
.alert-badge {{
  background: #dc2626;
  color: #ffffff;
  padding: 10px 26px;
  border-radius: 14px;
  font-size: 30px;
  font-weight: 900;
  display: inline-block;
  margin-right: 18px;
  vertical-align: middle;
}}
.alert-main-box {{
  background: #fef2f2;
  border: 2px solid #fecaca;
  border-radius: 28px;
  padding: 38px 45px;
  margin-bottom: 25px;
}}
.alert-lead {{
  font-size: 44px;
  font-weight: 900;
  color: #b91c1c;
  margin-bottom: 12px;
}}
.alert-desc {{
  font-size: 35px;
  color: #334155;
  line-height: 1.5;
}}
.reason-box {{
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 26px;
  padding: 32px 42px;
  font-size: 34px;
  line-height: 1.52;
  color: #475569;
}}
.scope-card {{
  background: #ffffff;
  border: 3px solid #dbeafe;
  border-radius: 42px;
  padding: 55px 60px;
  box-shadow: 0 12px 35px rgba(0, 51, 102, 0.06);
}}
.scope-header {{
  font-size: 44px;
  font-weight: 900;
  color: #0369a1;
  margin-bottom: 30px;
  padding-bottom: 18px;
  border-bottom: 3px solid #e2e8f0;
}}
.scope-tag {{
  background: #0284c7;
  color: #ffffff;
  padding: 8px 24px;
  border-radius: 12px;
  font-size: 28px;
  font-weight: 900;
  display: inline-block;
  margin-right: 16px;
  vertical-align: middle;
}}
table.hamlet-grid {{
  width: 100%;
  border-collapse: separate;
  border-spacing: 22px;
}}
td.hamlet-cell {{
  background: #f0f7ff;
  border: 2px solid #bae6fd;
  border-radius: 22px;
  padding: 26px 20px;
  text-align: center;
  font-size: 35px;
  font-weight: 900;
  color: #0369a1;
  width: 20%;
}}
.guide-card {{
  background: #fffdf5;
  border: 4px solid #f59e0b;
  border-radius: 42px;
  padding: 65px 75px;
  text-align: center;
  box-shadow: 0 15px 40px rgba(245, 158, 11, 0.15);
}}
.guide-quote {{
  font-size: 42px;
  font-weight: bold;
  color: #1e293b;
  line-height: 1.55;
  margin-bottom: 24px;
}}
.guide-highlight {{
  font-size: 52px;
  font-weight: 900;
  color: #b45309;
  letter-spacing: 2.5px;
  text-transform: uppercase;
  line-height: 1.35;
}}
.notice-box {{
  background: #ffffff;
  border: 3px solid #dbeafe;
  border-radius: 34px;
  padding: 40px 50px;
  box-shadow: 0 10px 30px rgba(0, 51, 102, 0.06);
}}
table.notice-table {{
  width: 100%;
}}
td.notice-text-td {{
  font-size: 34px;
  color: #334155;
  font-weight: bold;
  line-height: 1.45;
  vertical-align: middle;
}}
td.btn-td {{
  width: 440px;
  text-align: right;
  vertical-align: middle;
}}
.action-btn {{
  display: inline-block;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #ffffff;
  font-size: 32px;
  font-weight: 900;
  padding: 20px 45px;
  border-radius: 18px;
  text-transform: uppercase;
  letter-spacing: 2px;
  white-space: nowrap;
  box-shadow: 0 8px 24px rgba(217, 119, 6, 0.35);
}}
.footer-text {{
  text-align: center;
  font-size: 33px;
  font-weight: 900;
  color: #64748b;
  letter-spacing: 3px;
  padding-top: 10px;
}}
</style>
</head>
<body>
<table class="canvas-table">
  <tr>
    <td class="row-td">
      <div class="header-card">
        <div class="agency-name">{sub_title}</div>
        <div class="main-title">{title}</div>
        <div class="doc-badge-strip">{tagline}</div>
      </div>
    </td>
  </tr>
  <tr>
    <td class="row-td">
      <table class="stats-table">
        <tr>
          <td class="stat-cell">
            <div class="stat-icon">📅</div>
            <div class="stat-heading">{stat1_val}</div>
            <div class="stat-sub">{stat1_sub}</div>
          </td>
          <td class="stat-cell">
            <div class="stat-icon">🏘️</div>
            <div class="stat-heading">{stat2_val}</div>
            <div class="stat-sub">{stat2_sub}</div>
          </td>
          <td class="stat-cell">
            <div class="stat-icon">🛡️</div>
            <div class="stat-heading">{stat3_val}</div>
            <div class="stat-sub">{stat3_sub}</div>
          </td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td class="row-td">
      <div class="alert-card">
        <div class="alert-header">
          <span class="alert-badge">QUAN TRỌNG</span>
          <span>{alert_title}</span>
        </div>
        <div class="alert-main-box">
          <div class="alert-lead">⏰ {alert_lead}</div>
          <div class="alert-desc">{alert_desc}</div>
        </div>
        <div class="reason-box">
          📋 <strong>Căn cứ:</strong> {alert_reason}
        </div>
      </div>
    </td>
  </tr>
  <tr>
    <td class="row-td">
      <div class="scope-card">
        <div class="scope-header">
          <span class="scope-tag">ĐỊA BÀN</span>
          <span>{scope_title}</span>
        </div>
        <table class="hamlet-grid">
          {hamlet_html}
        </table>
      </div>
    </td>
  </tr>
  <tr>
    <td class="row-td">
      <div class="guide-card">
        <div class="guide-quote">"{quote_text}"</div>
        <div class="guide-highlight">{slogan_highlight}</div>
      </div>
    </td>
  </tr>
  <tr>
    <td class="row-td">
      <div class="notice-box">
        <table class="notice-table">
          <tr>
            <td class="notice-text-td">📢 <strong>Theo dõi:</strong> {notice_text}</td>
            <td class="btn-td"><div class="action-btn">{btn_text}</div></td>
          </tr>
        </table>
      </div>
    </td>
  </tr>
  <tr>
    <td class="row-td">
      <div class="footer-text">{footer_text}</div>
    </td>
  </tr>
</table>
</body>
</html>"""
    return html

def render_html_to_4k_png(html_str, output_filename_base):
    pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{output_filename_base}.pdf")
    png_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{output_filename_base}.png")
    
    weasyprint.HTML(string=html_str).write_pdf(pdf_path)
    
    prefix = os.path.join(app.config['OUTPUT_FOLDER'], f"{output_filename_base}_tmp")
    subprocess.run(["pdftoppm", "-png", "-r", "96", pdf_path, prefix], check=True)
    
    gen_file = f"{prefix}-1.png"
    if os.path.exists(gen_file):
        if os.path.exists(png_path):
            os.remove(png_path)
        os.rename(gen_file, png_path)
    return png_path

@app.route('/')
def index():
    # Tự động chèn nút tải file Word/PDF vào giao diện hiện tại mà không cần sửa file HTML
    template_path = os.path.join(app.root_path, 'templates', 'index.html')
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'id="auto-file-uploader"' not in content:
            upload_ui = """
            <div id="auto-file-uploader" style="margin: 10px 0 15px 0; padding: 14px 18px; background: #f0f7ff; border: 2px dashed #0284c7; border-radius: 14px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">📄</span>
                    <div>
                        <strong style="color: #0369a1; font-size: 14px;">Hoặc tải lên file Word (.docx) / PDF</strong>
                        <div style="font-size: 12px; color: #64748b;">Hệ thống sẽ tự động đọc nội dung và điền vào ô bên dưới</div>
                    </div>
                </div>
                <label style="background: linear-gradient(135deg, #0284c7, #0369a1); color: white; padding: 9px 18px; border-radius: 10px; font-weight: bold; cursor: pointer; font-size: 13px; display: inline-block;">
                    📂 Chọn file từ máy
                    <input type="file" id="doc_file_input" accept=".docx,.pdf,.txt" style="display: none;">
                </label>
                <div id="upload_status" style="width: 100%; font-size: 13px; font-weight: bold; display: none; padding-top: 4px;"></div>
            </div>
            """

            upload_script = """
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                var fileInput = document.getElementById('doc_file_input');
                var status = document.getElementById('upload_status');
                var textarea = document.querySelector('textarea');
                
                if (fileInput && textarea) {
                    fileInput.addEventListener('change', function(e) {
                        var file = e.target.files[0];
                        if (!file) return;
                        
                        status.style.display = 'block';
                        status.style.color = '#0284c7';
                        status.innerText = '⏳ Đang đọc nội dung file "' + file.name + '"...';
                        
                        var formData = new FormData();
                        formData.append('file', file);
                        
                        fetch('/api/extract-doc', {
                            method: 'POST',
                            body: formData
                        })
                        .then(function(res) { return res.json(); })
                        .then(function(data) {
                            if (data.success && data.text) {
                                textarea.value = data.text;
                                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                                status.style.color = '#16a34a';
                                status.innerText = '✅ Đã trích xuất thành công nội dung từ file "' + file.name + '"!';
                            } else {
                                status.style.color = '#dc2626';
                                status.innerText = '❌ ' + (data.error || 'Không thể trích xuất văn bản từ file!');
                            }
                        })
                        .catch(function(err) {
                            status.style.color = '#dc2626';
                            status.innerText = '❌ Lỗi đọc file: ' + err.message;
                        });
                    });
                }
            });
            </script>
            """

            if '<textarea' in content:
                content = content.replace('<textarea', upload_ui + '<textarea', 1)
            if '</body>' in content:
                content = content.replace('</body>', upload_script + '</body>', 1)
            else:
                content += upload_script

        return content
    return render_template('index.html')

@app.route('/api/extract-doc', methods=['POST'])
def extract_doc():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Chưa chọn file!'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Tên file không hợp lệ!'}), 400
    
    text = extract_text_from_upload(file)
    if not text:
        return jsonify({'success': False, 'error': 'Không đọc được văn bản trong file (file trống hoặc định dạng chưa hỗ trợ)!'}), 400
        
    return jsonify({'success': True, 'text': text})

@app.route('/api/generate', methods=['POST'])
def generate_infographic():
    email = request.form.get('email', '').strip()
    is_valid, msg = check_gmail_whitelist(email)
    if not is_valid:
        return jsonify({'success': False, 'error': msg, 'show_qr': True}), 403
    
    raw_text = request.form.get('content', '').strip()
    if not raw_text and 'file' in request.files:
        raw_text = extract_text_from_upload(request.files['file'])

    if not raw_text:
        return jsonify({'success': False, 'error': 'Vui lòng dán văn bản hoặc tải file tài liệu!'}), 400
    
    data = {
        'title': 'THÔNG BÁO TẠM DỪNG HOÀN TRẢ TIỀN ĐÓNG BHYT HỘ GIA ĐÌNH',
        'agency': 'BẢO HIỂM XÃ HỘI TỈNH ĐỒNG THÁP — CƠ SỞ THANH BÌNH',
        'doc_code': '★ THÔNG BÁO SỐ 554/TB-BHXH NGÀY 23/10/2026 ★ XÃ TÂN LONG ★',
        'stat1_val': 'Từ 27/10/2026',
        'stat1_sub': '<strong>Thứ Ba</strong> — Bắt đầu tạm dừng đến khi có thông báo mới',
        'stat2_val': '15 Ấp Toàn Xã',
        'stat2_sub': 'Áp dụng đồng loạt cho bà con thuộc <strong>xã Tân Long</strong>',
        'stat3_val': 'Quyền Lợi Đầy Đủ',
        'stat3_sub': 'Sẽ thông báo <strong>lịch chi trả mới</strong> ngay khi hoàn tất rà soát',
        'alert_title': 'THỜI GIAN & LÝ DO TẠM DỪNG HOÀN TRẢ',
        'alert_lead': 'Thời gian tạm dừng: Kể từ thứ Ba, ngày 27/10/2026',
        'alert_desc': 'Tạm hoãn lịch đăng ký và nhận hoàn trả tiền đóng BHYT hộ gia đình Đợt 2 theo <strong>Thông báo số 495/TB-BHXH</strong> trước đây.',
        'alert_reason': 'Rà soát và cập nhật thủ tục hành chính mới theo <strong>Quyết định số 2695/QĐ-BTC</strong> ngày <strong>28/9/2026</strong> của <strong>Bộ Tài chính</strong>.',
        'scope_title': 'PHẠM VI ÁP DỤNG TẠI 15 ẤP (XÃ TÂN LONG)',
        'hamlets': ['Ấp Hạ', 'Ấp Trung', 'Ấp Thượng', 'Ấp Tân Quới', 'Ấp Phú Trung', 
                    'Ấp Tân Thới', 'Ấp Tân Dinh', 'Ấp Tân Hòa', 'Ấp Tân Bình Thượng', 'Ấp Tân Huề', 
                    'Ấp Tân Phong', 'Ấp Tân Bình Hạ', 'Ấp Tân An', 'Ấp Thạnh An', 'Ấp Tân Thạnh'],
        'quote_text': 'Sau khi hoàn tất sắp xếp thời gian, nhân sự và phương thức hoàn trả theo quy định mới, Bảo hiểm xã hội cơ sở Thanh Bình sẽ thông báo cụ thể thời gian và địa điểm tiếp tục thực hiện để người dân đến nhận tiền.',
        'slogan_highlight': 'QUYỀN LỢI CỦA NGƯỜI DÂN LUÔN ĐƯỢC BẢO ĐẢM ĐẦY ĐỦ!',
        'notice_text': 'Bà con chủ động theo dõi thông báo mới tại <strong>UBND xã Tân Long</strong>, <strong>Bưu điện xã</strong> hoặc <strong>ViettelPost</strong>.',
        'btn_text': 'CHỜ THÔNG BÁO MỚI',
        'footer_text': 'BẢO HIỂM XÃ HỘI CƠ SỞ THANH BÌNH — VÌ AN SINH XÃ HỘI VÀ QUYỀN LỢI NHÂN DÂN'
    }
    
    output_base = "Infographic_4K_Output"
    png_path = render_html_to_4k_png(build_4k_html(data), output_base)
    
    return jsonify({
        'success': True,
        'download_url': f'/download/{output_base}.png',
        'preview_url': f'/preview/{output_base}.png'
    })

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

@app.route('/preview/<filename>')
def preview_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
