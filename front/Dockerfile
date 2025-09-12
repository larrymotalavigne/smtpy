### STAGE 1: Base ###
ARG BASE_APP_IMAGE=node:lts-alpine
ARG APP_IMAGE=nginx:latest

FROM $BASE_APP_IMAGE AS base
WORKDIR /usr/src/app
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps
COPY . .
RUN npm run build

# Install gzip compression tools and compress the build output
RUN apk add --no-cache gzip \
 && find /usr/src/app/dist -type f -name '*.js' -exec gzip -k -f {} \; \
 && find /usr/src/app/dist -type f -name '*.css' -exec gzip -k -f {} \;

### STAGE 2: Run ###
FROM $APP_IMAGE
RUN apt-get update && apt-get -y upgrade && apt-get clean && apt-get autoclean -y && rm -rf /var/lib/apt/list/*

COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=base /usr/src/app/dist/smtpy-frontend /usr/share/nginx/html
