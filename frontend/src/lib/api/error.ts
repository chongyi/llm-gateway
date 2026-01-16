/**
 * API error helpers
 * Normalizes unknown errors into user-friendly messages.
 */

type FastApiValidationError = {
  msg?: unknown;
};

function formatFastApiDetail(detail: unknown): string | null {
  if (!detail) return null;

  if (typeof detail === 'string') return detail;

  if (Array.isArray(detail)) {
    // FastAPI validation errors often look like: [{ loc, msg, type }, ...]
    const messages = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object' && 'msg' in item) {
          const msg = (item as FastApiValidationError).msg;
          if (typeof msg === 'string') return msg;
        }
        return null;
      })
      .filter((m): m is string => !!m);

    if (messages.length > 0) return messages.join(', ');
  }

  if (typeof detail === 'object') {
    if ('message' in detail && typeof (detail as { message?: unknown }).message === 'string') {
      return (detail as { message: string }).message;
    }
  }

  return null;
}

export function getApiErrorMessage(error: unknown, fallback = 'Request failed'): string {
  if (!error) return fallback;
  if (typeof error === 'string') return error;

  if (error instanceof Error && error.message) return error.message;

  // In case an AxiosError bubbles up (e.g. if interceptors are bypassed)
  if (typeof error === 'object') {
    const maybeResponse = (error as { response?: unknown }).response;
    if (maybeResponse && typeof maybeResponse === 'object') {
      const data = (maybeResponse as { data?: unknown }).data;
      if (data && typeof data === 'object') {
        const detail = (data as { detail?: unknown }).detail;
        const detailMessage = formatFastApiDetail(detail);
        if (detailMessage) return detailMessage;

        const apiErrorMessage = (data as { error?: { message?: unknown } }).error?.message;
        if (typeof apiErrorMessage === 'string' && apiErrorMessage) return apiErrorMessage;
      }
    }

    const message = (error as { message?: unknown }).message;
    if (typeof message === 'string' && message) return message;
  }

  return fallback;
}

