// frontend-admin/tailwind.config.js (修改后)

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  // 确保排版插件被正确引入
  plugins: [
    require('@tailwindcss/typography'),
  ],
}