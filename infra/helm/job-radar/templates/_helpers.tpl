{{- define "job-radar.fullname" -}}
{{- printf "%s" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "job-radar.labels" -}}
app: job-radar
release: {{ .Release.Name }}
{{- end -}}
