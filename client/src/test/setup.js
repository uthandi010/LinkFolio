import "@testing-library/jest-dom";

// Node 22+ ships a native `localStorage`, and on some Node/jsdom version
// combinations it silently wins over jsdom's own implementation but is left
// unusable without a `--localstorage-file` path (methods like `.clear()`
// are missing). Rather than depend on Node flags or version, install a
// simple in-memory polyfill so tests get a working localStorage no matter
// which Node version runs them.
class MemoryStorage {
  #store = new Map();

  get length() {
    return this.#store.size;
  }

  clear() {
    this.#store.clear();
  }

  getItem(key) {
    return this.#store.has(key) ? this.#store.get(key) : null;
  }

  key(index) {
    return Array.from(this.#store.keys())[index] ?? null;
  }

  removeItem(key) {
    this.#store.delete(key);
  }

  setItem(key, value) {
    this.#store.set(key, String(value));
  }
}

const memoryStorage = new MemoryStorage();

for (const target of [globalThis, typeof window !== "undefined" ? window : undefined]) {
  if (target) {
    Object.defineProperty(target, "localStorage", {
      value: memoryStorage,
      configurable: true,
    });
  }
}
