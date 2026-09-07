export function isCsvFile(file: File): boolean {
  return file.name.toLowerCase().endsWith('.csv') || file.type === 'text/csv'
}

export function validateCsvFile(file: File | null): string | null {
  if (!file) return 'Choose a CSV file to upload.'
  if (!isCsvFile(file)) return 'Only CSV files can be uploaded.'
  return null
}
