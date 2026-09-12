<template>
  <Teleport to="body">
    <Transition name="payment-fade">
      <div v-if="open" class="payment-backdrop" @click.self="dismiss">
        <section
          class="payment-dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="wechat-payment-title"
        >
          <header class="payment-header">
            <button
              v-if="isPasswordStep"
              class="payment-back"
              type="button"
              aria-label="返回支付确认"
              :disabled="locked"
              @click="navigateBack"
            >
              ‹
            </button>
            <span v-else aria-hidden="true"></span>
            <div class="payment-brand">
              <span class="wechat-mark" aria-hidden="true">¥</span>
              <span id="wechat-payment-title">微信支付</span>
            </div>
            <button
              class="payment-close"
              type="button"
              aria-label="关闭支付窗口"
              :disabled="locked"
              @click="dismiss"
            >
              ×
            </button>
          </header>

          <div v-if="status === 'success'" class="payment-result" aria-live="polite">
            <div class="success-mark" aria-hidden="true">✓</div>
            <h3>支付成功</h3>
            <p class="result-amount">¥{{ formattedAmount }}</p>
            <p v-if="hasReward" class="result-reward">奖励金已抵扣 ¥{{ formattedRewardAmount }}</p>
            <p class="result-note">订单已生成，可以查看取货凭证</p>
            <button ref="primaryAction" class="payment-primary" type="button" @click="$emit('done')">
              查看取货码
            </button>
          </div>

          <div v-else-if="isPasswordStep" class="password-content">
            <p class="merchant-name">{{ merchant || '食愿商家' }}</p>
            <p class="password-amount">¥{{ formattedAmount }}</p>
            <h3 class="password-title">请输入支付密码</h3>

            <div class="password-entry" @click="focusPinInput">
              <input
                ref="pinInput"
                class="pin-input"
                type="password"
                inputmode="numeric"
                pattern="[0-9]*"
                maxlength="6"
                autocomplete="one-time-code"
                aria-label="请输入6位支付密码"
                :value="paymentPin"
                :disabled="status === 'processing'"
                @input="onPinInput"
              />
              <div class="password-dots" aria-hidden="true">
                <span v-for="index in 6" :key="index">
                  <i v-if="paymentPin.length >= index"></i>
                </span>
              </div>
            </div>

            <p class="password-notice">请输入任意 6 位数字完成验证</p>
            <p v-if="error" class="payment-error" role="alert">{{ error }}</p>
            <div class="processing-line" aria-live="polite">
              <template v-if="status === 'processing'">
                <span class="payment-spinner green" aria-hidden="true"></span>
                正在验证并创建订单…
              </template>
            </div>

            <div class="number-keypad" aria-label="支付数字键盘">
              <template v-for="(key, index) in KEYPAD" :key="index">
                <span v-if="key === null" class="keypad-spacer" aria-hidden="true"></span>
                <button
                  v-else
                  type="button"
                  class="keypad-button"
                  :aria-label="key === 'delete' ? '删除一位' : `数字 ${key}`"
                  :disabled="status === 'processing'"
                  @click="key === 'delete' ? removeDigit() : inputDigit(key)"
                >
                  {{ key === 'delete' ? '⌫' : key }}
                </button>
              </template>
            </div>
          </div>

          <div v-else class="payment-content">
            <p class="merchant-name">{{ merchant || '食愿商家' }}</p>
            <p class="product-name">{{ product || '商品订单' }}</p>
            <div class="payment-amount">
              <small>商品售价</small>
              <div><span>¥</span>{{ formattedOrderAmount }}</div>
            </div>

            <div class="payment-divider"></div>
            <div v-if="hasReward" class="payment-breakdown">
              <div class="reward-row">
                <span>奖励金自动抵扣</span>
                <strong>-¥{{ formattedRewardAmount }}</strong>
              </div>
              <div class="cash-row">
                <span>微信实付</span>
                <strong>¥{{ formattedAmount }}</strong>
              </div>
            </div>
            <div class="payment-method">
              <span>支付方式</span>
              <strong v-if="isFullyCovered"><b aria-hidden="true">奖</b> 奖励金支付</strong>
              <strong v-else><i aria-hidden="true">¥</i> 微信支付</strong>
            </div>

            <p v-if="error" class="payment-error" role="alert">{{ error }}</p>

            <button
              ref="primaryAction"
              class="payment-primary"
              type="button"
              @click="startPayment"
            >
              {{ isFullyCovered ? '确认使用奖励金' : '确认支付' }}
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  amount: { type: [Number, String], default: 0 },
  orderAmount: { type: [Number, String], default: 0 },
  rewardAmount: { type: [Number, String], default: 0 },
  merchant: { type: String, default: '' },
  product: { type: String, default: '' },
  status: { type: String, default: 'idle' },
  error: { type: String, default: '' }
})

const emit = defineEmits(['cancel', 'confirm', 'done'])
const primaryAction = ref(null)
const pinInput = ref(null)
const paymentStep = ref('confirm')
const paymentPin = ref('')
const KEYPAD = ['1', '2', '3', '4', '5', '6', '7', '8', '9', null, '0', 'delete']
const locked = computed(() => props.status === 'processing')
const isPasswordStep = computed(() => paymentStep.value === 'password' && props.status !== 'success')
const formattedAmount = computed(() => {
  const value = Number(props.amount)
  return Number.isFinite(value) ? value.toFixed(2) : '0.00'
})
const formatMoney = (value) => {
  const amount = Number(value)
  return Number.isFinite(amount) ? amount.toFixed(2) : '0.00'
}
const formattedOrderAmount = computed(() => {
  const statedAmount = Number(props.orderAmount)
  const derivedAmount = Number(props.amount || 0) + Number(props.rewardAmount || 0)
  return formatMoney(statedAmount > 0 ? statedAmount : derivedAmount)
})
const formattedRewardAmount = computed(() => formatMoney(props.rewardAmount))
const hasReward = computed(() => Number(props.rewardAmount) > 0)
const isFullyCovered = computed(() => hasReward.value && Number(props.amount) <= 0)

let previousOverflow = ''
let confirmTimer = null

function dismiss() {
  if (!locked.value) emit('cancel')
}

function navigateBack() {
  if (locked.value) return
  if (isPasswordStep.value) {
    paymentStep.value = 'confirm'
    paymentPin.value = ''
    return
  }
  dismiss()
}

async function showPasswordStep() {
  paymentPin.value = ''
  paymentStep.value = 'password'
  await nextTick()
  focusPinInput()
}

function startPayment() {
  if (isFullyCovered.value) {
    emit('confirm', '')
    return
  }
  showPasswordStep()
}

function setPaymentPin(value) {
  paymentPin.value = String(value).replace(/\D/g, '').slice(0, 6)
  clearTimeout(confirmTimer)
  if (paymentPin.value.length === 6 && props.status === 'idle') {
    clearTimeout(confirmTimer)
    confirmTimer = setTimeout(() => {
      if (props.open && paymentPin.value.length === 6 && props.status === 'idle') {
        emit('confirm', paymentPin.value)
      }
    }, 180)
  }
}

function inputDigit(digit) {
  if (props.status !== 'idle' || paymentPin.value.length >= 6) return
  setPaymentPin(paymentPin.value + digit)
  focusPinInput()
}

function removeDigit() {
  if (props.status !== 'idle') return
  setPaymentPin(paymentPin.value.slice(0, -1))
  focusPinInput()
}

function onPinInput(event) {
  setPaymentPin(event.target.value)
  event.target.value = paymentPin.value
}

function focusPinInput() {
  if (props.status === 'idle') pinInput.value?.focus()
}

function onKeydown(event) {
  if (event.key === 'Escape') navigateBack()
}

watch(
  () => [props.open, props.status, paymentStep.value],
  async ([open]) => {
    if (!open) return
    await nextTick()
    if (isPasswordStep.value) focusPinInput()
    else primaryAction.value?.focus()
  }
)

watch(
  () => props.open,
  (open) => {
    if (open) {
      paymentStep.value = 'confirm'
      paymentPin.value = ''
      previousOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
      window.addEventListener('keydown', onKeydown)
    } else {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', onKeydown)
    }
  }
)

watch(
  () => props.status,
  (status, previousStatus) => {
    if (status === 'success' || (previousStatus === 'processing' && status === 'idle')) {
      paymentPin.value = ''
    }
  }
)

onBeforeUnmount(() => {
  clearTimeout(confirmTimer)
  document.body.style.overflow = previousOverflow
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.payment-backdrop {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgba(17, 24, 39, 0.5);
}

.payment-dialog {
  width: min(390px, 100%);
  max-height: calc(100vh - 32px);
  overflow-y: auto;
  border-radius: 8px;
  background: #fff;
  color: #1f2937;
  box-shadow: 0 20px 50px rgba(17, 24, 39, 0.24);
}

.payment-header {
  display: grid;
  grid-template-columns: 36px 1fr 48px;
  align-items: center;
  min-height: 56px;
  padding: 8px 14px;
  border-bottom: 1px solid #e5e7eb;
}

.payment-back,
.payment-close {
  width: 32px;
  height: 32px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #6b7280;
  font-size: 28px;
  line-height: 1;
  cursor: pointer;
}

.payment-close { justify-self: end; }
.payment-back { font-size: 30px; }
.payment-back:disabled,
.payment-close:disabled { opacity: 0.35; cursor: default; }
.payment-back:focus-visible,
.payment-close:focus-visible,
.payment-primary:focus-visible { outline: 3px solid rgba(7, 193, 96, 0.25); outline-offset: 2px; }

.payment-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 700;
}

.wechat-mark,
.payment-method i {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: #07c160;
  color: #fff;
  font-style: normal;
  font-weight: 800;
}

.payment-content { padding: 30px 24px 24px; text-align: center; }
.password-content { padding: 24px 20px 20px; text-align: center; }
.merchant-name { margin: 0; color: #374151; font-size: 15px; font-weight: 600; }
.product-name { margin: 5px auto 0; max-width: 290px; overflow-wrap: anywhere; color: #9ca3af; font-size: 13px; }

.payment-amount {
  margin: 18px 0 26px;
  color: #111827;
  font-size: 38px;
  font-weight: 700;
  line-height: 1.2;
}

.payment-amount small { display: block; margin-bottom: 4px; color: #9ca3af; font-size: 12px; font-weight: 500; }
.payment-amount span { margin-right: 4px; font-size: 22px; font-weight: 600; }
.payment-divider { height: 1px; background: #e5e7eb; }
.payment-breakdown { padding: 12px 0; border-bottom: 1px solid #e5e7eb; }
.payment-breakdown > div { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 5px 0; color: #6b7280; font-size: 13px; text-align: left; }
.payment-breakdown strong { flex-shrink: 0; color: #374151; font-variant-numeric: tabular-nums; }
.payment-breakdown .reward-row { color: #c76a16; }
.payment-breakdown .reward-row strong { color: #d65f14; }
.payment-breakdown .cash-row { color: #374151; font-size: 14px; }
.payment-breakdown .cash-row strong { color: #111827; font-size: 18px; }

.payment-method {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 0;
  color: #6b7280;
  font-size: 14px;
  text-align: left;
}

.payment-method strong { display: flex; align-items: center; justify-content: flex-end; gap: 7px; color: #1f2937; font-size: 14px; }
.payment-method i { width: 21px; height: 21px; border-radius: 5px; font-size: 13px; }
.payment-method b { display: inline-flex; width: 21px; height: 21px; align-items: center; justify-content: center; border-radius: 5px; background: #f59e0b; color: #fff; font-size: 11px; }
.payment-error { margin: -4px 0 14px; color: #dc2626; font-size: 13px; }

.password-amount { margin: 6px 0 22px; color: #111827; font-size: 26px; font-weight: 700; }
.password-title { margin: 0 0 14px; color: #1f2937; font-size: 16px; }
.password-entry { position: relative; width: max-content; max-width: 100%; margin: 0 auto; cursor: text; }
.pin-input {
  position: absolute;
  inset: 0;
  z-index: 1;
  width: 100%;
  height: 100%;
  border: 0;
  opacity: 0;
  font-size: 16px;
  cursor: text;
}
.password-dots {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 40px));
  justify-content: center;
  gap: 6px;
}

.password-dots span {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 42px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
}

.password-dots i { width: 10px; height: 10px; border-radius: 50%; background: #111827; }
.password-notice { margin: 10px 0 0; color: #9ca3af; font-size: 12px; }
.processing-line {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-height: 30px;
  color: #078f49;
  font-size: 13px;
}

.number-keypad {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 4px;
}

.keypad-button,
.keypad-spacer { min-height: 48px; }
.keypad-button {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
  color: #111827;
  font-size: 21px;
  font-weight: 600;
  cursor: pointer;
}

.keypad-button:hover:not(:disabled) { background: #f3f4f6; border-color: #d1d5db; }
.keypad-button:active:not(:disabled) { background: #e5e7eb; }
.keypad-button:focus-visible { outline: 3px solid rgba(7, 193, 96, 0.22); outline-offset: 1px; }
.keypad-button:disabled { opacity: 0.48; cursor: wait; }

.payment-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  min-height: 46px;
  border: 1px solid #07c160;
  border-radius: 8px;
  background: #07c160;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

.payment-primary:hover { background: #06ad56; border-color: #06ad56; }
.payment-primary:disabled { opacity: 0.68; cursor: wait; }

.payment-spinner {
  width: 17px;
  height: 17px;
  border: 2px solid rgba(255, 255, 255, 0.45);
  border-top-color: #fff;
  border-radius: 50%;
  animation: payment-spin 0.7s linear infinite;
}

.payment-spinner.green { border-color: rgba(7, 193, 96, 0.25); border-top-color: #07c160; }

.payment-result { padding: 36px 24px 24px; text-align: center; }
.success-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 58px;
  height: 58px;
  margin: 0 auto 16px;
  border-radius: 50%;
  background: #07c160;
  color: #fff;
  font-size: 34px;
  line-height: 1;
}

.payment-result h3 { margin: 0; font-size: 21px; }
.result-amount { margin: 8px 0 0; color: #111827; font-size: 28px; font-weight: 700; }
.result-reward { margin: 3px 0 0; color: #d65f14; font-size: 12px; font-weight: 650; }
.result-note { margin: 8px 0 24px; color: #6b7280; font-size: 13px; }

.payment-fade-enter-active,
.payment-fade-leave-active { transition: opacity 0.18s ease; }
.payment-fade-enter-active .payment-dialog,
.payment-fade-leave-active .payment-dialog { transition: transform 0.18s ease; }
.payment-fade-enter-from,
.payment-fade-leave-to { opacity: 0; }
.payment-fade-enter-from .payment-dialog,
.payment-fade-leave-to .payment-dialog { transform: translateY(10px); }

@keyframes payment-spin { to { transform: rotate(360deg); } }

@media (max-width: 480px) {
  .payment-backdrop { align-items: flex-end; padding: 0; }
  .payment-dialog { width: 100%; max-height: calc(100vh - 24px); border-radius: 8px 8px 0 0; }
}

@media (prefers-reduced-motion: reduce) {
  .payment-fade-enter-active,
  .payment-fade-leave-active,
  .payment-fade-enter-active .payment-dialog,
  .payment-fade-leave-active .payment-dialog { transition: none; }
  .payment-spinner { animation-duration: 1.4s; }
}
</style>
