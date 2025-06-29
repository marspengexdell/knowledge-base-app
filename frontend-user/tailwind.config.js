/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'salesforce-blue': 'var(--salesforce-blue)',
        'salesforce-blue-dark': 'var(--salesforce-blue-dark)',
        'neutral': {
          100: 'var(--neutral-100)',
          95: 'var(--neutral-95)',
          80: 'var(--neutral-80)',
          50: 'var(--neutral-50)',
          10: 'var(--neutral-10)',
        },
      }
    },
  },
  // VVV --- 新增代码区域 --- VVV
  plugins: [
    require('@tailwindcss/typography'),
  ],
  // ^^^ --- 新增代码区域 --- ^^^
}
