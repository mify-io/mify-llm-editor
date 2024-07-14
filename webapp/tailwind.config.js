module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
        colors: {
            'chat-background': '#2D3748',
            'chat-frame': '#0A121E',
            'llm-message': '#112230',
            'user-message': '#5555aa',
            'send-button': {
                '100': '#556689',
                '200': '#6677ab',
            },
            'delete-button': {
                '100': '#490407',
                '200': '#bc1e28',
            },
            'new-button': {
                '100': '#4466cc',
                '200': '#4477ff',
            },
            'active-project': '#002244',
        },

    },
  },
  plugins: [],
}
