import streamlit as st
import pandas as pd
import datetime
import json
import os

# --- 1. CẤU HÌNH TRANG (PAGE CONFIG) ---
st.set_page_config(
    page_title="Sổ Tay Tuân Thủ & Cổng Biểu Mẫu Nội Bộ",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THUẬT NGỮ & GIẢI THÍCH (GLOSSARY) ---
# SOP: Standard Operating Procedure - Quy trình thao tác chuẩn quy định chi tiết các bước xử lý
# KPI: Key Performance Indicator - Chỉ số đo lường hiệu suất (ở đây là tỷ lệ tuân thủ %)
# RACI: Responsible, Accountable, Consulted, Informed - Ma trận phân công trách nhiệm
# Single Source of Truth (SSOT): Nguồn dữ liệu gốc duy nhất (file Google Sheets)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7vrN3GLRabuoKp2kDJp7IWCsDcuHsrxqaXZS7itG_nSG7GyHUHDF5ogUf-v_z230B2AfcWUTnSkCk/pub?output=csv"
UPLOAD_DIR = "uploaded_forms"
METADATA_FILE = os.path.join(UPLOAD_DIR, "forms_registry.json")
CUSTOM_UPDATES_FILE = os.path.join(UPLOAD_DIR, "item_updates.json")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# Khởi tạo tệp lưu trữ nếu chưa có
if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False)

if not os.path.exists(CUSTOM_UPDATES_FILE):
    with open(CUSTOM_UPDATES_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False)

def get_uploaded_forms():
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_uploaded_form(entry):
    forms = get_uploaded_forms()
    forms.append(entry)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(forms, f, ensure_ascii=False, indent=2)

def get_item_updates():
    try:
        with open(CUSTOM_UPDATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_item_update(item_id, update_dict):
    updates = get_item_updates()
    if item_id not in updates:
        updates[item_id] = {}
    updates[item_id].update(update_dict)
    with open(CUSTOM_UPDATES_FILE, "w", encoding="utf-8") as f:
        json.dump(updates, f, ensure_ascii=False, indent=2)

# --- 2. NẠP DỮ LIỆU THỜI GIAN THỰC TỪ GOOGLE SHEETS ---
@st.cache_data(ttl=300)
def load_data_from_sheets(url):
    try:
        df = pd.read_csv(url)
        df.columns = [str(c).strip() for c in df.columns]
        return df, None
    except Exception as e:
        return None, str(e)

df_raw, error_msg = load_data_from_sheets(CSV_URL)

# Header giao diện
st.markdown("""
<div style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); padding: 22px; border-radius: 14px; color: white; margin-bottom: 20px;">
    <h2 style="color: white; margin: 0; font-size: 24px;">🏢 SỔ TAY TUÂN THỦ QUY TRÌNH & KHO BIỂU MẪU PHÒNG BAN</h2>
    <p style="color: #93c5fd; margin-top: 6px; font-size: 13px; margin-bottom: 0;">
        Dữ liệu gốc đồng bộ trực tiếp từ Google Sheets • Phân loại chuyên sâu theo từng phòng ban • Upload và đính kèm biểu mẫu cho từng mục quy trình
    </p>
</div>
""", unsafe_allow_html=True)

if error_msg:
    st.error(f"⚠️ Không thể nạp dữ liệu từ Google Sheets: {error_msg}")
    st.info("Vui lòng kiểm tra lại quyền truy cập hoặc kết nối mạng.")
    st.stop()

if df_raw is None or df_raw.empty:
    st.warning("Bảng tính hiện chưa có dữ liệu.")
    st.stop()

df = df_raw.copy()
if "_id" not in df.columns:
    df["_id"] = [f"item_{i+1}" for i in range(len(df))]

# Tự động nhận diện các cột chính từ Google Sheets
cols = list(df.columns)
dept_col = next((c for c in cols if any(k in c.lower() for k in ["phòng ban", "bộ phận", "phân loại", "chủ đề", "nhóm", "lĩnh vực", "category"])), None)
risk_col = next((c for c in cols if any(k in c.lower() for k in ["rủi ro", "risk", "mức độ"])), None)
legal_col = next((c for c in cols if any(k in c.lower() for k in ["pháp lý", "căn cứ", "nghị định", "luật", "thông tư", "quy định"])), None)
title_col = next((c for c in cols if any(k in c.lower() for k in ["nội dung", "mục", "tiêu đề", "hạng mục", "tên", "yêu cầu"])), cols[0])

# Đọc các cập nhật tuân thủ đã lưu
item_updates = get_item_updates()
uploaded_forms = get_uploaded_forms()

# Đồng bộ trạng thái vào dataframe
df["Trạng thái"] = df["_id"].apply(lambda x: item_updates.get(x, {}).get("status", "Chưa hoàn tất"))
df["Ghi chú nội bộ"] = df["_id"].apply(lambda x: item_updates.get(x, {}).get("note", ""))

# --- 3. THANH ĐIỀU HƯỚNG BÊN TRÁI (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Quản Trị Hệ Thống")
    
    view_mode = st.radio(
        "Chế độ làm việc:",
        ["📖 Sổ Tay Quy Trình Từng Phòng Ban", "📤 Tải Lên & Kho Biểu Mẫu Tập Trung", "📊 Bảng Đo Lường Tuân Thủ (KPI)"],
        index=0
    )
    
    st.markdown("---")
    st.subheader("🔍 Lọc Phòng Ban & Nghiệp Vụ")
    
    selected_dept = "Tất cả phòng ban"
    if dept_col:
        depts_list = ["Tất cả phòng ban"] + sorted([str(x) for x in df[dept_col].dropna().unique() if str(x).strip()])
        selected_dept = st.selectbox(f"Chọn phòng ban ({dept_col}):", depts_list)
        
    selected_risk = "Tất cả mức độ"
    if risk_col:
        risks_list = ["Tất cả mức độ"] + sorted([str(x) for x in df[risk_col].dropna().unique() if str(x).strip()])
        selected_risk = st.selectbox("Mức độ rủi ro:", risks_list)
        
    search_text = st.text_input("Tìm kiếm từ khóa:", "")
    
    st.markdown("---")
    if st.button("🔄 Đồng bộ lại từ Google Sheets", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Lọc dữ liệu
filtered_df = df.copy()
if dept_col and selected_dept != "Tất cả phòng ban":
    filtered_df = filtered_df[filtered_df[dept_col].astype(str) == selected_dept]
if risk_col and selected_risk != "Tất cả mức độ":
    filtered_df = filtered_df[filtered_df[risk_col].astype(str) == selected_risk]
if search_text.strip():
    kw = search_text.strip().lower()
    mask = filtered_df.astype(str).apply(lambda row: row.str.lower().str.contains(kw, regex=False).any(), axis=1)
    filtered_df = filtered_df[mask]

# --- 4. CHỨC NĂNG 1: SỔ TAY QUY TRÌNH & CẬP NHẬT TỪNG MỤC ---
if view_mode == "📖 Sổ Tay Quy Trình Từng Phòng Ban":
    st.subheader(f"📑 Danh Mục Quy Trình Tuân Thủ Theo Phòng Ban (Hiển thị: {len(filtered_df)} / {len(df)} mục)")
    st.caption("Nhân viên chọn từng mục quy trình để xem căn cứ, đính kèm biểu mẫu sử dụng và cập nhật tiến độ thực hiện.")
    
    # Nhóm theo phòng ban nếu có cột phòng ban
    if dept_col and selected_dept == "Tất cả phòng ban":
        dept_groups = filtered_df[dept_col].dropna().unique()
    else:
        dept_groups = [selected_dept]
        
    for dept_name in dept_groups:
        sub_df = filtered_df if selected_dept != "Tất cả phòng ban" else filtered_df[filtered_df[dept_col] == dept_name]
        
        st.markdown(f"### 📁 Khối / Phòng Ban: {dept_name} ({len(sub_df)} quy trình)")
        
        for idx, row in sub_df.iterrows():
            item_id = row["_id"]
            current_status = row["Trạng thái"]
            title_text = str(row.get(title_col, f"Mục {item_id}"))
            risk_text = f"• Rủi ro: {row[risk_col]}" if risk_col and pd.notna(row.get(risk_col)) else ""
            
            badge = "✅ ĐÃ ĐẠT CHUẨN" if current_status == "Đã đạt chuẩn" else "⏳ CẦN RÀ SOÁT"
            
            with st.expander(f"[{badge}] {title_text} {risk_text}"):
                c1, c2 = st.columns([3, 2])
                
                with c1:
                    st.markdown(f"**Nội dung rà soát / Yêu cầu:**\n{title_text}")
                    if legal_col and pd.notna(row.get(legal_col)):
                        st.info(f"⚖️ **Căn cứ pháp lý & Chế tài:**\n\n{row[legal_col]}")
                        
                    # Các trường thông tin khác từ Google Sheets
                    other_cols = [c for c in cols if c not in [title_col, dept_col, risk_col, legal_col, "_id", "Trạng thái", "Ghi chú nội bộ"]]
                    if other_cols:
                        st.markdown("**Thông tin chi tiết quy định:**")
                        for oc in other_cols:
                            if pd.notna(row.get(oc)):
                                st.write(f"- *{oc}:* {row[oc]}")
                                
                    # Danh sách biểu mẫu đã đính kèm riêng cho mục này
                    item_forms = [f for f in uploaded_forms if f.get("item_id") == item_id]
                    st.markdown("---")
                    st.markdown("📎 **Biểu mẫu & File đính kèm cho mục này:**")
                    if not item_forms:
                        st.caption("Chưa có biểu mẫu nào được tải lên cho mục này.")
                    else:
                        for iform in item_forms:
                            file_path = os.path.join(UPLOAD_DIR, iform["filename"])
                            if os.path.exists(file_path):
                                with open(file_path, "rb") as f_data:
                                    st.download_button(
                                        label=f"📥 Tải {iform['form_name']} ({iform['filename']})",
                                        data=f_data.read(),
                                        file_name=iform["filename"],
                                        key=f"dl_{item_id}_{iform['filename']}"
                                    )
                                st.caption(f"Đăng bởi: {iform.get('uploader', 'N/A')} vào {iform.get('date', '')} | Ghi chú: {iform.get('note', '')}")
                
                with c2:
                    st.markdown("#### 🛠️ Cập nhật tiến độ & Biểu mẫu")
                    
                    # 1. Cập nhật trạng thái & ghi chú
                    with st.form(key=f"update_form_{item_id}"):
                        new_status = st.selectbox(
                            "Trạng thái tuân thủ:",
                            ["Chưa hoàn tất", "Đã đạt chuẩn", "Không áp dụng"],
                            index=["Chưa hoàn tất", "Đã đạt chuẩn", "Không áp dụng"].index(current_status) if current_status in ["Chưa hoàn tất", "Đã đạt chuẩn", "Không áp dụng"] else 0
                        )
                        new_note = st.text_area("Ghi chú nội bộ / Tiến độ thực hiện:", value=row["Ghi chú nội bộ"], height=80)
                        
                        btn_update_info = st.form_submit_button("💾 Lưu Trạng Thái & Ghi Chú", use_container_width=True)
                        if btn_update_info:
                            save_item_update(item_id, {"status": new_status, "note": new_note})
                            st.success("Đã cập nhật thông tin!")
                            st.rerun()
                            
                    st.markdown("---")
                    
                    # 2. Upload file biểu mẫu trực tiếp vào mục này
                    with st.form(key=f"upload_form_{item_id}", clear_on_submit=True):
                        st.markdown("**📤 Tải lên Biểu mẫu mới cho mục này:**")
                        form_name = st.text_input("Tên biểu mẫu:", placeholder="Ví dụ: Phiếu kiểm tra MTC, Tờ trình thanh toán...")
                        uploader_name = st.text_input("Người cập nhật (Họ tên - Phòng ban):", placeholder="Nguyễn Văn A - Kế toán")
                        form_note = st.text_input("Ghi chú biểu mẫu:", placeholder="Áp dụng từ tháng này...")
                        up_file = st.file_uploader("Chọn file (.xlsx, .docx, .pdf, .csv):", type=["xlsx", "xls", "docx", "doc", "pdf", "csv"], key=f"file_{item_id}")
                        
                        btn_upload = st.form_submit_button("🚀 Tải Lên & Đính Kèm", use_container_width=True)
                        if btn_upload:
                            if not form_name or not up_file:
                                st.error("Vui lòng nhập tên biểu mẫu và chọn tệp!")
                            else:
                                safe_fname = f"{item_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{up_file.name}"
                                save_dest = os.path.join(UPLOAD_DIR, safe_fname)
                                with open(save_dest, "wb") as f_out:
                                    f_out.write(up_file.getbuffer())
                                    
                                save_uploaded_form({
                                    "item_id": item_id,
                                    "item_title": title_text,
                                    "department": str(row.get(dept_col, "Chung")) if dept_col else "Chung",
                                    "form_name": form_name,
                                    "filename": safe_fname,
                                    "uploader": uploader_name,
                                    "note": form_note,
                                    "date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                                })
                                st.success("Đã đăng tải biểu mẫu thành công!")
                                st.rerun()

# --- 5. CHỨC NĂNG 2: KHO BIỂU MẪU TẬP TRUNG ---
elif view_mode == "📤 Tải Lên & Kho Biểu Mẫu Tập Trung":
    st.subheader("📁 Kho Biểu Mẫu Toàn Doanh Nghiệp (Central Template Repository)")
    st.caption("Tổng hợp toàn bộ biểu mẫu nghiệp vụ đã được các phòng ban tải lên.")
    
    all_forms = get_uploaded_forms()
    if not all_forms:
        st.info("Chưa có biểu mẫu nào được tải lên hệ thống. Hãy vào từng mục quy trình ở tab Sổ tay để tải lên.")
    else:
        forms_df = pd.DataFrame(all_forms)
        
        # Bộ lọc theo phòng ban trong kho biểu mẫu
        dept_filter = st.selectbox("Lọc biểu mẫu theo phòng ban:", ["Tất cả"] + sorted(list(set(forms_df["department"].tolist()))))
        if dept_filter != "Tất cả":
            forms_df = forms_df[forms_df["department"] == dept_filter]
            
        st.markdown(f"**Danh sách gồm {len(forms_df)} biểu mẫu:**")
        
        for idx, frow in forms_df.iterrows():
            with st.container():
                c_a, c_b = st.columns([3, 1])
                with c_a:
                    st.markdown(f"📄 **{frow['form_name']}** (Phòng ban: `{frow['department']}`)")
                    st.caption(f"Quy trình liên kết: {frow['item_title']} • Đăng bởi: {frow.get('uploader', 'N/A')} ({frow.get('date', '')})")
                    if frow.get("note"):
                        st.write(f"- *Ghi chú:* {frow['note']}")
                with c_b:
                    fpath = os.path.join(UPLOAD_DIR, frow["filename"])
                    if os.path.exists(fpath):
                        with open(fpath, "rb") as f_open:
                            st.download_button(
                                label=f"📥 Tải về ({frow['filename'].split('_')[-1]})",
                                data=f_open.read(),
                                file_name=frow["filename"].split("_")[-1],
                                key=f"central_dl_{idx}",
                                use_container_width=True
                            )
                st.markdown("---")

# --- 6. CHỨC NĂNG 3: BẢNG ĐO LƯỜNG TUÂN THỦ (KPI) ---
else:
    st.subheader("📊 Báo Cáo Tiến Độ Tuân Thủ & Tỷ Lệ Đạt Theo Phòng Ban (KPI Dashboard)")
    
    total_items = len(df)
    done_items = len([i for i, u in item_updates.items() if u.get("status") == "Đã đạt chuẩn" and any(df["_id"] == i)])
    pending_items = total_items - done_items
    pct_rate = int(done_items / total_items * 100) if total_items > 0 else 0
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tổng số mục tuân thủ (Sheets)", f"{total_items} mục")
    k2.metric("Đã rà soát đạt chuẩn", f"{done_items} mục", delta=f"{pct_rate}%")
    k3.metric("Còn nợ / Cần hoàn thiện", f"{pending_items} mục", delta=f"-{100-pct_rate}%", delta_color="inverse")
    k4.metric("Tổng số biểu mẫu đã upload", f"{len(uploaded_forms)} file")
    
    st.progress(pct_rate / 100.0)
    st.markdown("---")
    
    if dept_col:
        st.markdown(f"#### 📈 Tỷ lệ hoàn thành phân bổ theo {dept_col}")
        stat_rows = []
        for d in sorted([str(x) for x in df[dept_col].dropna().unique() if str(x).strip()]):
            sub_d = df[df[dept_col].astype(str) == d]
            sub_total = len(sub_d)
            sub_done = len([rid for rid in sub_d["_id"] if item_updates.get(rid, {}).get("status") == "Đã đạt chuẩn"])
            sub_pct = int(sub_done / sub_total * 100) if sub_total > 0 else 0
            stat_rows.append({
                "Phòng Ban / Khối": d,
                "Tổng số quy định": sub_total,
                "Đã đạt": sub_done,
                "Chưa đạt": sub_total - sub_done,
                "Tiến độ (%)": f"{sub_pct}%"
            })
        st.table(pd.DataFrame(stat_rows))

# --- XUẤT BÁO CÁO KẾT QUẢ RÀ SOÁT ---
st.markdown("---")
st.subheader("📥 Xuất Báo Cáo Tuân Thủ Tổng Hợp")
export_data = df.copy()
export_data["Trạng thái tuân thủ"] = export_data["_id"].apply(lambda x: item_updates.get(x, {}).get("status", "Chưa hoàn tất"))
export_data["Ghi chú nội bộ"] = export_data["_id"].apply(lambda x: item_updates.get(x, {}).get("note", ""))
export_data["Số lượng biểu mẫu đính kèm"] = export_data["_id"].apply(lambda x: len([f for f in uploaded_forms if f.get("item_id") == x]))
export_data = export_data.drop(columns=["_id"], errors="ignore")

st.download_button(
    label="📥 Tải Báo Cáo Toàn Bộ Quy Trình & Tiến Độ (CSV UTF-8 with BOM)",
    data=export_data.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
    file_name=f"Bao_Cao_Tuan_Thu_{datetime.date.today().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)
