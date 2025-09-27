# =========================================
# variables.tf
# =========================================
variable "project_id" {
  description = "project id"
  type        = string
  default = "tuwaiq-final-project-473403"
}

variable "region" {
  description = "Region for Cloud Functions (2nd gen) / Eventarc"
  type        = string
  default     = "europe-west1"
}

variable "bucket_name" {
  description = "Cloud Storage bucket to hold your data files"
  type        = string
  default     = "tuwaiq-project-1937" # must be globally unique
}

variable "bucket_location" {
  description = "Location/region for the data bucket"
  type        = string
  default     = "europe-west1" # or set to var.region if you prefer single region
}

variable "topic_name" {
  description = "Pub/Sub topic for GCS notifications"
  type        = string
  default     = "tuwaiq-events"
}

variable "function_name" {
  description = "Cloud Functions (2nd gen) function name (runs on Cloud Run)"
  type        = string
  default     = "tuwaiq-event-fn"
}

variable "function_entry_point" {
  description = "Python entry point (the function name in your code)"
  type        = string
  default     = "handle_pubsub_cloudevent"
}

variable "source_bucket_name" {
  description = "Bucket to store the source ZIP used to build the function"
  type        = string
  default     = null
}

variable "source_object_name" {
  description = "Name for the uploaded ZIP object in the source bucket"
  type        = string
  default     = "services_will-work_.zip"
}

variable "local_zip_path" {
  description = "Local path to your ZIP with the function code"
  type        = string
  default     = "./services_will-work_.zip"
}

variable "memory_mb" {
  description = "Function memory"
  type        = number
  default     = 500
}

variable "timeout_seconds" {
  description = "Function timeout"
  type        = number
  default     = 260
}
