// ============================================================
//  ULTIMATE QUICK-REFERENCE:
//  Decorators, Debounce, and Throttle in JavaScript
// ============================================================
//
//  TABLE OF CONTENTS
//  -----------------
//  1. DECORATOR FUNCTIONS
//     1a. [BASIC]        Call Counter Decorator
//     1b. [BASIC]        Param Validation Decorators (countParams + requiresIntegers)
//     1c. [INTERMEDIATE] Async Timing Decorator (dataResponseTime)
//     1d.                Gotchas
//
//  2. DEBOUNCE
//     2a. [BASIC]        Concept + ASCII Timeline
//     2b. [BASIC]        Minimal Debounce Implementation
//     2c. [BASIC]        Input Box Example
//     2d. [INTERMEDIATE] Button Click Example
//     2e. [INTERMEDIATE] Leading-Edge Debounce
//     2f. [ADVANCED]     Full-Featured Debounce (leading, trailing, maxWait, cancel, flush)
//     2g. [ADVANCED]     Lodash-Style Debounce API
//     2h.                Gotchas
//
//  3. THROTTLE
//     3a. [BASIC]        Concept + ASCII Timeline
//     3b. [BASIC]        Minimal Throttle Implementation
//     3c. [BASIC]        Click + Scroll Examples
//     3d. [INTERMEDIATE] Button-Disable Throttle Pattern
//     3e. [INTERMEDIATE] Leading vs Trailing Throttle
//     3f. [ADVANCED]     requestAnimationFrame Throttle
//     3g. [ADVANCED]     Full-Featured Throttle (leading, trailing, cancel)
//     3h.                Gotchas
//
//  4. DEBOUNCE vs THROTTLE -- COMPARISON TABLES
//  5. REAL-WORLD USE CASES TABLE
//  6. INTERVIEW QUICK-FIRE
// ============================================================


// ============================================================
// 1. DECORATOR FUNCTIONS
// ============================================================
// A decorator wraps a function in another function, adding
// new capabilities without modifying the original.
//
// Pattern:
//   const decorator = (fn) => (...args) => { /* extra logic */ return fn(...args); }
//   originalFn = decorator(originalFn);
//
// INTERVIEW: "What is a decorator?" -- A higher-order function that takes a function
// and returns a new function with augmented behavior. JavaScript does not have native
// decorator syntax for plain functions (TC39 Stage 3 decorators target classes/methods),
// so we use the wrapper pattern shown below.


// ------------------------------------------------------------
// 1a. Call Counter Decorator [BASIC]
// ------------------------------------------------------------
// Uses closure to track how many times a function is called.

let sum = (...args) => args.reduce((acc, num) => acc + num);

const callCounter = (fn) => {
  let counter = 0;
  return (...args) => {
    console.log(`${fn.name || "fn"} called ${++counter} time(s)`);
    return fn(...args);
  };
};

sum = callCounter(sum);
console.log(sum(2, 3, 5)); // "fn called 1 time(s)" -> 10
console.log(sum(1, 5));    // "fn called 2 time(s)" -> 6
console.log(sum(14, 5));   // "fn called 3 time(s)" -> 19


// ------------------------------------------------------------
// 1b. Param Validation Decorators [BASIC]
// ------------------------------------------------------------
// Stack multiple decorators: countParams checks arity,
// requiresIntegers checks types. Order matters --
// outermost decorator runs first.

let rectangleArea = (length, width) => length * width;

const countParams = (fn) => {
  return (...params) => {
    if (params.length !== fn.length) {
      throw new Error(`Expected ${fn.length} params for ${fn.name}, got ${params.length}`);
    }
    return fn(...params);
  };
};

const requiresIntegers = (fn) => {
  return (...params) => {
    params.forEach((param) => {
      if (!Number.isInteger(param)) {
        throw new TypeError(`Params for ${fn.name} must be integers`);
      }
    });
    return fn(...params);
  };
};

// Stacking decorators (applied inside-out: requiresIntegers runs after countParams)
rectangleArea = countParams(rectangleArea);
rectangleArea = requiresIntegers(rectangleArea);
// console.log(rectangleArea(20, 30));      // 600
// console.log(rectangleArea(20, "30"));    // TypeError
// console.log(rectangleArea(20, 30, 300)); // Error: Expected 2 params


// ------------------------------------------------------------
// 1c. Async Timing Decorator [INTERMEDIATE]
// ------------------------------------------------------------
// Measures how long an async API call takes. Useful during development.

let requestData = async (url) => {
  try {
    const response = await fetch(url);
    return response.json();
  } catch (error) {
    console.error(error);
  }
};

const dataResponseTime = (fn) => {
  return async (url) => {
    console.time("request");
    const data = await fn(url);
    console.timeEnd("request");
    return data;
  };
};

const myTestFunction = async () => {
  requestData = dataResponseTime(requestData);
  const data = await requestData("https://jsonplaceholder.typicode.com/posts");
  console.log(data);
};
myTestFunction();


// ------------------------------------------------------------
// 1d. Decorator GOTCHAS
// ------------------------------------------------------------
//
// GOTCHA 1: Decorators lose the original function's `.name` and `.length`.
//   Workaround: Use Object.defineProperty to copy them, or use a library.
//
// GOTCHA 2: `this` context can be lost with arrow functions.
//   If the original function relies on `this`, use function() {} not =>
//   and call fn.apply(this, args) or fn.call(this, ...args).
//
// GOTCHA 3: Stacking order matters.
//   decoratorA(decoratorB(fn)) -- decoratorA's wrapper runs first,
//   then decoratorB's, then fn. Think of it like middleware.
//
// GOTCHA 4: Decorated functions are NOT the same reference.
//   fn !== decorator(fn). If something holds a reference to the
//   original, it will not see the decorated version.


// ============================================================
// 2. DEBOUNCE
// ============================================================

// ------------------------------------------------------------
// 2a. Concept + ASCII Timeline [BASIC]
// ------------------------------------------------------------
//
// DEBOUNCE: "Wait until the caller stops calling, THEN fire once."
//
// Delay = 300ms. Each "X" = a call. "F" = function actually fires.
//
//  Calls:     X  X  X  X  X . . . . . . . . X  X . . . . . . .
//  Time (ms): 0  50 100 150 200             800 850
//  Timer:     [restarted each X]            [restarted]
//  Fires:                         F (at 500)              F (at 1150)
//                                 ^                       ^
//                                 |                       |
//                          300ms after                300ms after
//                          last call (200)            last call (850)
//
// The function ONLY fires after the caller has been QUIET for the
// full delay period. Every new call resets the timer.
//
// INTERVIEW: "When would you use debounce?"
// -- Search input (wait until user stops typing), window resize handler,
//    auto-save (wait until user stops editing), form validation.


// ------------------------------------------------------------
// 2b. Minimal Debounce Implementation [BASIC]
// ------------------------------------------------------------
// INTERVIEW: "Implement debounce from scratch."

const debounce = (fn, delay) => {
  let timerId;
  return (...args) => {
    clearTimeout(timerId);                   // Cancel previous timer
    timerId = setTimeout(() => {
      fn(...args);                           // Fire after delay of inactivity
    }, delay);
  };
};

// How it works:
// 1. Each call clears the previous setTimeout.
// 2. A new setTimeout is set for `delay` ms.
// 3. Only when no new calls arrive for `delay` ms does fn() execute.


// ------------------------------------------------------------
// 2c. Input Box Example [BASIC]
// ------------------------------------------------------------
// Debounce user input -- only fire after 2 seconds of no typing.
// Prevents firing an API call on every keystroke.

const initInput = () => {
  const inputBox = document.querySelector("input");
  inputBox.addEventListener("input", debounce(onchangeHandler, 2000));
};

const onchangeHandler = (e) => console.log(e.target.value);

document.addEventListener("DOMContentLoaded", initInput);


// ------------------------------------------------------------
// 2d. Button Click Example [INTERMEDIATE]
// ------------------------------------------------------------
// Prevent rapid-fire button clicks from spamming an action.

// const initApp = () => {
//   const button = document.querySelector("button");
//   button.addEventListener("click", debounce(clickLog, 3000));
// };
// const clickLog = () => console.log("button clicked");
// document.addEventListener("DOMContentLoaded", initApp);


// ------------------------------------------------------------
// 2e. Leading-Edge Debounce [INTERMEDIATE]
// ------------------------------------------------------------
// INTERVIEW: "What is leading vs trailing debounce?"
//
// TRAILING (default): fires AFTER the delay.  (shown above)
// LEADING:            fires IMMEDIATELY on first call, then ignores
//                     subsequent calls until quiet for `delay` ms.
//
//  Calls:     X  X  X  X . . . . . X  X . . . . .
//  Leading:   F  .  .  . . . . . . F  . . . . . .
//  Trailing:  .  .  .  . . . . F . .  . . . . F .
//
// Leading is useful for: button clicks (fire immediately, prevent double-submit).

const debounceLeading = (fn, delay) => {
  let timerId;
  return (...args) => {
    if (!timerId) {
      fn(...args);                           // Fire immediately on first call
    }
    clearTimeout(timerId);
    timerId = setTimeout(() => {
      timerId = null;                        // Reset -- next call will fire immediately
    }, delay);
  };
};


// ------------------------------------------------------------
// 2f. Full-Featured Debounce [ADVANCED]
// ------------------------------------------------------------
// Supports: leading, trailing, maxWait, cancel, flush, pending.
//
// maxWait: guarantees the function fires at least every maxWait ms
// even if calls keep coming. This is how lodash's maxWait works.
//
// INTERVIEW: "How would you add a maxWait to debounce?"

const debounceAdvanced = (fn, delay, options = {}) => {
  const { leading = false, trailing = true, maxWait = null } = options;

  let timerId = null;
  let lastCallTime = null;
  let lastInvokeTime = 0;
  let lastArgs = null;
  let lastThis = null;
  let result;

  const invoke = (time) => {
    const args = lastArgs;
    const thisArg = lastThis;
    lastArgs = lastThis = null;
    lastInvokeTime = time;
    result = fn.apply(thisArg, args);
    return result;
  };

  const startTimer = (pendingFn, wait) => {
    timerId = setTimeout(pendingFn, wait);
  };

  const remainingWait = (time) => {
    const timeSinceLastCall = time - lastCallTime;
    const timeSinceLastInvoke = time - lastInvokeTime;
    const timeWaiting = delay - timeSinceLastCall;
    return maxWait !== null
      ? Math.min(timeWaiting, maxWait - timeSinceLastInvoke)
      : timeWaiting;
  };

  const shouldInvoke = (time) => {
    const timeSinceLastCall = time - lastCallTime;
    const timeSinceLastInvoke = time - lastInvokeTime;
    return (
      lastCallTime === null ||                         // First call
      timeSinceLastCall >= delay ||                     // Enough idle time
      timeSinceLastCall < 0 ||                          // System clock adjusted
      (maxWait !== null && timeSinceLastInvoke >= maxWait)  // maxWait exceeded
    );
  };

  const timerExpired = () => {
    const time = Date.now();
    if (shouldInvoke(time)) {
      return trailingEdge(time);
    }
    startTimer(timerExpired, remainingWait(time));
  };

  const leadingEdge = (time) => {
    lastInvokeTime = time;
    startTimer(timerExpired, delay);
    return leading ? invoke(time) : result;
  };

  const trailingEdge = (time) => {
    timerId = null;
    if (trailing && lastArgs) {
      return invoke(time);
    }
    lastArgs = lastThis = null;
    return result;
  };

  // --- Public API ---

  const debounced = function (...args) {
    const time = Date.now();
    const isInvoking = shouldInvoke(time);
    lastArgs = args;
    lastThis = this;
    lastCallTime = time;

    if (isInvoking && timerId === null) {
      return leadingEdge(time);
    }
    if (timerId === null) {
      startTimer(timerExpired, delay);
    }
    return result;
  };

  debounced.cancel = () => {
    if (timerId !== null) clearTimeout(timerId);
    lastInvokeTime = 0;
    lastArgs = lastCallTime = lastThis = timerId = null;
  };

  debounced.flush = () => {
    return timerId === null ? result : trailingEdge(Date.now());
  };

  debounced.pending = () => {
    return timerId !== null;
  };

  return debounced;
};

// Usage:
// const search = debounceAdvanced(apiCall, 300, { leading: false, trailing: true, maxWait: 1000 });
// search.cancel();   // Cancel pending execution
// search.flush();    // Execute immediately if pending
// search.pending();  // Check if a call is scheduled


// ------------------------------------------------------------
// 2g. Lodash-Style Debounce API Reference [ADVANCED]
// ------------------------------------------------------------
// _.debounce(func, [wait=0], [options={}])
//
// options.leading   = false  -- Invoke on the leading edge
// options.trailing  = true   -- Invoke on the trailing edge
// options.maxWait   = --     -- Max time fn can be delayed (turns debounce into throttle-like)
//
// Returns: debounced function with .cancel(), .flush(), .pending()
//
// INTERVIEW: "What is the difference between _.debounce with maxWait and _.throttle?"
// Answer: _.throttle(fn, wait) is shorthand for _.debounce(fn, wait, { leading: true, trailing: true, maxWait: wait })
// They are functionally equivalent. Throttle IS debounce with maxWait = wait.


// ------------------------------------------------------------
// 2h. Debounce GOTCHAS
// ------------------------------------------------------------
//
// GOTCHA 1: Event object reuse. In React, synthetic events are pooled.
//   If you debounce a handler, the event may be nullified by the time
//   the debounced function runs. Fix: call e.persist() or extract
//   the value first: const value = e.target.value;
//
// GOTCHA 2: Memory leaks. If a component unmounts while a debounced
//   call is pending, the callback fires on a stale closure.
//   Fix: call debounced.cancel() in componentWillUnmount / useEffect cleanup.
//
// GOTCHA 3: Arrow functions in render create a NEW debounced function every render.
//   Fix: useRef or useMemo to persist the debounced function across renders.
//     const debouncedFn = useRef(debounce(handler, 300)).current;
//
// GOTCHA 4: `this` binding. If fn uses `this` (e.g., a class method),
//   the debounce wrapper must preserve context via fn.apply(this, args).
//   Arrow function wrappers do NOT have their own `this`.
//
// GOTCHA 5: Return values. A debounced function returns undefined on
//   the trailing edge because it fires asynchronously. If you need the
//   return value, use a Promise-based debounce or a callback pattern.


// ============================================================
// 3. THROTTLE
// ============================================================

// ------------------------------------------------------------
// 3a. Concept + ASCII Timeline [BASIC]
// ------------------------------------------------------------
//
// THROTTLE: "Fire at most once every N ms, no matter how many calls."
//
// Delay = 300ms. Each "X" = a call. "F" = function actually fires.
//
//  Calls:     X  X  X  X  X  X  X  X  X  X  X  X  X  X  X
//  Time (ms): 0  50 100 150 200 250 300 350 400 450 500 550 600 650 700
//  Fires:     F  .  .  .  .  .  F  .  .  .  .  .  F  .  .
//             ^                 ^                 ^
//             |                 |                 |
//          Fires immediately  300ms later       300ms later
//          (leading edge)
//
// Unlike debounce, throttle guarantees REGULAR execution while calls
// keep coming. The function fires on a fixed schedule.
//
// INTERVIEW: "When would you use throttle?"
// -- Scroll handlers, resize handlers, mousemove tracking, game loop
//    updates, rate-limiting API calls, infinite scroll loading.


// ------------------------------------------------------------
// 3b. Minimal Throttle Implementation [BASIC]
// ------------------------------------------------------------
// INTERVIEW: "Implement throttle from scratch."

const throttle = (fn, delay) => {
  let lastTime = 0;
  return (...args) => {
    const now = Date.now();
    if (now - lastTime < delay) return;      // Too soon -- skip
    lastTime = now;
    fn(...args);                             // Enough time passed -- fire
  };
};

// How it works:
// 1. Track the timestamp of the last invocation.
// 2. On each call, check if enough time has elapsed.
// 3. If yes, invoke fn and update the timestamp. If no, do nothing.


// ------------------------------------------------------------
// 3c. Click + Scroll Examples [BASIC]
// ------------------------------------------------------------

const initApp = () => {
  const button = document.getElementById("throttle");
  button.addEventListener("click", throttle(clickLog, 4000));
  window.addEventListener("scroll", throttle(scrollLog, 3000));
};

const clickLog = () => console.log("throttle logged");
const scrollLog = () => console.log("scroll log");

document.addEventListener("DOMContentLoaded", initApp);


// ------------------------------------------------------------
// 3d. Button-Disable Throttle Pattern [INTERMEDIATE]
// ------------------------------------------------------------
// Alternative to timestamp-based throttle: disable the button via DOM,
// re-enable after delay. Simple but tightly coupled to the UI.

const myThrottle = (fn, d) => {
  return function (...args) {
    const btn = document.getElementById("clickme");
    btn.disabled = true;
    setTimeout(() => {
      fn(...args);
      btn.disabled = false;
    }, d);
  };
};

const newFun = myThrottle(() => {
  console.log("User clicked");
}, 5000);


// ------------------------------------------------------------
// 3e. Leading vs Trailing Throttle [INTERMEDIATE]
// ------------------------------------------------------------
// INTERVIEW: "What is leading vs trailing throttle?"
//
// LEADING (default):  fires at the START of each interval.
// TRAILING:           fires at the END of each interval.
// BOTH:               fires at start AND end (lodash default).
//
//  Calls:     X  X  X  X  X  X  X  X  X  X  X  X  .  .  .
//  Leading:   F  .  .  .  .  .  F  .  .  .  .  .  .  .  .
//  Trailing:  .  .  .  .  .  .  F  .  .  .  .  .  F  .  .
//  Both:      F  .  .  .  .  .  F  .  .  .  .  .  F  .  .
//
// Leading is good for: immediate feedback (button clicks).
// Trailing is good for: final-state capture (scroll position).
// Both is good for: responsive + accurate (resize handlers).

const throttleWithEdges = (fn, delay, { leading = true, trailing = true } = {}) => {
  let lastTime = 0;
  let timerId = null;
  let lastArgs = null;
  let lastThis = null;

  const invoke = () => {
    fn.apply(lastThis, lastArgs);
    lastArgs = lastThis = null;
  };

  return function (...args) {
    const now = Date.now();
    lastArgs = args;
    lastThis = this;

    const elapsed = now - lastTime;

    if (elapsed >= delay) {
      // Enough time passed
      if (timerId) {
        clearTimeout(timerId);
        timerId = null;
      }
      if (leading) {
        lastTime = now;
        invoke();
      } else if (trailing) {
        lastTime = now;
        timerId = setTimeout(() => {
          lastTime = Date.now();
          timerId = null;
          invoke();
        }, delay);
      }
    } else if (trailing && !timerId) {
      // Schedule trailing call
      timerId = setTimeout(() => {
        lastTime = Date.now();
        timerId = null;
        invoke();
      }, delay - elapsed);
    }
  };
};


// ------------------------------------------------------------
// 3f. requestAnimationFrame Throttle [ADVANCED]
// ------------------------------------------------------------
// INTERVIEW: "How would you throttle using requestAnimationFrame?"
//
// rAF fires ~60 times/sec (once per frame). It automatically
// syncs with the browser's paint cycle, making it ideal for
// visual updates (scroll animations, parallax, canvas rendering).
//
// Advantage over setTimeout throttle:
// - Fires in sync with browser repaint (no jank)
// - Automatically paused in background tabs (saves CPU)
// - No need to guess a delay value

const throttleRAF = (fn) => {
  let rafId = null;
  const throttled = function (...args) {
    if (rafId) return;                        // Already scheduled for next frame
    rafId = requestAnimationFrame(() => {
      fn.apply(this, args);
      rafId = null;                           // Ready for next scheduling
    });
  };

  throttled.cancel = () => {
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
  };

  return throttled;
};

// Usage:
// window.addEventListener("scroll", throttleRAF(updateParallax));
// On cleanup: throttledFn.cancel();


// ------------------------------------------------------------
// 3g. Full-Featured Throttle (leading, trailing, cancel) [ADVANCED]
// ------------------------------------------------------------
// Production-quality throttle with all options.

const throttleAdvanced = (fn, delay, options = {}) => {
  const { leading = true, trailing = true } = options;

  let timerId = null;
  let lastArgs = null;
  let lastThis = null;
  let lastInvokeTime = 0;
  let result;

  const invoke = (time) => {
    const args = lastArgs;
    const thisArg = lastThis;
    lastArgs = lastThis = null;
    lastInvokeTime = time;
    result = fn.apply(thisArg, args);
    return result;
  };

  const startTimer = (pendingFn, wait) => {
    timerId = setTimeout(pendingFn, wait);
  };

  const timerExpired = () => {
    const now = Date.now();
    timerId = null;
    if (trailing && lastArgs) {
      invoke(now);
    } else {
      lastArgs = lastThis = null;
    }
  };

  const throttled = function (...args) {
    const now = Date.now();
    const timeSinceLastInvoke = now - lastInvokeTime;
    lastArgs = args;
    lastThis = this;

    if (timeSinceLastInvoke >= delay) {
      // Enough time passed
      if (timerId) {
        clearTimeout(timerId);
        timerId = null;
      }
      if (leading) {
        return invoke(now);
      }
    }

    if (!timerId && trailing) {
      const remaining = delay - timeSinceLastInvoke;
      startTimer(timerExpired, remaining > 0 ? remaining : delay);
    }

    return result;
  };

  // --- Public API ---
  throttled.cancel = () => {
    if (timerId) clearTimeout(timerId);
    lastInvokeTime = 0;
    lastArgs = lastThis = timerId = null;
  };

  throttled.flush = () => {
    if (timerId === null) return result;
    clearTimeout(timerId);
    timerId = null;
    if (lastArgs) return invoke(Date.now());
    return result;
  };

  return throttled;
};

// Usage:
// const onScroll = throttleAdvanced(handleScroll, 200, { leading: true, trailing: true });
// window.addEventListener("scroll", onScroll);
// onScroll.cancel();  // Cancel any pending trailing call
// onScroll.flush();   // Fire immediately if pending


// ------------------------------------------------------------
// 3h. Throttle GOTCHAS
// ------------------------------------------------------------
//
// GOTCHA 1: Timestamp throttle (3b) ONLY fires on the leading edge.
//   If the last call happens mid-interval, you miss the final state.
//   Fix: Use trailing: true (section 3e/3g) to capture the last call.
//
// GOTCHA 2: rAF throttle runs at ~16ms intervals (~60fps).
//   If your handler is expensive, even 60fps may cause jank.
//   Fix: Combine rAF with a timestamp check for longer intervals.
//
// GOTCHA 3: Throttled scroll/resize handlers can still fire after
//   component unmount. Fix: removeEventListener + throttled.cancel().
//
// GOTCHA 4: Date.now() can jump (clock skew, NTP sync, sleep/wake).
//   The minimal throttle (3b) handles this poorly.
//   The advanced version (3g) should check for negative elapsed time.
//
// GOTCHA 5: In React, do NOT create throttled functions inside render.
//   Same issue as debounce -- a new wrapper is created each render.
//   Fix: useRef or useMemo to persist across renders.


// ============================================================
// 4. DEBOUNCE vs THROTTLE -- COMPARISON TABLE
// ============================================================
//
// +------------------+-------------------------------+-------------------------------+
// | Aspect           | DEBOUNCE                      | THROTTLE                      |
// +------------------+-------------------------------+-------------------------------+
// | Core idea        | Wait for SILENCE, then fire   | Fire at REGULAR intervals     |
// +------------------+-------------------------------+-------------------------------+
// | When it fires    | After caller stops for N ms   | At most once every N ms       |
// +------------------+-------------------------------+-------------------------------+
// | Guarantee        | Fires ONCE after quiet period | Fires PERIODICALLY while busy |
// +------------------+-------------------------------+-------------------------------+
// | Rapid calls      | Resets timer on every call     | Ignores calls within interval |
// +------------------+-------------------------------+-------------------------------+
// | Cares about      | END state (final value)       | INTERMEDIATE states (progress)|
// +------------------+-------------------------------+-------------------------------+
// | Latency          | Adds delay to every response  | First call can fire instantly  |
// +------------------+-------------------------------+-------------------------------+
// | Starvation risk  | YES -- if calls never stop,   | NO -- fires on schedule       |
// |                  | function never fires (without  | regardless of call frequency  |
// |                  | maxWait)                      |                               |
// +------------------+-------------------------------+-------------------------------+
// | maxWait fixes    | YES -- adds throttle-like     | N/A (already guaranteed)      |
// | starvation?      | guarantee to debounce         |                               |
// +------------------+-------------------------------+-------------------------------+
//
// MENTAL MODEL:
// - Debounce = elevator doors: keep resetting as people arrive, close only after no one comes
// - Throttle = bus schedule: bus leaves every 15 minutes regardless of how many people show up


// ============================================================
// 5. REAL-WORLD USE CASES TABLE
// ============================================================
//
// +-----------------------------+----------+----------+-------------------------------------------+
// | Use Case                    | Debounce | Throttle | Why                                       |
// +-----------------------------+----------+----------+-------------------------------------------+
// | Search-as-you-type          |    X     |          | Wait for user to finish typing             |
// | Auto-save                   |    X     |          | Save after edits pause, not on every key   |
// | Form validation             |    X     |          | Validate when user stops changing input    |
// | Window resize (layout)      |    X     |          | Recalc layout once resizing stops          |
// +-----------------------------+----------+----------+-------------------------------------------+
// | Scroll position tracking    |          |    X     | Update position regularly while scrolling  |
// | Infinite scroll             |          |    X     | Check proximity to bottom at intervals     |
// | Mouse move / drag           |          |    X     | Track position without overwhelming        |
// | Game input polling          |          |    X     | Sample input at regular tick rate          |
// | API rate limiting           |          |    X     | Cap outgoing requests per second           |
// | Analytics event logging     |          |    X     | Log events at intervals, not every action  |
// +-----------------------------+----------+----------+-------------------------------------------+
// | Resize (smooth animation)   |          |    X     | Keep visual updates smooth during resize   |
// | Parallax / scroll animation |          |   rAF    | Sync with browser paint cycle              |
// | Canvas rendering            |          |   rAF    | Render at display refresh rate             |
// +-----------------------------+----------+----------+-------------------------------------------+
// | Search + loading indicator  |   both   |          | Debounce API call, throttle spinner toggle |
// | Window resize (responsive)  |   both   |          | Throttle for animation, debounce for final |
// +-----------------------------+----------+----------+-------------------------------------------+


// ============================================================
// 6. INTERVIEW QUICK-FIRE
// ============================================================
//
// INTERVIEW: "Implement debounce" -- See 2b.
// INTERVIEW: "Implement throttle" -- See 3b.
// INTERVIEW: "Leading vs trailing" -- See 2e, 3e.
// INTERVIEW: "What is maxWait in debounce?" -- A cap on how long fn can be delayed.
//   Prevents starvation. Makes debounce behave like throttle. See 2f.
// INTERVIEW: "Difference between debounce and throttle?" -- See section 4 table.
//   Debounce waits for silence. Throttle fires on a schedule.
// INTERVIEW: "How is lodash throttle related to debounce?" --
//   _.throttle(fn, wait) === _.debounce(fn, wait, { leading: true, trailing: true, maxWait: wait })
// INTERVIEW: "How do you cancel a debounced/throttled function?" --
//   Call debounced.cancel() / throttled.cancel(). See 2f, 3g.
// INTERVIEW: "What is requestAnimationFrame throttle?" -- See 3f.
//   Throttle to browser paint cycle (~60fps). Ideal for visual updates.
// INTERVIEW: "Memory leak with debounce in React?" -- See Gotcha 2h-2.
//   Cleanup in useEffect return: return () => debouncedFn.cancel();
// INTERVIEW: "How do you preserve `this` in a decorator?" --
//   Use function() {} (not =>) and call fn.apply(this, args). See 1d Gotcha 2.
// INTERVIEW: "Can you stack decorators?" --
//   Yes. Apply inside-out: a(b(fn)) runs a's wrapper first, then b's, then fn. See 1b.
// INTERVIEW: "What about the TC39 Decorators proposal?" --
//   Stage 3 as of 2024. Targets class methods/accessors/fields, not plain functions.
//   Syntax: @decorator class Foo { @log method() {} }
//   The patterns in this file work for plain functions and are framework-agnostic.
