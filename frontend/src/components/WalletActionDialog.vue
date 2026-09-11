<template>
  <Teleport to="body">
    <Transition name="wallet-dialog-fade">
      <div v-if="open" class="wallet-dialog-backdrop" @click.self="close">
        <section class="wallet-dialog" role="dialog" aria-modal="true" :aria-labelledby="titleId">
          <header class="dialog-header">
            <div>
              <span class="dialog-kicker">FOODLINK WALLET</span>
              <h3 :id="titleId">{{ actionLabel }}</h3>
            </div>
            <button class="close-button" type="button" aria-label="关闭" :disabled="loading" @click="close">×</button>
          </header>

          <div class="balance-summary">
            <span>当前可用余额</span>
            <strong>¥{{ formattedBalance }}</strong>
          </div>

          <form @submit.prevent="submit">
            <label class="field-label" for="wallet-amount">{{ action === 'withdraw' ? '提现金额' : '充值金额' }}</label>
            <div class="amount-field" :class="{ focused: amountFocused }">
              <span>¥</span>
              <input
                id="wallet-amount"
                ref="amountInput"
                v-model.trim="amount"
                type="text"
                inputmode="decimal"
                autocomplete="off"
                placeholder="0.00"
                :disabled="loading"
                @focus="amountFocused = true"
                @blur="amountFocused = false"
              />
            </div>

            <div class="quick-amounts" aria-label="快捷金额">
              <button v-for="value in quickAmounts" :key="value" type="button" :disabled="loading" @click="amount = value.toFixed(2)">
                ¥{{ value }}
              </button>
            </div>

            <label class="field-label" for="wallet-password">6 位演示支付密码</label>
            <input
              id="wallet-password"
              v-model="paymentPassword"
              class="password-input"
              type="password"
              inputmode="numeric"
              maxlength="6"
              autocomplete="one-time-code"
              placeholder="请输入任意 6 位数字"
              :disabled="loading"
              @input="onlyDigits"
            />

            <div class="result-row">
              <span>{{ action === 'withdraw' ? '预计到账' : '充值后余额' }}</span>
              <strong>¥{{ resultAmount }}</strong>
            </div>
            <p class="demo-note">演示环境，不会发生真实充值或转账</p>
            <p v-if="error" class="dialog-error" role="alert">{{ error }}</p>

            <div class="dialog-actions">
              <button class="cancel-button" type="button" :disabled="loading" @click="close">取消</button>
              <button class="confirm-button" :class="action" type="submit" :disabled="loading">
                {{ loading ? '处理中…' : `确认${actionLabel}` }}
              </button>
            </div>
          </form>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  action: { type: String, default: 'recharge' },
  balance: { type: [Number, String], default: 0 },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['close', 'submit'])
const amountInput = ref(null)
const amount = ref('')
const paymentPassword = ref('')
const error = ref('')
const amountFocused = ref(false)
const quickAmounts = [20, 50, 100]
const titleId = 'wallet-action-title'
const actionLabel = computed(() => props.action === 'withdraw' ? '提现' : '充值')
const balanceNumber = computed(() => Number(props.balance) || 0)
const formattedBalance = computed(() => balanceNumber.value.toFixed(2))
const parsedAmount = computed(() => Number(amount.value) || 0)
const resultAmount = computed(() => {
  if (props.action === 'withdraw') return Math.max(0, parsedAmount.value).toFixed(2)
  return Math.max(0, balanceNumber.value + parsedAmount.value).toFixed(2)
})

let previousOverflow = ''

function onlyDigits(event) {
  paymentPassword.value = event.target.value.replace(/\D/g, '').slice(0, 6)
}

function close() {
  if (!props.loading) emit('close')
}

function submit() {
  error.value = ''
  const rawAmount = amount.value.trim()
  if (!/^(?:0|[1-9]\d{0,8})(?:\.\d{1,2})?$/.test(rawAmount) || Number(rawAmount) <= 0) {
    error.value = '请输入正确的金额，最多保留两位小数'
    return
  }
  if (props.action === 'withdraw' && Number(rawAmount) > balanceNumber.value) {
    error.value = '提现金额不能超过当前可用余额'
    return
  }
  if (!/^\d{6}$/.test(paymentPassword.value)) {
    error.value = '请输入 6 位数字支付密码'
    return
  }
  emit('submit', {
    amount: Number(rawAmount).toFixed(2),
    payment_password: paymentPassword.value
  })
}

function onKeydown(event) {
  if (event.key === 'Escape') close()
}

watch(() => props.open, async (open) => {
  if (open) {
    amount.value = ''
    paymentPassword.value = ''
    error.value = ''
    previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', onKeydown)
    await nextTick()
    amountInput.value?.focus()
  } else {
    document.body.style.overflow = previousOverflow
    window.removeEventListener('keydown', onKeydown)
  }
})

onBeforeUnmount(() => {
  document.body.style.overflow = previousOverflow
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.wallet-dialog-backdrop { position: fixed; inset: 0; z-index: 10000; display: grid; place-items: center; padding: 16px; background: rgba(17, 25, 21, .56); }
.wallet-dialog { width: min(400px, 100%); max-height: calc(100vh - 32px); overflow-y: auto; border-radius: 8px; background: #fff; color: #1f2923; box-shadow: 0 24px 64px rgba(17, 25, 21, .28); }
.dialog-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 22px 15px; border-bottom: 1px solid #e7ebe8; }
.dialog-kicker { display: block; margin-bottom: 3px; color: #87918b; font-size: 9px; font-weight: 800; }
.dialog-header h3 { margin: 0; font-size: 20px; }
.close-button { width: 34px; height: 34px; padding: 0; border: 0; border-radius: 7px; background: #f3f5f3; color: #68716c; font-size: 24px; line-height: 1; cursor: pointer; }
.balance-summary { display: flex; align-items: center; justify-content: space-between; margin: 20px 22px 0; padding: 13px 14px; border-radius: 7px; background: #f2f6f3; }
.balance-summary span { color: #68716c; font-size: 12px; }
.balance-summary strong { font-size: 17px; font-variant-numeric: tabular-nums; }
form { padding: 20px 22px 22px; }
.field-label { display: block; margin-bottom: 7px; color: #56605a; font-size: 12px; font-weight: 700; }
.amount-field { display: flex; align-items: center; height: 56px; padding: 0 14px; border: 1px solid #dce2de; border-radius: 8px; background: #fff; transition: border-color .15s, box-shadow .15s; }
.amount-field.focused { border-color: #4f8d68; box-shadow: 0 0 0 3px rgba(79, 141, 104, .12); }
.amount-field span { color: #627069; font-size: 19px; font-weight: 700; }
.amount-field input { min-width: 0; flex: 1; padding: 0 0 0 8px; border: 0; outline: 0; color: #17211c; font-size: 28px; font-weight: 700; font-variant-numeric: tabular-nums; }
.amount-field input::placeholder { color: #c5cbc7; }
.quick-amounts { display: grid; grid-template-columns: repeat(3, 1fr); gap: 7px; margin: 9px 0 20px; }
.quick-amounts button { min-height: 34px; border: 1px solid #e0e5e2; border-radius: 7px; background: #fafbfa; color: #56605a; cursor: pointer; }
.quick-amounts button:hover { border-color: #9db5a5; background: #f2f7f3; }
.password-input { width: 100%; height: 44px; padding: 0 12px; border: 1px solid #dce2de; border-radius: 8px; outline: 0; font-size: 15px; letter-spacing: 0; }
.password-input:focus { border-color: #4f8d68; box-shadow: 0 0 0 3px rgba(79, 141, 104, .12); }
.result-row { display: flex; align-items: center; justify-content: space-between; margin-top: 18px; padding-top: 14px; border-top: 1px dashed #dce2de; color: #68716c; font-size: 13px; }
.result-row strong { color: #17211c; font-size: 16px; font-variant-numeric: tabular-nums; }
.demo-note { margin: 7px 0 0; color: #9ba39e; font-size: 11px; }
.dialog-error { margin: 10px 0 0; color: #c23c32; font-size: 12px; }
.dialog-actions { display: grid; grid-template-columns: .7fr 1.3fr; gap: 8px; margin-top: 20px; }
.dialog-actions button { min-height: 44px; border-radius: 8px; font-size: 14px; font-weight: 700; cursor: pointer; }
.cancel-button { border: 1px solid #dce2de; background: #fff; color: #56605a; }
.confirm-button { border: 1px solid #17211c; background: #17211c; color: #fff; }
.confirm-button.recharge { border-color: #23794b; background: #23794b; }
.dialog-actions button:disabled, .close-button:disabled, .quick-amounts button:disabled { opacity: .5; cursor: default; }
.wallet-dialog-fade-enter-active, .wallet-dialog-fade-leave-active { transition: opacity .16s ease; }
.wallet-dialog-fade-enter-from, .wallet-dialog-fade-leave-to { opacity: 0; }
@media (max-width: 420px) {
  .wallet-dialog-backdrop { align-items: end; padding: 0; }
  .wallet-dialog { width: 100%; max-height: calc(100vh - 22px); border-radius: 8px 8px 0 0; }
  .dialog-header, form { padding-right: 18px; padding-left: 18px; }
  .balance-summary { margin-right: 18px; margin-left: 18px; }
}
</style>
