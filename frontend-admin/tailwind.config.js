/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Salesforce Lightning Design System 颜色定义
        'salesforce-blue': {
          DEFAULT: '#0070D2', // 品牌主色，用于按钮、链接等
          dark: '#005FB2',    // Hover 状态
        },
        'neutral': {
          100: '#FFFFFF', // 卡片背景
          95: '#F3F3F3',  // 页面背景
          80: '#E0E0E0',  // 边框、分割线
          50: '#999999',  // 次要文字、图标
          10: '#181818',  // 主要文字
        },
        'destructive': {
          DEFAULT: '#EA001E', // 删除等危险操作
          dark: '#C23934',
        },
        'success': '#04844B',
      },
    },
  },
  plugins: [],
}
