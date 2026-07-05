<template>
  <UDashboardPanel id="aide" :ui="{ body: 'p-3 sm:p-6 bg-neutral-100 dark:bg-transparent' }">
    <template #header>
      <UDashboardNavbar title="Aide">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="w-full space-y-8 pb-6">
        <!-- Contenu du dossier (compact) -->
        <section>
          <h2 class="text-highlighted mb-3 text-base font-semibold">Ce que contient le dossier</h2>
          <div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            <div v-for="f in folder" :key="f.name" class="flex items-center gap-3 rounded-xl px-3 py-2.5" :class="cardClass">
              <span class="flex size-8 shrink-0 items-center justify-center rounded-lg" :style="{ backgroundColor: f.color }">
                <UIcon :name="f.icon" class="size-4 text-white" />
              </span>
              <div class="min-w-0">
                <p class="text-highlighted text-sm font-medium">{{ f.name }}</p>
                <p class="text-muted truncate text-xs">{{ f.short }}</p>
              </div>
            </div>
          </div>
        </section>

        <!-- Installer une signature -->
        <section>
          <h2 class="text-highlighted mb-3 text-base font-semibold">Installer une signature</h2>

          <div class="rounded-2xl p-5 sm:p-6" :class="cardClass">
            <div class="bg-elevated mb-6 flex max-w-md gap-1.5 rounded-xl p-1.5">
              <button
                v-for="c in clients"
                :key="c.key"
                type="button"
                class="flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors"
                :class="tab === c.key ? 'bg-default text-highlighted shadow-sm' : 'text-muted hover:text-highlighted'"
                @click="tab = c.key"
              >
                <PortalMailIcon :client="c.key" :px="20" />
                <span class="hidden sm:inline">{{ c.label }}</span>
              </button>
            </div>

            <div class="flex items-center gap-3">
              <PortalMailIcon :client="active.key" :px="34" />
              <div>
                <p class="text-highlighted font-semibold">{{ active.title }}</p>
                <p v-if="active.hint" class="text-muted text-sm">{{ active.hint }}</p>
              </div>
            </div>

            <ol class="mt-5 max-w-3xl space-y-4">
              <li v-for="(step, i) in active.steps" :key="i" class="flex gap-3">
                <span class="bg-primary/10 text-primary flex size-7 shrink-0 items-center justify-center rounded-full text-sm font-semibold">
                  {{ i + 1 }}
                </span>
                <span class="text-muted pt-0.5 text-sm leading-relaxed [&_a]:text-primary [&_a]:font-medium [&_a]:underline [&_b]:text-highlighted" v-html="step" />
              </li>
            </ol>
          </div>
        </section>

        <!-- Contact -->
        <p class="text-muted flex items-center gap-2 text-sm">
          <UIcon name="i-lucide-mail" class="size-4 shrink-0" />
          <span>Un doute sur l'installation ? Écrivez à <a class="text-primary font-medium underline" href="mailto:contact@dibodev.fr">contact@dibodev.fr</a>.</span>
        </p>
      </div>
    </template>
  </UDashboardPanel>
</template>

<script setup lang="ts">
import type { ComputedRef } from 'vue'

type ClientKey = 'outlook' | 'gmail' | 'apple'

interface ClientHelp {
  key: ClientKey
  label: string
  title: string
  hint?: string
  steps: string[]
}

definePageMeta({ layout: 'portal' })
useHead({ title: 'Aide' })

const cardClass = 'bg-default ring-1 ring-default shadow-sm dark:bg-elevated/60 dark:shadow-none'

const folder = [
  { name: 'HTML/', icon: 'i-lucide-code-2', short: 'Liens cliquables (Outlook, Gmail)', color: '#0ea5e9' },
  { name: 'apple-mail/', icon: 'i-lucide-mail', short: 'Import dans Mail (macOS)', color: '#6366f1' },
  { name: 'PNG/ · JPG/', icon: 'i-lucide-image', short: 'Image (liens non cliquables)', color: '#f59e0b' },
  { name: 'EXEMPLES/', icon: 'i-lucide-eye', short: 'Aperçu du rendu final', color: '#22c55e' },
]

const clients: ClientHelp[] = [
  {
    key: 'outlook',
    label: 'Outlook',
    title: 'Outlook (Windows, version classique)',
    steps: [
      'Ouvrez le fichier <b>HTML</b> de la personne dans un navigateur (double-clic sur le fichier).',
      'Sélectionnez tout (<b>Ctrl + A</b>) puis copiez (<b>Ctrl + C</b>).',
      'Dans Outlook : <b>Fichier › Options › Courrier › Signatures…</b>',
      'Cliquez sur <b>Nouveau</b>, nommez la signature, placez le curseur dans la zone d\'édition, puis collez (<b>Ctrl + V</b>).',
      'Choisissez cette signature pour les <b>nouveaux messages</b> et les <b>réponses</b>, puis <b>OK</b>.',
    ],
  },
  {
    key: 'gmail',
    label: 'Gmail',
    title: 'Gmail',
    hint: 'Gmail nécessite une étape par le site « Probador » pour garder les liens cliquables.',
    steps: [
      'Ouvrez le fichier <b>HTML</b> avec un éditeur de texte (le <b>Bloc-notes</b>), puis <b>Ctrl + A</b> puis <b>Ctrl + C</b> — vous copiez le code.',
      'Ouvrez le site Probador : <a href="https://solamentecodigoshtmlbybcn.jimdofree.com/probador-de-html/" target="_blank" rel="noopener">solamentecodigoshtmlbybcn.jimdofree.com/probador-de-html</a>. Collez le code dans la zone de texte et lancez la conversion : un nouvel onglet affiche l\'aperçu de la signature.',
      'Sur cet aperçu, sélectionnez tout (<b>Ctrl + A</b>) puis copiez (<b>Ctrl + C</b>).',
      'Dans Gmail : <b>⚙️ › Voir tous les paramètres › Général › Signature › Créer</b>. Nommez-la, collez dans la zone (<b>Ctrl + V</b>).',
      'Descendez en bas de page et cliquez sur <b>Enregistrer les modifications</b>.',
    ],
  },
  {
    key: 'apple',
    label: 'Apple Mail',
    title: 'Apple Mail (macOS)',
    steps: [
      'Dans Mail : <b>Mail › Réglages › Signatures</b>, sélectionnez le compte, cliquez sur <b>+</b> pour créer une signature (contenu quelconque), puis <b>quittez Mail</b> (<b>Cmd + Q</b>).',
      'Finder → menu <b>Aller</b> en maintenant <b>Option ⌥</b> → <b>Bibliothèque</b>, puis ouvrez <b>Mail › V10 › MailData › Signatures</b> (ou <b>Cmd + Maj + G</b> et collez <b>~/Library/Mail/V10/MailData/Signatures</b>).',
      'Clic droit sur le fichier <b>.mailsignature</b> → <b>Ouvrir avec › TextEdit</b>, tout sélectionner (<b>Cmd + A</b>) et supprimer.',
      'Ouvrez notre <b>signature.mailsignature</b> (dossier <b>apple-mail</b>) avec TextEdit, copiez tout (<b>Cmd + A</b> puis <b>Cmd + C</b>), collez dans le fichier de votre Mac et enregistrez (<b>Cmd + S</b>).',
      'Finder → clic droit sur ce fichier → <b>Lire les informations</b> (<b>Cmd + I</b>) → cochez <b>Verrouillé</b> (sinon Mail écrase la signature).',
      'Rouvrez Mail → <b>Réglages › Signatures</b> et choisissez votre signature en bas.',
    ],
  },
]

const tab = ref<ClientKey>('outlook')
const active: ComputedRef<ClientHelp> = computed(() => clients.find(c => c.key === tab.value) || clients[0]!)
</script>
