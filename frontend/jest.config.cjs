module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  transform: {
    '^.+\.(ts|tsx|js|jsx)$': ['ts-jest', { // Handle TS, TSX, JS, JSX
      useESM: true, // Enable ES Modules for ts-jest
      tsconfig: '<rootDir>/tsconfig.test.json', // Point to tsconfig.test.json
      compilerOptions: { // Explicitly set compiler options for ts-jest
        jsx: 'react-jsx',
        esModuleInterop: true,
        allowSyntheticDefaultImports: true,
        // No explicit 'types' here, rely on tsconfig.test.json
      },
    }],
  },
  transformIgnorePatterns: [
    '/node_modules/(?!(?:.pnpm/)?(@apollo-client|@apollo/client|@apollo/client/testing|@apollo/react-hooks|@apollo/react-ssr|@apollo/react-components)/)',
  ],
  moduleNameMapper: {
    '\.(css|less|scss|sass)$': 'identity-obj-proxy', // Mock CSS imports
  },
  extensionsToTreatAsEsm: ['.ts', '.tsx'], // Treat .ts and .tsx as ESM
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'], // Include js, jsx
  collectCoverageFrom: [
    "src/**/*.{ts,tsx,js,jsx}",
    "!src/**/*.d.ts"
  ],
  coverageDirectory: "coverage",
};