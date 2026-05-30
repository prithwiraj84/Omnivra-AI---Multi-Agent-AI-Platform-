module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  extends: ['eslint:recommended', 'plugin:@typescript-eslint/recommended', 'plugin:react-hooks/recommended'],
  ignorePatterns: ['dist', '.eslintrc.cjs', 'vite.config.ts'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
  },
  overrides: [
    {
      // UI primitives commonly co-export cva variant fns (buttonVariants, …)
      // alongside the component; fast-refresh still works in practice.
      files: ['src/components/ui/**/*.{ts,tsx}'],
      rules: { 'react-refresh/only-export-components': 'off' },
    },
  ],
}
