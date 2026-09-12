/**
 * 周边地点（POI）搜索。
 *
 * 默认走 OpenStreetMap 的 Overpass 接口，免费、无需 key；
 * 若在 .env 里配了 VITE_AMAP_KEY（高德 Web 服务 key），则优先用高德——国内更快、数据更全。
 *
 * 统一返回：[{ id, name, category, address, distance, lat, lng }]（按距离升序）
 */

// 高德 Web 服务 key（可选）。在 frontend/.env.development 里配置：VITE_AMAP_KEY=xxxxxxxx
const AMAP_KEY = import.meta.env.VITE_AMAP_KEY || ''

// Overpass 公共节点，前一个为社区镜像（通常更快），后一个为官方
const OVERPASS_ENDPOINTS = [
  'https://overpass.kumi.systems/api/interpreter',
  'https://overpass-api.de/api/interpreter'
]

function haversine(lat1, lng1, lat2, lng2) {
  const R = 6371000
  const toRad = (d) => (d * Math.PI) / 180
  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2
  return Math.round(R * 2 * Math.asin(Math.sqrt(a)))
}

function request(url, options, timeout = 15000) {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), timeout)
  return fetch(url, { ...options, signal: ctrl.signal }).finally(() => clearTimeout(timer))
}

function categoryOf(tags = {}) {
  const map = {
    amenity: { restaurant: '餐饮', cafe: '餐饮', fast_food: '餐饮', school: '学校', university: '学校', college: '学校', library: '公共设施', hospital: '医疗', pharmacy: '医疗', bank: '金融', parking: '停车场', marketplace: '购物' },
    shop: { supermarket: '购物', convenience: '购物', mall: '购物', bakery: '餐饮', clothes: '购物', hairdresser: '生活服务', laundry: '生活服务' },
    building: { university: '学校', dormitory: '宿舍', retail: '购物', commercial: '商业' },
    office: { default: '办公' },
    tourism: { hotel: '住宿', attraction: '景点' }
  }
  for (const key of ['amenity', 'shop', 'building', 'tourism', 'office']) {
    const value = tags[key]
    if (!value) continue
    const hit = map[key]?.[value]
    if (hit) return hit
    return key === 'amenity' ? '生活设施' : key === 'shop' ? '商铺' : key === 'building' ? '建筑' : '地点'
  }
  return '地点'
}

async function overpassAround({ lat, lng, radius, keyword, limit }) {
  const nameFilter = keyword
    ? `["name"~"${String(keyword).replace(/["\\]/g, ' ')}",i]`
    : '["name"]'
  const query =
    `[out:json][timeout:25];(` +
    `node(around:${radius},${lat},${lng})${nameFilter};` +
    `way(around:${radius},${lat},${lng})${nameFilter};` +
    `);out center ${limit * 3};`

  for (const endpoint of OVERPASS_ENDPOINTS) {
    try {
      const res = await request(
        endpoint,
        { method: 'POST', body: new URLSearchParams({ data: query }) },
        15000
      )
      if (!res.ok) continue
      const data = await res.json()
      const list = (data.elements || [])
        .map((el) => {
          const p = el.lat != null ? { lat: el.lat, lng: el.lon } : el.center
          if (!p || p.lat == null || p.lng == null) return null
          const tags = el.tags || {}
          if (!tags.name) return null
          return {
            id: `${el.type}-${el.id}`,
            name: tags.name,
            category: categoryOf(tags),
            address: [tags['addr:street'], tags['addr:housenumber']].filter(Boolean).join('') || '',
            distance: haversine(lat, lng, p.lat, p.lng),
            lat: Number(p.lat.toFixed(6)),
            lng: Number(p.lng.toFixed(6))
          }
        })
        .filter(Boolean)
        .filter((item) => item.distance <= radius)
      if (list.length) {
        // 有明确分类（餐饮/学校/商铺…）的排前面，纯坐标点排后面
        const rank = (x) => (x.category === '地点' ? 1 : 0)
        return list.sort((a, b) => rank(a) - rank(b) || a.distance - b.distance).slice(0, limit)
      }
    } catch (e) { /* 换下一个节点 */ }
  }
  return []
}

async function amapAround({ lat, lng, radius, keyword, limit }) {
  const params = new URLSearchParams({
    key: AMAP_KEY,
    location: `${lng},${lat}`,
    radius: String(radius),
    offset: String(limit),
    extensions: 'base',
    output: 'JSON'
  })
  if (keyword) params.set('keywords', keyword)
  const res = await request(`https://restapi.amap.com/v3/place/around?${params}`, {}, 12000)
  if (!res.ok) return []
  const data = await res.json()
  if (data.status !== '1' || !Array.isArray(data.pois)) return []
  return data.pois
    .map((poi) => {
      const [plng, plat] = String(poi.location || '').split(',').map(Number)
      if (!Number.isFinite(plat) || !Number.isFinite(plng)) return null
      return {
        id: poi.id,
        name: poi.name,
        category: poi.type || '地点',
        address: poi.address || '',
        distance: Number(poi.distance) || haversine(lat, lng, plat, plng),
        lat: Number(plat.toFixed(6)),
        lng: Number(plng.toFixed(6))
      }
    })
    .filter(Boolean)
    .sort((a, b) => a.distance - b.distance)
}

/**
 * 搜索指定坐标周边 radius 米内的地点。
 * @returns {Promise<Array>} 按距离升序的地点列表；全部失败时返回空数组
 */
export async function searchAround({ lat, lng, radius = 500, keyword = '', limit = 20 } = {}) {
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return []
  if (AMAP_KEY) {
    try {
      const list = await amapAround({ lat, lng, radius, keyword, limit })
      if (list.length) return list
    } catch (e) { /* 高德失败则退回 Overpass */ }
  }
  return overpassAround({ lat, lng, radius, keyword, limit })
}
