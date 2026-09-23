terraform { required_version = ">= 1.7"; required_providers { aws = { source = "hashicorp/aws"; version = "~> 5.0" } } }
provider "aws" { region = var.region }
variable "region" { type = string; default = "us-east-1" }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "database_password" { type = string; sensitive = true }
resource "aws_s3_bucket" "models" { bucket_prefix = "fraudstream-models-" }
resource "aws_s3_bucket_versioning" "models" { bucket = aws_s3_bucket.models.id; versioning_configuration { status = "Enabled" } }
resource "aws_s3_bucket_server_side_encryption_configuration" "models" { bucket = aws_s3_bucket.models.id; rule { apply_server_side_encryption_by_default { sse_algorithm = "AES256" } } }
resource "aws_db_subnet_group" "main" { name_prefix = "fraudstream-"; subnet_ids = var.private_subnet_ids }
resource "aws_db_instance" "ledger" { identifier_prefix = "fraudstream-"; engine = "postgres"; engine_version = "16"; instance_class = "db.t4g.medium"; allocated_storage = 30; db_name = "fraudstream"; username = "fraudstream"; password = var.database_password; db_subnet_group_name = aws_db_subnet_group.main.name; storage_encrypted = true; backup_retention_period = 7; skip_final_snapshot = true; publicly_accessible = false }
resource "aws_elasticache_subnet_group" "main" { name = "fraudstream"; subnet_ids = var.private_subnet_ids }
resource "aws_elasticache_replication_group" "features" { replication_group_id = "fraudstream-features"; description = "Online feature store"; node_type = "cache.t4g.small"; port = 6379; subnet_group_name = aws_elasticache_subnet_group.main.name; automatic_failover_enabled = true; multi_az_enabled = true; num_cache_clusters = 2; at_rest_encryption_enabled = true; transit_encryption_enabled = true }

