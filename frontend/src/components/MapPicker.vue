<template>
  <div>
    <div class="map-box" :style="{ height: height + 'px' }">
      <div ref="mapEl" style="height:100%"></div>
      <div v-if="!tilesLoaded" class="map-overlay">地图加载中…（离线时请用搜索选择位置）</div>
    </div>
    <div class="map-tip">
      {{ readonly ? '地图仅用于查看，请用上方搜索选择店铺位置' : '在地图上点击或拖拽图钉，选择店铺位置' }}
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  modelValue: { type: Object, default: () => ({ lat: null, lng: null }) },
  height: { type: Number, default: 260 },
  /** 只读模式：地图只做展示，不能点击/拖拽改坐标 */
  readonly: { type: Boolean, default: false },
  /** 以当前坐标为中心画的辐射圈半径（米），0 表示不画 */
  radius: { type: Number, default: 0 }
})
const emit = defineEmits(['update:modelValue'])

const mapEl = ref(null)
const tilesLoaded = ref(false)
let map = null
let marker = null
let circle = null

const pin = L.divIcon({
  html: '<div style="width:26px;height:34px;background:#f97316;border:2px solid #fff;border-radius:15px 15px 15px 0;transform:rotate(-45deg);box-shadow:0 2px 6px rgba(0,0,0,.3)"></div>',
  iconSize: [26, 34],
  iconAnchor: [13, 34]
})

function setPosition(lat, lng) {
  if (marker) marker.setLatLng([lat, lng])
  else marker = L.marker([lat, lng], { icon: pin, draggable: !props.readonly }).addTo(map)
  map.panTo([lat, lng])
  if (props.radius > 0) {
    if (circle) circle.setLatLng([lat, lng])
    else circle = L.circle([lat, lng], {
      radius: props.radius,
      color: '#e97950',
      weight: 1,
      fillColor: '#e97950',
      fillOpacity: 0.08
    }).addTo(map)
  }
}

onMounted(() => {
  const lat = props.modelValue.lat ?? 22.1496
  const lng = props.modelValue.lng ?? 113.565
  map = L.map(mapEl.value, { dragging: !props.readonly, doubleClickZoom: !props.readonly })
    .setView([lat, lng], props.radius > 0 ? 16 : 14)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18 })
    .addTo(map)
    .on('load', () => { tilesLoaded.value = true })

  setPosition(lat, lng)
  if (props.readonly) return
  marker.on('dragend', () => {
    const ll = marker.getLatLng()
    emit('update:modelValue', { lat: +ll.lat.toFixed(6), lng: +ll.lng.toFixed(6) })
  })
  map.on('click', (e) => {
    emit('update:modelValue', { lat: +e.latlng.lat.toFixed(6), lng: +e.latlng.lng.toFixed(6) })
    setPosition(e.latlng.lat, e.latlng.lng)
  })
})

// 外部修改坐标（如「获取当前位置」按钮）时，同步移动图钉并居中
watch(() => props.modelValue, (v) => {
  if (map && v && v.lat && v.lng) setPosition(v.lat, v.lng)
}, { deep: true })

onBeforeUnmount(() => {
  if (map) { map.remove(); map = null }
})
</script>
