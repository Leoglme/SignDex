<script setup lang="ts">
/**
 * Deux inputs « Couleur 1 / Couleur 2 » synchronisés au modèle parent (chaîne `#rrggbb` ou vide).
 *
 * - Préremplis avec les couleurs de la fiche client passées via `defaultColor1` / `defaultColor2`.
 * - L'utilisateur peut modifier indépendamment ; un bouton retour ramène la couleur du client.
 * - Champ texte (#hex) + sélecteur natif `<input type="color">` cliquable sur la pastille.
 * - On ne propage QUE les valeurs `#rrggbb` valides (le picker natif n'accepte que ce format).
 */
const props = defineProps<{
  color1: string
  color2: string
  defaultColor1: string | null
  defaultColor2: string | null
  disabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:color1', v: string): void
  (e: 'update:color2', v: string): void
}>()

const HEX_FULL_RE: RegExp = /^#[0-9a-fA-F]{6}$/
const HEX_SHORT_RE: RegExp = /^#[0-9a-fA-F]{3}$/

function expandShortHex(value: string): string {
  if (!HEX_SHORT_RE.test(value)) return value
  const r: string = value[1] || '0'
  const g: string = value[2] || '0'
  const b: string = value[3] || '0'
  return `#${r}${r}${g}${g}${b}${b}`.toLowerCase()
}

function pickerValueFor(text: string): string {
  const v: string = (text || '').trim()
  if (HEX_FULL_RE.test(v)) return v.toLowerCase()
  if (HEX_SHORT_RE.test(v)) return expandShortHex(v)
  return '#000000'
}

const color1Picker = computed<string>(() => pickerValueFor(props.color1))
const color2Picker = computed<string>(() => pickerValueFor(props.color2))

function onText(slot: 1 | 2, value: string): void {
  const v: string = value ?? ''
  if (slot === 1) emit('update:color1', v)
  else emit('update:color2', v)
}

function onPicker(slot: 1 | 2, value: string): void {
  const v: string = (value || '').toLowerCase()
  if (slot === 1) emit('update:color1', v)
  else emit('update:color2', v)
}

function reset(slot: 1 | 2): void {
  const fallback: string = (slot === 1 ? props.defaultColor1 : props.defaultColor2) || ''
  if (slot === 1) emit('update:color1', fallback)
  else emit('update:color2', fallback)
}

function isOverridden(slot: 1 | 2): boolean {
  const cur: string = (slot === 1 ? props.color1 : props.color2) || ''
  const def: string = (slot === 1 ? props.defaultColor1 : props.defaultColor2) || ''
  return cur.trim().toLowerCase() !== def.trim().toLowerCase()
}
</script>

<template>
  <div class="grid gap-3 sm:grid-cols-2">
    <UFormField
      v-for="slot in [1, 2] as const"
      :key="slot"
      :label="`Couleur ${slot}`"
      :description="
        slot === 1
          ? 'Préremplie avec la couleur 1 du client. Modifiable pour cette variante uniquement.'
          : 'Préremplie avec la couleur 2 du client. Modifiable pour cette variante uniquement.'
      "
      class="min-w-0"
    >
      <div class="flex items-center gap-2">
        <label
          class="ring-default focus-within:ring-primary relative size-9 shrink-0 cursor-pointer overflow-hidden rounded-md ring-1"
          :class="{ 'opacity-50 pointer-events-none': disabled }"
        >
          <span
            class="block size-full"
            :style="{ background: slot === 1 ? color1Picker : color2Picker }"
            aria-hidden="true"
          />
          <input
            type="color"
            class="absolute inset-0 size-full cursor-pointer opacity-0"
            :value="slot === 1 ? color1Picker : color2Picker"
            :disabled="disabled"
            @input="(e) => onPicker(slot, (e.target as HTMLInputElement).value)"
          />
        </label>

        <UInput
          class="min-w-0 flex-1"
          :model-value="slot === 1 ? color1 : color2"
          placeholder="#rrggbb"
          :disabled="disabled"
          @update:model-value="(v: string | number) => onText(slot, String(v ?? ''))"
        />

        <UButton
          v-if="isOverridden(slot)"
          color="neutral"
          variant="ghost"
          size="xs"
          icon="i-lucide-rotate-ccw"
          :title="`Revenir à la couleur ${slot} du client`"
          :disabled="disabled"
          @click="reset(slot)"
        />
      </div>
    </UFormField>
  </div>
</template>
