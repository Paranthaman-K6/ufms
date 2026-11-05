// universal-frontend-master-source/browser/engines/chromium.js
// Chromium network adapter using Chrome DevTools Protocol events via
// Selenium WebDriver performance logging.
//
// Configures Chrome performance logging explicitly and captures:
//   - Network.requestWillBeSent
//   - Network.responseReceived
//   - Network.loadingFailed
//   - Network.loadingFinished
//   - Network.redirectReceived
//
// Sensitive request data (Authorization headers, cookies, request bodies)
// is intentionally excluded from all recorded events.
'use strict';

const { Builder } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const { EVENT_TYPES, makeEvent, makeNetworkResult } = require('./schema');

const PERF_LOGGING_PREFS = {
  enableNetwork: true,
  enablePage: false,
  traceCategories: '',
};

// Chrome logging preferences for performance (CDP) events.
function chromeLoggingPrefs() {
  const o = new chrome.Options();
  o.setLoggingPrefs({ performance: 'ALL' });
  return o;
}

// Merge performance logging prefs into an existing Chrome Options object.
function applyLoggingPrefs(options) {
  // selenium-webdriver Chrome Options: set logging prefs via setLoggingPrefs
  if (typeof options.setLoggingPrefs === 'function') {
    options.setLoggingPrefs({ performance: 'ALL' });
  }
  return options;
}

async function startMonitoring(driver) {
  // Enable performance logging domain via CDP if available (best-effort).
  try {
    if (typeof driver.createCDPSession === 'function') {
      const cdp = await driver.createCDPSession();
      if (cdp && typeof cdp.send === 'function') {
        await cdp.send('Network.enable');
      }
    }
  } catch (e) {
    // CDP not available in this WebDriver implementation; fall back to
    // performance log polling.
  }
}

async function collectEvents(driver) {
  const events = [];
  try {
    const entries = await driver.manage().logs().get('performance');
    for (const entry of entries) {
      try {
        const msg = JSON.parse(entry.message).message;
        const method = msg.method || '';
        const params = msg.params || {};

        if (method === EVENT_TYPES.REQUEST_WILL_BE_SENT) {
          const req = params.request || {};
          events.push(makeEvent(EVENT_TYPES.REQUEST_WILL_BE_SENT, {
            timestamp: params.timestamp,
            url: req.url || '',
            method: req.method || '',
            resourceType: params.type || 'other',
            requestId: params.requestId || null,
            timing: params.timestamp || null,
          }));
        } else if (method === EVENT_TYPES.RESPONSE_RECEIVED) {
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
        } else if (method === EVENT_TYPES.LOADING_FAILED) {
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
        } else if (method === EVENT_TYPES.LOADING_FINISHED) {
          events.push(makeEvent(EVENT_TYPES.LOADING_FINISHED, {
            timestamp: params.timestamp,
            url: '',
            method: '',
            resourceType: 'other',
            status: null,
            requestId: params.requestId || null,
            timing: params.timestamp || null,
          }));
        } else if (method === EVENT_TYPES.REDIRECT_RECEIVED) {
          const res = params.response || {};
          events.push(makeEvent(EVENT_TYPES.REDIRECT_RECEIVED, {
            timestamp: params.timestamp,
            url: res.url || '',
            method: res.requestMethod || '',
            resourceType: res.type || 'other',
            status: res.status || null,
            redirectUrl: res.redirectURL || null,
            requestId: params.requestId || null,
            timing: res.timing || null,
          }));
        }
      } catch (parseErr) {
        // Ignore unparseable performance log entries.
      }
    }
  } catch (e) {
    // Performance logs not available in this session.
  }

  return makeNetworkResult(events);
}

async function launchChromiumWithNetwork(binary) {
  const o = new chrome.Options();
  // selenium-webdriver v4 Chrome Options has no setBinary(); the binary is
  // located via the CHROME_BIN environment variable or system PATH. When an
  // explicit binary is supplied (e.g. from CHROMIUM_BIN or a --chrome-bin
  // flag), pin it via CHROME_BIN so Selenium Manager uses that exact build.
  if (binary) {
    process.env.CHROME_BIN = binary;
  }
  // UFME_CHROME_FLAGS lets a runner add flags the environment needs, e.g.
  // CI containers that require --no-sandbox. Sandboxing stays on by default.
  const extraFlags = (process.env.UFME_CHROME_FLAGS || '').split(/\s+/).filter(Boolean);
  o.addArguments('--headless=new', '--disable-dev-shm-usage',
    '--disable-gpu', '--window-size=1440,900', ...extraFlags);
  applyLoggingPrefs(o);

  const driver = await new Builder()
    .forBrowser('chrome')
    .setChromeOptions(o)
    .build();

  await startMonitoring(driver);
  return driver;
}

module.exports = {
  launchChromiumWithNetwork,
  collectEvents,
  applyLoggingPrefs,
  chromeLoggingPrefs,
  makeNetworkResult,
};
