// universal-frontend-master-source/browser/engines/firefox.js
// Firefox network adapter.
//
// Firefox support for WebDriver performance logging is limited compared to Chromium.
// This adapter attempts the following in order:
//   1. WebDriver BiDi (network events) - if available
//   2. Performance log polling - limited support
//   3. Explicit UNSUPPORTED status - if neither works
//
// Sensitive request data (Authorization headers, cookies, request bodies)
// is intentionally excluded from all recorded events.
'use strict';

const { Builder } = require('selenium-webdriver');
const firefox = require('selenium-webdriver/firefox');
const { EVENT_TYPES, makeEvent, makeNetworkResult } = require('./schema');

function firefoxLoggingPrefs(options) {
  const o = options || new firefox.Options();
  o.setPreference('devtools.toolbox.feature.enabled', true);
  return o;
}

async function startMonitoring(driver) {
  // Attempt WebDriver BiDi network subscription.
  try {
    const bidi = await driver.getBidi ? await driver.getBidi() : null;
    if (bidi) {
      await bidi.session.subscribe({
        events: ['network.beforeRequestSent', 'network.responseCompleted', 'network.loadingFailed'],
      });
    }
  } catch (e) {
    // BiDi not available; will try performance log fallback.
  }
}

async function collectEvents(driver) {
  const events = [];

  // Try WebDriver BiDi first.
  try {
    const bidi = await driver.getBidi ? await driver.getBidi() : null;
    if (bidi) {
      // BiDi network events are delivered via event listeners in some
      // implementations. Here we attempt a one-shot read if supported.
      const eventsResult = await bidi.network ? await bidi.network.getEvents ? await bidi.network.getEvents() : [] : [];
      for (const ev of eventsResult) {
        events.push(normalizeBidiEvent(ev));
      }
      return makeNetworkResult(events);
    }
  } catch (e) {
    // BiDi not available.
  }

  // Fall back to performance log polling (limited Firefox support).
  try {
    const entries = await driver.manage().logs().get('performance');
    for (const entry of entries) {
      try {
        const msg = JSON.parse(entry.message).message;
        const method = msg.method || '';
        const params = msg.params || {};
        if (method === EVENT_TYPES.RESPONSE_RECEIVED || method === 'Network.responseReceived') {
          const res = params.response || {};
          events.push(makeEvent(EVENT_TYPES.RESPONSE_RECEIVED, {
            timestamp: params.timestamp,
            url: res.url || '',
            method: res.requestMethod || '',
            resourceType: res.type || 'other',
            status: res.status || null,
            requestId: params.requestId || null,
            timing: res.timing || null,
          }));
        } else if (method === EVENT_TYPES.LOADING_FAILED || method === 'Network.loadingFailed') {
          events.push(makeEvent(EVENT_TYPES.LOADING_FAILED, {
            timestamp: params.timestamp,
            url: params.url || '',
            method: '',
            resourceType: params.type || 'other',
            status: null,
            errorText: params.errorText || 'failed',
            requestId: params.requestId || null,
            timing: params.timestamp || null,
          }));
        }
      } catch (parseErr) {
        // Ignore unparseable entries.
      }
    }
  } catch (e) {
    // Performance logs not available for Firefox.
  }

  return makeNetworkResult(events);
}

function normalizeBidiEvent(ev) {
  // Normalize a WebDriver BiDi network event into the shared schema.
  const method = ev.method || ev.type || '';
  let type = EVENT_TYPES.REQUEST_WILL_BE_SENT;
  let data = { url: '', method: '', resourceType: 'other' };

  if (method.includes('beforeRequestSent') || method.includes('requestWillBeSent')) {
    type = EVENT_TYPES.REQUEST_WILL_BE_SENT;
    data = { url: ev.request ? ev.request.url : '', method: ev.request ? ev.request.method : '' };
  } else if (method.includes('responseCompleted') || method.includes('responseReceived')) {
    type = EVENT_TYPES.RESPONSE_RECEIVED;
    data = {
      url: ev.response ? ev.response.url : '',
      method: ev.request ? ev.request.method : '',
      status: ev.response ? ev.response.status : null,
      resourceType: ev.response ? ev.response.resourceType : 'other',
    };
  } else if (method.includes('loadingFailed')) {
    type = EVENT_TYPES.LOADING_FAILED;
    data = { url: ev.request ? ev.request.url : '', errorText: ev.errorText || 'failed' };
  }

  return makeEvent(type, data);
}

async function launchFirefoxWithNetwork(binary) {
  const o = new firefox.Options();
  if (binary) o.setBinary(binary);
  const extraFlags = (process.env.UFME_FIREFOX_FLAGS || '').split(/\s+/).filter(Boolean);
  o.addArguments('-headless', ...extraFlags);
  firefoxLoggingPrefs(o);
  const driver = await new Builder()
    .forBrowser('firefox')
    .setFirefoxOptions(o)
    .build();

  await startMonitoring(driver);
  return driver;
}

module.exports = {
  launchFirefoxWithNetwork,
  collectEvents,
  firefoxLoggingPrefs,
  makeNetworkResult,
};
