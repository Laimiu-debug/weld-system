import DOMPurify from 'dompurify'
import type { Config } from 'dompurify'

const DOCUMENT_HTML_CONFIG: Config = {
  USE_PROFILES: { html: true },
  FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button'],
  FORBID_ATTR: ['srcdoc'],
}

export const sanitizeDocumentHtml = (html: unknown): string => {
  if (typeof html !== 'string') return ''
  return String(DOMPurify.sanitize(html, DOCUMENT_HTML_CONFIG))
}
