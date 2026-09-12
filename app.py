import streamlit as st
import pandas as pd
import datetime
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

# --- CẤU HÌNH TRANG (PAGE CONFIG) ---
st.set_page_config(
    page_title="Hệ Thống Quản Trị Quy Trình & Biểu Mẫu - METALIC",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THUẬT NGỮ & GIẢI THÍCH (GLOSSARY) ---
# SOP: Standard Operating Procedure - Quy trình thao tác chuẩn
# Service Account: Tài khoản dịch vụ kết nối ngầm an toàn giữa Streamlit và Google Drive
# Folder ID: Mã định danh duy nhất của thư mục gốc CONG_TY_METALIC trên Google Drive
# Audit Trail: Nhật ký kiểm toán ghi nhận mọi lượt tải lên hoặc cập nhật biểu mẫu

# --- KẾT NỐI GOOGLE DRIVE QUA SECRETS ---
@st.cache_resource
def get_drive_service():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = ['https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=scopes
        )
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        st.error(f"⚠️ Lỗi xác thực Google Drive API: {e}")
        return None

drive_service = get_drive_service()
ROOT_FOLDER_ID = st.secrets.get("FOLDER_ID", "")

# --- HÀM TƯƠNG TÁC GOOGLE DRIVE ---
def list_subfolders(parent_id):
    """Lấy danh sách các thư mục con trực tiếp."""
    if not drive_service:
        return []
    query = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    try:
        results = drive_service.files().list(
            q=query,
            fields="files(id, name)",
            orderBy="name"
        ).execute()
        return results.get('files', [])
    except Exception as e:
        st.error(f"Lỗi đọc thư mục con: {e}")
        return []

def list_files_in_folder(folder_id):
    """Lấy danh sách các tệp tin trong thư mục."""
    if not drive_service:
        return []
    query = f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
    try:
        results = drive_service.files().list(
            q=query,
            fields="files(id, name, size, modifiedTime, webViewLink, mimeType)",
            orderBy="name"
        ).execute()
        return results.get('files', [])
    except Exception as e:
        st.error(f"Lỗi đọc tệp tin: {e}")
        return []

def download_drive_file(file_id):
    """Tải nội dung tệp tin từ Google Drive."""
    try:
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read()
    except Exception as e:
        st.error(f"Lỗi tải file: {e}")
        return None

def upload_file_to_drive(folder_id, file_name, file_bytes, mime_type="application/octet-stream"):
    """Tải tệp tin lên thư mục Google Drive tương ứng."""
    try:
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type, resumable=True)
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
        return file
    except Exception as e:
        st.error(f"Lỗi tải file lên Drive: {e}")
        return None

# --- GIAO DIỆN HEADER ---
st.markdown("""
<div style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); padding: 22px; border-radius: 14px; color: white; margin-bottom: 20px;">
    <h2 style="color: white; margin: 0; font-size: 24px;">🏭 HỆ THỐNG QUẢN TRỊ QUY TRÌNH & BIỂU MẪU - CÔNG TY METALIC</h2>
    <p style="color: #93c5fd; margin-top: 6px; font-size: 13px; margin-bottom: 0;">
        Đồng bộ trực tiếp 2 chiều với Google Drive • Phân cấp Khối / Phòng ban • Lưu vết kiểm toán phiên bản (Audit Trail)
    </p>
</div>
""", unsafe_allow_html=True)

if not ROOT_FOLDER_ID:
    st.error("Chưa cấu hình FOLDER_ID trong Streamlit Secrets.")
    st.stop()

# --- NẠP DANH SÁCH KHỐI PHÒNG BAN TỪ GOOGLE DRIVE ---
with st.spinner("Đang đồng bộ dữ liệu từ Google Drive..."):
    dept_folders = list_subfolders(ROOT_FOLDER_ID)

if not dept_folders:
    st.warning("⚠️ Không tìm thấy thư mục con nào trong thư mục CÔNG TY METALIC trên Google Drive.")
    st.info("Vui lòng kiểm tra: Bạn đã chia sẻ quyền 'Người chỉnh sửa (Editor)' cho email Service Account chưa?")
    st.stop()

# --- SIDEBAR ĐIỀU HƯỚNG ---
with st.sidebar:
    st.header("🗂️ Danh Mục Phòng Ban")
    menu = st.radio(
        "Chức năng thao tác:",
        ["📖 Tra Cứu Quy Trình & Biểu Mẫu", "📤 Tải Lên / Cập Nhật Bản Mới", "📊 Thống Kê Chuẩn Hóa (KPI)"],
        index=0
    )
    st.markdown("---")
    
    dept_options = {d['name']: d['id'] for d in dept_folders if not d['name'].startswith("00_")}
    selected_dept_name = st.selectbox("Chọn Khối / Phòng ban:", list(dept_options.keys()))
    selected_dept_id = dept_options[selected_dept_name]
    
    st.markdown("---")
    if st.button("🔄 Làm mới dữ liệu từ Drive", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# --- LẤY THƯ MỤC CON: QUY_TRINH_SOP VÀ BIEU_MAU_FORM ---
sub_folders = list_subfolders(selected_dept_id)
sop_folder = next((f for f in sub_folders if "quy_trinh" in f['name'].lower() or "sop" in f['name'].lower()), None)
form_folder = next((f for f in sub_folders if "bieu_mau" in f['name'].lower() or "form" in f['name'].lower()), None)

# --- CHỨC NĂNG 1: TRA CỨU QUY TRÌNH & BIỂU MẪU ---
if menu == "📖 Tra Cứu Quy Trình & Biểu Mẫu":
    st.subheader(f"📁 Khối / Phòng Ban: {selected_dept_name.replace('_', ' ')}")
    st.caption("Tra cứu văn bản hướng dẫn nghiệp vụ và tải các biểu mẫu bảng tính thực tế đang lưu hành.")
    
    tab1, tab2 = st.tabs(["📑 1. Quy Trình Vận Hành (SOP)", "📋 2. Biểu Mẫu Nghiệp Vụ (Forms)"])
    
    with tab1:
        if not sop_folder:
            st.info("Chưa có thư mục `Quy_Trinh_SOP` trong khối này trên Google Drive.")
        else:
            files = list_files_in_folder(sop_folder['id'])
            if not files:
                st.info("Chưa có tệp quy trình nào được lưu trữ.")
            else:
                for f in files:
                    c_a, c_b = st.columns([3, 1])
                    with c_a:
                        st.markdown(f"📄 **{f['name']}**")
                        mod_time = f.get('modifiedTime', '')[:10]
                        st.caption(f"Cập nhật trên Drive: {mod_time}")
                    with c_b:
                        file_bytes = download_drive_file(f['id'])
                        if file_bytes:
                            st.download_button(
                                label="📥 Tải Về",
                                data=file_bytes,
                                file_name=f['name'],
                                key=f"dl_sop_{f['id']}",
                                use_container_width=True
                            )
                    st.markdown("---")
                    
    with tab2:
        if not form_folder:
            st.info("Chưa có thư mục `Bieu_Mau_Form` trong khối này trên Google Drive.")
        else:
            files = list_files_in_folder(form_folder['id'])
            if not files:
                st.info("Chưa có biểu mẫu nào được lưu trữ.")
            else:
                for f in files:
                    c_a, c_b = st.columns([3, 1])
                    with c_a:
                        st.markdown(f"📝 **{f['name']}**")
                        mod_time = f.get('modifiedTime', '')[:10]
                        st.caption(f"Cập nhật trên Drive: {mod_time}")
                    with c_b:
                        file_bytes = download_drive_file(f['id'])
                        if file_bytes:
                            st.download_button(
                                label="📥 Tải Biểu Mẫu",
                                data=file_bytes,
                                file_name=f['name'],
                                key=f"dl_form_{f['id']}",
                                use_container_width=True
                            )
                    st.markdown("---")

# --- CHỨC NĂNG 2: TẢI LÊN / CẬP NHẬT BẢN MỚI ---
elif menu == "📤 Tải Lên / Cập Nhật Bản Mới":
    st.subheader(f"📤 Đăng Tải Tài Liệu Vào: {selected_dept_name.replace('_', ' ')}")
    st.caption("File tải lên sẽ được chuyển trực tiếp vào đúng thư mục Google Drive của công ty.")
    
    with st.form("form_upload_gdrive", clear_on_submit=True):
        doc_type = st.radio(
            "Loại tài liệu:",
            ["Biểu Mẫu Nghiệp Vụ (Lưu vào Bieu_Mau_Form)", "Quy Trình Chuẩn (Lưu vào Quy_Trinh_SOP)"],
            index=0
        )
        target_folder = form_folder if "Biểu Mẫu" in doc_type else sop_folder
        
        uploader_name = st.text_input("Người cập nhật (Họ tên - Mã nhân viên):", placeholder="Nguyễn Văn A - NV-0102")
        version_tag = st.text_input("Phiên bản cập nhật (Ví dụ: V1.1, V2.0):", value="V1.0")
        change_note = st.text_area("Ghi chú nội dung thay đổi:", placeholder="Bổ sung cột quy chuẩn phôi xuất khẩu...")
        
        uploaded_file = st.file_uploader("Chọn file (.xlsx, .docx, .pdf, .csv):", type=["xlsx", "xls", "docx", "doc", "pdf", "csv"])
        btn_upload = st.form_submit_button("🚀 Đẩy Lên Google Drive Ngay", use_container_width=True)
        
        if btn_upload:
            if not target_folder:
                st.error("Không tìm thấy thư mục đích trên Google Drive để lưu tệp!")
            elif not uploaded_file:
                st.error("Vui lòng đính kèm tệp tin!")
            else:
                with st.spinner("Đang tải tệp lên Google Drive..."):
                    bytes_data = uploaded_file.getvalue()
                    new_fname = f"{version_tag}_{uploaded_file.name}"
                    res = upload_file_to_drive(target_folder['id'], new_fname, bytes_data, uploaded_file.type)
                    if res:
                        st.success(f"🎉 Đã lưu thành công tệp '{new_fname}' vào Google Drive!")
                        st.rerun()

# --- CHỨC NĂNG 3: BÁO CÁO THỐNG KÊ (KPI) ---
else:
    st.subheader("📊 Tổng Quan Tiến Độ Số Hóa Tài Liệu Trên Google Drive (KPI)")
    
    kpi_data = []
    total_sops = 0
    total_forms = 0
    
    for d_name, d_id in dept_options.items():
        s_folders = list_subfolders(d_id)
        s_sop = next((f for f in s_folders if "quy_trinh" in f['name'].lower() or "sop" in f['name'].lower()), None)
        s_form = next((f for f in s_folders if "bieu_mau" in f['name'].lower() or "form" in f['name'].lower()), None)
        
        count_sop = len(list_files_in_folder(s_sop['id'])) if s_sop else 0
        count_form = len(list_files_in_folder(s_form['id'])) if s_form else 0
        
        total_sops += count_sop
        total_forms += count_form
        
        kpi_data.append({
            "Khối / Phòng Ban": d_name.replace("_", " "),
            "Số Lượng SOP": count_sop,
            "Số Lượng Biểu Mẫu": count_form,
            "Đánh Giá": "Đạt chuẩn" if (count_sop > 0 and count_form > 0) else "Cần bổ sung"
        })
        
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng khối phòng ban", f"{len(dept_options)} khối")
    k2.metric("Tổng quy trình (SOP)", f"{total_sops} văn bản")
    k3.metric("Tổng biểu mẫu (Forms)", f"{total_forms} file")
    pct_ready = int(len([x for x in kpi_data if x["Đánh Giá"] == "Đạt chuẩn"]) / len(dept_options) * 100) if dept_options else 0
    k4.metric("Tỷ lệ chuẩn hóa", f"{pct_ready}%")
    
    st.progress(pct_ready / 100.0)
    st.markdown("---")
    st.table(pd.DataFrame(kpi_data))
