export type JobStatus = 'queued' | 'running' | 'retrying' | 'succeeded' | 'failed'
export type Provider = 'rules' | 'openai'
export type Severity = 'low' | 'medium' | 'high'

export interface Dataset {
  id: number
  original_filename: string
  content_type: string
  size_bytes: number
}

export interface NumericStatistics {
  minimum: number
  maximum: number
  mean: number
  median: number
  standard_deviation: number
  first_quartile: number
  third_quartile: number
  outlier_count: number
  outlier_percentage: number
}

export interface ColumnProfile {
  name: string
  data_type: string
  missing_count: number
  missing_percentage: number
  unique_count: number
  numeric_statistics: NumericStatistics | null
}

export interface QualityIssue {
  code: string
  severity: Severity
  message: string
  column: string | null
}

export interface DatasetProfile {
  dataset_id: number
  original_filename: string
  row_count: number
  column_count: number
  duplicate_row_count: number
  columns: ColumnProfile[]
  preview: Record<string, unknown>[]
  quality: {
    score: number
    missing_cell_count: number
    completeness_percentage: number
    duplicate_percentage: number
    issues: QualityIssue[]
  }
}

export interface ProcessingJob {
  id: number
  dataset_id: number
  analysis_id: number | null
  job_type: 'dataset_profile'
  status: JobStatus
  task_id: string | null
  attempt_count: number
  error_message: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export type CleaningRequest = {
  remove_duplicate_rows: boolean
  numeric_missing_strategy: 'keep' | 'mean' | 'median'
  text_missing_strategy: 'keep' | 'mode'
  numeric_outlier_strategy: 'keep' | 'remove' | 'clip_iqr'
}

export interface CleanedDataset {
  id: number
  dataset_id: number
  original_filename: string
  stored_filename: string
  cleaning_config: CleaningRequest
  summary: Record<string, number>
  original_row_count: number
  cleaned_row_count: number
  created_at: string
}

export interface InsightItem {
  category: 'quality' | 'missing_values' | 'duplicates' | 'outliers' | 'columns' | 'general'
  severity: Severity
  title: string
  description: string
  evidence: string[]
  confidence: number
}

export interface RecommendationItem {
  priority: Severity
  action: string
  reason: string
}

export interface DatasetInsight {
  id: number
  dataset_id: number
  analysis_id: number
  provider: Provider
  model: string | null
  summary: string
  insights: InsightItem[]
  recommendations: RecommendationItem[]
  created_at: string
}
