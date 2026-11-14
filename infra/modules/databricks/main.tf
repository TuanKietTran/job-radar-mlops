terraform {
  required_version = ">= 1.5.0"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }
}

resource "databricks_catalog" "this" {
  name    = var.catalog_name
  comment = "Catalog for job-radar analytics."
}

resource "databricks_schema" "this" {
  catalog_name = databricks_catalog.this.name
  name         = var.schema_name
  comment      = "Gold tables for job-radar analytics."
}

resource "databricks_cluster_policy" "this" {
  name = "${var.project}-${var.environment}-policy"

  definition = jsonencode({
    spark_version = {
      type  = "fixed"
      value = var.spark_version
    }
    node_type_id = {
      type  = "fixed"
      value = var.node_type_id
    }
    num_workers = {
      type         = "range"
      minValue     = 0
      maxValue     = 4
      defaultValue = var.num_workers
    }
    autotermination_minutes = {
      type  = "fixed"
      value = 30
    }
  })
}
