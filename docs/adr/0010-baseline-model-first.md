# ADR-0010: เริ่มจาก baseline model (TF-IDF + Logistic Regression) และใช้ champion/challenger

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 1

## บริบท
เป้าหมายของ phase 1 คือฝึก **ระบบ** (versioning, tracking, registry, quality gate) ไม่ได้ต้องการโมเดลที่ดีที่สุด
ถ้าใช้ transformer ตั้งแต่แรก การเทรนบน CPU จะใช้เวลาหลายสิบนาที ทำให้ feedback loop ช้าเกินไป

## การตัดสินใจ
- dataset: AG News (ภาษาอังกฤษ 4 classes, มีใน Hugging Face) สุ่มมา 20,000 แถว
- model: scikit-learn Pipeline (TF-IDF → LogisticRegression) เทรนเสร็จในไม่กี่วินาที
- **Quality gate**: accuracy < `register_threshold` (0.85) จะไม่ register เข้า registry
- **Champion/challenger**: version ใหม่ได้ alias `champion` เฉพาะเมื่อดีกว่า champion ปัจจุบัน

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| TF-IDF + LR (เลือก) | เร็ว, อธิบายได้, ได้ baseline ไว้เทียบ | accuracy ไม่สูงสุด |
| Fine-tune BERT / WangchanBERTa | accuracy สูง, รองรับภาษาไทย | ต้องมี GPU หรือใช้เวลานาน |
| Wisesight sentiment (ภาษาไทย) | ตรงกับบริบทไทย | การโหลด dataset ผ่าน HF เปลี่ยนรูปแบบบ่อย |

## ผลที่ตามมา
- ✅ `dvc repro` ทั้ง pipeline ใช้เวลาไม่ถึง 1 นาที จึงทดลองได้หลายรอบ
- ✅ ได้เรียนว่า "โมเดลใหม่ ≠ โมเดลที่ดีกว่า" จึงต้องมี gate ก่อน promote
- 🔁 แบบฝึกหัด: เปลี่ยน dataset เป็นภาษาไทย หรือเพิ่ม stage `evaluate` ที่ตรวจ fairness ต่อ class (f1 ของ class ต่ำสุดต้องไม่ต่ำกว่า X)
