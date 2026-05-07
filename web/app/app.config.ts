export default defineAppConfig({
  icon: {
    mode: 'svg',
  },
  ui: {
    colors: {
      primary: 'primary',
      neutral: 'zinc',
    },
    button: {
      slots: {
        base: 'cursor-pointer',
      },
    },
  },
})
