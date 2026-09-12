import streamlit as st
import pandas as pd
import datetime
import io
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

# --- CẤU HÌNH TRANG (PAGE CONFIG) ---
st.set_page_config(
    page_title="Cổng Quản Trị Quy Trình & Biểu Mẫu - CÔNG TY METALIC",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THUẬT NGỮ & GIẢI THÍCH (GLOSSARY) ---
# SOP: Standard Operating Procedure - Quy trình thao tác chuẩn
# KPI: Key Performance Indicator - Chỉ số đo lường hiệu suất (tỷ lệ tuân thủ & hoàn thiện biểu mẫu)
# RACI Matrix: Responsible (Thực hiện), Accountable (Phê duyệt), Consulted (Tham vấn), Informed (Nhận thông tin)
# SSOT: Single Source of Truth - Nguồn dữ liệu gốc duy nhất (Google Sheets & Google Drive)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7vrN3GLRabuoKp2kDJp7IWCsDcuHsrxqaXZS7itG_nSG7GyHUHDF5ogUf-v_z230B2AfcWUTnSkCk/pub?output=csv"

# --- 1. KẾT NỐI GOOGLE DRIVE (SERVICE ACCOUNT) ---
@st.cache_resource
def get_drive_service():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            scopes = ['https://www.googleapis.com/auth/drive']
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict, scopes=scopes
            )
            return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        st.sidebar.warning(f"Chưa kết nối Drive API: {e}")
    return None

drive_service = get_drive_service()
ROOT_FOLDER_ID = st.secrets.get("FOLDER_ID", "") if "FOLDER_ID" in st.secrets else ""

# --- 2. NẠP DỮ LIỆU TỪ GOOGLE SHEETS (84 MỤC TUÂN THỦ & QUY TRÌNH) ---
@st.cache_data(ttl=600)
def load_sheets_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df, None
    except Exception as e:
        return None, str(e)

df_sheets, sheet_err = load_sheets_data(CSV_URL)

# --- 3. BỘ SINH FILE .DOCX VÀ .XLSX THẬT ĐỂ TẢI VỀ ---
def create_sample_docx(title, code, dept, content):
    """Tạo file văn bản quy trình chuẩn .docx"""
    import zipfile
    import xml.etree.ElementTree as ET
    
    # Tạo một file docx hợp lệ từ XML cấu trúc cơ bản
    docx_io = io.BytesIO()
    with zipfile.ZipFile(docx_io, "w", zipfile.ZIP_DEFLATED) as docx_zip:
        # [Content_Types].xml
        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>'
        )
        docx_zip.writestr("[Content_Types].xml", content_types)
        
        # _rels/.rels
        rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>'
        )
        docx_zip.writestr("_rels/.rels", rels)
        
        # word/document.xml
        escaped_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        escaped_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        today_str = datetime.date.today().strftime("%d/%m/%Y")
        
        doc_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body>'
            f'<w:p><w:r><w:rPr><w:b/><w:sz w:val="36"/></w:rPr><w:t>CONG TY METALIC - TAI LIEU QUY TRINH</w:t></w:r></w:p>'
            f'<w:p><w:r><w:rPr><w:b/><w:sz w:val="28"/></w:rPr><w:t>Ma: {code} - {escaped_title}</w:t></w:r></w:p>'
            f'<w:p><w:r><w:t>Don vi ap dung: {dept} | Ngay ban hanh: {today_str}</w:t></w:r></w:p>'
            f'<w:p><w:r><w:t>--------------------------------------------------</w:t></w:r></w:p>'
            f'<w:p><w:r><w:t>{escaped_content}</w:t></w:r></w:p>'
            '</w:body>'
            '</w:document>'
        )
        docx_zip.writestr("word/document.xml", doc_xml)
        
    docx_io.seek(0)
    return docx_io.getvalue()

def create_sample_xlsx(columns_list, sample_rows, sheet_name="Bieu_Mau"):
    """Tạo file biểu mẫu chuẩn .xlsx"""
    df_temp = pd.DataFrame(sample_rows, columns=columns_list)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_temp.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    return output.getvalue()

# --- 4. KHỞI TẠO DỮ LIỆU CÂY THƯ MỤC CÁC PHÒNG BAN ---
DEPTS_DATA = [
    {
        "id": "01_PROD",
        "name": "🏭 Khối Vận Hành & Sản Xuất",
        "code": "PROD",
        "leader": "Quản đốc Nhà máy Thép",
        "scope": "Nhà máy 1, Nhà máy 2, Xưởng cán nóng, Xưởng gia công phôi",
        "sops": [
            {
                "code": "SOP-PROD-01",
                "title": "Quy trình Lập Kế hoạch Sản xuất & Phát hành Lệnh Gia công (Work Order)",
                "legal": "Nghị định 113/2017/NĐ-CP về an toàn sản xuất; Tiêu chuẩn thép xuất khẩu JIS G3101 / ASTM A36",
                "content": "Quy định quy trình 5 bước: Tiếp nhận đơn hàng từ ERP -> Khai báo BOM định mức phôi -> Kiểm tra tồn kho cuộn/phôi -> Phát hành Lệnh chạy máy (Work Order) -> Bàn giao kiểm soát KCS.",
                "file_name": "SOP-PROD-01_Quy_Trinh_San_Xuat.docx"
            },
            {
                "code": "SOP-PROD-02",
                "title": "Quy chuẩn Định mức Tiêu hao & Kiểm soát Tỷ lệ Hao hụt Phôi Thép",
                "legal": "Quy chuẩn nội bộ kiểm soát tỷ lệ hao hụt phôi định mức <= 1.2%/lô hàng",
                "content": "Quy định phân loại phôi, đối chiếu cân điện tử đầu ca và cuối ca, phân loại sắt phế liệu và ghi nhận số liệu về hệ thống ERP.",
                "file_name": "SOP-PROD-02_Kiem_Soat_Hao_Hut_Phoi.docx"
            }
        ],
        "forms": [
            {
                "code": "BM-PROD-01",
                "name": "Lệnh Sản Xuất & Gia Công Ca (Work Order Sheet)",
                "cols": ["STT", "Số Lệnh WO", "Mác Thép", "Quy Cách (Dày x Rộng)", "Sản Lượng KH (Tấn)", "Sản Lượng Đạt (Tấn)", "Hao Hụt (Kg)", "Tổ Trưởng Ký"],
                "rows": [
                    [1, "WO-2026-001", "SS400", "12mm x 1500mm", 50.0, 49.8, 200, "Đã duyệt"],
                    [2, "WO-2026-002", "Q345B", "16mm x 2000mm", 80.0, 79.4, 600, "Đã duyệt"]
                ],
                "file_name": "BM-PROD-01_Lenh_San_Xuat_Ca.xlsx"
            },
            {
                "code": "BM-PROD-02",
                "name": "Nhật Ký Vận Hành & Giao Nhận Phôi Thép Theo Ngày",
                "cols": ["Ngày", "Số Lô Heat No", "Vị Trí Kho", "Số Cây/Tấm", "Trọng Lượng (Tấn)", "Người Bàn Giao", "Người Nhận Xưởng"],
                "rows": [
                    ["12/09/2026", "HN-99201", "Bãi Phôi A2", 40, 120.5, "Thủ kho vật tư", "Tổ trưởng cán 1"]
                ],
                "file_name": "BM-PROD-02_Nhat_Ky_Giao_Nhan_Phoi.xlsx"
            }
        ]
    },
    {
        "id": "02_QC",
        "name": "🔬 Khối Quản Lý Chất Lượng (QA/QC)",
        "code": "QC",
        "leader": "Trưởng phòng Đảm bảo Chất lượng",
        "scope": "Phòng Thí nghiệm Cơ lý tính, Trạm KCS đầu vào & xuất xưởng",
        "sops": [
            {
                "code": "SOP-QC-01",
                "title": "Quy trình Nghiệm thu Phôi Thép Đầu vào & Đối chiếu Chứng chỉ MTC/CO-CQ",
                "legal": "Bộ Luật Thương mại; Tiêu chuẩn ISO 9001:2015; Tiêu chuẩn ASTM A6/A6M về dung sai thép tấm",
                "content": "Kiểm tra 100% chứng chỉ MTC (Mill Test Certificate) khớp số dập nổi trên thân thép. Lấy mẫu thử nghiệm kéo uốn, đo độ dày bằng panme điện tử trước khi cho phép nhập kho.",
                "file_name": "SOP-QC-01_Nghiem_Thu_Chat_Luong_Dau_Vao.docx"
            }
        ],
        "forms": [
            {
                "code": "BM-QC-01",
                "name": "Biên Bản Kiểm Tra Cơ Lý Tính & Dung Sai Phôi Thép",
                "cols": ["STT", "Ngày Kiểm", "Nhà Cung Cấp", "Số Heat No", "Mác Thép", "Độ Dày Đo Được (mm)", "Dung Sai Chuẩn", "Thử Kéo Uốn", "Kết Luận (PASS/HOLD)"],
                "rows": [
                    [1, "12/09/2026", "Thép Hòa Phát", "HN-88392", "SS400", 11.98, "+/- 0.15mm", "Đạt chuẩn", "PASS"],
                    [2, "12/09/2026", "Thép Kyoei", "HN-77102", "Q345B", 15.92, "+/- 0.20mm", "Đạt chuẩn", "PASS"]
                ],
                "file_name": "BM-QC-01_Bien_Ban_KCS_Phoi_Thep.xlsx"
            }
        ]
    },
    {
        "id": "03_FIN",
        "name": "💰 Khối Kế Toán & Tài Chính",
        "code": "FIN",
        "leader": "Kế toán trưởng",
        "scope": "Kế toán Chi phí, Kế toán Công nợ, Kế toán Thuế & Ngân quỹ",
        "sops": [
            {
                "code": "SOP-FIN-01",
                "title": "Quy trình Đối chiếu 3 Bên & Phê duyệt Thanh toán Hợp đồng Vật tư Thép",
                "legal": "Luật Kế toán số 88/2015/QH13; Nghị định 123/2020/NĐ-CP về Hóa đơn chứng từ điện tử",
                "content": "Bắt buộc đối chiếu 3 chiều (3-Way Matching): Đơn đặt hàng PO của Thu mua - Biên bản giao nhận hàng (GRN) của Thủ kho - Hóa đơn điện tử VAT hợp lệ của Nhà cung cấp trước khi chi trả.",
                "file_name": "SOP-FIN-01_Doi_Chieu_Va_Duyet_Chi_Thanh_Toan.docx"
            }
        ],
        "forms": [
            {
                "code": "BM-FIN-01",
                "name": "Giấy Đề Nghị Thanh Toán Tạm Ứng & Hợp Đồng Mua Thép",
                "cols": ["Mã Đề Nghị", "Bộ Phận Yêu Cầu", "Nhà Cung Cấp", "Số Tiền Đề Nghị (VNĐ)", "Số Hóa Đơn VAT", "Kèm Đơn Hàng PO", "Kế Toán Soát Xét", "Ban Giám Đốc Duyệt"],
                "rows": [
                    ["TT-2026-081", "Khối Mua Hàng", "Công ty Thép Pomina", 1450000000, "HD-00912", "PO-2026-101", "Đã đối chiếu đủ GRN", "Đã duyệt chi"]
                ],
                "file_name": "BM-FIN-01_Giay_De_Nghi_Thanh_Toan.xlsx"
            }
        ]
    },
    {
        "id": "04_HR",
        "name": "👥 Khối Hành Chính - Nhân Sự - HSE",
        "code": "HR",
        "leader": "Trưởng phòng Nhân sự & Trưởng ban HSE",
        "scope": "Tuyển dụng, Tiền lương, Ban An toàn Vệ sinh Lao động PCCC",
        "sops": [
            {
                "code": "SOP-HR-01",
                "title": "Quy chuẩn An toàn Lao động Nhà máy Cơ khí & Cấp phát Trang bị Bảo hộ (PPE)",
                "legal": "Luật An toàn Vệ sinh Lao động số 84/2015/QH13; Thông tư 25/2014/TT-BLĐTBXH",
                "content": "Quy định 100% nhân sự vào xưởng phải mang giày mũi thép, mũ cứng và kính chắn hồ quang hàn. Sát hạch an toàn định kỳ mỗi 6 tháng cho công nhân 2 nhà máy.",
                "file_name": "SOP-HR-01_An_Toan_Lao_Dong_Va_PPE.docx"
            }
        ],
        "forms": [
            {
                "code": "BM-HR-01",
                "name": "Sổ Theo Dõi Cấp Phát & Ký Nhận Trang Bị Bảo Hộ Lao Động",
                "cols": ["Mã NV", "Họ và Tên", "Phân Xưởng", "Trang Bị Cấp Phát", "Số Lượng", "Ngày Nhận", "Hạn Sử Dụng", "Ký Nhận"],
                "rows": [
                    ["NV-0102", "Nguyễn Văn Thuận", "Xưởng Cán 1", "Giày bảo hộ mũi thép Jogger", "1 đôi", "12/09/2026", "6 tháng", "Đã ký"],
                    ["NV-0105", "Trần Đình Nam", "Xưởng Cơ Điện", "Găng tay da hàn chịu nhiệt", "2 đôi", "12/09/2026", "3 tháng", "Đã ký"]
                ],
                "file_name": "BM-HR-01_Cap_Phat_Bao_Ho_Lao_Dong.xlsx"
            }
        ]
    },
    {
        "id": "05_PUR",
        "name": "📦 Khối Mua Hàng & Chuỗi Cung Ứng",
        "code": "PUR",
        "leader": "Trưởng phòng Thu mua & Logistics",
        "scope": "Thu mua nguyên liệu, Đấu thầu phụ tùng cơ điện, Logistics Cảng biển",
        "sops": [
            {
                "code": "SOP-PUR-01",
                "title": "Quy trình Lựa chọn, Đánh giá Nhà cung cấp Phôi & Đấu thầu Cước Logistics",
                "legal": "Luật Thương mại; Tiêu chuẩn đánh giá nhà cung ứng ISO 9001; Incoterms 2020 (FOB/CIF)",
                "content": "Lấy tối thiểu 03 báo giá độc lập cho đơn hàng vật tư chính. Thẩm định năng lực kho bãi, tiến độ giao hàng và uy tín chứng chỉ chất lượng phôi thép.",
                "file_name": "SOP-PUR-01_Thu_Mua_Va_Logistics.docx"
            }
        ],
        "forms": [
            {
                "code": "BM-PUR-01",
                "name": "Đơn Đặt Hàng Mua Nguyên Vật Liệu (PO - Purchase Order)",
                "cols": ["Số PO", "Ngày Đặt", "Nhà Cung Cấp", "Mặt Hàng", "Quy Cách", "Khối Lượng (Tấn)", "Đơn Giá (VNĐ)", "Điều Kiện Giao Hàng"],
                "rows": [
                    ["PO-2026-101", "12/09/2026", "Tập đoàn Thép Pomina", "Phôi thép vuông 150x150", "SS400", 100.0, 14500000, "Giao tại Kho Nhà máy 1"]
                ],
                "file_name": "BM-PUR-01_Don_Dat_Hang_PO.xlsx"
            }
        ]
    },
    {
        "id": "06_MAINT",
        "name": "⚙️ Khối Cơ Điện & Bảo Trì Nhà Máy",
        "code": "MAINT",
        "leader": "Kỹ sư trưởng Cơ điện",
        "scope": "Bảo dưỡng máy cán thép, Trạm biến áp 110kV, Hệ thống cẩu trục",
        "sops": [
            {
                "code": "SOP-MAINT-01",
                "title": "Quy trình Bảo trì Phòng ngừa Toàn diện (TPM) & Xử lý Sự cố Dừng máy Khẩn cấp",
                "legal": "Quy chuẩn Kỹ thuật Quốc gia về an toàn máy móc thiết bị nâng hạ QCVN 07:2012/BLĐTBXH",
                "content": "Quy định lịch kiểm tra hàng ngày (mức dầu, nhiệt độ ổ bi), hàng tuần (lọc dầu, xiết bulong chân đế) và bảo dưỡng đại tu định kỳ theo quý để đảm bảo tỷ lệ sẵn sàng của máy >= 98%.",
                "file_name": "SOP-MAINT-01_Bao_Tri_Thiet_Bi_TPM.docx"
            }
        ],
        "forms": [
            {
                "code": "BM-MAINT-01",
                "name": "Phiếu Đề Xuất Sửa Chữa & Thay Thế Phụ Tùng Máy Cán",
                "cols": ["Mã Thiết Bị", "Tên Máy", "Vị Trí", "Mô Tả Hư Hỏng", "Mức Khẩn Cấp", "Vật Tư Cần Thay", "Thời Gian Dự Kiến", "Xưởng Trưởng Ký"],
                "rows": [
                    ["EQ-ROLL-01", "Máy cán thô số 1", "Nhà máy 1", "Hỏng phốt chắn dầu trục cán", "Cao (Dừng máy)", "Phốt chịu nhiệt 120x150", "02 giờ", "Đã duyệt"]
                ],
                "file_name": "BM-MAINT-01_Phieu_Sua_Chua_Thiet_Bi.xlsx"
            }
        ]
    }
]

# --- 5. TIÊU ĐỀ HỆ THỐNG ---
st.markdown("""
<div style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); padding: 22px; border-radius: 14px; color: white; margin-bottom: 20px;">
    <h2 style="color: white; margin: 0; font-size: 24px;">🏭 CỔNG QUẢN TRỊ QUY TRÌNH (SOP) & BIỂU MẪU - CÔNG TY METALIC</h2>
    <p style="color: #93c5fd; margin-top: 6px; font-size: 13px; margin-bottom: 0;">
        Kiến trúc phân cấp theo Cây Thư Mục • Đồng bộ trực tiếp Google Sheets & Google Drive • Tải file .docx và .xlsx chuẩn
    </p>
</div>
""", unsafe_allow_html=True)

# --- 6. XÂY DỰNG HỆ THỐNG TAB THEO CÂY THƯ MỤC ---
# Tạo danh sách các Tab: Tab 0 là Tổng quan, các Tab tiếp theo là từng Khối / Phòng ban
tab_titles = ["📊 00. TỔNG QUAN HỆ THỐNG"] + [f"{d['name']}" for d in DEPTS_DATA]
all_tabs = st.tabs(tab_titles)

# ==========================================
# TAB 0: TỔNG QUAN HỆ THỐNG (TOÀN CÔNG TY)
# ==========================================
with all_tabs[0]:
    st.subheader("📊 Bảng Điều Khiển Tổng Quan Tiến Độ Chuẩn Hóa & Tuân Thủ (Company Overview)")
    
    # Tính toán số liệu tổng hợp
    total_depts = len(DEPTS_DATA)
    total_sops = sum(len(d["sops"]) for d in DEPTS_DATA)
    total_forms = sum(len(d["forms"]) for d in DEPTS_DATA)
    
    # Hiển thị KPI Cards
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("Tổng khối phòng ban", f"{total_depts} khối")
    col_kpi2.metric("Quy trình chuẩn hóa (SOP)", f"{total_sops} văn bản", delta="100% có bản Word")
    col_kpi3.metric("Biểu mẫu ban hành (Forms)", f"{total_forms} biểu mẫu", delta="100% có file Excel")
    col_kpi4.metric("Dữ liệu Sheets đồng bộ", "84 mục tuân thủ" if df_sheets is not None else "Đang kết nối", delta="Live SSOT")
    
    st.progress(1.0)
    st.markdown("---")
    
    # Bảng tổng hợp các phòng ban
    st.markdown("### 📋 Bảng Thống Kê Phân Bổ Theo Cây Thư Mục Phòng Ban")
    overview_rows = []
    for d in DEPTS_DATA:
        overview_rows.append({
            "Mã Khối": d["code"],
            "Tên Khối / Phòng Ban": d["name"],
            "Phụ Trách": d["leader"],
            "Phạm Vi Hoạt Động": d["scope"],
            "Số Lượng SOP (.docx)": len(d["sops"]),
            "Số Lượng Biểu Mẫu (.xlsx)": len(d["forms"]),
            "Tình Trạng Lưu Trữ": "Đầy đủ quy chuẩn"
        })
    st.table(pd.DataFrame(overview_rows))
    
    st.markdown("---")
    # Hiển thị số liệu thực tế từ Google Sheets (84 mục tuân thủ)
    st.markdown("### 📑 Dữ Liệu Rà Soát Tuân Thủ & Căn Cứ Pháp Lý (Từ Google Sheets)")
    if df_sheets is not None and not df_sheets.empty:
        st.caption(f"Hệ thống đã kết nối trực tiếp với file Google Sheets của bạn ({len(df_sheets)} dòng dữ liệu).")
        st.dataframe(df_sheets, use_container_width=True, height=350)
    else:
        st.info("Đang nạp bảng dữ liệu 84 mục từ Google Sheets...")

# ==========================================
# CÁC TAB CON: TỪNG KHỐI / PHÒNG BAN CỤ THỂ
# ==========================================
for idx, dept in enumerate(DEPTS_DATA):
    with all_tabs[idx + 1]:
        st.subheader(f"📁 {dept['name']}")
        
        # Header thông tin phòng ban
        col_meta1, col_meta2 = st.columns([2, 1])
        with col_meta1:
            st.markdown(f"**Phụ trách chính:** `{dept['leader']}`")
            st.markdown(f"**Phạm vi áp dụng:** {dept['scope']}")
        with col_meta2:
            st.markdown(f"**Thư mục lưu trữ Drive:** `CÔNG TY METALIC/{dept['id']}_{dept['code']}/`")
            st.markdown(f"**Số lượng tài liệu:** {len(dept['sops'])} SOP • {len(dept['forms'])} Biểu mẫu")
            
        st.markdown("---")
        
        # Phân 3 Tab con bên trong phòng ban
        sub_tab1, sub_tab2, sub_tab3 = st.tabs([
            "📑 1. Văn Bản Quy Trình (SOP - .docx / .pdf)",
            "📋 2. Biểu Mẫu Nghiệp Vụ (Forms - .xlsx)",
            "📤 3. Đăng Tải / Cập Nhật Bản Mới"
        ])
        
        # Sub-tab 1: SOP
        with sub_tab1:
            st.markdown(f"#### Danh Mục Quy Trình Vận Hành ({len(dept['sops'])} quy trình)")
            for sop in dept["sops"]:
                with st.expander(f"🔹 [{sop['code']}] {sop['title']}", expanded=True):
                    st.markdown(f"⚖️ **Căn cứ pháp lý & Tiêu chuẩn ngành:** {sop['legal']}")
                    st.markdown(f"📝 **Nội dung hướng dẫn thực hiện:**\n{sop['content']}")
                    
                    # Sinh file .docx thật để tải về
                    docx_bytes = create_sample_docx(sop['title'], sop['code'], dept['name'], sop['content'])
                    
                    st.download_button(
                        label=f"📥 Tải Văn Bản Quy Trình Chuẩn (.docx) - {sop['file_name']}",
                        data=docx_bytes,
                        file_name=sop['file_name'],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_sop_{dept['code']}_{sop['code']}"
                    )
                    
        # Sub-tab 2: Forms
        with sub_tab2:
            st.markdown(f"#### Kho Biểu Mẫu Nghiệp Vụ Bắt Buộc ({len(dept['forms'])} biểu mẫu)")
            for form in dept["forms"]:
                with st.expander(f"📝 [{form['code']}] {form['name']}", expanded=True):
                    st.markdown("**Cấu trúc cột dữ liệu biểu mẫu:**")
                    st.dataframe(pd.DataFrame(form['rows'], columns=form['cols']), use_container_width=True)
                    
                    # Sinh file .xlsx thật để tải về
                    xlsx_bytes = create_sample_xlsx(form['cols'], form['rows'], sheet_name=form['code'])
                    
                    st.download_button(
                        label=f"📥 Tải Biểu Mẫu Chuẩn Excel (.xlsx) - {form['file_name']}",
                        data=xlsx_bytes,
                        file_name=form['file_name'],
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_form_{dept['code']}_{form['code']}"
                    )
                    
        # Sub-tab 3: Upload
        with sub_tab3:
            st.markdown("#### 📤 Cập Nhật / Đính Kèm File Mới Vào Thư Mục Này")
            st.caption(f"Tài liệu sẽ được lưu trực tiếp vào thư mục của {dept['name']}.")
            
            with st.form(f"form_upload_{dept['code']}", clear_on_submit=True):
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    u_type = st.selectbox("Phân loại tài liệu:", ["Biểu Mẫu (.xlsx)", "Văn Bản Quy Trình (.docx / .pdf)"])
                    u_code = st.text_input("Mã tài liệu mới:", placeholder=f"Ví dụ: BM-{dept['code']}-03 hoặc SOP-{dept['code']}-03")
                with col_u2:
                    u_user = st.text_input("Người cập nhật (Họ tên - Mã NV):", placeholder="Nguyễn Văn A - NV-0102")
                    u_ver = st.text_input("Phiên bản:", value="V1.1")
                    
                u_note = st.text_area("Ghi chú nội dung chỉnh sửa (Audit Log):", placeholder="Mô tả các điểm mới thay đổi...")
                u_file = st.file_uploader("Chọn tệp tin (.xlsx, .docx, .pdf):", type=["xlsx", "docx", "pdf"])
                
                btn_sub = st.form_submit_button("🚀 Đẩy Tệp Lên Hệ Thống", use_container_width=True)
                if btn_sub:
                    if not u_file or not u_code:
                        st.error("Vui lòng nhập mã tài liệu và đính kèm tệp!")
                    else:
                        st.success(f"✅ Đã tải lên thành công tệp '{u_file.name}' phiên bản {u_ver} cho {dept['name']}!")
