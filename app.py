import streamlit as st
import pandas as pd
import datetime
import json
import os
import shutil

# --- CẤU HÌNH TRANG (PAGE CONFIG) ---
st.set_page_config(
    page_title="Hệ Thống Quản Trị Quy Trình & Biểu Mẫu Phòng Ban",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THUẬT NGỮ & GIẢI THÍCH (GLOSSARY) ---
# SOP: Standard Operating Procedure - Quy trình thao tác chuẩn
# KPI: Key Performance Indicator - Chỉ số đo lường hiệu suất (tỷ lệ chuẩn hóa biểu mẫu & quy trình)
# RACI: Responsible, Accountable, Consulted, Informed - Ma trận phân định trách nhiệm
# Dynamic Directory Architecture: Kiến trúc cây thư mục động (tự nhận diện phòng ban theo folder)

ROOT_DIR = "HE_THONG_PHONG_BAN"

# Danh sách phòng ban mẫu mặc định nếu thư mục trống
DEFAULT_DEPTS = [
    "01_Khoi_San_Xuat_Gia_Cong_Thep",
    "02_Khoi_Quan_Ly_Chat_Luong_QA_QC",
    "03_Khoi_Ke_Toan_Tai_Chinh",
    "04_Khoi_Hanh_Chinh_Nhan_Su_HSE",
    "05_Khoi_Mua_Hang_Chuoi_Cung_Ung",
    "06_Khoi_Co_Dien_Bao_Tri_Nha_May"
]

def init_folder_structure():
    """Khởi tạo cấu trúc thư mục gốc và thư mục con chuẩn."""
    if not os.path.exists(ROOT_DIR):
        os.makedirs(ROOT_DIR, exist_ok=True)
    for dept in DEFAULT_DEPTS:
        dept_path = os.path.join(ROOT_DIR, dept)
        os.makedirs(os.path.join(dept_path, "Quy_Trinh_SOP"), exist_ok=True)
        os.makedirs(os.path.join(dept_path, "Bieu_Mau_Form"), exist_ok=True)

init_folder_structure()

def get_departments():
    """Tự động quét toàn bộ thư mục phòng ban hiện có trong thư mục tổng."""
    if not os.path.exists(ROOT_DIR):
        return []
    items = [d for d in os.listdir(ROOT_DIR) if os.path.isdir(os.path.join(ROOT_DIR, d))]
    return sorted(items)

def get_dept_files(dept_name, subfolder):
    """Lấy danh sách các tệp tin trong thư mục Quy_Trinh_SOP hoặc Bieu_Mau_Form."""
    target_path = os.path.join(ROOT_DIR, dept_name, subfolder)
    if not os.path.exists(target_path):
        return []
    return [f for f in os.listdir(target_path) if not f.startswith(".")]

def get_metadata(dept_name):
    """Đọc file metadata mô tả quy trình/biểu mẫu của phòng ban."""
    meta_path = os.path.join(ROOT_DIR, dept_name, "metadata.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_metadata(dept_name, data):
    """Ghi dữ liệu mô tả quy trình/biểu mẫu của phòng ban."""
    meta_path = os.path.join(ROOT_DIR, dept_name, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Header giao diện
st.markdown("""
<div style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); padding: 22px; border-radius: 14px; color: white; margin-bottom: 20px;">
    <h2 style="color: white; margin: 0; font-size: 24px;">🗂️ HỆ THỐNG QUẢN TRỊ QUY TRÌNH & BIỂU MẪU THEO CÂY THƯ MỤC NỘI BỘ</h2>
    <p style="color: #93c5fd; margin-top: 6px; font-size: 13px; margin-bottom: 0;">
        Kiến trúc thư mục tự động: Tạo thư mục mới là hệ thống tự nhận diện phòng ban • Tách biệt Quy trình (SOP) và Biểu mẫu (Forms)
    </p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR: ĐIỀU HƯỚNG & QUẢN TRỊ PHÒNG BAN ---
with st.sidebar:
    st.header("🗂️ Cây Thư Mục Phòng Ban")
    menu = st.radio(
        "Chức năng làm việc:",
        ["📖 Tra Cứu & Tải Tài Liệu", "📤 Cập Nhật Quy Trình & Biểu Mẫu", "➕ Quản Lý & Tạo Phòng Ban Mới", "📊 Dashboard Thống Kê (KPI)"],
        index=0
    )
    st.markdown("---")
    
    depts = get_departments()
    dept_labels = {d: d.replace("_", " ") for d in depts}
    
    selected_dept = st.selectbox(
        "Chọn phòng ban thao tác:",
        depts,
        format_func=lambda x: dept_labels.get(x, x)
    )

# --- CHỨC NĂNG 1: TRA CỨU & TẢI TÀI LIỆU ---
if menu == "📖 Tra Cứu & Tải Tài Liệu":
    st.subheader(f"📁 Phòng Ban: {selected_dept.replace('_', ' ')}")
    meta = get_metadata(selected_dept)
    
    # Hiển thị thông tin tổng quan phòng ban
    col_info1, col_info2 = st.columns([2, 1])
    with col_info1:
        st.markdown(f"**Chức năng / Nhiệm vụ cốt lõi:**\n{meta.get('description', 'Chưa cập nhật mô tả chức năng.')}")
        st.markdown(f"**Trưởng bộ phận phụ trách:** `{meta.get('leader', 'Chưa chỉ định')}`")
    with col_info2:
        st.markdown(f"**Vị trí lưu trữ vật lý:**\n`{ROOT_DIR}/{selected_dept}/`")
        st.markdown(f"**Cập nhật lần cuối:** `{meta.get('last_updated', 'N/A')}`")

    st.markdown("---")
    
    tab_sop, tab_form = st.tabs(["📑 1. Quy Trình Vận Hành (SOP / Hướng Dẫn)", "📋 2. Kho Biểu Mẫu Nghiệp Vụ (Templates / Forms)"])
    
    # Tab Quy trình
    with tab_sop:
        sop_files = get_dept_files(selected_dept, "Quy_Trinh_SOP")
        if not sop_files:
            st.info("Chưa có văn bản quy trình nào trong thư mục `Quy_Trinh_SOP/` của phòng ban này.")
        else:
            st.markdown(f"**Danh sách gồm {len(sop_files)} tài liệu quy trình:**")
            for f in sop_files:
                fpath = os.path.join(ROOT_DIR, selected_dept, "Quy_Trinh_SOP", f)
                fsize = round(os.path.getsize(fpath) / 1024, 2)
                fdate = datetime.datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%d/%m/%Y %H:%M')
                
                c_l, c_r = st.columns([3, 1])
                with c_l:
                    st.markdown(f"📄 **{f}**")
                    st.caption(f"Dung lượng: {fsize} KB • Cập nhật: {fdate}")
                with c_r:
                    with open(fpath, "rb") as fp:
                        st.download_button(
                            label=f"📥 Tải Quy Trình",
                            data=fp.read(),
                            file_name=f,
                            key=f"dl_sop_{selected_dept}_{f}",
                            use_container_width=True
                        )
                st.markdown("---")

    # Tab Biểu mẫu
    with tab_form:
        form_files = get_dept_files(selected_dept, "Bieu_Mau_Form")
        if not form_files:
            st.info("Chưa có biểu mẫu nào trong thư mục `Bieu_Mau_Form/` của phòng ban này.")
        else:
            st.markdown(f"**Danh sách gồm {len(form_files)} biểu mẫu chuẩn:**")
            for f in form_files:
                fpath = os.path.join(ROOT_DIR, selected_dept, "Bieu_Mau_Form", f)
                fsize = round(os.path.getsize(fpath) / 1024, 2)
                fdate = datetime.datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%d/%m/%Y %H:%M')
                
                c_l, c_r = st.columns([3, 1])
                with c_l:
                    st.markdown(f"📝 **{f}**")
                    st.caption(f"Dung lượng: {fsize} KB • Cập nhật: {fdate}")
                with c_r:
                    with open(fpath, "rb") as fp:
                        st.download_button(
                            label=f"📥 Tải Biểu Mẫu",
                            data=fp.read(),
                            file_name=f,
                            key=f"dl_form_{selected_dept}_{f}",
                            use_container_width=True
                        )
                st.markdown("---")

# --- CHỨC NĂNG 2: CẬP NHẬT QUY TRÌNH & BIỂU MẪU (UPLOAD) ---
elif menu == "📤 Cập Nhật Quy Trình & Biểu Mẫu":
    st.subheader(f"📤 Cập Nhật Tài Liệu Vào Thư Mục: {selected_dept.replace('_', ' ')}")
    st.caption(f"Đường dẫn thư mục đích: `{ROOT_DIR}/{selected_dept}/`")
    
    with st.form("upload_doc_form", clear_on_submit=True):
        target_sub = st.radio(
            "Chọn loại tài liệu cần lưu trữ:",
            ["Bieu_Mau_Form (Biểu mẫu, Bảng tính, Phiếu đề xuất)", "Quy_Trinh_SOP (Quy trình chuẩn, Hướng dẫn công việc)"],
            index=0
        )
        subfolder_name = target_sub.split(" ")[0]
        
        uploader_name = st.text_input("Người cập nhật (Họ tên - Chức danh):", placeholder="Nguyễn Văn A - Trưởng bộ phận")
        doc_note = st.text_area("Mục đích / Ghi chú nội dung thay đổi của phiên bản:", placeholder="Thay đổi biểu mẫu theo quy chuẩn ISO/ERP...")
        
        uploaded_file = st.file_uploader(
            "Chọn tệp tin (.xlsx, .xls, .docx, .doc, .pdf, .csv):",
            type=["xlsx", "xls", "docx", "doc", "pdf", "csv"]
        )
        
        btn_upload = st.form_submit_button("🚀 Lưu Tệp Vào Thư Mục Phòng Ban", use_container_width=True)
        
        if btn_upload:
            if not uploaded_file:
                st.error("Vui lòng đính kèm tệp tin!")
            else:
                target_folder = os.path.join(ROOT_DIR, selected_dept, subfolder_name)
                os.makedirs(target_folder, exist_ok=True)
                
                # Lưu tệp tin
                dest_file_path = os.path.join(target_folder, uploaded_file.name)
                with open(dest_file_path, "wb") as f_out:
                    f_out.write(uploaded_file.getbuffer())
                
                # Cập nhật metadata
                meta = get_metadata(selected_dept)
                meta["last_updated"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                if "logs" not in meta:
                    meta["logs"] = []
                meta["logs"].append({
                    "file": uploaded_file.name,
                    "type": subfolder_name,
                    "uploader": uploader_name,
                    "note": doc_note,
                    "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                })
                save_metadata(selected_dept, meta)
                
                st.success(f"✅ Đã lưu tệp '{uploaded_file.name}' vào thư mục `{ROOT_DIR}/{selected_dept}/{subfolder_name}/`!")
                st.rerun()

# --- CHỨC NĂNG 3: QUẢN LÝ & TẠO PHÒNG BAN MỚI ---
elif menu == "➕ Quản Lý & Tạo Phòng Ban Mới":
    st.subheader("➕ Khởi Tạo Thư Mục Phòng Ban Mới")
    st.caption("Khi công ty thành lập bộ phận mới, chỉ cần khai báo tên tại đây. Hệ thống sẽ tự động khởi tạo toàn bộ cấu trúc thư mục con và tệp dữ liệu tương ứng.")
    
    with st.form("create_dept_form", clear_on_submit=True):
        new_dept_code = st.text_input("Mã/Tiền tố thư mục (Ví dụ: 07_Khoi_Kinh_Doanh_Xuat_Khau):", placeholder="XX_Ten_Phong_Ban_Khong_Dau")
        new_dept_leader = st.text_input("Trưởng phòng / Người quản lý:", placeholder="Trần Văn B")
        new_dept_desc = st.text_area("Chức năng & Trách nhiệm phòng ban:", placeholder="Phụ trách quản lý đơn hàng xuất khẩu, hợp đồng thương mại...")
        
        btn_create = st.form_submit_button("📁 Tạo Thư Mục Phòng Ban Ngay", use_container_width=True)
        if btn_create:
            if not new_dept_code.strip():
                st.error("Vui lòng nhập tên thư mục phòng ban!")
            else:
                safe_folder_name = new_dept_code.strip().replace(" ", "_")
                new_dept_path = os.path.join(ROOT_DIR, safe_folder_name)
                
                if os.path.exists(new_dept_path):
                    st.warning("⚠️ Thư mục phòng ban này đã tồn tại trên hệ thống!")
                else:
                    os.makedirs(os.path.join(new_dept_path, "Quy_Trinh_SOP"), exist_ok=True)
                    os.makedirs(os.path.join(new_dept_path, "Bieu_Mau_Form"), exist_ok=True)
                    
                    save_metadata(safe_folder_name, {
                        "name": safe_folder_name.replace("_", " "),
                        "leader": new_dept_leader,
                        "description": new_dept_desc,
                        "created_at": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "last_updated": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "logs": []
                    })
                    st.success(f"🎉 Khởi tạo thành công thư mục: `{new_dept_path}`!")
                    st.rerun()

# --- CHỨC NĂNG 4: DASHBOARD THỐNG KÊ (KPI) ---
else:
    st.subheader("📊 Báo Cáo Đo Lường Quy Trình & Biểu Mẫu Toàn Công Ty (KPI Dashboard)")
    
    all_depts = get_departments()
    total_depts = len(all_depts)
    
    table_stats = []
    total_sops = 0
    total_forms = 0
    
    for d in all_depts:
        sops = get_dept_files(d, "Quy_Trinh_SOP")
        forms = get_dept_files(d, "Bieu_Mau_Form")
        meta = get_metadata(d)
        
        n_sop = len(sops)
        n_form = len(forms)
        total_sops += n_sop
        total_forms += n_form
        
        table_stats.append({
            "Mã / Thư Mục Phòng Ban": d,
            "Tên Phòng Ban": d.replace("_", " "),
            "Số Lượng Quy Trình (SOP)": n_sop,
            "Số Lượng Biểu Mẫu (Forms)": n_form,
            "Trạng Thái Số Hóa": "Đạt chuẩn" if (n_sop > 0 and n_form > 0) else "Cần bổ sung",
            "Cập Nhật Lần Cuối": meta.get("last_updated", "N/A")
        })
        
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng số phòng ban", f"{total_depts} bộ phận")
    k2.metric("Tổng số quy trình (SOP)", f"{total_sops} tài liệu")
    k3.metric("Tổng số biểu mẫu (Forms)", f"{total_forms} file")
    pct_ready = int(len([x for x in table_stats if x["Trạng Thái Số Hóa"] == "Đạt chuẩn"]) / total_depts * 100) if total_depts > 0 else 0
    k4.metric("Tỷ lệ phòng ban chuẩn hóa", f"{pct_ready}%")
    
    st.progress(pct_ready / 100.0)
    st.markdown("---")
    
    st.dataframe(pd.DataFrame(table_stats), use_container_width=True, hide_index=True)
