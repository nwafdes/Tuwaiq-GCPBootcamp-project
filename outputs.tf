# =========================================
# outputs.tf
# =========================================
output "data_bucket" {
  value       = google_storage_bucket.data.name
  description = "Data bucket for your uploads"
}

output "pubsub_topic" {
  value       = google_pubsub_topic.gcs_events.name
  description = "Topic receiving GCS notifications"
}

output "function_name" {
  value       = google_cloudfunctions2_function.event_fn.name
  description = "Cloud Functions 2nd gen function name (runs on Cloud Run)"
}

output "function_region" {
  value       = google_cloudfunctions2_function.event_fn.location
  description = "Region of the function"
}

output "source_bucket" {
  value       = google_storage_bucket.src.name
  description = "Bucket storing the uploaded ZIP used to build the function"
}
