import api from './client'


export type ExportFormat =
  'csv' | 'xlsx'


function getFilename(
  contentDisposition:
    string | undefined,
  fallbackFilename: string,
): string {
  if (!contentDisposition) {
    return fallbackFilename
  }

  const match =
    contentDisposition.match(
      /filename="?([^"]+)"?/i,
    )

  return (
    match?.[1] ??
    fallbackFilename
  )
}


export async function downloadFormVersionExport(
  formVersionId: number,
  format: ExportFormat,
): Promise<void> {
  const response =
    await api.get<Blob>(
      `/exports/form-versions/${formVersionId}/${format}`,
      {
        responseType: 'blob',
      },
    )

  const fallbackFilename =
    `form_version_${formVersionId}.${format}`

  const filename =
    getFilename(
      response.headers[
        'content-disposition'
      ],
      fallbackFilename,
    )

  const url =
    window.URL.createObjectURL(
      response.data,
    )

  const link =
    document.createElement('a')

  link.href =
    url

  link.download =
    filename

  document.body.appendChild(
    link,
  )

  link.click()

  link.remove()

  window.URL.revokeObjectURL(
    url,
  )
}