// ============================================================
//  FETCH API -- ULTIMATE QUICK-REFERENCE
//  Covers: CRUD, headers, error handling, cancellation,
//          timeouts, retries, streaming, file uploads,
//          parallel requests, interceptors, and more.
// ============================================================

/*
  TABLE OF CONTENTS
  -----------------
  1. ASCII DIAGRAMS
  2. BASIC   -- GET, POST, PUT, PATCH, DELETE
  3. BASIC   -- Request & Response Headers
  4. BASIC   -- Error Handling (Network vs HTTP)
  5. INTERMEDIATE -- AbortController (Cancellation)
  6. INTERMEDIATE -- Timeout Pattern
  7. INTERMEDIATE -- File Upload with FormData
  8. INTERMEDIATE -- Parallel Requests (Promise.all)
  9. ADVANCED -- Retry Pattern (Exponential Backoff)
  10. ADVANCED -- Interceptor Pattern (Wrapper)
  11. ADVANCED -- Streaming Responses
  12. COMPARISON TABLES (fetch vs XMLHttpRequest vs axios)
  13. GOTCHAS CHEAT-SHEET
*/


// ============================================================
// 1. ASCII DIAGRAMS
// ============================================================

/*
  FETCH REQUEST / RESPONSE CYCLE
  ==============================

  Browser / Node                            Server
  ----------------                          ----------------
  |              |   --- HTTP Request --->   |              |
  |  fetch(url,  |       method, headers,   |  Route       |
  |    options)  |       body (if any)      |  Handler     |
  |              |                          |              |
  |  Promise     |   <-- HTTP Response ---  |  Returns     |
  |  (pending)   |       status, headers,   |  status +    |
  |              |       body stream        |  body        |
  |              |                          |              |
  |  .then()     |                          |              |
  |  await       |                          |              |
  ----------------                          ----------------

  Step-by-step:
  1. fetch() returns a Promise<Response> immediately.
  2. The promise resolves once the HEADERS arrive (not the body).
  3. The body is a ReadableStream -- call .json(), .text(),
     .blob(), .arrayBuffer(), or .formData() to consume it.
  4. The promise ONLY rejects on NETWORK failure (DNS, offline).
     HTTP 4xx/5xx still RESOLVE -- you must check response.ok.


  ERROR HANDLING FLOW
  ===================

  fetch(url)
      |
      |--- Network error (offline, DNS, CORS block)
      |       |
      |       +---> Promise REJECTS ---> catch block
      |
      |--- Server responds (any status)
              |
              +---> Promise RESOLVES ---> .then / await
                      |
                      +--- response.ok === true  (200-299)
                      |       |
                      |       +---> Parse body, use data
                      |
                      +--- response.ok === false (4xx, 5xx)
                              |
                              +---> YOU must throw / handle manually


  ABORT CONTROLLER FLOW
  =====================

  const controller = new AbortController();
  const signal = controller.signal;
      |
      +--- fetch(url, { signal }) ---- request in flight --->
      |                                        |
      +--- controller.abort()                  |
              |                                |
              +--- signal fires "abort" ----->-+
                                               |
                                  Promise REJECTS with
                                  AbortError (DOMException)
*/


// ============================================================
// 2. BASIC -- CRUD OPERATIONS (GET, POST, PUT, PATCH, DELETE)
// ============================================================
// [BASIC]
// INTERVIEW: "Walk me through a basic fetch GET request."
//   - fetch returns a Promise that resolves to a Response object.
//   - You must call .json() (also a Promise) to parse the body.
//   - fetch does NOT reject on HTTP errors -- only network failures.

const API = "https://jsonplaceholder.typicode.com";

// --- GET --------------------------------------------------------
// [BASIC]
async function fetchGet() {
  const res = await fetch(`${API}/posts`);
  if (!res.ok) throw new Error(`GET failed: ${res.status}`);
  const data = await res.json();
  console.log("GET:", data);
}
// fetchGet();

// --- GET with query params --------------------------------------
// [BASIC]
async function fetchGetWithParams() {
  const params = new URLSearchParams({ userId: 1, _limit: 5 });
  const res = await fetch(`${API}/posts?${params}`);
  if (!res.ok) throw new Error(`GET failed: ${res.status}`);
  const data = await res.json();
  console.log("GET w/ params:", data);
}
// fetchGetWithParams();

// --- POST -------------------------------------------------------
// [BASIC]
async function fetchCreatePost() {
  const res = await fetch(`${API}/posts`, {
    method: "POST",
    headers: { "Content-Type": "application/json; charset=UTF-8" },
    body: JSON.stringify({ title: "foo", body: "bar", userId: 1 }),
  });
  const data = await res.json();
  console.log("POST:", data);
}
// fetchCreatePost();

// --- PUT (full replace) -----------------------------------------
// [BASIC]
async function fetchUpdatePost() {
  const res = await fetch(`${API}/posts/1`, {
    method: "PUT",
    headers: { "Content-Type": "application/json; charset=UTF-8" },
    body: JSON.stringify({ title: "updated", body: "new body", userId: 1 }),
  });
  const data = await res.json();
  console.log("PUT:", data);
}
// fetchUpdatePost();

// --- PATCH (partial update) -------------------------------------
// [BASIC]
async function fetchPatchPost() {
  const res = await fetch(`${API}/posts/1`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json; charset=UTF-8" },
    body: JSON.stringify({ title: "patched title" }),
  });
  const data = await res.json();
  console.log("PATCH:", data);
}
// fetchPatchPost();

// --- DELETE -----------------------------------------------------
// [BASIC]
async function fetchDeletePost() {
  const res = await fetch(`${API}/posts/1`, { method: "DELETE" });
  const data = await res.json();
  console.log("DELETE:", data);
}
// fetchDeletePost();

/*
  GOTCHAS -- CRUD
  ----------------
  - PUT replaces the ENTIRE resource; use PATCH for partial updates.
  - DELETE may return an empty body -- guard against parsing errors.
  - The second arg to fetch() is the RequestInit object; omitting
    "method" defaults to GET.
  - JSON.stringify is REQUIRED for objects in the body; passing a
    plain object silently sends "[object Object]".
*/


// ============================================================
// 3. BASIC -- REQUEST & RESPONSE HEADERS
// ============================================================
// [BASIC]
// INTERVIEW: "How do you read/set headers with fetch?"
//   - Use the Headers constructor or a plain object.
//   - Response headers are read-only; Request headers are settable.

// --- Setting request headers ------------------------------------
async function fetchWithHeaders() {
  const headers = new Headers();
  headers.append("Content-Type", "application/json");
  headers.append("Authorization", "Bearer my_token_here");
  headers.append("X-Custom-Header", "custom-value");

  const res = await fetch(`${API}/posts`, { headers });
  console.log("Status:", res.status);                  // 200
  console.log("Content-Type:", res.headers.get("content-type"));
  console.log("All headers:");
  res.headers.forEach((val, key) => console.log(`  ${key}: ${val}`));
}
// fetchWithHeaders();

// --- Common headers reference ------------------------------------
/*
  REQUEST HEADERS (you set these)
  +------------------------+--------------------------------------+
  | Header                 | Purpose                              |
  +------------------------+--------------------------------------+
  | Content-Type           | Body format (application/json, etc.) |
  | Authorization          | Auth token (Bearer, Basic)           |
  | Accept                 | Desired response format              |
  | X-Requested-With       | Identify AJAX (XMLHttpRequest)       |
  | Cache-Control          | Caching directives                   |
  +------------------------+--------------------------------------+

  RESPONSE HEADERS (server sets these)
  +------------------------+--------------------------------------+
  | Header                 | Purpose                              |
  +------------------------+--------------------------------------+
  | Content-Type           | Body format of response              |
  | Set-Cookie             | Cookies (not readable via JS CORS)   |
  | Cache-Control          | Caching rules                        |
  | ETag                   | Version identifier                   |
  | X-RateLimit-Remaining  | API rate-limit info                  |
  +------------------------+--------------------------------------+
*/

/*
  GOTCHAS -- HEADERS
  -------------------
  - Header names are case-INSENSITIVE per the HTTP spec.
  - Some headers are "forbidden" and cannot be set programmatically
    (e.g., Cookie, Host, Origin) -- the browser controls them.
  - res.headers.get() returns null if the header is absent, not
    undefined.
  - CORS may hide response headers; the server must send
    Access-Control-Expose-Headers to make custom headers visible.
*/


// ============================================================
// 4. BASIC -- ERROR HANDLING (NETWORK vs HTTP ERRORS)
// ============================================================
// [BASIC]
// INTERVIEW: "Does fetch reject on a 404 or 500?"
//   - NO. fetch only rejects on network-level failures.
//   - HTTP error statuses (4xx, 5xx) resolve normally.
//   - You MUST check response.ok or response.status yourself.

// --- Proper error handling --------------------------------------
async function fetchWithErrorHandling() {
  try {
    const res = await fetch(`${API}/posts/99999`);

    // HTTP errors (4xx, 5xx) -- fetch does NOT reject these
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    const data = await res.json();
    console.log("Success:", data);
  } catch (err) {
    // Network errors (offline, DNS, CORS) end up here
    // AbortError also ends up here
    if (err.name === "AbortError") {
      console.log("Request was cancelled");
    } else if (err.name === "TypeError") {
      // TypeError: Failed to fetch -- usually network / CORS
      console.error("Network error:", err.message);
    } else {
      console.error("Error:", err.message);
    }
  }
}
// fetchWithErrorHandling();

// --- Helper: throw on non-OK responses --------------------------
async function handleResponse(res) {
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${body || res.statusText}`);
  }
  return res.json();
}

// Usage:
// const data = await fetch(url).then(handleResponse);

/*
  GOTCHAS -- ERROR HANDLING
  --------------------------
  - A CORS failure looks like a TypeError("Failed to fetch") with
    NO status code -- indistinguishable from being offline.
  - res.json() throws SyntaxError if the body is not valid JSON.
    Wrap it in try/catch or check Content-Type first.
  - You can only consume a Response body ONCE. Calling .json()
    after .text() on the same response throws.
    Use res.clone() if you need to read the body twice.
  - response.ok is shorthand for status >= 200 && status < 300.
*/


// ============================================================
// 5. INTERMEDIATE -- ABORTCONTROLLER (CANCELLATION)
// ============================================================
// [INTERMEDIATE]
// INTERVIEW: "How do you cancel a fetch request?"
//   - Create an AbortController, pass its signal to fetch.
//   - Call controller.abort() to cancel.
//   - The fetch promise rejects with an AbortError.
//   - Useful for: search-as-you-type, component unmount cleanup,
//     racing requests, and timeouts.

async function fetchWithAbort() {
  const controller = new AbortController();

  // Cancel after 3 seconds for demo purposes
  setTimeout(() => controller.abort(), 3000);

  try {
    const res = await fetch(`${API}/posts`, {
      signal: controller.signal,
    });
    const data = await res.json();
    console.log("Data:", data);
  } catch (err) {
    if (err.name === "AbortError") {
      console.log("Fetch aborted by user / timeout");
    } else {
      throw err; // re-throw unexpected errors
    }
  }
}
// fetchWithAbort();

// --- React useEffect cleanup example ----------------------------
/*
  useEffect(() => {
    const controller = new AbortController();

    fetch(`/api/data`, { signal: controller.signal })
      .then(res => res.json())
      .then(setData)
      .catch(err => {
        if (err.name !== "AbortError") console.error(err);
      });

    return () => controller.abort();   // cleanup on unmount
  }, []);
*/

// --- AbortSignal.timeout() (modern browsers) --------------------
// [INTERMEDIATE]
// A simpler built-in alternative to manual setTimeout + abort.
async function fetchWithSignalTimeout() {
  try {
    const res = await fetch(`${API}/posts`, {
      signal: AbortSignal.timeout(5000), // auto-abort after 5s
    });
    const data = await res.json();
    console.log("Data:", data);
  } catch (err) {
    if (err.name === "TimeoutError") {
      console.log("Request timed out (AbortSignal.timeout)");
    } else if (err.name === "AbortError") {
      console.log("Request aborted");
    } else {
      throw err;
    }
  }
}
// fetchWithSignalTimeout();

/*
  GOTCHAS -- ABORTCONTROLLER
  ---------------------------
  - One AbortController can cancel MULTIPLE fetches that share
    its signal. Calling abort() cancels ALL of them.
  - Once aborted, the controller is spent. Create a NEW controller
    for the next batch of requests.
  - AbortSignal.timeout() throws TimeoutError (not AbortError)
    in modern browsers. Check for both.
  - In Node.js < 17.3, AbortController must be polyfilled.
  - signal.reason can carry a custom abort reason (newer API):
      controller.abort("user navigated away");
*/


// ============================================================
// 6. INTERMEDIATE -- TIMEOUT PATTERN
// ============================================================
// [INTERMEDIATE]
// INTERVIEW: "fetch has no built-in timeout -- how do you add one?"
//   - Race fetch against a timer promise.
//   - Or use AbortSignal.timeout() (modern API, shown above).

function fetchWithTimeout(url, options = {}, timeoutMs = 5000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  return fetch(url, { ...options, signal: controller.signal })
    .then((res) => {
      clearTimeout(timer);
      return res;
    })
    .catch((err) => {
      clearTimeout(timer);
      if (err.name === "AbortError") {
        throw new Error(`Request timed out after ${timeoutMs}ms`);
      }
      throw err;
    });
}

// Usage:
// const res = await fetchWithTimeout(`${API}/posts`, {}, 3000);

// --- Alternative: Promise.race approach -------------------------
function fetchWithTimeoutRace(url, options = {}, timeoutMs = 5000) {
  const timeout = new Promise((_, reject) =>
    setTimeout(() => reject(new Error("Request timed out")), timeoutMs)
  );
  return Promise.race([fetch(url, options), timeout]);
}

/*
  GOTCHAS -- TIMEOUT
  -------------------
  - The Promise.race approach does NOT cancel the underlying fetch.
    The request keeps running in the background. Prefer
    AbortController to actually cancel the network request.
  - clearTimeout is important to avoid memory leaks if the fetch
    resolves before the timer fires.
*/


// ============================================================
// 7. INTERMEDIATE -- FILE UPLOAD WITH FORMDATA
// ============================================================
// [INTERMEDIATE]
// INTERVIEW: "How do you upload files with fetch?"
//   - Use FormData. Do NOT set Content-Type manually -- the browser
//     sets it to multipart/form-data WITH the correct boundary.

async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);             // File or Blob
  formData.append("description", "My upload");

  const res = await fetch(`${API}/posts`, {
    method: "POST",
    body: formData,
    // Do NOT set Content-Type -- browser adds boundary automatically
  });

  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

// --- Upload with progress (XMLHttpRequest required) -------------
/*
  fetch() does NOT support upload progress out of the box.
  For progress tracking, use XMLHttpRequest:

  const xhr = new XMLHttpRequest();
  xhr.upload.onprogress = (e) => {
    const pct = Math.round((e.loaded / e.total) * 100);
    console.log(`Upload: ${pct}%`);
  };
  xhr.open("POST", url);
  xhr.send(formData);
*/

/*
  GOTCHAS -- FILE UPLOAD
  -----------------------
  - Setting Content-Type to "multipart/form-data" manually BREAKS
    the upload because it omits the boundary string.
  - FormData can hold File, Blob, or string values.
  - Large file uploads should use chunked transfer or resumable
    upload protocols (e.g., tus).
  - fetch does NOT fire upload progress events. Use XMLHttpRequest
    or a library like axios if you need progress tracking.
*/


// ============================================================
// 8. INTERMEDIATE -- PARALLEL REQUESTS (Promise.all)
// ============================================================
// [INTERMEDIATE]
// INTERVIEW: "How do you fetch multiple resources at once?"
//   - Promise.all: fails fast if ANY request fails.
//   - Promise.allSettled: waits for all; returns status per promise.

// --- Promise.all (fail-fast) ------------------------------------
async function fetchParallel() {
  try {
    const [posts, comments, users] = await Promise.all([
      fetch(`${API}/posts?_limit=5`).then(handleResponse),
      fetch(`${API}/comments?_limit=5`).then(handleResponse),
      fetch(`${API}/users?_limit=5`).then(handleResponse),
    ]);
    console.log("Posts:", posts.length);
    console.log("Comments:", comments.length);
    console.log("Users:", users.length);
  } catch (err) {
    console.error("One request failed, all results lost:", err);
  }
}
// fetchParallel();

// --- Promise.allSettled (no fail-fast) --------------------------
async function fetchParallelSettled() {
  const results = await Promise.allSettled([
    fetch(`${API}/posts?_limit=5`).then(handleResponse),
    fetch(`${API}/invalid-endpoint`).then(handleResponse),
    fetch(`${API}/users?_limit=5`).then(handleResponse),
  ]);

  results.forEach((result, i) => {
    if (result.status === "fulfilled") {
      console.log(`Request ${i}: OK, ${result.value.length} items`);
    } else {
      console.log(`Request ${i}: FAILED, ${result.reason.message}`);
    }
  });
}
// fetchParallelSettled();

/*
  GOTCHAS -- PARALLEL REQUESTS
  -----------------------------
  - Promise.all rejects as soon as ONE promise rejects -- all
    other results are discarded (even if they succeeded).
  - Promise.allSettled never rejects; it returns an array of
    { status: "fulfilled", value } or { status: "rejected", reason }.
  - Browsers limit concurrent connections per host (typically 6).
    Fetching 100 URLs simultaneously queues most of them.
  - For ordered sequential execution, use a for...of loop with
    await, not Promise.all.
*/


// ============================================================
// 9. ADVANCED -- RETRY PATTERN (EXPONENTIAL BACKOFF)
// ============================================================
// [ADVANCED]
// INTERVIEW: "How would you implement retry logic for fetch?"
//   - Retry on transient failures (5xx, network errors).
//   - Use exponential backoff to avoid hammering the server.
//   - Cap the number of retries.

async function fetchWithRetry(url, options = {}, maxRetries = 3) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const res = await fetch(url, options);

      // Retry only on server errors (5xx) or 429 (rate limit)
      if (res.status >= 500 || res.status === 429) {
        // Check for Retry-After header
        const retryAfter = res.headers.get("Retry-After");
        if (retryAfter && attempt < maxRetries) {
          const delayMs = isNaN(retryAfter)
            ? Date.parse(retryAfter) - Date.now()   // HTTP-date
            : Number(retryAfter) * 1000;             // seconds
          await sleep(Math.max(delayMs, 0));
          continue;
        }
        if (attempt < maxRetries) {
          await sleep(getBackoff(attempt));
          continue;
        }
      }

      return res; // success or non-retryable status
    } catch (err) {
      // Network error -- retry if attempts remain
      if (attempt === maxRetries) throw err;
      await sleep(getBackoff(attempt));
    }
  }
}

function getBackoff(attempt) {
  // Exponential backoff: 1s, 2s, 4s... with jitter
  const base = Math.pow(2, attempt) * 1000;
  const jitter = Math.random() * 1000;
  return base + jitter;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Usage:
// const res = await fetchWithRetry(`${API}/posts`, {}, 3);
// const data = await res.json();

/*
  GOTCHAS -- RETRY
  -----------------
  - Never retry POST/PUT/DELETE blindly -- they may not be
    idempotent. The server might process the request even though
    you got a timeout.
  - Always cap retries. Infinite retries can DDoS your own server.
  - Jitter prevents "thundering herd" when many clients retry
    at the exact same backoff interval.
  - 429 (Too Many Requests) often includes a Retry-After header.
    Respect it instead of using your own backoff.
*/


// ============================================================
// 10. ADVANCED -- INTERCEPTOR PATTERN (WRAPPER)
// ============================================================
// [ADVANCED]
// INTERVIEW: "fetch has no interceptors like axios. How do you
//             add request/response interceptors?"
//   - Wrap fetch in a function that runs hooks before/after.
//   - This is the pattern used by libraries and production apps.

function createFetchClient(baseURL = "", defaultOptions = {}) {
  const requestInterceptors = [];
  const responseInterceptors = [];

  async function client(endpoint, options = {}) {
    const url = `${baseURL}${endpoint}`;
    let config = { ...defaultOptions, ...options };

    // --- Run request interceptors ---
    for (const interceptor of requestInterceptors) {
      config = await interceptor(config);
    }

    let response = await fetch(url, config);

    // --- Run response interceptors ---
    for (const interceptor of responseInterceptors) {
      response = await interceptor(response);
    }

    return response;
  }

  client.addRequestInterceptor = (fn) => requestInterceptors.push(fn);
  client.addResponseInterceptor = (fn) => responseInterceptors.push(fn);

  return client;
}

// --- Usage example -----------------------------------------------
/*
  const api = createFetchClient(API, {
    headers: { "Content-Type": "application/json" },
  });

  // Add auth token to every request
  api.addRequestInterceptor((config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers = { ...config.headers, Authorization: `Bearer ${token}` };
    }
    return config;
  });

  // Log every response status
  api.addResponseInterceptor((response) => {
    console.log(`[${response.status}] ${response.url}`);
    return response;
  });

  // Auto-refresh token on 401
  api.addResponseInterceptor(async (response) => {
    if (response.status === 401) {
      await refreshToken();
      // Retry original request with new token...
    }
    return response;
  });

  const res = await api("/posts");
  const data = await res.json();
*/

/*
  GOTCHAS -- INTERCEPTORS
  ------------------------
  - Interceptors run in the order they are added.
  - Response interceptors receive a Response object. If you
    consume the body (e.g., res.json()), later interceptors and
    the caller cannot read it. Use res.clone() if needed.
  - This pattern replaces axios interceptors but requires you
    to build it yourself (or use a library like ky or wretch).
*/


// ============================================================
// 11. ADVANCED -- STREAMING RESPONSES
// ============================================================
// [ADVANCED]
// INTERVIEW: "How do you handle streaming data with fetch?"
//   - Response.body is a ReadableStream.
//   - Use .getReader() to read chunks as they arrive.
//   - Useful for: large files, SSE, NDJSON, progress tracking.

async function fetchStream(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let result = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    result += chunk;
    console.log("Received chunk:", chunk.length, "bytes");
  }

  console.log("Total:", result.length, "bytes");
  return result;
}
// fetchStream(`${API}/posts`);

// --- Streaming with download progress ---------------------------
async function fetchWithProgress(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  const contentLength = +res.headers.get("Content-Length");
  const reader = res.body.getReader();
  let received = 0;
  const chunks = [];

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    received += value.length;
    if (contentLength) {
      console.log(`Progress: ${((received / contentLength) * 100).toFixed(1)}%`);
    }
  }

  // Merge chunks into a single Uint8Array
  const body = new Uint8Array(received);
  let pos = 0;
  for (const chunk of chunks) {
    body.set(chunk, pos);
    pos += chunk.length;
  }

  return new TextDecoder().decode(body);
}
// fetchWithProgress(`${API}/posts`);

// --- NDJSON (newline-delimited JSON) streaming -------------------
async function fetchNDJSON(url) {
  const res = await fetch(url);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop(); // keep incomplete line in buffer

    for (const line of lines) {
      if (line.trim()) {
        const obj = JSON.parse(line);
        console.log("Parsed object:", obj);
      }
    }
  }
}

/*
  GOTCHAS -- STREAMING
  ---------------------
  - res.body is null for HEAD requests and 204 No Content.
  - You CANNOT call res.json() after reading from res.body
    manually -- the body is already consumed.
  - TextDecoder with { stream: true } handles multi-byte chars
    split across chunks. Without it, you get garbled text.
  - ReadableStream is not available in older browsers or in some
    Node.js versions (use node-fetch v3+).
  - Once the reader is locked, no other consumer can read the
    stream. Call reader.releaseLock() if you need to hand off.
*/


// ============================================================
// 12. COMPARISON TABLES
// ============================================================

/*
  FETCH vs XMLHTTPREQUEST vs AXIOS
  =================================

  +-------------------------+----------+----------------+----------+
  | Feature                 | fetch    | XMLHttpRequest | axios    |
  +-------------------------+----------+----------------+----------+
  | Promise-based           | Yes      | No (callbacks) | Yes      |
  | Streaming response      | Yes      | Partial        | No*      |
  | Upload progress         | No       | Yes            | Yes      |
  | Download progress       | Manual** | Yes            | Yes      |
  | Request cancellation    | Yes***   | Yes (.abort()) | Yes      |
  | Interceptors            | No       | No             | Yes      |
  | Automatic JSON parse    | No       | No             | Yes      |
  | Timeout option          | No****   | Yes            | Yes      |
  | Reject on HTTP errors   | No       | No             | Yes      |
  | XSRF protection         | No       | No             | Yes      |
  | Browser support         | Modern   | All            | All*****|
  | Node.js built-in        | v18+     | No             | No       |
  | Bundle size             | 0 KB     | 0 KB           | ~13 KB   |
  +-------------------------+----------+----------------+----------+

  *   axios can stream in Node.js with responseType: "stream".
  **  via ReadableStream + getReader() (manual work).
  *** via AbortController (separate object, not on fetch itself).
  **** AbortSignal.timeout() added in modern browsers / Node 18+.
  ***** axios uses XMLHttpRequest in browser, http in Node.js.


  WHEN TO USE WHAT
  =================

  +------------------+--------------------------------------------+
  | Use case         | Recommendation                             |
  +------------------+--------------------------------------------+
  | Simple app,      | fetch -- zero dependencies, built-in       |
  | few requests     |                                            |
  +------------------+--------------------------------------------+
  | Complex app,     | axios or fetch wrapper (ky, wretch) --     |
  | many endpoints   | interceptors, auto-retry, transforms       |
  +------------------+--------------------------------------------+
  | File upload with | XMLHttpRequest or axios -- fetch cannot     |
  | progress bar     | track upload progress natively              |
  +------------------+--------------------------------------------+
  | Legacy browser   | XMLHttpRequest or axios -- fetch needs      |
  | support (IE 11)  | a polyfill                                  |
  +------------------+--------------------------------------------+
  | SSR / Node.js    | fetch (v18+) or node-fetch                  |
  +------------------+--------------------------------------------+
  | Streaming / SSE  | fetch -- native ReadableStream support      |
  +------------------+--------------------------------------------+


  FETCH OPTIONS REFERENCE
  ========================

  fetch(url, {
    method,           // "GET" | "POST" | "PUT" | "PATCH" | "DELETE" | "HEAD" | "OPTIONS"
    headers,          // Headers object or plain object
    body,             // string | Blob | ArrayBuffer | FormData | URLSearchParams | ReadableStream
    mode,             // "cors" | "no-cors" | "same-origin"
    credentials,      // "omit" | "same-origin" | "include"
    cache,            // "default" | "no-store" | "reload" | "no-cache" | "force-cache" | "only-if-cached"
    redirect,         // "follow" | "error" | "manual"
    referrer,         // "" | "no-referrer" | URL string
    referrerPolicy,   // "no-referrer" | "origin" | "same-origin" | ...
    integrity,        // subresource integrity hash
    keepalive,        // keep connection alive after page unload (for analytics beacons)
    signal,           // AbortSignal for cancellation
    priority,         // "high" | "low" | "auto" (Fetch Priority API)
  })


  RESPONSE OBJECT PROPERTIES
  ============================

  response.ok              // boolean -- true if status 200-299
  response.status          // number  -- HTTP status code (200, 404, etc.)
  response.statusText      // string  -- "OK", "Not Found", etc.
  response.headers         // Headers object (iterable)
  response.url             // string  -- final URL after redirects
  response.redirected      // boolean -- true if response is from a redirect
  response.type            // "basic" | "cors" | "opaque" | ...
  response.body            // ReadableStream (or null)
  response.bodyUsed        // boolean -- true if body already consumed

  response.json()          // Promise<any>    -- parse body as JSON
  response.text()          // Promise<string> -- read body as text
  response.blob()          // Promise<Blob>   -- read body as Blob
  response.arrayBuffer()   // Promise<ArrayBuffer>
  response.formData()      // Promise<FormData>
  response.clone()         // Response -- clone for multiple reads
*/


// ============================================================
// 13. GOTCHAS CHEAT-SHEET (ALL-IN-ONE)
// ============================================================

/*
  FETCH API -- MASTER GOTCHAS LIST
  ==================================

  1. fetch does NOT reject on 4xx/5xx.
     Always check response.ok or response.status.

  2. fetch does NOT have a built-in timeout.
     Use AbortController or AbortSignal.timeout().

  3. Setting Content-Type on FormData BREAKS file uploads.
     The browser must set multipart/form-data with the boundary.

  4. Response body can only be consumed ONCE.
     Use response.clone() before consuming if you need it twice.

  5. credentials default to "same-origin".
     To send cookies cross-origin, set credentials: "include".

  6. CORS errors appear as TypeError("Failed to fetch").
     You cannot distinguish them from network-offline errors in JS.

  7. fetch does NOT send cookies by default in cross-origin mode.
     You need credentials: "include" AND the server must send
     Access-Control-Allow-Credentials: true.

  8. AbortController is single-use. Once aborted, create a new one.

  9. No built-in interceptors, retries, or request transforms.
     Wrap fetch or use a library (ky, wretch, axios).

  10. In Node.js < 18, fetch is NOT available.
      Use node-fetch or undici.

  11. keepalive: true is needed for analytics beacons sent
      during page unload (navigator.sendBeacon is simpler).

  12. response.json() throws SyntaxError on empty or invalid JSON.
      Check Content-Type or Content-Length before parsing.

  13. HEAD requests return a Response with a null body.
      Calling .json() or .text() on it throws.

  14. The Request object created from fetch options is read-only.
      You cannot modify a Request after creation (clone and
      recreate instead).

  15. query parameters must be manually appended to the URL.
      fetch does NOT accept a "params" option like axios.
      Use URLSearchParams to build query strings.
*/


// ============================================================
// INTERVIEW TIPS -- RAPID-FIRE Q&A
// ============================================================

/*
  Q: "What does fetch return?"
  A: A Promise<Response>. It resolves when headers arrive.

  Q: "Does fetch throw on a 404?"
  A: No. It resolves with response.ok === false. Only network
     errors and aborts cause rejection.

  Q: "How do you send JSON with fetch?"
  A: Set Content-Type to "application/json" and call
     JSON.stringify() on the body object.

  Q: "How do you cancel a fetch?"
  A: Create an AbortController, pass signal to fetch, call
     controller.abort(). Catch the AbortError.

  Q: "What's the difference between fetch and axios?"
  A: fetch is native, lower-level, no auto-JSON, no interceptors,
     no reject on HTTP errors. axios adds all of those plus
     upload progress and request/response transforms.

  Q: "Can you track upload progress with fetch?"
  A: No. Use XMLHttpRequest.upload.onprogress or a library.
     Download progress is possible via ReadableStream.

  Q: "How do you handle streaming with fetch?"
  A: Read response.body (a ReadableStream) with getReader().
     Loop over reader.read() until done === true.

  Q: "What is the credentials option?"
  A: Controls whether cookies are sent.
     "omit" = never, "same-origin" = same domain only,
     "include" = always (even cross-origin).

  Q: "How does fetch handle redirects?"
  A: By default (redirect: "follow"), fetch follows redirects
     transparently. Set "manual" to inspect them yourself,
     or "error" to reject on any redirect.

  Q: "Is fetch available in Node.js?"
  A: Built-in since Node 18 (using undici). Before that,
     use the node-fetch package.
*/
