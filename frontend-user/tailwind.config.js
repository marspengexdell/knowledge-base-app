/** @type {import('tailwindcss').Config} */
export default {
  // content 数组告诉 Tailwind要去哪些文件里寻找class名
  // 下面这个配置是标准且正确的，它会扫描所有src目录下的.vue和.js文件
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-blue': 'var(--salesforce-blue)',
        'brand-blue-dark': 'var(--salesforce-blue-dark)',
        'light': {
          DEFAULT: '#FFFFFF',
          'secondary': '#F7F7F8',
        },
        'dark': {
          DEFAULT: '#202123',
          'secondary': '#6B6B6B',
        },
        'border': '#E5E5E5',
      },
      boxShadow: {
        'glow': '0 0 15px 0 rgba(0, 112, 210, 0.25)',
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}