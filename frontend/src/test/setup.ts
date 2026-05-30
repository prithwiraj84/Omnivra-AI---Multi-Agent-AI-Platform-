/**
 * jsdom polyfills for the component test environment.
 * Radix UI (Tooltip/DropdownMenu/ScrollArea) and Recharts (ResponsiveContainer) expect
 * browser APIs that jsdom does not implement. Stub the minimum needed to mount components.
 */

if (!window.matchMedia) {
  window.matchMedia = (query: string) =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    }) as unknown as MediaQueryList
}

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof globalThis.ResizeObserver

class IntersectionObserverStub {
  root = null
  rootMargin = ''
  thresholds = []
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() {
    return []
  }
}
globalThis.IntersectionObserver =
  IntersectionObserverStub as unknown as typeof globalThis.IntersectionObserver

// Radix interaction helpers occasionally touched during mount/layout.
Element.prototype.scrollIntoView = () => {}
Element.prototype.hasPointerCapture = () => false
Element.prototype.setPointerCapture = () => {}
Element.prototype.releasePointerCapture = () => {}
