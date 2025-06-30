// frontend-user/postcss.config.js (正确配置)
export default {
  plugins: {
    '@tailwindcss/postcss': {}, // 使用新的、正确的插件名
    autoprefixer: {},
  },
}