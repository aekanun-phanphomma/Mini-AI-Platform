# OpenTofu ทำหน้าที่ "bootstrap" อย่างเดียว คือติดตั้ง Argo CD และ root Application
# จากนั้น Argo CD ดูแลทุกอย่างใน cluster จาก Git (ADR-0017)
#
#   tofu apply ──▶ Argo CD ──▶ root app ──▶ gitops/apps/*.yaml ──▶ ai-deps, rag-api, monitoring

resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = var.argocd_chart_version
  namespace        = "argocd"
  create_namespace = true
  wait             = true
  timeout          = 600

  values = [file("${path.module}/values/argocd.yaml")]
}

# root Application (app-of-apps): Application ที่ชี้ไปยังโฟลเดอร์ซึ่งมี Application อื่นอยู่ข้างใน
# ใช้ chart argocd-apps แทน kubernetes_manifest เพราะ kubernetes_manifest
# ต้องมี CRD อยู่แล้วตอน `plan` แต่ CRD ถูกสร้างใน resource ข้างบน (ปัญหาไก่กับไข่)
resource "helm_release" "root_app" {
  depends_on = [helm_release.argocd]

  name       = "root-app"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argocd-apps"
  version    = var.argocd_apps_chart_version
  namespace  = "argocd"

  values = [templatefile("${path.module}/values/root-app.yaml.tftpl", {
    repo_url        = var.repo_url
    target_revision = var.target_revision
  })]
}
