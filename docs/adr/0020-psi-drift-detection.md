# ADR-0020: ตรวจ data drift ด้วย PSI ที่เขียนเอง (ยังไม่ใช้ Evidently)

- **สถานะ:** Accepted
- **วันที่:** 2026-10-19
- **Phase:** 4

## บริบท
เมื่อเวลาผ่านไป โมเดลจะเสื่อมแม้ code ไม่เปลี่ยน เพราะข้อมูลที่เข้ามาไม่เหมือนตอนเทรน (data drift)
ใน production มักยังไม่มี label ของข้อมูลใหม่ จึงวัด accuracy ทันทีไม่ได้ ต้องดู distribution ของ input/prediction แทน
แผนเดิมใช้ Evidently แต่ API ของ Evidently เปลี่ยนมากระหว่าง 0.4 → 0.7

## การตัดสินใจ
- เขียน `drift/drift.py` ด้วย numpy/pandas (~100 บรรทัด)
- feature ที่ดู: ความยาวข้อความ, จำนวนคำ, สัดส่วนตัวเลข/ตัวพิมพ์ใหญ่ และ distribution ของ label
- ใช้ **PSI** (bin ตาม quantile ของ reference) เกณฑ์ `> 0.25` = drift
- exit code `2` = drift เพื่อให้ orchestrator (Prefect) ใช้ตัดสินใจต่อ
- มี `--simulate-shift` ไว้จำลองข้อมูลที่เปลี่ยน (ข่าวสั้นลง และมีแต่ข่าวกีฬา)

## ทางเลือกที่พิจารณา
| ตัวเลือก | ข้อดี | ข้อเสีย |
|---|---|---|
| PSI เขียนเอง (เลือก) | เข้าใจหลักการ, ไม่มี dependency หนัก, ไม่พังเมื่อ library เปลี่ยน API | มีแค่ metric เดียว, ไม่มี report สวย ๆ |
| Evidently | report HTML ครบ, มีหลาย test | API เปลี่ยนบ่อย |
| KS-test (scipy) | มีค่าทางสถิติ (p-value) | ข้อมูลเยอะ p-value จะเล็กเสมอ (sensitive เกินไป) |

## ผลที่ตามมา
- ✅ อธิบายได้ว่า drift detection คือการเทียบ histogram สองชุด
- ⚠️ drift ไม่ได้แปลว่าโมเดลแย่ลงเสมอไป ต้องยืนยันด้วย label จริงเมื่อมีข้อมูล
- 🔁 เมื่อเข้าใจแล้ว ลองเปลี่ยนเป็น Evidently และเทียบผลกับ PSI ที่เขียนเอง
