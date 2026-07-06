import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="ระบบคำนวณค่าไฟหาร 3", layout="wide")
st.title("⚡ ระบบคำนวณค่าไฟและจัดสรรตามการใช้งานจริง")

# ชื่อไฟล์สำหรับเซฟข้อมูลถาวร
FILE_NAME = "room_data.csv"
roommates = ["เติ้ล", "โก้", "ดิค"]

# ฟังก์ชันสำหรับโหลดหรือสร้างตาราง 31 วัน
def load_data():
    if os.path.exists(FILE_NAME):
        return pd.read_csv(FILE_NAME)
    else:
        # ถ้ายังไม่มีไฟล์ ให้สร้างตารางเปล่า 31 วัน
        days = list(range(1, 32))
        data = {"วันที่": days}
        for name in roommates:
            data[f"{name}_อยู่ห้อง"] = [False] * 31  # ค่าเริ่มต้นคือไม่อยู่ห้อง
            data[f"{name}_แอร์(ชม)"] = [0.0] * 31    # ค่าเริ่มต้นคือแอร์ 0 ชม.
        return pd.DataFrame(data)

df = load_data()

# --- ส่วนกรอกค่าไฟรวม ---
st.sidebar.header("📋 ข้อมูลบิลค่าไฟประจำเดือน")
total_bill = st.sidebar.number_input("ยอดบิลค่าไฟรวม (บาท):", min_value=0.0, value=1685.0, step=10.0)
fixed_cost = st.sidebar.number_input("ค่าไฟส่วนกลาง Fix (บาท):", min_value=0.0, value=300.0, step=10.0)

variable_cost = total_bill - fixed_cost
fixed_per_person = fixed_cost / 3

st.sidebar.write(f"**ค่าไฟผันแปรที่จะนำมาหาร:** {variable_cost:,.2f} บาท")
st.sidebar.write(f"**ค่าไฟ Fix ตกคนละ:** {fixed_per_person:,.2f} บาท")

# --- ส่วนตารางกรอกข้อมูลรายวัน ---
st.write("### 📅 ตารางบันทึกการใช้งานรายวัน (31 วัน)")
st.write("📝 **วิธีใช้:** สามารถติ๊กถูกช่อง 'อยู่ห้อง' และดับเบิ้ลคลิกพิมพ์ตัวเลขในช่อง 'แอร์' ได้เลย (ระบบเซฟอัตโนมัติ กด F5 ข้อมูลก็ไม่หาย)")

# แสดงตารางแบบแก้ไขได้ (Data Editor)
edited_df = st.data_editor(df, num_rows="fixed", use_container_width=True, hide_index=True)

# ตรวจสอบว่ามีการแก้ไขข้อมูลในตารางหรือไม่ ถ้ามีให้เซฟทับไฟล์เดิมทันที
if not edited_df.equals(df):
    edited_df.to_csv(FILE_NAME, index=False)
    st.success("💾 บันทึกข้อมูลล่าสุดลงระบบแล้ว!")

st.markdown("---")
st.header("📊 สรุปยอดค่าไฟที่ต้องจ่าย")

scores = {}

# คำนวณคะแนนรวมของแต่ละคนจากตาราง 31 วัน
for name in roommates:
    # ดึงข้อมูลรายคอลัมน์
    is_here = edited_df[f"{name}_อยู่ห้อง"].astype(bool)
    ac_hours = edited_df[f"{name}_แอร์(ชม)"]
    
    # ฐานคะแนนอยู่ห้อง: ถ้าอยู่ห้อง = 0.5 ถ้าไม่อยู่ = 0
    base_score = is_here.astype(int) * 0.5
    
    # ฐานคะแนนแอร์: เอาชั่วโมงหาร 6 (และจะคิดคะแนนแอร์เฉพาะวันที่ติ๊กว่า 'อยู่ห้อง' เท่านั้น ป้องกันการลืมติ๊ก)
    ac_score = (ac_hours / 6) * is_here.astype(int)
    
    # รวมคะแนนทั้งเดือนของคนนั้น
    total_score = (base_score + ac_score).sum()
    scores[name] = total_score

total_room_scores = sum(scores.values())

if total_room_scores > 0:
    cost_per_score = variable_cost / total_room_scores
    st.write(f"💰 อัตราค่าไฟผันแปรเฉลี่ย: **{cost_per_score:.4f} บาท ต่อ 1 คะแนน**")
    
    # สรุปข้อมูลลงตาราง
    summary_data = []
    for name in roommates:
        user_variable_cost = scores[name] * cost_per_score
        final_pay = fixed_per_person + user_variable_cost
        summary_data.append({
            "ชื่อ": name,
            "คะแนนการใช้ไฟรวม": round(scores[name], 2),
            "ค่าไฟ Fix": round(fixed_per_person, 2),
            "ค่าไฟผันแปร": round(user_variable_cost, 2),
            "ยอดสุทธิที่ต้องจ่าย (บาท)": round(final_pay, 2)
        })
    
    st.table(pd.DataFrame(summary_data))
    
    # ปุ่มสำหรับล้างข้อมูลขึ้นเดือนใหม่
    if st.button("🗑️ ล้างข้อมูลตารางเพื่อเริ่มเดือนใหม่"):
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
        st.rerun()
else:
    st.warning("กรุณาติ๊กเลือกวันที่อยู่ห้องเพื่อเริ่มต้นการคำนวณ")
