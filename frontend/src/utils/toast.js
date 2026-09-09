let container = null
function ensureContainer() {
  if (container) return container
  container = document.createElement('div')
  container.className = 'toast-container'
  document.body.appendChild(container)
  return container
}

export function toast(message, type = 'info', duration = 2500) {
  const node = document.createElement('div')
  node.className = 'toast ' + (type === 'error' ? 'toast-error' : 'toast-success')
  node.textContent = message
  ensureContainer().appendChild(node)
  setTimeout(() => {
    node.classList.add('toast-out')
    setTimeout(() => node.remove(), 250)
  }, duration)
}