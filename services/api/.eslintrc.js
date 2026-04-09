/** @type {import('eslint').Linter.Config} */
module.exports = {
  root: true,
  extends: ['@zroky/eslint-config/node'],
  parserOptions: {
    project: './tsconfig.json',
  },
};
