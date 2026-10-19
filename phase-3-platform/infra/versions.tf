terraform {
  required_version = ">= 1.8.0"

  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.16" # v3 เปลี่ยน syntax ของ block `kubernetes` จึง pin major ไว้
    }
  }

  # แล็บใช้ local state (terraform.tfstate) งานจริงต้องใช้ remote backend ที่มี locking
  # เช่น S3 + DynamoDB, GCS หรือ Terraform Cloud (ADR-0017)
}

provider "helm" {
  kubernetes {
    config_path    = pathexpand(var.kubeconfig_path)
    config_context = var.kube_context
  }
}
