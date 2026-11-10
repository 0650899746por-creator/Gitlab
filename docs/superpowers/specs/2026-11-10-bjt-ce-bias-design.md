# BJT Common-Emitter DC Bias — Design (สั้น)

วันที่: 2026-11-10
สถานะ: รออนุมัติ
ขนาดงาน: small change (แอปแล็บเดียว) — ใช้ดีไซน์สั้น ไม่มี builder review

## 1. บริบทและเป้าหมาย

แล็บสั้นของ ENG29 2121 ต้องการเว็บแอป Flask จริงหนึ่งตัวสำหรับคำนวณจุดทำงาน DC
ของวงจรไบแอสแบบ voltage divider (CE amplifier) ผู้ใช้กรอก 6 ค่า แล้วได้จุดทำงาน
พร้อมหน่วย มี validation และคำเตือนโหมดการทำงาน และมีผลตรวจสอบจากการคำนวณ
อีกวิธีหนึ่งที่เป็นอิสระจากกัน

เหตุผล: นักศึกษาต้องตรวจผลคำนวณมือกับเครื่อง และต้องเห็นว่าเครื่องคำนวณเองจริง
ไม่ใช่แค่ฟอร์มที่จัดรูปแบบตัวเลข

## 2. ขอบเขต

**Goals**
- รับอินพุต VCC, R1, R2, RC, RE, beta, VBE
- แสดง IB (µA), IC, IE (mA), VB, VE, VC, VCE (V) พร้อมหน่วย
- Validation ครบ แสดงข้อผิดพลาดทั้งหมดพร้อมกัน
- คำเตือนโหมด: cutoff / active / saturation
- คำนวณสองวิธี (closed form กับ nodal) แล้วเทียบผลและรายงาน PASS/FAIL
- Flask จริง: logic แยกจาก routes/templates/CSS/tests
- รัน localhost ได้ และ commit ขึ้น GitHub

**Non-goals (ห้ามเพิ่มในแล็บนี้)**
- AC analysis, frequency response, Bode plot
- Transient / time-domain / function generator
- ตัวแก้ไขวงจร, schematic editor, netlist
- FET/MOSFET, op-amp, multi-stage
- JavaScript คำนวณเลข, chart library, CSS framework, UI ตกแต่งเต็มรูปแบบ
- ฐานข้อมูล, login, deployment

**Anti-goals (ถือว่าล้มเหลวแม้รันได้)**
- ตัวเลขในหน้าเว็บคำนวณจาก template หรือ JS แทน backend
- มีเพียงวิธีคำนวณเดียวแล้วเรียกว่า "ตรวจสอบอิสระ"
- โค้ดคำนวณซ้ำใน route หรือ template
- เพิ่มฟีเจอร์นอก scope ข้างต้น

## 3. ข้อจำกัด

- Python 3.12.7, Flask 3.x, pytest (ยังไม่ติดตั้ง; pip ต่อ PyPI ได้)
- ไม่ใช้ numpy/sympy — เขียน linear solve เองเพื่อคง dependency น้อย
- git อยู่ที่ `C:\Users\B6828417\AppData\Local\Programs\Git\cmd\git.exe` (ไม่อยู่ใน PATH)
- remote `origin` = `https://github.com/0650899746por-creator/Gitlab.git`, branch `main`
- ไม่แตะ `electrical.py` / `test_electrical.py` (ของเดิม คนละ scope)

## 4. แนวทางที่พิจารณา

| ทาง | วิธี | ข้อดี | ข้อเสีย |
|---|---|---|---|
| A (เลือก) | Nodal analysis 3×3 linear solve | อิสระจริงจาก closed form, จับผิดพีชคณิต/โค้ด | โค้ด solve เพิ่มเล็กน้อย |
| B | สูตรประมาณ (ละ IB, VB = VBB) | เห็นขนาด error เชิงการสอน | ไม่ใช่การตรวจสอบอิสระ, คลาดเคลื่อนหลาย % |
| C | Newton/iterative Ebers–Moll | ใกล้ของจริง | เกิน scope แล็บ DC สั้น |

**เลือก A** เพราะเป็นวิธีเดียวที่ตรวจสอบอิสระได้จริงและยังเล็ก — ไม่ทำ B/C

## 5. โมเดลและสมการ

วงจร: VCC → R1 → base, base → R2 → ground, VCC → RC → collector, emitter → RE → ground
ทรานซิสเตอร์ NPN, โมเดลคงที่: `VBE` คงที่, `IC = beta * IB`, `IE = (beta + 1) * IB`

**วิธีที่ 1 — Closed form (Thevenin)**
```
VBB = VCC * R2 / (R1 + R2)
RB  = R1 * R2 / (R1 + R2)
IB  = (VBB - VBE) / (RB + (beta + 1) * RE)
IC  = beta * IB
IE  = (beta + 1) * IB
VE  = IE * RE
VB  = VE + VBE
VC  = VCC - IC * RC
VCE = VC - VE
```

**วิธีที่ 2 — Nodal (อิสระ, ไม่ใช้ Thevenin)**
แก้ระบบเชิงเส้น 3×3 ในตัวแปร `VB, VE, IB`:
```
(1)  VB - VE = VBE
(2)  (VCC - VB)/R1 - VB/R2 - IB = 0
(3)  (beta + 1) * IB - VE/RE = 0
```
แล้วคำนวณ `IC = beta*IB`, `VC = VCC - IC*RC`, `VCE = VC - VE`
แก้ด้วย Gaussian elimination + partial pivoting (pure Python)

**การตรวจสอบ:** `max |ค่าจากวิธี 1 - ค่าจากวิธี 2|` ต้อง ≤ tolerance
(rel 1e-9) → แสดง PASS/FAIL; ถ้า FAIL ถือเป็นบั๊กและต้องแก้ก่อนส่ง

**Cutoff:** ถ้า `VBB <= VBE` (หรือ IB ≤ 0 จาก nodal) ให้ทั้งสองวิธีคืนค่า
`IB=IC=IE=0, VE=0, VB=VBB, VC=VCC, VCE=VCC` และ region = cutoff
(ไม่ใช้สมการ active เพราะโมเดลใช้ไม่ได้เมื่อทรานซิสเตอร์ไม่นำ)

## 6. Validation

ตรวจทุกค่า: ต้องเป็นตัวเลข finite
- `VCC > 0`
- `R1 > 0`, `R2 > 0`, `RC > 0`, `RE > 0`
- `beta > 0`
- `0 <= VBE < VCC`
- ค่าที่ผิดทั้งหมดถูกรวบรวมเป็น list แล้วแสดงพร้อมกัน (ไม่ fail-fast)

## 7. โหมดการทำงาน

- **cutoff**: `VBB <= VBE` → คำเตือน "transistor is cut off"
- **saturation**: `VCE < 0.2 V` → คำเตือน "transistor is in saturation; fixed-beta model is not valid"
- **active**: นอกนั้น → แสดง "Active region"
คำเตือนไม่บล็อกการแสดงผล (ยกเว้น validation error)

## 8. โครงสร้างไฟล์

```
app.py                              # create_app(), routes, app.run
bjt_bias.py                         # validation, closed_form, nodal, analyze, region
templates/index.html                # ฟอร์ม + ผลลัพธ์ + คำเตือน (ไม่มี JS)
static/style.css                    # CSS สั้น ~60-80 บรรทัด
tests/test_bjt_bias.py              # logic, validation, region, independence
tests/test_app.py                   # routes + หลักฐานว่า backend คำนวณเอง
requirements.txt                    # Flask, pytest
README.md                           # เขียนใหม่ให้ตรงแล็บ BJT
docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md
```

## 9. Routes และการไหลของข้อมูล

- `GET /` → ฟอร์ม พร้อมค่าเริ่มต้นตัวอย่าง (12, 47000, 10000, 2200, 470, 150, 0.7)
- `POST /` → `bjt_bias.analyze(...)` → ถ้า validation ผิด เรนเดอร์ฟอร์มเดิม + error list
  ถ้าผ่าน เรนเดอร์ผลลัพธ์
- `create_app()` เพื่อให้ test สร้าง app ได้โดยไม่ชน state
- template รับ dict ที่คำนวณเสร็จแล้ว; Jinja ทำได้แค่จัดรูปแบบตัวเลข (`:.3f`) ห้ามคำนวณ

## 10. หลักฐานว่า Backend คำนวณเองจริง

1. สูตรทั้งหมดอยู่ใน `bjt_bias.py` เท่านั้น; `app.py` เรียก `analyze()` ตรง ๆ
2. `index.html` ไม่มี `<script>` และไม่มีการบวก/ลบ/คูณ/หาร
3. Test: POST ค่าที่รู้คำตอบ → HTML ต้องมีตัวเลขที่คำนวณได้ (เช่น `2.661 mA`, `4.887 V`)
4. Test: monkeypatch `bjt_bias.analyze` ให้คืนค่า sentinel → หน้าเว็บต้องเปลี่ยนตาม
   (พิสูจน์ว่า route ใช้ผลจาก backend ไม่ได้คำนวณเอง)
5. Test: ตรวจว่า HTML ที่ได้ไม่มีแท็ก `<script>`
6. Test: closed form กับ nodal ตรงกันในหลายชุดพารามิเตอร์

## 11. UI

หน้าเดียว: ฟอร์ม 7 ช่อง, ปุ่ม Calculate, กล่อง error, ตารางผลลัพธ์ (IB เป็น µA,
IC/IE เป็น mA, แรงดัน V), กล่องโหมด (cutoff/active/saturation), บรรทัดตรวจสอบสองวิธี
(`closed form vs nodal: max diff = ... → PASS`) และกล่อง "hand calculation"
แสดง `VBB` กับ `RB` เพื่อใช้เทียบกับที่นักศึกษาคำนวณมือ
CSS เรียบง่าย อ่านง่าย ไม่มี framework ไม่มีภาพประกอบ

## 12. การตรวจรับ, demo และ commit

- `python -m pytest -q` ผ่านทั้งหมด
- `python app.py` แล้วเปิด `http://127.0.0.1:5000` กรอกค่าตัวอย่างเห็นผลจริง
- commit ด้วย git path เต็ม: `Add BJT common-emitter DC bias Flask app`
- push ขึ้น `origin main` (ถ้า auth ล้มเหลว จะรายงานทันที ไม่แต่งผล)

## 13. สิ่งที่เหลือให้ผู้สร้างตัดสินใจ

- ข้อความ UI ภาษาอังกฤษ (ตามค่าเริ่มต้น) — เปลี่ยนเป็นไทยได้ถ้าต้องการ
- ตำแหน่ง/รูปแบบเลขทศนิยม (mA 3 ตำแหน่ง, V 3 ตำแหน่ง)
- จะแสดง `VBB`/`RB` หรือไม่ (ดีไซน์นี้ใส่ไว้เพราะช่วยเทียบมือ)
