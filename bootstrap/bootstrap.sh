#!/usr/bin/env bash
# Phase 0 / Linux side: ติดตั้ง Ansible แล้วรัน playbook (ADR-0005)
# ใช้: ./bootstrap/bootstrap.sh            (ติดตั้งทั้งหมด)
#      ./bootstrap/bootstrap.sh --check    (dry-run ดูว่าจะเปลี่ยนอะไร)
#      ./bootstrap/bootstrap.sh --tags docker
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"

# repo ที่อยู่บน /mnt/c ช้ากว่า filesystem ของ Linux 5-20 เท่า และมีปัญหาเรื่อง
# file permission / inotify (ADR-0003) จึงเตือนก่อน
case "$here" in
  /mnt/*) echo "WARNING: repo อยู่บน Windows filesystem ($here) แนะนำให้ clone ไว้ใน ~/code" >&2 ;;
esac

if ! command -v ansible-playbook >/dev/null 2>&1; then
  echo "==> ติดตั้ง Ansible"
  sudo apt-get update
  sudo apt-get install -y ansible git make
fi

cd "$here/ansible"
# -K = ถามรหัส sudo ครั้งเดียว ใช้กับ task ที่ต้อง become root
ansible-playbook site.yml -K "$@"

cat <<'EOF'

==> เสร็จแล้ว
ถ้ารันครั้งแรก: ไปที่ PowerShell แล้วรัน `wsl --shutdown` จากนั้นเปิด Ubuntu ใหม่
(เพื่อให้ systemd ทำงานและ user อยู่ใน docker group)
แล้วตรวจด้วย:  docker run --rm hello-world && kubectl version --client
EOF
