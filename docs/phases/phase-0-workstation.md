# Phase 0 — Workstation as Code

**เป้าหมาย:** ได้เครื่องที่พร้อมทำแล็บ โดยติดตั้งทุกอย่างด้วย code ทั้งหมด
**ADR:** [0003](../adr/0003-wsl2-linux-filesystem.md) · [0004](../adr/0004-docker-engine-in-wsl.md) · [0005](../adr/0005-ansible-workstation.md) · [0006](../adr/0006-pin-tool-versions.md) · [0007](../adr/0007-uv-for-python.md)
**เวลา:** 1-2 ชั่วโมง (ส่วนใหญ่รอดาวน์โหลด)

## สิ่งที่จะถูกติดตั้ง

| ฝั่ง | ของ | ติดตั้งโดย |
|---|---|---|
| Windows | WSL2, Ubuntu 24.04, `.wslconfig` | `bootstrap/windows/setup-wsl.ps1` |
| Ubuntu | build-essential, git, jq, make, unzip, systemd | role `base` |
| Ubuntu | Docker Engine, buildx, compose plugin | role `docker` |
| Ubuntu | kubectl, k3d, helm, argocd, k9s, tofu, k6, yq, node | role `cli_tools` |
| Ubuntu | uv, dvc, ruff, pre-commit | role `python_tools` |

## ขั้นตอน

### 1. Windows: ติดตั้ง WSL2
เปิด **PowerShell แบบ Run as Administrator** ที่โฟลเดอร์ของ repo:
```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\bootstrap\windows\setup-wsl.ps1            # ปรับได้: -MemoryGB 10 -Processors 4
```
ถ้าเพิ่งติดตั้ง WSL ครั้งแรก ให้ restart เครื่อง แล้วเปิด "Ubuntu 24.04" จาก Start menu เพื่อสร้าง username/password
จากนั้น:
```powershell
wsl --shutdown
```

### 2. นำ repo เข้า Linux filesystem
ตอนนี้ repo อยู่ใน OneDrive แนะนำให้ push ขึ้น GitHub (public) ก่อน เพราะ phase 3 ต้องใช้:
```bash
# ใน Ubuntu
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
mkdir -p ~/code && cd ~/code
git clone https://github.com/aekanun-phanphomma/Mini-AI-Platform.git
cd Mini-AI-Platform
```
> ถ้ายังไม่ได้ push ใช้ `cp -r /mnt/c/Users/<win-user>/OneDrive/Desktop/self-learning/Mini-AI-Platform ~/code/` แล้ว `git init` ทีหลังได้

### 3. Ubuntu: รัน Ansible
```bash
./bootstrap/bootstrap.sh --check   # dry-run: ดูก่อนว่าจะเปลี่ยนอะไร
./bootstrap/bootstrap.sh           # ติดตั้งจริง (ถามรหัส sudo)
```
รันครั้งแรกเสร็จแล้ว **ต้อง** `wsl --shutdown` จาก PowerShell อีกครั้ง (ให้ systemd + docker group มีผล)

## ✅ Checkpoint
```bash
docker run --rm hello-world
kubectl version --client && helm version --short && k3d version && tofu version
uv --version && dvc --version
./bootstrap/bootstrap.sh           # รันซ้ำ: ต้องได้ changed=0 (หรือเกือบ 0) = idempotent
```

## 💥 Break it (แบบฝึกหัด)
1. `sudo rm /usr/local/bin/helm` แล้วรัน `./bootstrap/bootstrap.sh --tags tools` ต้องได้ helm กลับมา
2. เปลี่ยน `k9s` version ใน `group_vars/all.yml` เป็น `0.32.4` แล้วรันใหม่ ดูว่า symlink เปลี่ยน แต่ของเก่ายังอยู่ใน `/opt/tools`
3. เขียน task ใหม่ใน role `base` ให้ติดตั้ง `htop` แล้วรัน `--check` ก่อน

## 🧠 ต้องตอบได้
- ทำไม repo ไม่ควรอยู่บน `/mnt/c` ?
- idempotent คืออะไร และทำไม `shell:` ต้องมี `creates:` ?
- การอยู่ใน group `docker` มีความเสี่ยงอะไร?

## 🔧 Troubleshooting
| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| `bash\r: No such file or directory` | ไฟล์เป็น CRLF: `git config --global core.autocrlf false` แล้ว clone ใหม่ (repo มี `.gitattributes` บังคับ LF แล้ว) |
| `permission denied ... docker.sock` | ยังไม่ได้ `wsl --shutdown` หลังเพิ่ม group |
| docker ไม่ start | `systemctl status docker` ถ้า systemd ไม่ทำงาน ให้ตรวจ `/etc/wsl.conf` แล้ว `wsl --shutdown` |
| ดาวน์โหลด GitHub ล้ม | rate limit / network: รันซ้ำได้ เพราะ task ที่สำเร็จแล้วจะข้าม |
