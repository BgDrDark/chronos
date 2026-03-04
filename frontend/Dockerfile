FROM node:20-alpine

WORKDIR /app

# Инсталираме 'serve' за сервиране на статични файлове
RUN npm install -g serve

# Копираме и инсталираме зависимостите
COPY package*.json ./
RUN npm install

# Копираме сорс кода
COPY . .

# Приемаме URL на API-то като аргумент и билдваме
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Експозваме порт 3000
EXPOSE 3000

# Стартираме сървъра в Single Page Application режим (-s)
CMD ["serve", "-s", "dist", "-l", "3000"]