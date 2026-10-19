// Load test ของ rag-api (ADR-0022)
//   k6 run loadtest/k6.js
//   BASE_URL=http://localhost:8000 HOST_HEADER= k6 run loadtest/k6.js   (compose)
//
// ระหว่างรันให้ดู Grafana และ `kubectl -n ai get hpa -w`
// คำถามที่ต้องตอบได้หลังทดสอบ: HPA เพิ่ม pod ของ rag-api แล้ว latency ลดลงไหม ถ้าไม่ลด เพราะอะไร
import http from "k6/http";
import { check, sleep } from "k6";

const BASE = __ENV.BASE_URL || "http://localhost:8080";
const HOST = __ENV.HOST_HEADER === undefined ? "rag.localhost" : __ENV.HOST_HEADER;

const QUESTIONS = [
  "พนักงานมีวันลาพักร้อนกี่วันต่อปี",
  "รหัสผ่านต้องยาวอย่างน้อยกี่ตัวอักษร",
  "เบี้ยเลี้ยงเดินทางในประเทศวันละเท่าไหร่",
  "ลาป่วยกี่วันถึงต้องมีใบรับรองแพทย์",
  "ทำโน้ตบุ๊กหายต้องทำอย่างไร",
];

export const options = {
  scenarios: {
    ramp: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "1m", target: 2 },
        { duration: "3m", target: 6 },
        { duration: "1m", target: 0 },
      ],
    },
  },
  // SLO: ถ้าเกินเกณฑ์ k6 จะ exit ด้วย code ที่ไม่ใช่ 0 → ใช้เป็น gate ใน pipeline ได้
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<60000"],
  },
};

export default function () {
  const q = QUESTIONS[Math.floor(Math.random() * QUESTIONS.length)];
  const headers = { "Content-Type": "application/json" };
  if (HOST) headers["Host"] = HOST;

  const res = http.post(`${BASE}/ask`, JSON.stringify({ question: q }), {
    headers,
    timeout: "180s",
  });
  check(res, {
    "status 200": (r) => r.status === 200,
    "has answer": (r) => r.status === 200 && r.json("answer") !== "",
  });
  sleep(1);
}
