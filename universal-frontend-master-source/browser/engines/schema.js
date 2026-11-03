// universal-frontend-master-source/browser/engines/schema.js
// Shared network event schema for browser network monitoring.
//
// All network events are normalized to this shape regardless of the underlying
// browser engine. Sensitive request data (authorization headers, cookies,
// request bodies) is intentionally excluded.

const EVENT_TYPES = {
  REQUEST_WILL_BE_SENT: 'Network.requestWillBeSent',
  RESPONSE_RECEIVED: 'Network.responseReceived',
  LOADING_FAILED: 'Network.loadingFailed',
  LOADING_FINISHED: 'Network.loadingFinished',
  REDIRECT_RECEIVED: 'Network.redirectReceived',
};

function makeEvent(type, data) {
  return {
    type,
    timestamp: data.timestamp || Date.now(),
    url: data.url || '',
    method: data.method || '',
    resourceType: data.resourceType || 'other',
    status: data.status || null,
    errorText: data.errorText || null,
    timing: data.timing || null,
    requestId: data.requestId || null,
    ...(data.redirectUrl ? { redirectUrl: data.redirectUrl } : {}),
  };
}

function isHttpError(event) {
  return event.type === EVENT_TYPES.RESPONSE_RECEIVED
    && event.status !== null
    && event.status >= 400;
}

function isNetworkFailure(event) {
  return event.type === EVENT_TYPES.LOADING_FAILED
    || (event.type === EVENT_TYPES.RESPONSE_RECEIVED && event.status === null && event.errorText !== null);
}

function makeNetworkResult(events) {
  const httpErrors = events.filter(isHttpError);
  const networkFailures = events.filter(isNetworkFailure);
  return {
    events,
    httpErrors,
    networkFailures,
    total: events.length,
    hasErrors: httpErrors.length > 0 || networkFailures.length > 0,
  };
}

module.exports = {
  EVENT_TYPES,
  makeEvent,
  isHttpError,
  isNetworkFailure,
  makeNetworkResult,
};
