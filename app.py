import streamlit as st
import pandas as pd

st.set_page_config(page_title="ระบบคำนวณค่าไฟหาร 3", layout="wide")
st.title("⚡ ระบบคำนวณค่าไฟและจัดสรรตามการใช้งานจริง")
st.write("แพลตฟอร์มสำหรับคำนวณค่าไฟรายเดือนตามจำนวนวันที่อยู่และชั่วโมงการเปิดแอร์")

# --- ส่วนข้อมูลนำเข้าหลัก (เจ้าของห้องกรอกเมื่อบิลมา) ---
st.sidebar.header("📋 ข้อมูลบิลค่าไฟประจำเดือน")
total_bill = st.sidebar.number_input("ยอดบิลค่าไฟรวม (บาท):", min_value=0.0, value=1685.0, step=10.0)
fixed_cost = st.sidebar.number_input("ค่าไฟส่วนกลาง Fix (บาท):", min_value=0.0, value=300.0, step=10.0)

variable_cost = total_bill - fixed_cost
fixed_per_person = fixed_cost / 3

st.sidebar.write(f"**ค่าไฟผันแปรที่จะนำมาหาร:** {variable_cost:,.2f} บาท")
st.sidebar.write(f"**ค่าไฟ Fix ตกคนละ:** {fixed_per_person:,.2f} บาท")

# --- โครงสร้างการเก็บข้อมูลของผู้พักอาศัยทั้ง 3 คน ---
roommates = ["เติ้ล", "โก้", "ดิค"]
scores = {}

cols = st.columns(3)

for i, name in enumerate(roommates):
    with cols[i]:
        st.subheader(f"👤 ข้อมูลของ: {name}")
        st.write("กรอกข้อมูลการใช้งานรายวัน (จำลองสเกล 5 วันเพื่อความรวดเร็ว หรือบันทึกยอดรวมปลายเดือน)")
        
        # เลือกรูปแบบการกรอกเพื่อความสะดวกในการใช้งาน
        input_type = st.radio(f"รูปแบบการกรอกของ {name}:", ["กรอกสรุปยอดรวมปลายเดือน", "กรอกละเอียดรายวัน (ตัวอย่าง)"], key=f"mode_{name}")
        
        if input_type == "กรอกสรุปยอดรวมปลายเดือน":
            days_present = st.number_input(f"จำนวนวันที่อยู่ห้องทั้งหมด (วัน):", min_value=0, max_value=31, value=5 if name=="เติ้ล" else (10 if name=="โก้" else 30), key=f"days_{name}")
            total_ac_hours = st.number_input(f"รวมชั่วโมงเปิดแอร์ทั้งเดือน (ชม.):", min_value=0.0, value=40.0 if name=="เติ้ล" else (60.0 if name=="โก้" else 720.0), key=f"ac_{name}")
            
            # คำนวณคะแนนรวม
            base_score = days_present * 0.5
            ac_score = total_ac_hours / 6
            total_score = base_score + ac_score
            st.info(f"🔹 คะแนนรวมของ {name}: {total_score:.2f} คะแนน\n(ฐานอยู่ห้อง: {base_score:.1f}, แอร์: {ac_score:.2f})")
            scores[name] = total_score
            
        else:
            # ตัวเลือกแบบละเอียดรายวัน มี Checkbox บังคับคิดค่าไฟ 0.5 และช่องใส่ชั่วโมงแอร์
            daily_data = []
            for day in range(1, 6): # สมมติตัวอย่าง 5 วันเพื่อความกระชับ สามารถขยายเป็น 31 วันได้
                c1, c2 = st.columns([1, 2])
                with c1:
                    is_here = st.checkbox(f"วันที่ {day} อยู่ห้อง", value=True, key=f"here_{name}_{day}")
                with c2:
                    ac_hour = st.number_input(f"ชั่วโมงแอร์ วันที่ {day}:", min_value=0.0, max_value=24.0, value=8.0 if name=="เติ้ล" and is_here else (6.0 if name=="โก้" and is_here else 24.0 if is_here else 0.0), step=1.0, key=f"achour_{name}_{day}")
                
                # คิดคะแนนตามกติกาหลัก
                day_score = 0.5 + (ac_hour / 6) if is_here else 0.0
                daily_data.append(day_score)
            
            total_score = sum(daily_data)
            st.success(f"🔹 คะแนนรวมจากการติ๊กรายวัน: {total_score:.2f} คะแนน")
            scores[name] = total_score

st.markdown("---")
st.header("📊 สรุปการจัดสรรและยอดที่ต้องชำระ")

total_room_scores = sum(scores.values())

if total_room_scores > 0:
    cost_per_score = variable_cost / total_room_scores
    st.write(f"💰 อัตราค่าไฟผันแปร: **{cost_per_score:.4f} บาท ต่อ 1 คะแนนการใช้งาน**")
    
    # คำนวณยอดสุทธิของแต่ละคน
    summary_data = []
    for name in roommates:
        user_variable_cost = scores[name] * cost_per_score
        final_pay = fixed_per_person + user_variable_cost
        summary_data.append({
            "ชื่อ": name,
            "คะแนนการใช้ไฟรวม": round(scores[name], 2),
            "ค่าไฟ Fix (ส่วนกลาง)": round(fixed_per_person, 2),
            "ค่าไฟผันแปร (ตามจริง)": round(user_variable_cost, 2),
            "ยอดที่ต้องจ่ายสุทธิ (บาท)": round(final_pay, 2)
        })
    
    df = pd.DataFrame(summary_data)
    st.table(df)
else:
    st.warning("กรุณากรอกข้อมูลวันและชั่วโมงแอร์ในระบบเพื่อเริ่มต้นการคำนวณ")
