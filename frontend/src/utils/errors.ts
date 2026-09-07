export function parseApiError(error: unknown): string {
  if (error instanceof Error) return error.message
  return 'Something went wrong while contacting the backend.'
}

export async function extractApiError(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json()
    if (typeof body === 'object' && body !== null && 'detail' in body) {
      const detail = body.detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail)) return detail.map(String).join(', ')
    }
  } catch {
    // Fall through to the status text for non-JSON responses.
  }
  return response.statusText || `Request failed with status ${response.status}.`
}
