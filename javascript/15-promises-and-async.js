// ============================================================
// PROMISES, ASYNC/AWAIT & EVENT LOOP
// Ultimate Quick-Reference & Interview Prep
// ============================================================
// Resources:
//   https://dmitripavlutin.com/tag/promise/
//   https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise
//   https://dev.to/lydiahallie/javascript-visualized-promises-async-await-5gke
//   https://levelup.gitconnected.com/vimp-javascript-promise-implementation-challenges-5a4f120d8606
//   Visualize: http://latentflip.com/loupe/

// ============================================================
// TABLE OF CONTENTS
// ============================================================
// 1.  [BASIC]        Callbacks & Callback Hell
// 2.  [BASIC]        Promise States & State Machine
// 3.  [BASIC]        Creating & Consuming Promises
// 4.  [BASIC]        Promise Chaining
// 5.  [BASIC]        then / catch / finally
// 6.  [INTERMEDIATE] then(f,f) vs then(f).catch(f)
// 7.  [BASIC]        Async / Await Fundamentals
// 8.  [INTERMEDIATE] Await Timing Deep Dive
// 9.  [INTERMEDIATE] Fetch with Async/Await
// 10. [INTERMEDIATE] return await vs return promise
// 11. [INTERMEDIATE] Promise.all (+ Polyfill)
// 12. [INTERMEDIATE] Promise.allSettled (+ Polyfill + Real-World)
// 13. [INTERMEDIATE] Promise.race (+ Polyfill)
// 14. [INTERMEDIATE] Promise.any
// 15. [INTERMEDIATE] Event Loop Deep Dive (ASCII Diagram)
// 16. [INTERMEDIATE] setTimeout vs Promise Ordering
// 17. [INTERMEDIATE] Promisifying Callbacks (util.promisify)
// 18. [ADVANCED]     Promise.withResolvers() (ES2024)
// 19. [ADVANCED]     Promise.try() (ES2025 Proposal)
// 20. [ADVANCED]     Top-Level Await
// 21. [ADVANCED]     Async Iterators & for-await-of
// 22. [ADVANCED]     Promise Anti-Patterns
// 23. [ADVANCED]     Unhandled Promise Rejection Handling
// 24. [ADVANCED]     AbortController with Promises/Fetch
// 25. [ADVANCED]     Promise-Based Timeout Pattern
// 26. [ADVANCED]     Sequential vs Parallel vs Concurrent
// 27. [ADVANCED]     Retry & Throttle Patterns
// 28. [ADVANCED]     Structured Concurrency Patterns
// 29. [ADVANCED]     Error Boundaries Pattern
// 30. [ADVANCED]     Error Handling Best Practices
// 31. GOTCHAS
// 32. COMPARISON TABLES
// 33. INTERVIEW LIGHTNING ROUND


// ============================================================
// 1. CALLBACKS & CALLBACK HELL [BASIC]
// ============================================================
// INTERVIEW: "Explain callbacks and why they can be problematic."
//
// JavaScript is synchronous and single-threaded -- it can do
// one thing at a time. Callbacks let it handle async operations
// by deferring execution until a result is available.
//
// IMPORTANT: Callbacks themselves are NOT asynchronous -- they
// are synchronous functions that ENABLE async patterns.

console.log("start");
setTimeout(function () { console.log("processing"); }, 5000);
console.log("end");
// Output: start, end, (5s later) processing

// --- Basic callback pattern ---
// const getData = (url, callback) => {
//     fetch(url).then(callback).catch(err => console.log(err));
// };
// const myResult = (result) => console.log(result.json());
// getData("https://jsonplaceholder.typicode.com/posts", myResult);

// --- Callback hell (pyramid of doom) ---
// Nesting grows horizontally, becomes unmaintainable:
// const cart = ["shoes", "pants", "kurta"];
// api.createOrder(cart, function () {
//     api.proceedToPayment(function () {
//         api.showOrderSummary(function () {
//             api.updateWallet();
//         });
//     });
// });

// Problems with callbacks:
//   1. Pyramid of doom (readability -- grows horizontally)
//   2. Inversion of control (we hand control to createOrder to call
//      our callback; it might never call it, or call it twice)
//   3. No standardized error handling
//   4. Hard to compose or cancel


// ============================================================
// 2. PROMISE STATES & STATE MACHINE [BASIC]
// ============================================================
// INTERVIEW: "Draw the promise state diagram."
//
//   +-----------------------------------------------------------+
//   |                   PROMISE STATE MACHINE                    |
//   +-----------------------------------------------------------+
//   |                                                           |
//   |  new Promise(executor)                                    |
//   |         |                                                 |
//   |         v                                                 |
//   |    +---------+                                            |
//   |    | PENDING |  (initial state)                           |
//   |    +---------+                                            |
//   |     /       \                                             |
//   |    /  settle  \                                           |
//   |   v            v                                          |
//   | +-----------+ +-----------+                               |
//   | | FULFILLED | | REJECTED  |                               |
//   | |  (value)  | |  (reason) |                               |
//   | +-----------+ +-----------+                               |
//   |       |              |                                    |
//   |       v              v                                    |
//   |    .then()        .catch()                                |
//   |                  .then(_, onRejected)                     |
//   |         \        /                                        |
//   |          v      v                                         |
//   |       .finally()   <-- always runs, no args, passes       |
//   |                       through value/reason                |
//   |                                                           |
//   |  RULE: Once settled, a promise NEVER changes state.       |
//   |  Promise objects are IMMUTABLE (externally).               |
//   +-----------------------------------------------------------+
//
//   +-----------------------------------------------------+
//   | PROMISE UNDER THE HOOD                               |
//   +-----------------------------------------------------+
//   |  const p = new Promise((resolve, reject) => {        |
//   |      // executor runs SYNCHRONOUSLY                  |
//   |      // call resolve(value) on success               |
//   |      // call reject(reason) on failure               |
//   |  });                                                 |
//   |                                                      |
//   |  Internal slots:                                     |
//   |    [[PromiseState]]  : "pending"|"fulfilled"|"rejected"|
//   |    [[PromiseResult]] : value or reason               |
//   +-----------------------------------------------------+


// ============================================================
// 3. CREATING & CONSUMING PROMISES [BASIC]
// ============================================================
// INTERVIEW: "How do promises solve inversion of control?"
//
// With promises, WE attach the callback (.then). We retain control.
// The promise guarantees: callback runs at most ONCE, only after
// settlement. Promise objects are immutable from outside.
//
// Key difference: we ATTACH cb (control retained) vs PASS cb (control lost)

const cart = ["shoes", "pants", "kurta"];

// --- Consumer: fetch returns a promise ---
const GITHUB_API = "https://api.github.com/users/shubhamvinayak";
const user = fetch(GITHUB_API);
console.log(user); // Promise { <pending> }
user.then(function (data) { console.log(data); });

// --- Producer: creating a promise ---
const promise1 = createOrder(cart);
promise1
  .then(function (orderId) {
      console.log(orderId);
      return orderId;
  })
  .then(function (orderId) {
      return proceedToPayment(orderId);
  })
  .then(function (message) {
      console.log(message);
  })
  .catch(function (err) {
      console.log(err.message);
  });

function createOrder(cart) {
    return new Promise(function (resolve, reject) {
        if (!validateCart(cart)) {
            reject(new Error("Cart is not valid"));
            return;
        }
        const orderId = "12345";
        if (orderId) {
            setTimeout(function () { resolve(orderId); }, 5000);
        }
    });
}

function proceedToPayment(orderId) {
    return new Promise(function (resolve, reject) {
        resolve("Payment successful");
    });
}

function validateCart(cart) { return true; }


// ============================================================
// 4. PROMISE CHAINING [BASIC]
// ============================================================
// INTERVIEW: "How does promise chaining solve callback hell?"
//
// Flat chain replaces nested callbacks. Each .then() returns a
// NEW promise, enabling sequential async operations.

// fetch("https://jsonplaceholder.typicode.com/posts")
//   .then(posts => {
//       console.log("posts", posts.json());
//       return fetch("https://jsonplaceholder.typicode.com/photos");
//   })
//   .then(photos => {
//       console.log("photos", photos.json());
//       return fetch("https://jsonplaceholder.typicode.com/users");
//   })
//   .then(users => {
//       console.log("users", users.json());
//       return fetch("https://jsonplaceholder.typicode.com/todos");
//   })
//   .then(todos => console.log("todos", todos.json()));

// KEY: You MUST return the next promise in each .then() to
// maintain the chain. Forgetting `return` breaks the flow.


// ============================================================
// 5. THEN / CATCH / FINALLY [BASIC]
// ============================================================
// INTERVIEW: "Explain then, catch, and finally on promises."

// --- .then(onFulfilled, onRejected) ---
// Returns a NEW pending promise. If handler:
//   - returns value    -> new promise fulfilled with that value
//   - throws error     -> new promise rejected with that error
//   - returns promise  -> new promise follows that promise
// If handler is not a function:
//   - onFulfilled missing -> identity: (x) => x
//   - onRejected missing  -> thrower:  (x) => { throw x; }

// --- .catch(onRejected) ---
// Shortcut for .then(undefined, onRejected)
// Returns a new promise (allows chain recovery)

// let p1 = new Promise((resolve, reject) => {
//     setTimeout(() => resolve('p1'), 1000);
// });
// p1.then(value => {
//     console.log(value);
//     return Promise.reject("catch block");
// })
// .catch(value => {
//     console.log(value);              // "catch block"
//     return Promise.reject("simple catch");
// })
// .then(
//     value  => console.log(value),
//     error  => console.log("error", error) // "error simple catch"
// );

// --- .finally(onFinally) ---
// Runs on BOTH fulfillment and rejection. Receives NO arguments.
// Return value is ignored (passes through original value/reason)
// UNLESS it throws or returns a rejected promise.

// let p1 = new Promise((resolve, reject) => resolve("p1 resolved"));
// p1
//   .then(value => {
//       console.log(value);                // "p1 resolved"
//       return Promise.resolve("p1 first block");
//   })
//   .finally(value => {
//       console.log("finally", value);     // "finally undefined" (no args!)
//   })
//   .then(value => {
//       console.log(value);               // "p1 first block" (passed through)
//   });


// ============================================================
// 6. then(f,f) vs then(f).catch(f) [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What is the difference between these two patterns?"

function success(value) { console.log("Resolved:", value); }
function error(err) { console.log("Error:", err); }
function rejectSuccess(invalidValue) {
    console.log("Invalid success:", invalidValue);
    return Promise.reject("Invalid!");
}

// Pattern 1: then(success, error) -- error handler only catches
// rejection of the ORIGINAL promise, NOT errors in success handler
Promise.resolve("Zzz!")
  .then(rejectSuccess, error);
// Logs: "Invalid success: Zzz!"
// The rejection from rejectSuccess is UNCAUGHT!

// Pattern 2: then(success).catch(error) -- catch handles rejections
// from BOTH the original promise AND the success handler
Promise.resolve("Zzz!")
  .then(rejectSuccess)
  .catch(error);
// Logs: "Invalid success: Zzz!"
// Logs: "Error: Invalid!"   <-- CAUGHT by .catch()

//   +------------------------------------------------------+
//   |      then(onFulfilled, onRejected)                   |
//   |  - onRejected catches original promise rejection     |
//   |  - Does NOT catch errors thrown by onFulfilled       |
//   +------------------------------------------------------+
//   |      then(onFulfilled).catch(onRejected)             |
//   |  - catch catches original promise rejection          |
//   |  - ALSO catches errors thrown by onFulfilled         |
//   |  - Almost always preferred                            |
//   +------------------------------------------------------+

// Real-world example:
// axios("/list.json")
//   .then(response => {
//       const list = response.data;
//       if (list.length === 0) return Promise.reject(new Error("Empty list!"));
//       return list;
//   })
//   .catch(err => console.log(err)); // catches BOTH network + empty list


// ============================================================
// 7. ASYNC / AWAIT FUNDAMENTALS [BASIC]
// ============================================================
// INTERVIEW: "What does async/await do under the hood?"
//
// async/await is syntactic sugar over promises:
//   - async function ALWAYS returns a promise
//   - await PAUSES the function until the promise settles
//   - The function is suspended and removed from the call stack
//   - Other code runs while waiting (non-blocking)
//
//   +-----------------------------------------------------+
//   |         ASYNC/AWAIT UNDER THE HOOD                   |
//   +-----------------------------------------------------+
//   |                                                      |
//   |  async function foo() {      Equivalent to:          |
//   |    const x = await bar();    function foo() {        |
//   |    return x + 1;               return bar()          |
//   |  }                                .then(x => x + 1); |
//   |                              }                       |
//   |                                                      |
//   |  At `await`:                                         |
//   |  1. Evaluate bar() -> get promise                    |
//   |  2. SUSPEND foo(), remove from call stack            |
//   |  3. Return implicit promise to caller                |
//   |  4. Continue other code (event loop runs)            |
//   |  5. When bar() settles -> RESUME foo()               |
//   |  6. x = resolved value, continue execution           |
//   +-----------------------------------------------------+

// --- async returns a promise ---
async function getData() {
    return "shubham"; // auto-wrapped in Promise.resolve("shubham")
}
const data = getData();
console.log("~async", data); // Promise { "shubham" }
data.then(function (d) { console.log(d); }); // "shubham"

// --- returning an existing promise (no double-wrapping) ---
const p = new Promise((resolve, reject) => resolve("resolve promise value"));
async function getDataP() { return p; }
const dataPromise = getDataP();
dataPromise.then(function (d) { console.log(d); });

// --- handling promises: old way vs await ---
const promiseVariable = new Promise((resolve, reject) => {
    resolve("Promise resolved value!!");
});

// Old way:
function getData1() {
    promiseVariable.then((res) => console.log(res));
}
getData1();

// With async/await:
async function handlePromiseBasic() {
    const val = await promiseVariable;
    console.log("val~~~", val);
}
handlePromiseBasic();


// ============================================================
// 8. AWAIT TIMING DEEP DIVE [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What happens when you await multiple promises?"
//
// KEY INSIGHT: await suspends the function. Promises that are
// already created continue running in parallel in the background.

// --- CASE 1: Two awaits on the SAME promise ---
// const p1 = new Promise((resolve) => {
//     setTimeout(() => resolve("Promise1 resolved"), 10000);
// });
// async function handlePromise() {
//     console.log("Hello World");
//     const value1 = await p1;
//     console.log("await 1:", value1);
//     const value2 = await p1;  // already resolved, resolves instantly
//     console.log("await 2:", value2);
// }
// handlePromise();
// After 10s: everything prints at once

// --- CASE 2: p1=10s, p2=5s -- await p1 THEN p2 ---
// Both start immediately. p2 resolves at 5s but we are waiting
// for p1 (10s). When p1 resolves at 10s, p2 is already done.
// Total time: ~10s (not 15s!)

// --- CASE 3: p1=10s, p2=5s -- await p2 THEN p1 ---
const p1 = new Promise((resolve) => {
    setTimeout(() => resolve("Promise1 resolved value"), 10000);
});
const p2 = new Promise((resolve) => {
    setTimeout(() => resolve("Promise2 resolved value"), 5000);
});

async function handlePromise() {
    console.log("Hello World");
    const value2 = await p2; // suspends ~5s
    console.log("namaste javascript 2");
    console.log(value2);
    const value1 = await p1; // p1 started at same time, only ~5s left
    console.log("namaste javascript 1");
    console.log(value1);
}
handlePromise();
// Total time: ~10s (both timers started at creation, run in parallel)

//   +-----------------------------------------------------+
//   | TIMING DIAGRAM: await p2 then await p1              |
//   +-----------------------------------------------------+
//   |  0s     5s         10s                               |
//   |  |------|----------|                                 |
//   |  p2: [==========]  resolved at 5s                   |
//   |  p1: [====================] resolved at 10s         |
//   |                                                      |
//   |  handlePromise():                                    |
//   |  0s: log "Hello World", await p2                     |
//   |  5s: p2 resolves, log p2, await p1                   |
//   |  10s: p1 resolves, log p1                            |
//   |  Total: 10s (NOT 15s -- timers run concurrently)     |
//   +-----------------------------------------------------+


// ============================================================
// 9. FETCH WITH ASYNC/AWAIT [INTERMEDIATE]
// ============================================================

async function callAnAPI() {
    // fetch() returns Response with a ReadableStream body
    // .json() returns another promise that resolves to parsed JSON
    const value = await fetch(GITHUB_API);
    const jsonValue = await value.json();
    console.log("~~~~~~~~~~~~~~~~~", jsonValue);
}
callAnAPI();

// Error handling: try/catch or .catch() on the call
// callAnAPI().catch(err => console.error(err));


// ============================================================
// 10. 'return await promise' vs 'return promise' [INTERMEDIATE]
// ============================================================
// INTERVIEW: "When does it matter to use return await?"

function promisedDivision(n1, n2) {
    if (n2 === 0) return Promise.reject(new Error("Cannot divide by 0"));
    return Promise.resolve(n1 / n2);
}

// --- No difference for fulfilled promises ---
async function divideWithAwait() {
    return await promisedDivision(6, 2);
}
async function divideWithoutAwait() {
    return promisedDivision(6, 2);
}
// Both yield 3 when awaited

// --- CRITICAL DIFFERENCE: error handling in try/catch ---
async function divideWithAwait3() {
    try {
        return await promisedDivision(5, 0); // rejection IS caught here
    } catch (error) {
        console.log("Caught:", error.message); // "Cannot divide by 0"
    }
}

async function divideWithoutAwait4() {
    try {
        return promisedDivision(5, 0); // rejection NOT caught!
    } catch (error) {
        console.log("Never reached:", error); // this never runs
    }
}
// divideWithoutAwait4() returns the rejected promise, and the
// rejection propagates to the CALLER, bypassing this try/catch.

// RULE: Use `return await` inside try/catch to catch local errors.
// Outside try/catch, either form works identically.

//   +-----------------------------------------------+
//   | return await promise  | return promise         |
//   |-----------------------------------------------|
//   | Unwraps, then re-wraps| Passes promise through |
//   | Error caught in local | Error escapes to caller|
//   | try/catch             | try/catch              |
//   | Slightly slower (1    | Slightly faster         |
//   | extra microtick)      |                        |
//   | Shows in async stack  | May miss stack frames  |
//   +-----------------------------------------------+


// ============================================================
// 11. Promise.all (+ Polyfill) [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Explain Promise.all and its fail-fast behavior."
//
// Promise.all(iterable) -- parallel execution, fail-fast
//
//   +-----------------------------------------------------+
//   | Promise.all BEHAVIOR                                 |
//   +-----------------------------------------------------+
//   | Input:  [p1(3s), p2(1s), p3(2s)]                    |
//   | All succeed -> [val1, val2, val3] after 3s           |
//   |                                                      |
//   | p2 rejects at 1s:                                    |
//   | -> Immediately rejects with p2's error at 1s         |
//   | -> p1, p3 continue running but results are ignored   |
//   | -> You CANNOT cancel in-flight promises              |
//   +-----------------------------------------------------+

// --- Success ---
// const p1 = new Promise(r => setTimeout(() => r("P1 success"), 3000));
// const p2 = new Promise(r => setTimeout(() => r("P2 success"), 1000));
// const p3 = new Promise(r => setTimeout(() => r("P3 success"), 2000));
// Promise.all([p1, p2, p3]).then(result => console.log(result));
// ["P1 success", "P2 success", "P3 success"] after 3s

// --- Failure (fail-fast) ---
// const p1 = new Promise(r => setTimeout(() => r("P1 success"), 3000));
// const p2 = new Promise((_, rj) => setTimeout(() => rj("P2 failed"), 1000));
// const p3 = new Promise(r => setTimeout(() => r("P3 success"), 2000));
// Promise.all([p1, p2, p3])
//   .then(result => console.log(result))
//   .catch(error => console.error(error)); // "P2 failed" at 1s

// --- Polyfill ---
const PromiseArr = [
    new Promise(resolve => setTimeout(resolve, 1000, "promise1")),
    new Promise(resolve => setTimeout(resolve, 1000, "promise2")),
    new Promise(resolve => setTimeout(resolve, 2000, "promise3"))
];

function all(promises) {
    return new Promise((resolve, reject) => {
        if (!promises.length) return resolve([]);
        const results = [];
        let count = 0;
        promises.forEach((p, idx) => {
            Promise.resolve(p)
                .then(res => {
                    results[idx] = res;
                    if (++count === promises.length) resolve(results);
                })
                .catch(reject);
        });
    });
}
// all(PromiseArr).then(v => console.log(v));


// ============================================================
// 12. Promise.allSettled (+ Polyfill + Real-World) [INTERMEDIATE]
// ============================================================
// INTERVIEW: "When would you use allSettled instead of all?"
//
// Promise.allSettled(iterable) -- waits for ALL to settle
// Never short-circuits. Returns array of { status, value/reason }
//
//   +-----------------------------------------------------+
//   | Promise.allSettled BEHAVIOR                          |
//   +-----------------------------------------------------+
//   | Input:  [p1(3s), p2(1s reject), p3(2s)]             |
//   | Waits for ALL -> result after 3s:                    |
//   | [                                                    |
//   |   { status: "fulfilled", value: val1 },              |
//   |   { status: "rejected",  reason: err2 },             |
//   |   { status: "fulfilled", value: val3 }               |
//   | ]                                                    |
//   +-----------------------------------------------------+

// --- Success ---
// const p1 = new Promise(r => setTimeout(() => r("P1 success"), 3000));
// const p2 = new Promise(r => setTimeout(() => r("P2 success"), 1000));
// const p3 = new Promise(r => setTimeout(() => r("P3 success"), 2000));
// Promise.allSettled([p1, p2, p3]).then(result => console.log(result));

// --- Mixed (some fail) ---
// const p1 = new Promise((_, rj) => setTimeout(() => rj("P1 failed"), 3000));
// const p2 = new Promise((_, rj) => setTimeout(() => rj("P2 failed"), 1000));
// const p3 = new Promise(r => setTimeout(() => r("P3 success"), 2000));
// Promise.allSettled([p1, p2, p3]).then(result => console.log(result));

// --- Polyfill ---
function allSettledPolyfill(promises) {
    return Promise.all(
        promises.map(p =>
            Promise.resolve(p)
                .then(value => ({ status: "fulfilled", value }))
                .catch(reason => ({ status: "rejected", reason }))
        )
    );
}

// --- Real-World Use Case: Batch API Calls ---
// INTERVIEW: "Give a real-world use case for allSettled."
async function batchUserUpdate(users) {
    const results = await Promise.allSettled(
        users.map(user =>
            fetch(`/api/users/${user.id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(user)
            }).then(r => {
                if (!r.ok) throw new Error(`HTTP ${r.status} for user ${user.id}`);
                return r.json();
            })
        )
    );

    const succeeded = results.filter(r => r.status === "fulfilled");
    const failed = results.filter(r => r.status === "rejected");

    console.log(`Updated ${succeeded.length}/${results.length} users`);
    if (failed.length > 0) {
        console.error("Failed updates:", failed.map(r => r.reason.message));
    }
    return { succeeded, failed };
}

// --- Real-world: Health check multiple services ---
async function healthCheckAll(services) {
    const results = await Promise.allSettled(
        services.map(svc =>
            fetch(svc.url, { signal: AbortSignal.timeout(5000) })
                .then(r => ({ service: svc.name, status: r.status, healthy: r.ok }))
        )
    );
    return results.map((r, i) => ({
        service: services[i].name,
        healthy: r.status === "fulfilled" && r.value.healthy,
        error: r.status === "rejected" ? r.reason.message : null
    }));
}


// ============================================================
// 13. Promise.race (+ Polyfill) [INTERMEDIATE]
// ============================================================
// INTERVIEW: "What does Promise.race return?"
//
// Promise.race(iterable) -- settles with the FIRST settled promise
// (whether fulfilled or rejected)

// --- Success (fastest wins) ---
// const p1 = new Promise(r => setTimeout(() => r("P1 success"), 3000));
// const p2 = new Promise(r => setTimeout(() => r("P2 success"), 1000)); // wins
// const p3 = new Promise(r => setTimeout(() => r("P3 success"), 2000));
// Promise.race([p1, p2, p3]).then(r => console.log(r)); // "P2 success" at 1s

// --- Error (fastest is a rejection) ---
// const p2 = new Promise((_, rj) => setTimeout(() => rj("P2 reject"), 1000));
// Promise.race([p1, p2, p3]).then(console.log).catch(console.error);
// Error at 1s: "P2 reject"

// --- Polyfill ---
function race(promises) {
    return new Promise((resolve, reject) => {
        promises.forEach(p => Promise.resolve(p).then(resolve, reject));
    });
}
// race(PromiseArr).then(v => console.log(v));


// ============================================================
// 14. Promise.any [INTERMEDIATE]
// ============================================================
// INTERVIEW: "How does Promise.any differ from Promise.race?"
//
// Promise.any(iterable) -- resolves with FIRST FULFILLED promise
// Ignores rejections unless ALL reject -> AggregateError
//
//   +-----------------------------------------------------+
//   | Promise.any BEHAVIOR                                 |
//   +-----------------------------------------------------+
//   | [p1(3s ok), p2(1s reject), p3(2s ok)]                |
//   | -> Ignores p2 rejection, resolves with p3 at 2s      |
//   |                                                      |
//   | [p1 reject, p2 reject, p3 reject]                    |
//   | -> AggregateError with all reasons after all settle   |
//   |                                                      |
//   | Promise.any([]) -> rejects immediately                |
//   +-----------------------------------------------------+

// --- Some reject, first success wins ---
// const p1 = new Promise(r => setTimeout(() => r("P1 success"), 3000));
// const p2 = new Promise((_, rj) => setTimeout(() => rj("P2 failed"), 1000));
// const p3 = new Promise(r => setTimeout(() => r("P3 success"), 2000));
// Promise.any([p1, p2, p3]).then(r => console.log(r)); // "P3 success" at 2s

// --- All reject -> AggregateError ---
// const p1 = new Promise((_, rj) => setTimeout(() => rj("P1 fail"), 3000));
// const p2 = new Promise((_, rj) => setTimeout(() => rj("P2 fail"), 1000));
// const p3 = new Promise((_, rj) => setTimeout(() => rj("P3 fail"), 2000));
// Promise.any([p1, p2, p3])
//   .then(r => console.log(r))
//   .catch(err => console.log(err.errors)); // ["P1 fail", "P2 fail", "P3 fail"]


// ============================================================
// 15. EVENT LOOP DEEP DIVE [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Explain the JavaScript event loop."
// Visualize: http://latentflip.com/loupe/
//
//   +-------------------------------------------------------------+
//   |                   JAVASCRIPT RUNTIME                         |
//   +-------------------------------------------------------------+
//   |                                                             |
//   |  +---------------+    +----------------------------------+  |
//   |  |  CALL STACK   |    |         WEB APIs / Node APIs     |  |
//   |  | (single-      |    |  setTimeout, fetch, DOM events,  |  |
//   |  |  threaded)    |--->|  XMLHttpRequest, I/O, etc.       |  |
//   |  |               |    |  (run in separate threads)       |  |
//   |  +-------+-------+    +--------+--------+----------------+  |
//   |          ^                     |        |                   |
//   |          |                     |        |                   |
//   |          |        +------------v--+  +--v---------------+   |
//   |          |        | MICROTASK     |  | MACROTASK        |   |
//   |          |        | QUEUE         |  | (CALLBACK) QUEUE |   |
//   |          |        | (Job Queue)   |  | (Task Queue)     |   |
//   |          |        +---------------+  +------------------+   |
//   |          |        | Promise.then  |  | setTimeout       |   |
//   |          |        | catch/finally |  | setInterval      |   |
//   |          |        | queueMicro-   |  | setImmediate     |   |
//   |          |        |   task()      |  | I/O callbacks    |   |
//   |          |        | MutationObs.  |  | UI rendering     |   |
//   |          |        | process.next  |  | requestAnimation |   |
//   |          |        |   Tick (Node) |  |   Frame          |   |
//   |          |        +-------+-------+  +--------+---------+   |
//   |          |                |                   |             |
//   |          |                v                   |             |
//   |          +-----<---[EVENT LOOP]---<-----------+             |
//   |                                                             |
//   +-------------------------------------------------------------+
//
//   EVENT LOOP ALGORITHM (one "tick"):
//   +---------------------------------------------------------+
//   | 1. Execute everything in the CALL STACK (sync code)     |
//   | 2. Call stack empty? Drain ALL MICROTASKS               |
//   |    (including microtasks queued BY microtasks)           |
//   | 3. Microtask queue empty? Take ONE macrotask            |
//   | 4. Execute that macrotask                               |
//   | 5. Go to step 2 (drain microtasks again)                |
//   | 6. Repeat                                               |
//   +---------------------------------------------------------+
//
//   PRIORITY ORDER:
//   Sync code  >  Microtasks  >  Macrotasks
//     (1st)          (2nd)          (3rd)
//
//   +-----------------------------------------------+
//   | MICROTASKS (higher priority)                   |
//   |   - Promise .then / .catch / .finally          |
//   |   - queueMicrotask()                           |
//   |   - MutationObserver                           |
//   |   - process.nextTick() (Node.js, even higher)  |
//   +-----------------------------------------------+
//   | MACROTASKS (lower priority)                    |
//   |   - setTimeout / setInterval                   |
//   |   - setImmediate (Node.js)                     |
//   |   - I/O operations                             |
//   |   - UI rendering                               |
//   |   - requestAnimationFrame                      |
//   +-----------------------------------------------+


// ============================================================
// 16. setTimeout vs PROMISE ORDERING [INTERMEDIATE]
// ============================================================
// INTERVIEW: Classic question -- "What is the output and why?"

console.log("1: script start");                    // (1) sync

setTimeout(() => console.log("2: setTimeout"), 0); // (5) macrotask

Promise.resolve()
  .then(() => console.log("3: promise 1"))         // (3) microtask
  .then(() => console.log("4: promise 2"));        // (4) microtask

console.log("5: script end");                      // (2) sync

// OUTPUT:
//   1: script start
//   5: script end
//   3: promise 1
//   4: promise 2
//   2: setTimeout
//
// WHY: Sync runs first, then ALL microtasks (promises), then
// macrotasks (setTimeout). Even setTimeout(..., 0) waits for
// microtasks to drain.

// --- Advanced ordering puzzle ---
// INTERVIEW: "Predict the output."
console.log("A");
setTimeout(() => console.log("B"), 0);
Promise.resolve().then(() => {
    console.log("C");
    setTimeout(() => console.log("D"), 0);
}).then(() => console.log("E"));
queueMicrotask(() => console.log("F"));
console.log("G");
// OUTPUT: A, G, C, F, E, B, D
// Explanation:
// Sync: A, G
// Microtasks: C (promise1), F (queueMicrotask), E (promise2, queued by C's .then)
// Macrotasks: B (first setTimeout), D (setTimeout queued during microtask C)


// ============================================================
// 17. PROMISIFYING CALLBACKS [INTERMEDIATE]
// ============================================================
// INTERVIEW: "How do you convert callback-based APIs to promises?"

// --- Manual promisification ---
function readFilePromise(path) {
    return new Promise((resolve, reject) => {
        // require('fs').readFile(path, 'utf8', (err, data) => {
        //     if (err) reject(err);
        //     else resolve(data);
        // });
    });
}

// --- Using Node.js util.promisify (preferred) ---
// const { promisify } = require('util');
// const readFile = promisify(require('fs').readFile);
// const data = await readFile('./file.txt', 'utf8');

// --- Promisify any callback pattern ---
function promisify(fn) {
    return function (...args) {
        return new Promise((resolve, reject) => {
            fn(...args, (err, result) => {
                if (err) reject(err);
                else resolve(result);
            });
        });
    };
}

// GOTCHA: Only works with (err, result) Node-style callbacks.
// For event emitters or multi-arg callbacks, write a manual wrapper.


// ============================================================
// 18. Promise.withResolvers() (ES2024) [ADVANCED]
// ============================================================
// INTERVIEW: "What problem does Promise.withResolvers solve?"
//
// Extracts resolve/reject from the promise constructor so you
// can call them from OUTSIDE the executor. Replaces the common
// "deferred" pattern.

// --- Old deferred pattern ---
function oldDeferred() {
    let resolve, reject;
    const promise = new Promise((res, rej) => {
        resolve = res;
        reject = rej;
    });
    return { promise, resolve, reject };
}

// --- ES2024: Promise.withResolvers() ---
// const { promise, resolve, reject } = Promise.withResolvers();
// // pass resolve/reject to external code
// setTimeout(() => resolve("done!"), 1000);
// const result = await promise; // "done!"

// --- Real-world: Event-based resolution ---
function waitForEvent(element, eventName) {
    const { promise, resolve } = Promise.withResolvers();
    element.addEventListener(eventName, resolve, { once: true });
    return promise;
}
// const clickEvent = await waitForEvent(button, "click");

// --- Real-world: Stream to promise ---
function streamToString(readable) {
    const { promise, resolve, reject } = Promise.withResolvers();
    const chunks = [];
    readable.on("data", chunk => chunks.push(chunk));
    readable.on("end", () => resolve(chunks.join("")));
    readable.on("error", reject);
    return promise;
}

// Polyfill:
if (!Promise.withResolvers) {
    Promise.withResolvers = function () {
        let resolve, reject;
        const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
        return { promise, resolve, reject };
    };
}


// ============================================================
// 19. Promise.try() (ES2025 Proposal) [ADVANCED]
// ============================================================
// INTERVIEW: "What does Promise.try solve?"
//
// Normalizes sync-or-async functions: wraps execution in a promise
// so that sync throws become rejections (not uncaught exceptions).

// --- Problem: sync throw in .then() start ---
function mightThrowSync(value) {
    if (!value) throw new Error("bad value"); // sync throw!
    return fetch(`/api/${value}`);
}

// BAD: sync error is uncaught
// mightThrowSync(null).then(handle).catch(handleErr); // TypeError: cannot read .then of undefined

// WORKAROUND (today):
// Promise.resolve().then(() => mightThrowSync(null)).catch(handleErr);

// --- Promise.try (proposal) ---
// Promise.try(() => mightThrowSync(null))
//   .then(handle)
//   .catch(handleErr); // catches sync AND async errors uniformly

// Polyfill:
if (!Promise.try) {
    Promise.try = function (fn, ...args) {
        return new Promise((resolve) => resolve(fn(...args)));
    };
}
// Promise.try(() => JSON.parse(userInput))
//   .then(processData)
//   .catch(handleParseError);


// ============================================================
// 20. TOP-LEVEL AWAIT [ADVANCED]
// ============================================================
// INTERVIEW: "What is top-level await and when can you use it?"
//
// Available in ES Modules (type="module" in browser, .mjs in Node)
// The module itself becomes async -- importers wait for it.

// --- In an ES Module (.mjs or <script type="module">) ---
// const response = await fetch("/api/config");
// export const config = await response.json();

// --- Use case: Conditional imports ---
// const strings = await import(`./i18n/${navigator.language}.js`);

// --- Use case: Dependency fallback ---
// let db;
// try {
//     db = await import("better-sqlite3");
// } catch {
//     db = await import("sql.js");
// }
// export default db;

// GOTCHA: Top-level await blocks ALL importers of this module.
// Keep it fast or you stall the entire module graph.
//
//   +-----------------------------------------------------+
//   | WHERE TOP-LEVEL AWAIT WORKS                          |
//   +-----------------------------------------------------+
//   | ES Modules (.mjs, type="module")   | YES             |
//   | CommonJS (.cjs, require())         | NO              |
//   | Browser <script>                   | NO              |
//   | Browser <script type="module">     | YES             |
//   | Node.js REPL                       | YES (v14.8+)    |
//   | Deno                               | YES             |
//   | Bun                                | YES             |
//   +-----------------------------------------------------+


// ============================================================
// 21. ASYNC ITERATORS & for-await-of [ADVANCED]
// ============================================================
// INTERVIEW: "What is an async iterator? When would you use for-await-of?"

// --- Async Generator Function ---
async function* fetchPages(baseUrl, maxPages = 5) {
    let page = 1;
    while (page <= maxPages) {
        const response = await fetch(`${baseUrl}?page=${page}`);
        const data = await response.json();
        if (data.items.length === 0) return; // no more data
        yield data;
        page++;
    }
}

// --- Consuming with for-await-of ---
// async function getAllItems() {
//     const allItems = [];
//     for await (const page of fetchPages("/api/products")) {
//         allItems.push(...page.items);
//         console.log(`Fetched page with ${page.items.length} items`);
//     }
//     return allItems;
// }

// --- Async iterable protocol ---
// An object is async iterable if it has [Symbol.asyncIterator]()
// that returns { next() -> Promise<{ value, done }> }

const asyncRange = {
    from: 1,
    to: 5,
    [Symbol.asyncIterator]() {
        let current = this.from;
        const last = this.to;
        return {
            async next() {
                // simulate async work
                await new Promise(r => setTimeout(r, 100));
                if (current <= last) {
                    return { value: current++, done: false };
                }
                return { done: true };
            }
        };
    }
};
// for await (const num of asyncRange) { console.log(num); } // 1, 2, 3, 4, 5

// --- Real-world: Streaming API responses ---
async function* streamLines(url) {
    const response = await fetch(url);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep incomplete line in buffer
        for (const line of lines) {
            if (line.trim()) yield line;
        }
    }
    if (buffer.trim()) yield buffer;
}

// --- Converting callback streams to async iterators ---
function toAsyncIterable(emitter, eventName) {
    const { promise, resolve } = Promise.withResolvers();
    const queue = [];
    let done = false;
    let nextResolve = resolve;

    emitter.on(eventName, (data) => {
        const current = nextResolve;
        const next = Promise.withResolvers();
        nextResolve = next.resolve;
        current({ value: data, done: false, next: next.promise });
    });
    emitter.on("end", () => nextResolve({ done: true }));

    return {
        [Symbol.asyncIterator]() {
            let current = promise;
            return {
                async next() {
                    const result = await current;
                    if (result.done) return { done: true };
                    current = result.next;
                    return { value: result.value, done: false };
                }
            };
        }
    };
}


// ============================================================
// 22. PROMISE ANTI-PATTERNS [ADVANCED]
// ============================================================
// INTERVIEW: "What are common promise mistakes?"

// --- Anti-pattern 1: Explicit construction (Deferred anti-pattern) ---
// BAD: Wrapping a promise in another promise
function badFetch(url) {
    return new Promise((resolve, reject) => {   // unnecessary wrapper!
        fetch(url).then(res => resolve(res)).catch(err => reject(err));
    });
}
// GOOD: Just return the promise
function goodFetch(url) {
    return fetch(url);
}

// --- Anti-pattern 2: Using .then() inside async functions ---
// BAD: mixing .then() with async/await
async function badMix() {
    return fetch("/api").then(r => r.json()).then(data => data.items);
}
// GOOD: use await consistently
async function goodMix() {
    const r = await fetch("/api");
    const data = await r.json();
    return data.items;
}

// --- Anti-pattern 3: Forgotten return in .then() chain ---
// BAD:
// getUser().then(user => {
//     getOrders(user.id);  // no return! chain breaks
// }).then(orders => {
//     console.log(orders); // undefined!
// });
// GOOD: always return
// getUser().then(user => {
//     return getOrders(user.id);
// }).then(orders => {
//     console.log(orders); // actual orders
// });

// --- Anti-pattern 4: Catch-and-forget ---
// BAD:
// fetchData().catch(err => {}); // silently swallowing errors
// GOOD:
// fetchData().catch(err => {
//     logger.error("fetchData failed", err);
//     throw err; // re-throw if upstream should know
// });

// --- Anti-pattern 5: Nested .then() (callback hell in disguise) ---
// BAD:
// getUser().then(user => {
//     getProfile(user.id).then(profile => {
//         getAvatar(profile.avatarId).then(avatar => { ... });
//     });
// });
// GOOD: flat chain or async/await


// ============================================================
// 23. UNHANDLED PROMISE REJECTION HANDLING [ADVANCED]
// ============================================================
// INTERVIEW: "How do you handle unhandled promise rejections?"

// --- Browser ---
window.addEventListener("unhandledrejection", (event) => {
    console.error("Unhandled rejection:", event.reason);
    event.preventDefault(); // prevents default console error
    // send to error tracking service
});

// --- Node.js ---
// process.on("unhandledRejection", (reason, promise) => {
//     console.error("Unhandled rejection at:", promise, "reason:", reason);
//     // In Node.js 15+, unhandled rejections crash the process by default
// });

// --- Node.js: also listen for handled-after-the-fact ---
// process.on("rejectionHandled", (promise) => {
//     console.log("Rejection was handled late:", promise);
// });

// GOTCHA (Node.js 15+): Unhandled promise rejections terminate
// the process with a non-zero exit code by default. Always attach
// .catch() or use try/catch with await.


// ============================================================
// 24. AbortController WITH PROMISES / FETCH [ADVANCED]
// ============================================================
// INTERVIEW: "How do you cancel a fetch request or a promise?"

// --- Cancelling fetch ---
const controller = new AbortController();
const { signal } = controller;

// fetch("/api/data", { signal })
//   .then(res => res.json())
//   .then(data => console.log(data))
//   .catch(err => {
//       if (err.name === "AbortError") {
//           console.log("Fetch was cancelled");
//       } else {
//           throw err;
//       }
//   });

// Cancel after 5 seconds:
// setTimeout(() => controller.abort(), 5000);

// --- Making any promise cancellable ---
function cancellablePromise(promise, signal) {
    if (signal?.aborted) return Promise.reject(new DOMException("Aborted", "AbortError"));
    return new Promise((resolve, reject) => {
        const onAbort = () => reject(new DOMException("Aborted", "AbortError"));
        signal?.addEventListener("abort", onAbort, { once: true });
        promise.then(
            val => { signal?.removeEventListener("abort", onAbort); resolve(val); },
            err => { signal?.removeEventListener("abort", onAbort); reject(err); }
        );
    });
}

// Usage:
// const ctrl = new AbortController();
// const result = await cancellablePromise(longRunningOp(), ctrl.signal);
// ctrl.abort(); // cancels

// --- AbortSignal.timeout() (modern browsers / Node 18+) ---
// fetch("/api/data", { signal: AbortSignal.timeout(5000) })
//   .then(r => r.json())
//   .catch(err => {
//       if (err.name === "TimeoutError") console.log("Timed out");
//       if (err.name === "AbortError")   console.log("Aborted");
//   });

// --- AbortSignal.any() (combining signals) ---
// const manualCtrl = new AbortController();
// const combined = AbortSignal.any([
//     manualCtrl.signal,
//     AbortSignal.timeout(10000)
// ]);
// fetch("/api", { signal: combined });


// ============================================================
// 25. PROMISE-BASED TIMEOUT PATTERN [ADVANCED]
// ============================================================
// INTERVIEW: "Implement a timeout wrapper for promises."

function withTimeout(promise, ms, message = "Operation timed out") {
    const timeout = new Promise((_, reject) =>
        setTimeout(() => reject(new Error(message)), ms)
    );
    return Promise.race([promise, timeout]);
}

// Usage:
// const data = await withTimeout(fetch("/slow-api"), 5000);

// With cleanup (cancel the timeout if promise resolves first):
function withTimeoutCleanup(promise, ms) {
    let timeoutId;
    const timeout = new Promise((_, reject) => {
        timeoutId = setTimeout(() => reject(new Error("Timeout")), ms);
    });
    return Promise.race([promise, timeout]).finally(() => clearTimeout(timeoutId));
}


// ============================================================
// 26. SEQUENTIAL vs PARALLEL vs CONCURRENT [ADVANCED]
// ============================================================
// INTERVIEW: "What is the difference? When to use each?"

const urls = ["/api/1", "/api/2", "/api/3"];

// --- SEQUENTIAL: one after another (order guaranteed) ---
async function sequential(urls) {
    const results = [];
    for (const url of urls) {
        results.push(await fetch(url).then(r => r.json()));
    }
    return results;
}
// Use when: order matters, or each call depends on prior result
// Time: sum of all durations

// --- PARALLEL: all at once (fastest) ---
async function parallel(urls) {
    return Promise.all(urls.map(url => fetch(url).then(r => r.json())));
}
// Use when: calls are independent, server can handle load
// Time: duration of the slowest call

// --- CONCURRENT with limit (controlled parallelism) ---
async function concurrentLimit(urls, limit = 3) {
    const results = [];
    const executing = new Set();
    for (const [i, url] of urls.entries()) {
        const p = fetch(url).then(r => r.json()).then(data => { results[i] = data; });
        executing.add(p);
        p.finally(() => executing.delete(p));
        if (executing.size >= limit) {
            await Promise.race(executing);
        }
    }
    await Promise.all(executing);
    return results;
}
// Use when: many calls but need to limit server/memory pressure

//   +----------------------------------------------------------+
//   | Pattern      | Time         | Use Case                   |
//   |--------------|--------------|----------------------------|
//   | Sequential   | sum of all   | dependent calls, ordering  |
//   | Parallel     | max of all   | independent, few calls     |
//   | Concurrent   | between      | many calls, rate limiting  |
//   |   (limited)  | seq & par    |                            |
//   +----------------------------------------------------------+


// ============================================================
// 27. RETRY & THROTTLE PATTERNS [ADVANCED]
// ============================================================

// --- Auto-retry with exponential backoff ---
async function retry(fn, { retries = 3, delay = 1000, backoff = 2, shouldRetry } = {}) {
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            return await fn(attempt);
        } catch (err) {
            const isRetryable = shouldRetry ? shouldRetry(err) : true;
            if (attempt === retries || !isRetryable) throw err;
            const wait = delay * Math.pow(backoff, attempt);
            console.log(`Attempt ${attempt + 1} failed, retrying in ${wait}ms...`);
            await new Promise(r => setTimeout(r, wait));
        }
    }
}

// Usage:
// const data = await retry(
//     () => fetch("/flaky").then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }),
//     { retries: 3, delay: 500, shouldRetry: (err) => err.message !== "401" }
// );

// With AbortController for total timeout:
// const ctrl = new AbortController();
// setTimeout(() => ctrl.abort(), 30000); // total 30s budget
// const data = await retry(
//     () => fetch("/api", { signal: ctrl.signal }).then(r => r.json()),
//     { retries: 5 }
// );

// --- Throttle: limit concurrent promises ---
function throttle(tasks, limit) {
    return new Promise((resolve, reject) => {
        const results = new Array(tasks.length);
        let running = 0;
        let nextIndex = 0;
        let completed = 0;

        function runNext() {
            while (running < limit && nextIndex < tasks.length) {
                const idx = nextIndex++;
                running++;
                tasks[idx]()
                    .then(result => {
                        results[idx] = result;
                        running--;
                        completed++;
                        if (completed === tasks.length) resolve(results);
                        else runNext();
                    })
                    .catch(reject);
            }
        }
        runNext();
    });
}

// Usage:
// const urls = Array.from({ length: 100 }, (_, i) => `/api/item/${i}`);
// const tasks = urls.map(url => () => fetch(url).then(r => r.json()));
// const results = await throttle(tasks, 5); // max 5 concurrent

// --- Semaphore class (reusable concurrency limiter) ---
class Semaphore {
    constructor(max) {
        this.max = max;
        this.count = 0;
        this.queue = [];
    }
    async acquire() {
        if (this.count < this.max) {
            this.count++;
            return;
        }
        await new Promise(resolve => this.queue.push(resolve));
    }
    release() {
        this.count--;
        if (this.queue.length > 0) {
            this.count++;
            this.queue.shift()();
        }
    }
    async run(fn) {
        await this.acquire();
        try { return await fn(); }
        finally { this.release(); }
    }
}

// const sem = new Semaphore(3);
// const results = await Promise.all(
//     urls.map(url => sem.run(() => fetch(url).then(r => r.json())))
// );


// ============================================================
// 28. STRUCTURED CONCURRENCY PATTERNS [ADVANCED]
// ============================================================
// INTERVIEW: "How do you manage groups of concurrent async operations?"
//
// Structured concurrency means: child tasks are bounded by their
// parent scope. If the parent cancels/errors, children clean up.

// --- Pattern 1: Task group with cancellation ---
async function taskGroup(tasks, signal) {
    const controller = new AbortController();
    // Link to parent signal
    signal?.addEventListener("abort", () => controller.abort(), { once: true });

    try {
        return await Promise.all(
            tasks.map(task => task(controller.signal))
        );
    } catch (err) {
        controller.abort(); // cancel remaining tasks
        throw err;
    }
}

// Usage:
// const ctrl = new AbortController();
// const results = await taskGroup([
//     (signal) => fetch("/api/users", { signal }).then(r => r.json()),
//     (signal) => fetch("/api/orders", { signal }).then(r => r.json()),
//     (signal) => fetch("/api/products", { signal }).then(r => r.json()),
// ], ctrl.signal);

// --- Pattern 2: Race with cleanup ---
async function raceWithCleanup(tasks) {
    const controller = new AbortController();
    try {
        return await Promise.race(
            tasks.map(task => task(controller.signal))
        );
    } finally {
        controller.abort(); // cancel losers
    }
}

// --- Pattern 3: Supervised workers (restart on failure) ---
async function supervisedPool(workers, maxRestarts = 3) {
    const restarts = new Map();
    workers.forEach(w => restarts.set(w, 0));

    async function runWorker(worker) {
        while (true) {
            try {
                return await worker();
            } catch (err) {
                const count = restarts.get(worker) + 1;
                restarts.set(worker, count);
                if (count > maxRestarts) throw err;
                console.log(`Worker restarting (${count}/${maxRestarts})`);
                await new Promise(r => setTimeout(r, 1000 * count)); // backoff
            }
        }
    }

    return Promise.all(workers.map(runWorker));
}

// --- Pattern 4: Pipeline (producer -> transformer -> consumer) ---
async function pipeline(source, ...transforms) {
    let current = source;
    for (const transform of transforms) {
        current = transform(current);
    }
    // drain the final async iterable
    const results = [];
    for await (const item of current) {
        results.push(item);
    }
    return results;
}


// ============================================================
// 29. ERROR BOUNDARIES PATTERN [ADVANCED]
// ============================================================
// INTERVIEW: "How do you isolate errors in concurrent operations?"
//
// An error boundary prevents one failing operation from crashing
// its siblings (like React error boundaries, but for async).

// --- Async Error Boundary ---
async function errorBoundary(fn, fallback) {
    try {
        return await fn();
    } catch (err) {
        console.error("Error boundary caught:", err.message);
        return typeof fallback === "function" ? fallback(err) : fallback;
    }
}

// --- Using error boundaries with concurrent operations ---
async function loadDashboard() {
    const [userData, ordersData, analyticsData] = await Promise.all([
        errorBoundary(
            () => fetch("/api/user").then(r => r.json()),
            { name: "Guest", error: true }   // fallback for user
        ),
        errorBoundary(
            () => fetch("/api/orders").then(r => r.json()),
            []                                // fallback for orders
        ),
        errorBoundary(
            () => fetch("/api/analytics").then(r => r.json()),
            null                              // fallback for analytics
        ),
    ]);

    // Dashboard always renders, even if some APIs fail
    return { userData, ordersData, analyticsData };
}

// --- Composable error boundary with logging ---
function createErrorBoundary(name, reporter) {
    return async function boundary(fn, fallback) {
        try {
            return await fn();
        } catch (err) {
            reporter?.({ boundary: name, error: err, timestamp: Date.now() });
            return typeof fallback === "function" ? fallback(err) : fallback;
        }
    };
}

// const apiBoundary = createErrorBoundary("api", logToSentry);
// const result = await apiBoundary(() => fetch("/api"), defaultData);


// ============================================================
// 30. ERROR HANDLING BEST PRACTICES [ADVANCED]
// ============================================================

// RULE 1: Always handle errors at the end of a chain
// fetch("/api")
//   .then(processStep1)
//   .then(processStep2)
//   .catch(handleError);  // catches errors from ANY step above

// RULE 2: Use try/catch with async/await
async function fetchData() {
    try {
        const res = await fetch("/api");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (err) {
        if (err instanceof TypeError) {
            console.error("Network error:", err);
        } else {
            console.error("API error:", err);
        }
        throw err; // re-throw to let caller decide
    }
}

// RULE 3: Distinguish operational vs programmer errors
// Operational: network failure, 404, timeout -> handle gracefully
// Programmer: TypeError, undefined access -> fix the code

// RULE 4: Error recovery in chains (catch returns a value)
// fetch("/primary")
//   .catch(() => fetch("/fallback"))  // try fallback
//   .then(r => r.json())
//   .catch(err => ({ error: true, message: err.message })); // default

// RULE 5: Aggregate errors with Promise.allSettled
// const results = await Promise.allSettled(promises);
// const errors = results.filter(r => r.status === "rejected");
// const values = results.filter(r => r.status === "fulfilled").map(r => r.value);


// ============================================================
// 31. GOTCHAS
// ============================================================

// GOTCHA 1: Promise executor runs SYNCHRONOUSLY
console.log("before");
new Promise((resolve) => {
    console.log("inside executor"); // runs immediately!
    resolve("done");
});
console.log("after");
// Output: before, inside executor, after

// GOTCHA 2: .then() handler runs asynchronously even for resolved promises
Promise.resolve("instant").then(v => console.log(v));
console.log("sync");
// Output: sync, instant (microtask always deferred)

// GOTCHA 3: Forgetting to return in .then() breaks the chain
// Promise.resolve(1)
//   .then(v => { v + 1; })    // no return! next then gets undefined
//   .then(v => console.log(v)); // undefined

// GOTCHA 4: resolve() does not stop execution
// new Promise((resolve, reject) => {
//     resolve("done");
//     console.log("still runs!"); // this line executes!
//     // Use return resolve("done"); to stop
// });

// GOTCHA 5: Passing a non-function to .then() -- identity passthrough
// Promise.resolve(42).then(null).then(v => console.log(v)); // 42

// GOTCHA 6: Error in constructor rejects the promise
// new Promise(() => { throw new Error("oops"); })
//   .catch(e => console.log(e.message)); // "oops"

// GOTCHA 7: Chaining off the wrong reference
// const p = Promise.resolve(1);
// p.then(v => v + 1); // branch 1 (detached!)
// p.then(v => v + 2); // branch 2 (detached!)
// These are TWO separate chains from p, not sequential.

// GOTCHA 8: await in a forEach does NOT work sequentially
// BAD:
// [1,2,3].forEach(async (n) => {
//     await someAsync(n); // fires all three in parallel
// });
// GOOD: use for...of
// for (const n of [1,2,3]) {
//     await someAsync(n); // truly sequential
// }

// GOTCHA 9: Promise.race with empty array hangs forever
// Promise.race([]) -> never settles. Always check for empty input.

// GOTCHA 10: Async function ALWAYS returns a promise
// async function f() { return 42; }
// f() === 42; // false! f() is Promise<42>

// GOTCHA 11: Error in async function rejects the returned promise
// async function bad() { throw new Error("oops"); }
// bad(); // UnhandledPromiseRejection unless .catch() is attached

// GOTCHA 12: Mixing await and .then() can cause confusion
// const result = await fetch("/api").then(r => r.json());
// This works but is hard to debug. Pick ONE style.

// GOTCHA 13: Returning inside .finally() is mostly ignored
// Promise.resolve(1).finally(() => 2).then(v => console.log(v)); // 1, not 2
// Exception: returning a rejected promise or throwing DOES propagate

// GOTCHA 14: AggregateError from Promise.any -- access .errors
// catch (err) { console.log(err.errors); } // array of all reasons

// GOTCHA 15: Top-level await blocks module graph
// Slow top-level awaits stall ALL importers of your module.


// ============================================================
// 32. COMPARISON TABLES
// ============================================================

//   +---------------------------------------------------------------+
//   | CALLBACKS vs PROMISES vs ASYNC/AWAIT                          |
//   +---------------------------------------------------------------+
//   | Feature        | Callbacks   | Promises    | Async/Await      |
//   |----------------|-------------|-------------|------------------|
//   | Readability    | Poor (nest) | Good (chain)| Best (sync-like) |
//   | Error handling | Manual      | .catch()    | try/catch        |
//   | Composability  | Hard        | Good        | Good             |
//   | Cancellation   | Manual      | AbortCtrl   | AbortCtrl        |
//   | Debugging      | Hard        | OK          | Best (stack)     |
//   | Return value   | None        | Promise     | Promise          |
//   | Sequential     | Nesting     | .then chain | await in loop    |
//   | Parallel       | Manual      | Promise.all | Promise.all      |
//   +---------------------------------------------------------------+

//   +---------------------------------------------------------------+
//   | PROMISE API COMPARISON                                        |
//   +---------------------------------------------------------------+
//   | Method          | Resolves when     | Rejects when              |
//   |-----------------|-------------------|---------------------------|
//   | Promise.all     | ALL fulfill       | ANY rejects (fail-fast)   |
//   | Promise.allS... | ALL settle        | NEVER (always fulfills)   |
//   | Promise.race    | FIRST settles     | FIRST settles (if reject) |
//   | Promise.any     | FIRST fulfills    | ALL reject (AggregateErr) |
//   +---------------------------------------------------------------+
//
//   +---------------------------------------------------------------+
//   | Method          | Empty array []    | Use Case                  |
//   |-----------------|-------------------|---------------------------|
//   | Promise.all     | Resolves ([])     | Parallel, need all results|
//   | Promise.allS... | Resolves ([])     | Batch ops, partial OK     |
//   | Promise.race    | Hangs forever     | Timeout, first response   |
//   | Promise.any     | Rejects           | Fastest success, fallback |
//   +---------------------------------------------------------------+
//
//   +---------------------------------------------------------------+
//   | DECISION GUIDE                                                 |
//   +---------------------------------------------------------------+
//   | "I need ALL results, fail if any fails"  -> Promise.all        |
//   | "I need ALL results, even failures"      -> Promise.allSettled |
//   | "I need the FASTEST result"              -> Promise.race       |
//   | "I need the FASTEST SUCCESS"             -> Promise.any        |
//   | "I need sequential execution"            -> for...of + await   |
//   | "I need limited concurrency"             -> Semaphore/throttle |
//   +---------------------------------------------------------------+

//   +---------------------------------------------------------------+
//   | then/catch vs try/catch                                       |
//   +---------------------------------------------------------------+
//   | .then().catch()             | try { await } catch {}          |
//   |----------------------------|----------------------------------|
//   | Works everywhere           | Only in async functions          |
//   | Chainable                  | Linear/procedural                |
//   | .catch() catches chain     | catch {} catches single await    |
//   | Harder to do conditional   | Natural if/else flow             |
//   | Good for simple transforms | Better for complex logic         |
//   +---------------------------------------------------------------+

//   +------------------------------------------------------+
//   | then(f, f) vs then(f).catch(f)                       |
//   +------------------------------------------------------+
//   | Feature            | then(ok, err) | then(ok).catch  |
//   |--------------------|---------------|-----------------|
//   | Catches original   | YES           | YES             |
//   |   rejection        |               |                 |
//   | Catches error in   | NO            | YES             |
//   |   success handler  |               |                 |
//   | Use case           | Separate      | Catch-all       |
//   |                    | handling      | (preferred)     |
//   +------------------------------------------------------+

//   +---------------------------------------------------------------+
//   | ASYNC/AWAIT vs PROMISE CHAINS                                  |
//   +---------------------------------------------------------------+
//   | Feature              | async/await        | .then() chains     |
//   |----------------------|--------------------|--------------------|
//   | Readability          | Sync-like, linear  | Nested/chained     |
//   | Error handling       | try/catch          | .catch()           |
//   | Debugging            | Better stack traces| Can lose frames    |
//   | Conditional logic    | Natural if/else    | Awkward branching  |
//   | Loop integration     | for...of + await   | Recursive .then()  |
//   | Parallel execution   | Promise.all + await| Promise.all.then() |
//   | Performance          | Same (sugar)       | Same               |
//   +---------------------------------------------------------------+


// ============================================================
// 33. INTERVIEW LIGHTNING ROUND
// ============================================================

// Q: What are the three states of a promise?
// A: pending, fulfilled, rejected. Once settled, state is immutable.

// Q: What is the difference between microtask and macrotask?
// A: Microtasks (Promise.then, queueMicrotask) run before macrotasks
//    (setTimeout, setInterval). All microtasks drain before next macrotask.

// Q: Can you cancel a promise?
// A: No native cancellation. Use AbortController+signal pattern.
//    AbortSignal.timeout(ms) for automatic timeout cancellation.

// Q: What happens if you resolve a promise with another promise?
// A: The outer promise "follows" the inner one (adopts its state).
//    resolve(Promise.reject("x")) -> outer promise rejects with "x".

// Q: Promise.all vs Promise.allSettled?
// A: .all fails fast on first rejection. .allSettled waits for all,
//    returns {status, value/reason} for each. Use allSettled for
//    batch operations where partial success is acceptable.

// Q: What is Promise.withResolvers?
// A: ES2024. Returns {promise, resolve, reject} so you can resolve
//    from outside the executor. Replaces the deferred pattern.

// Q: Predict output: setTimeout vs Promise
//    console.log(1);
//    setTimeout(() => console.log(2));
//    Promise.resolve().then(() => console.log(3));
//    console.log(4);
// A: 1, 4, 3, 2 (sync first, then microtask, then macrotask)

// Q: What does `return await` do differently from `return`?
// A: Inside try/catch, `return await` lets the local catch handle
//    rejections. `return` passes the promise through uncaught.
//    Outside try/catch, they behave identically.

// Q: How do you handle errors in Promise.all?
// A: Wrap individual promises in error boundaries, or use
//    Promise.allSettled. Promise.all itself fails fast.

// Q: What is structured concurrency?
// A: Child async tasks are bounded by their parent scope. If the
//    parent cancels, children are aborted. Prevents leaked tasks.

// Q: What is Promise.try?
// A: ES2025 proposal. Normalizes sync-or-async functions into
//    a promise, so sync throws become rejections, not exceptions.

// Q: What is an async iterator?
// A: An object with [Symbol.asyncIterator]() returning
//    { next() -> Promise<{ value, done }> }. Consumed via for-await-of.
