{{- define "rag-api.selectorLabels" -}}
app.kubernetes.io/name: rag-api
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "rag-api.labels" -}}
{{ include "rag-api.selectorLabels" . }}
app.kubernetes.io/version: {{ .Values.image.tag | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}
