FROM node:20-alpine AS build

WORKDIR /app

# 連 package-lock.json 一起複製，並且用 npm ci 而不是 npm install。
#
# npm install 會依 package.json 的 ^ 範圍去抓當下最新的相容版本，等於每次
# build 裝的東西都可能不一樣，repo 裡的 lock 檔形同虛設。npm ci 則是完全照
# lock 檔安裝，build 才有重現性；lock 檔和 package.json 對不上時它會直接
# 報錯，而不是默默裝一套別的。
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
