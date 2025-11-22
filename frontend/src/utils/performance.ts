/**
 * 性能优化工具
 *
 * 职责：
 * - 图片懒加载指令
 * - 防抖/节流函数
 * - 虚拟滚动支持
 * - 性能监控
 * - 资源预加载
 *
 * 上游依赖：
 * - 无
 *
 * 下游调用者：
 * - main.ts（注册指令）
 * - 各组件（使用工具函数）
 */

import type { App, Directive, DirectiveBinding } from 'vue'

/**
 * 防抖函数
 * @param fn 要执行的函数
 * @param delay 延迟时间（毫秒）
 */
export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 300
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout> | null = null

  return function (this: any, ...args: Parameters<T>) {
    if (timer) {
      clearTimeout(timer)
    }
    timer = setTimeout(() => {
      fn.apply(this, args)
      timer = null
    }, delay)
  }
}

/**
 * 节流函数
 * @param fn 要执行的函数
 * @param limit 时间间隔（毫秒）
 */
export function throttle<T extends (...args: any[]) => any>(
  fn: T,
  limit: number = 300
): (...args: Parameters<T>) => void {
  let inThrottle = false

  return function (this: any, ...args: Parameters<T>) {
    if (!inThrottle) {
      fn.apply(this, args)
      inThrottle = true
      setTimeout(() => {
        inThrottle = false
      }, limit)
    }
  }
}

/**
 * 图片懒加载指令
 */
export const lazyLoadDirective: Directive = {
  mounted(el: HTMLImageElement, binding: DirectiveBinding) {
    const loadImage = () => {
      el.src = binding.value
      el.classList.add('lazy-loaded')
    }

    // 占位图
    const placeholder = el.getAttribute('data-placeholder') || ''
    if (placeholder) {
      el.src = placeholder
    }

    // 使用 IntersectionObserver
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              loadImage()
              observer.unobserve(el)
            }
          })
        },
        {
          rootMargin: '50px 0px',
          threshold: 0.01
        }
      )
      observer.observe(el)
    } else {
      // 降级方案：直接加载
      loadImage()
    }
  }
}

/**
 * 元素可见性指令（用于按需加载）
 */
export const visibleDirective: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const callback = binding.value

    if (typeof callback !== 'function') {
      console.warn('v-visible directive requires a callback function')
      return
    }

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              callback(entry)
              if (binding.modifiers.once) {
                observer.unobserve(el)
              }
            }
          })
        },
        {
          rootMargin: binding.arg || '0px',
          threshold: 0.1
        }
      )
      observer.observe(el)

      // 存储 observer 以便清理
      ;(el as any)._visibleObserver = observer
    } else {
      // 降级：直接执行
      callback({ isIntersecting: true, target: el })
    }
  },

  unmounted(el: HTMLElement) {
    const observer = (el as any)._visibleObserver
    if (observer) {
      observer.disconnect()
    }
  }
}

/**
 * 预加载资源
 * @param urls 资源 URL 列表
 * @param type 资源类型
 */
export function preloadResources(
  urls: string[],
  type: 'image' | 'script' | 'style' = 'image'
): void {
  urls.forEach((url) => {
    const link = document.createElement('link')
    link.rel = 'preload'
    link.href = url

    switch (type) {
      case 'image':
        link.as = 'image'
        break
      case 'script':
        link.as = 'script'
        break
      case 'style':
        link.as = 'style'
        break
    }

    document.head.appendChild(link)
  })
}

/**
 * 预取页面资源（用于路由预取）
 * @param path 页面路径
 */
export function prefetchPage(path: string): void {
  const link = document.createElement('link')
  link.rel = 'prefetch'
  link.href = path
  document.head.appendChild(link)
}

/**
 * 空闲时执行任务
 * @param callback 要执行的回调
 * @param options 配置选项
 */
export function runOnIdle(
  callback: () => void,
  options: { timeout?: number } = {}
): void {
  if ('requestIdleCallback' in window) {
    ;(window as any).requestIdleCallback(callback, options)
  } else {
    // 降级方案
    setTimeout(callback, options.timeout || 1)
  }
}

/**
 * 延迟加载组件（用于路由懒加载）
 * @param importFn 动态导入函数
 * @param delay 延迟时间
 */
export function lazyComponent(
  importFn: () => Promise<any>,
  delay: number = 0
): () => Promise<any> {
  return () =>
    new Promise((resolve) => {
      if (delay > 0) {
        setTimeout(() => {
          importFn().then(resolve)
        }, delay)
      } else {
        importFn().then(resolve)
      }
    })
}

/**
 * 性能标记
 */
export const performanceMarker = {
  start(name: string): void {
    if (performance.mark) {
      performance.mark(`${name}-start`)
    }
  },

  end(name: string): void {
    if (performance.mark && performance.measure) {
      performance.mark(`${name}-end`)
      try {
        performance.measure(name, `${name}-start`, `${name}-end`)
      } catch (e) {
        // 忽略重复测量的错误
      }
    }
  },

  getMeasure(name: string): PerformanceEntry | undefined {
    if (performance.getEntriesByName) {
      const entries = performance.getEntriesByName(name, 'measure')
      return entries[entries.length - 1]
    }
    return undefined
  },

  clear(name?: string): void {
    if (performance.clearMarks && performance.clearMeasures) {
      if (name) {
        performance.clearMarks(`${name}-start`)
        performance.clearMarks(`${name}-end`)
        performance.clearMeasures(name)
      } else {
        performance.clearMarks()
        performance.clearMeasures()
      }
    }
  }
}

/**
 * 获取性能指标
 */
export function getPerformanceMetrics(): {
  fcp: number
  lcp: number
  fid: number
  cls: number
  ttfb: number
} | null {
  if (!('PerformanceObserver' in window)) {
    return null
  }

  const metrics: any = {
    fcp: 0,
    lcp: 0,
    fid: 0,
    cls: 0,
    ttfb: 0
  }

  // First Contentful Paint
  const paintEntries = performance.getEntriesByType('paint')
  const fcpEntry = paintEntries.find((entry) => entry.name === 'first-contentful-paint')
  if (fcpEntry) {
    metrics.fcp = fcpEntry.startTime
  }

  // Time to First Byte
  const navEntries = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[]
  if (navEntries.length > 0) {
    metrics.ttfb = navEntries[0].responseStart
  }

  return metrics
}

/**
 * 监控 Web Vitals
 */
export function observeWebVitals(callback: (metric: { name: string; value: number }) => void): void {
  if (!('PerformanceObserver' in window)) {
    return
  }

  // LCP - Largest Contentful Paint
  try {
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      const lastEntry = entries[entries.length - 1] as any
      callback({ name: 'LCP', value: lastEntry.renderTime || lastEntry.loadTime })
    })
    lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true })
  } catch (e) {
    // 不支持 LCP
  }

  // FID - First Input Delay
  try {
    const fidObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries() as any[]
      entries.forEach((entry) => {
        callback({ name: 'FID', value: entry.processingStart - entry.startTime })
      })
    })
    fidObserver.observe({ type: 'first-input', buffered: true })
  } catch (e) {
    // 不支持 FID
  }

  // CLS - Cumulative Layout Shift
  try {
    let clsValue = 0
    const clsObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries() as any[]
      entries.forEach((entry) => {
        if (!entry.hadRecentInput) {
          clsValue += entry.value
        }
      })
      callback({ name: 'CLS', value: clsValue })
    })
    clsObserver.observe({ type: 'layout-shift', buffered: true })
  } catch (e) {
    // 不支持 CLS
  }
}

/**
 * 内存使用监控
 */
export function getMemoryUsage(): {
  usedJSHeapSize: number
  totalJSHeapSize: number
  jsHeapSizeLimit: number
} | null {
  if ('memory' in performance) {
    const memory = (performance as any).memory
    return {
      usedJSHeapSize: memory.usedJSHeapSize,
      totalJSHeapSize: memory.totalJSHeapSize,
      jsHeapSizeLimit: memory.jsHeapSizeLimit
    }
  }
  return null
}

/**
 * 注册性能优化指令
 */
export function registerPerformanceDirectives(app: App): void {
  app.directive('lazy', lazyLoadDirective)
  app.directive('visible', visibleDirective)
}

/**
 * 图片压缩（客户端）
 */
export function compressImage(
  file: File,
  options: {
    maxWidth?: number
    maxHeight?: number
    quality?: number
  } = {}
): Promise<Blob> {
  const { maxWidth = 1920, maxHeight = 1080, quality = 0.8 } = options

  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        const canvas = document.createElement('canvas')
        let { width, height } = img

        // 计算缩放比例
        if (width > maxWidth) {
          height = (height * maxWidth) / width
          width = maxWidth
        }
        if (height > maxHeight) {
          width = (width * maxHeight) / height
          height = maxHeight
        }

        canvas.width = width
        canvas.height = height

        const ctx = canvas.getContext('2d')
        if (!ctx) {
          reject(new Error('Failed to get canvas context'))
          return
        }

        ctx.drawImage(img, 0, 0, width, height)

        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob)
            } else {
              reject(new Error('Failed to compress image'))
            }
          },
          file.type,
          quality
        )
      }
      img.onerror = reject
      img.src = e.target?.result as string
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

/**
 * 请求空闲回调的 polyfill
 */
if (!('requestIdleCallback' in window)) {
  ;(window as any).requestIdleCallback = function (
    callback: (deadline: { didTimeout: boolean; timeRemaining: () => number }) => void,
    options?: { timeout?: number }
  ) {
    const start = Date.now()
    return setTimeout(function () {
      callback({
        didTimeout: false,
        timeRemaining: function () {
          return Math.max(0, 50 - (Date.now() - start))
        }
      })
    }, options?.timeout || 1)
  }

  ;(window as any).cancelIdleCallback = function (id: number) {
    clearTimeout(id)
  }
}
