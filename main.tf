# =========================================
# main.tf
# =========================================

# ---- Enable required APIs ----
resource "google_project_service" "enable_services" {
  for_each = toset([
    "storage.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "cloudfunctions.googleapis.com",   # 2nd gen control plane
    "eventarc.googleapis.com",
    "cloudbuild.googleapis.com"
  ])
  project                    = var.project_id
  service                    = each.key
  disable_on_destroy         = false
  disable_dependent_services = false
}

data "google_project" "this" {}

# ---- Data bucket (for your uploaded files) ----
resource "google_storage_bucket" "data" {
  name                        = var.bucket_name
  project                     = var.project_id
  location                    = var.bucket_location
  uniform_bucket_level_access = true

  lifecycle_rule {
    action { type = "Delete" }
    condition { age = 3650 } # 10 years; adjust as you like
  }

  depends_on = [google_project_service.enable_services]
}

# ---- Pub/Sub topic ----
resource "google_pubsub_topic" "gcs_events" {
  name    = var.topic_name
  project = var.project_id

  depends_on = [google_project_service.enable_services]
}

# Force-create/fetch the GCS service agent
resource "google_project_service_identity" "gcs_agent" {
  project = var.project_id
  provider = google-beta
  service = "storage.googleapis.com"
  depends_on = [google_project_service.enable_services]
}

locals {
  gcs_service_agent = "service-${data.google_project.this.number}@gs-project-accounts.iam.gserviceaccount.com"
}

# ---- Allow Cloud Storage to publish to the topic ----
# GCS publishes using this project-wide SA: service-{PROJECT_NUMBER}@gs-project-accounts.iam.gserviceaccount.com
resource "google_pubsub_topic_iam_member" "gcs_publisher" {
  project = var.project_id
  topic  = google_pubsub_topic.gcs_events.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${local.gcs_service_agent}"
  
  depends_on = [google_project_service.enable_services,google_pubsub_topic.gcs_events,google_project_service_identity.gcs_agent]
}

# ---- GCS Notification -> Pub/Sub (OBJECT_FINALIZE only) ----
resource "google_storage_notification" "on_finalize" {
  bucket         = google_storage_bucket.data.name
  topic          = google_pubsub_topic.gcs_events.id # projects/{project}/topics/{name}
  event_types    = ["OBJECT_FINALIZE"]
  payload_format = "JSON_API_V1" # includes full object metadata in message.data

  depends_on = [
    google_pubsub_topic_iam_member.gcs_publisher
  ]
}

# ---- Source bucket for building the function (if not provided) ----
resource "random_id" "src_suffix" {
  byte_length = 3
}

locals {
  src_bucket_name = coalesce(
    var.source_bucket_name,
    "${var.project_id}-src-${random_id.src_suffix.hex}"
  )
}

resource "google_storage_bucket" "src" {
  name                        = local.src_bucket_name
  project                     = var.project_id
  location                    = var.bucket_location
  uniform_bucket_level_access = true

  depends_on = [google_project_service.enable_services]
}

data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = "${path.module}/code"  # folder with your function code
  output_path = "${path.module}/code.zip"
}

# ---- Upload the provided ZIP to the source bucket ----
resource "google_storage_bucket_object" "source_zip" {
  name   = var.source_object_name
  bucket = google_storage_bucket.src.name
  source = data.archive_file.function_zip.output_path
}

# ---- (Optional) Dedicated SA you can use for the function runtime ----
resource "google_service_account" "fn_runtime" {
  account_id   = "tuwaiq-fn-runtime"
  display_name = "Tuwaiq Function Runtime SA"
}

# Minimum permissions if your code only reads from the data bucket:
resource "google_project_iam_member" "fn_runtime_storage_view" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.fn_runtime.email}"
}

# ---- Cloud Functions (2nd gen) -> Eventarc (Pub/Sub) ----
# This deploys your Python code as a CloudEvent function on Cloud Run.
resource "google_cloudfunctions2_function" "event_fn" {
  provider    = google-beta
  name        = var.function_name
  location    = var.region
  description = "Processes Pub/Sub notifications from GCS"

  build_config {
    runtime     = "python311"
    entry_point = var.function_entry_point

    source {
      storage_source {
        bucket = google_storage_bucket.src.name
        object = google_storage_bucket_object.source_zip.name
      }
    }
  }

  service_config {
    max_instance_count  = 3
    available_memory    = "${var.memory_mb}M"
    timeout_seconds     = var.timeout_seconds
    ingress_settings    = "ALLOW_ALL"
    service_account_email = google_service_account.fn_runtime.email
    environment_variables = {
      LOG_LEVEL = "INFO"
    }
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.gcs_events.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }

  depends_on = [
    google_project_service.enable_services,
    google_storage_bucket_object.source_zip,
    google_pubsub_topic.gcs_events
  ]
}
