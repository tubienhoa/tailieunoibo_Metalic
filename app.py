import streamlit as st
import pandas as pd
import datetime

# --- CẤU HÌNH TRANG (PAGE CONFIG) ---
st.set_page_config(
    page_title="Checklist Tuân Thủ Pháp Lý & Thuế Doanh Nghiệp",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THUẬT NGỮ & GIẢI THÍCH (GLOSSARY) ---
# KPI: Key Performance Indicator - Chỉ số đo lường hiệu quả công việc (ở đây là tỷ lệ tuân thủ %)
# SOP: Standard Operating Procedure - Quy trình thao tác chuẩn
# RACI: Responsible, Accountable, Consulted, Informed - Ma trận phân công trách nhiệm
# Cache: Cơ chế lưu tạm dữ liệu vào bộ nhớ để tải nhanh hơn

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR7vrN3GLRabuoKp2kDJp7IWCsDcuHsrxqaXZS7itG_nSG7GyHUHDF5ogUf-v_z230B2AfcWUTnSkCk/pub?output=csv"

# --- HÀM TẢI DỮ LIỆU TỪ GOOGLE SHEETS (DATA INGESTION) ---
@st.cache_data(ttl=600)  # Tự động làm mới cache mỗi 10 phút
def load_data(url):
    try:
        df = pd.read_csv(url)
        # Làm sạch tên cột
        df.columns = [str(c).strip() for c in df.columns]
        return df, None
    except Exception as e:
        return None, str(e)

# --- KHỞI TẠO SESSION STATE (LƯU TRỮ TRẠNG THÁI KIỂM TRA) ---
if "checked_items" not in st.session_state:
    st.session_state.checked_items = set()

# --- TẢI DỮ LIỆU ---
df_raw, error_msg = load_data(CSV_URL)

st.title("🛡️ Bảng Kiểm Soát Tuân Thủ Pháp Lý, Thuế & Vận Hành Doanh Nghiệp")
st.caption("Đồng bộ trực tiếp từ Google Sheets • Hỗ trợ rà soát rủi ro, phân loại phòng ban và theo dõi tiến độ KPI")

if error_msg:
    st.error(f"⚠️ Không thể nạp dữ liệu trực tiếp từ Google Sheets: {error_msg}")
    st.info("Vui lòng kiểm tra lại đường truyền hoặc đảm bảo link Google Sheets đã được 'Xuất bản lên web' (Publish to Web) ở định dạng CSV.")
    st.stop()

if df_raw is None or df_raw.empty:
    st.warning("Dữ liệu đang rỗng hoặc chưa có nội dung.")
    st.stop()

# Đảm bảo có chỉ mục định danh duy nhất (Unique ID)
df = df_raw.copy()
if "_id" not in df.columns:
    df["_id"] = [f"item_{i+1}" for i in range(len(df))]

# Nhận diện tự động các cột quan trọng (Dynamic Column Detection)
cols = list(df.columns)
risk_col = next((c for c in cols if any(k in c.lower() for k in ["rủi ro", "risk", "mức độ"])), None)
dept_col = next((c for c in cols if any(k in c.lower() for k in ["phòng ban", "bộ phận", "phân loại", "nhóm", "lĩnh vực", "category", "dept"])), None)
content_col = next((c for c in cols if any(k in c.lower() for k in ["nội dung", "mục", "yêu cầu", "chi tiết", "tên", "checklist", "content"])), cols[0])

# Cột checkbox trạng thái tuân thủ
df["Đã hoàn thành"] = df["_id"].apply(lambda x: x in st.session_state.checked_items)

# --- SIDEBAR: BỘ LỌC & THAO TÁC (FILTERS & ACTIONS) ---
with st.sidebar:
    st.header("🔍 Bộ Lọc & Điều Khiển")
    
    # Nút đồng bộ lại
    if st.button("🔄 Đồng bộ lại dữ liệu (Sync)", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    st.markdown("---")
    
    # Lọc theo trạng thái
    status_filter = st.radio(
        "Trạng thái tuân thủ:",
        ["Tất cả", "Chưa hoàn thành (Cần làm)", "Đã hoàn thành"],
        index=0
    )
    
    # Lọc theo phòng ban / phân loại
    selected_dept = "Tất cả"
    if dept_col:
        dept_list = ["Tất cả"] + sorted([str(x) for x in df[dept_col].dropna().unique() if str(x).strip()])
        selected_dept = st.selectbox(f"Phân loại / Phòng ban ({dept_col}):", dept_list)
        
    # Lọc theo mức độ rủi ro
    selected_risk = "Tất cả"
    if risk_col:
        risk_list = ["Tất cả"] + sorted([str(x) for x in df[risk_col].dropna().unique() if str(x).strip()])
        selected_risk = st.selectbox(f"Mức độ rủi ro ({risk_col}):", risk_list)
        
    # Tìm kiếm tự do
    search_query = st.text_input("🔎 Tìm kiếm từ khóa:", "")
    
    st.markdown("---")
    st.subheader("⚙️ Quản lý trạng thái")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Chọn tất cả", use_container_width=True):
            st.session_state.checked_items = set(df["_id"].tolist())
            st.rerun()
    with col_btn2:
        if st.button("Bỏ chọn hết", use_container_width=True):
            st.session_state.checked_items = set()
            st.rerun()

# --- XỬ LÝ LỌC DỮ LIỆU ---
filtered_df = df.copy()

if status_filter == "Chưa hoàn thành (Cần làm)":
    filtered_df = filtered_df[~filtered_df["Đã hoàn thành"]]
elif status_filter == "Đã hoàn thành":
    filtered_df = filtered_df[filtered_df["Đã hoàn thành"]]

if dept_col and selected_dept != "Tất cả":
    filtered_df = filtered_df[filtered_df[dept_col].astype(str) == selected_dept]

if risk_col and selected_risk != "Tất cả":
    filtered_df = filtered_df[filtered_df[risk_col].astype(str) == selected_risk]

if search_query.strip():
    q = search_query.strip().lower()
    mask = filtered_df.astype(str).apply(lambda row: row.str.lower().str.contains(q, regex=False).any(), axis=1)
    filtered_df = filtered_df[mask]

# --- KPI METRICS DASHBOARD ---
total_items = len(df)
done_items = len(st.session_state.checked_items.intersection(set(df["_id"])))
pending_items = total_items - done_items
pct_done = int((done_items / total_items * 100)) if total_items > 0 else 0

st.markdown("### 📊 Tổng Quan Chỉ Số Tuân Thủ (Compliance KPI Dashboard)")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Tổng số mục kiểm tra", f"{total_items} mục")
m2.metric("Đã tuân thủ / Đã làm", f"{done_items} mục", delta=f"{pct_done}% hoàn thành")
m3.metric("Cần rà soát bổ sung", f"{pending_items} mục", delta=f"-{100-pct_done}%", delta_color="inverse")
m4.metric("Tỷ lệ tuân thủ chung", f"{pct_done}%")

st.progress(pct_done / 100.0)

st.markdown("---")

# --- HIỂN THỊ DANH SÁCH & CHO PHÉP TICK TỪNG MỤC ---
st.subheader(f"📋 Bảng Chi Tiết Hạng Mục (Hiển thị: {len(filtered_df)} / {total_items} mục)")

# Hiển thị bảng dạng tương tác với st.data_editor
display_cols = ["Đã hoàn thành"] + [c for c in df.columns if c not in ["_id", "Đã hoàn thành"]]

edited_df = st.data_editor(
    filtered_df[display_cols],
    use_container_width=True,
    hide_index=True,
    disabled=[c for c in display_cols if c != "Đã hoàn thành"],
    key="compliance_editor"
)

# Cập nhật session_state từ tương tác của người dùng trên bảng
new_checked = set(st.session_state.checked_items)
for idx, row in edited_df.iterrows():
    item_id = filtered_df.loc[idx, "_id"]
    if row["Đã hoàn thành"]:
        new_checked.add(item_id)
    else:
        new_checked.discard(item_id)

if new_checked != st.session_state.checked_items:
    st.session_state.checked_items = new_checked
    st.rerun()

# --- XUẤT DỮ LIỆU BÁO CÁO (EXPORT) ---
st.markdown("---")
st.subheader("📥 Xuất Báo Cáo & Chia Sẻ")
export_df = df.copy()
export_df["Trạng thái tuân thủ"] = export_df["Đã hoàn thành"].apply(lambda x: "Đạt / Đã hoàn tất" if x else "Chưa đạt / Cần rà soát")
export_df = export_df.drop(columns=["_id", "Đã hoàn thành"], errors="ignore")

csv_data = export_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

col_exp1, col_exp2 = st.columns([1, 3])
with col_exp1:
    today_str = datetime.date.today().strftime("%Y%m%d")
    st.download_button(
        label="📥 Tải Báo Cáo (CSV / Excel)",
        data=csv_data,
        file_name=f"Bao_Cao_Tuan_Thu_Doanh_Nghiep_{today_str}.csv",
        mime="text/csv",
        use_container_width=True
    )
with col_exp2:
    st.caption("💡 File CSV xuất ra sử dụng bảng mã UTF-8 with BOM (utf-8-sig), tương thích 100% khi mở trực tiếp bằng Microsoft Excel không bị lỗi phông chữ tiếng Việt.")
