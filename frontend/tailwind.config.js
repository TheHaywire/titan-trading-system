/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                titan: {
                    dark: '#0B0F19',     // Deepest background
                    panel: '#151B2B',    // Card background
                    accent: '#3B82F6',   // Primary Blue
                    success: '#10B981',  // Neon Green
                    danger: '#EF4444',   // Neon Red
                    gold: '#F59E0B',     // Warning/Gold
                }
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            }
        },
    },
    plugins: [],
}
