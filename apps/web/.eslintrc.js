/** @type {import('eslint').Linter.Config} */
module.exports = {
  root: true,
  extends: ['@zroky/eslint-config/next'],
  parserOptions: {
    project: './tsconfig.json',
  },
};
