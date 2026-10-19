variable "kubeconfig_path" {
  type    = string
  default = "~/.kube/config"
}

variable "kube_context" {
  description = "ป้องกัน apply ผิด cluster: ระบุ context ชัดเจนแทนการใช้ current-context"
  type        = string
  default     = "k3d-ailab"
}

variable "repo_url" {
  description = "Git repo ที่ Argo CD ใช้เป็น source of truth เช่น https://github.com/aekanun-phanphomma/Mini-AI-Platform.git"
  type        = string

  validation {
    condition     = can(regex("^https://", var.repo_url))
    error_message = "repo_url ต้องเป็น https URL ของ public repo"
  }
}

variable "target_revision" {
  description = "branch / tag ที่ Argo CD ติดตาม"
  type        = string
  default     = "main"
}

variable "argocd_chart_version" {
  type    = string
  default = "7.7.3"
}

variable "argocd_apps_chart_version" {
  type    = string
  default = "2.0.2"
}
